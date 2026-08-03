from __future__ import annotations

import json
import logging
import threading
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from statistics import fmean

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.models.device_state import DeviceStateReading
from app.schemas.telemetry import TelemetryPayload
from app.services.event_detection.configuration import (
    DetectionConfig,
    DeviceConfigRepository,
)

logger = logging.getLogger(__name__)


class WorkState(StrEnum):
    OFFLINE = "OFFLINE"
    IDLE = "IDLE"
    MOVING = "MOVING"
    SPRAYING = "SPRAYING"
    PRESSURE_FAULT = "PRESSURE_FAULT"
    SENSOR_FAULT = "SENSOR_FAULT"
    SESSION_FINISHED = "SESSION_FINISHED"


@dataclass(frozen=True, slots=True)
class FeatureSample:
    vibration_rms: float | None
    pump_current_a: float | None
    pressure_bar: float | None


@dataclass(slots=True)
class DeviceRuntime:
    window_size: int
    samples: deque[FeatureSample] = field(default_factory=deque)
    stable_state: WorkState = WorkState.OFFLINE
    candidate_state: WorkState | None = None
    candidate_since: datetime | None = None
    last_timestamp: datetime | None = None


@dataclass(frozen=True, slots=True)
class DetectionDecision:
    state: WorkState
    raw_state: WorkState
    previous_state: WorkState
    changed: bool
    confidence: float
    reason: str
    features: dict[str, float | None]
    quality_flag: str
    config_version: str


def _average(values: list[float | None]) -> float | None:
    present = [value for value in values if value is not None]
    return fmean(present) if present else None


class StateDetectionService:
    """Explainable rule-based baseline; this is not a trained AI classifier."""

    def __init__(
        self,
        sessions: sessionmaker[Session],
        configs: DeviceConfigRepository,
    ) -> None:
        self._sessions = sessions
        self._configs = configs
        self._runtimes: dict[str, DeviceRuntime] = {}
        self._lock = threading.Lock()

    def process(
        self,
        payload: TelemetryPayload,
        reading_id: int,
    ) -> DetectionDecision:
        config, config_version = self._configs.get(payload.device_id)
        with self._lock:
            runtime = self._runtime(payload.device_id, config.window_size)
            sample = FeatureSample(
                vibration_rms=payload.imu.rms if payload.imu else None,
                pump_current_a=payload.pump.current_a if payload.pump else None,
                pressure_bar=(
                    payload.pressure.bar
                    if payload.pressure and payload.pressure.valid
                    else None
                ),
            )
            runtime.samples.append(sample)
            while len(runtime.samples) > config.window_size:
                runtime.samples.popleft()

            features = {
                "vibration_rms_avg": _average(
                    [item.vibration_rms for item in runtime.samples]
                ),
                "pump_current_a_avg": _average(
                    [item.pump_current_a for item in runtime.samples]
                ),
                "pressure_bar_avg": _average(
                    [item.pressure_bar for item in runtime.samples]
                ),
            }
            raw_state, reason = self._classify(payload, features, runtime, config)
            decision = self._stabilize(
                payload,
                features,
                raw_state,
                reason,
                runtime,
                config,
                config_version,
            )

        self._persist(reading_id, payload.device_id, decision)
        return decision

    def _runtime(self, device_id: str, window_size: int) -> DeviceRuntime:
        runtime = self._runtimes.get(device_id)
        if runtime is None:
            runtime = DeviceRuntime(window_size=window_size)
            self._runtimes[device_id] = runtime
        elif runtime.window_size != window_size:
            runtime.window_size = window_size
            runtime.samples = deque(list(runtime.samples)[-window_size:])
        return runtime

    @staticmethod
    def _classify(
        payload: TelemetryPayload,
        features: dict[str, float | None],
        runtime: DeviceRuntime,
        config: DetectionConfig,
    ) -> tuple[WorkState, str]:
        if payload.pressure is None or not payload.pressure.valid:
            return WorkState.SENSOR_FAULT, "pressure sensor missing or invalid"
        if payload.pump is None:
            return WorkState.SENSOR_FAULT, "pump current sensor missing"
        if payload.imu is None:
            return WorkState.SENSOR_FAULT, "IMU sensor missing"

        current = features["pump_current_a_avg"] or 0.0
        vibration = features["vibration_rms_avg"] or 0.0
        pressure = features["pressure_bar_avg"] or 0.0

        pump_was_active = runtime.stable_state in {
            WorkState.SPRAYING,
            WorkState.PRESSURE_FAULT,
        }
        current_threshold = (
            config.pump_current_off_a
            if pump_was_active
            else config.pump_current_on_a
        )
        pump_active = current >= current_threshold

        moving_was_active = runtime.stable_state is WorkState.MOVING
        vibration_threshold = (
            config.vibration_moving_off_rms
            if moving_was_active
            else config.vibration_moving_on_rms
        )
        moving = vibration >= vibration_threshold

        if pump_active:
            pressure_threshold = (
                config.pressure_fault_recovery_bar
                if runtime.stable_state is WorkState.PRESSURE_FAULT
                else config.pressure_spray_min_bar
            )
            if pressure < pressure_threshold:
                return (
                    WorkState.PRESSURE_FAULT,
                    f"pump active but pressure {pressure:.3f} bar is below "
                    f"{pressure_threshold:.2f} bar",
                )
            return WorkState.SPRAYING, "pump current and pressure indicate spraying"
        if moving:
            return WorkState.MOVING, "vibration exceeds moving threshold"
        return WorkState.IDLE, "pump current and vibration are below thresholds"

    @staticmethod
    def _stabilize(
        payload: TelemetryPayload,
        features: dict[str, float | None],
        raw_state: WorkState,
        reason: str,
        runtime: DeviceRuntime,
        config: DetectionConfig,
        config_version: str,
    ) -> DetectionDecision:
        event_time = payload.timestamp.astimezone(timezone.utc)
        if runtime.last_timestamp and event_time < runtime.last_timestamp:
            event_time = runtime.last_timestamp
        runtime.last_timestamp = event_time
        previous_state = runtime.stable_state
        changed = False

        if raw_state is runtime.stable_state:
            runtime.candidate_state = None
            runtime.candidate_since = None
        elif runtime.candidate_state is not raw_state:
            runtime.candidate_state = raw_state
            runtime.candidate_since = event_time
        elif runtime.candidate_since is not None:
            candidate_age = (event_time - runtime.candidate_since).total_seconds()
            if candidate_age >= config.minimum_state_duration_seconds:
                runtime.stable_state = raw_state
                runtime.candidate_state = None
                runtime.candidate_since = None
                changed = True

        completeness = sum(value is not None for value in features.values()) / 3
        agreement = 1.0 if runtime.stable_state is raw_state else 0.0
        confidence = round(min(0.95, 0.55 + 0.25 * completeness + 0.15 * agreement), 2)
        quality_flag = payload.quality_flag
        if raw_state is WorkState.SENSOR_FAULT:
            quality_flag = "sensor_fault"

        return DetectionDecision(
            state=runtime.stable_state,
            raw_state=raw_state,
            previous_state=previous_state,
            changed=changed,
            confidence=confidence,
            reason=reason,
            features=features,
            quality_flag=quality_flag,
            config_version=config_version,
        )

    def _persist(
        self,
        reading_id: int,
        device_id: str,
        decision: DetectionDecision,
    ) -> None:
        row = DeviceStateReading(
            reading_id=reading_id,
            device_id=device_id,
            state=decision.state.value,
            raw_state=decision.raw_state.value,
            previous_state=decision.previous_state.value,
            changed=int(decision.changed),
            confidence=decision.confidence,
            reason=decision.reason,
            features_json=json.dumps(decision.features, separators=(",", ":")),
            source="rule_based",
            version=decision.config_version,
            quality_flag=decision.quality_flag,
        )
        with self._sessions() as session:
            try:
                session.add(row)
                session.commit()
            except SQLAlchemyError:
                session.rollback()
                logger.exception(
                    "Failed to persist state decision for reading=%s",
                    reading_id,
                )
                raise

        if decision.changed:
            logger.info(
                "Device state changed: device=%s %s -> %s confidence=%.2f",
                device_id,
                decision.previous_state,
                decision.state,
                decision.confidence,
            )
