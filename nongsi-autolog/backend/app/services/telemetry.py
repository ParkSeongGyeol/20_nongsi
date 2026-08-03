from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import StrEnum

from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.models.sensor_reading import SensorReading
from app.schemas.telemetry import TelemetryPayload

logger = logging.getLogger(__name__)


class IngestStatus(StrEnum):
    STORED = "stored"
    DUPLICATE = "duplicate"
    INVALID = "invalid"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class IngestResult:
    status: IngestStatus
    detail: str
    reading_id: int | None = None


class TelemetryIngestor:
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def ingest_json(
        self,
        raw_payload: str,
        *,
        topic_device_id: str | None = None,
    ) -> IngestResult:
        try:
            payload = TelemetryPayload.model_validate_json(raw_payload)
        except ValidationError as exc:
            logger.warning("Rejected invalid telemetry payload: %s", exc)
            return IngestResult(IngestStatus.INVALID, "payload_validation_failed")

        if topic_device_id is not None and payload.device_id != topic_device_id:
            logger.warning(
                "Rejected telemetry with topic/payload device mismatch: topic=%s payload=%s",
                topic_device_id,
                payload.device_id,
            )
            return IngestResult(IngestStatus.INVALID, "device_id_mismatch")

        reading = SensorReading(
            device_id=payload.device_id,
            sequence=payload.sequence,
            recorded_at=payload.timestamp,
            imu_rms=payload.imu.rms if payload.imu else None,
            pump_current_a=payload.pump.current_a if payload.pump else None,
            pressure_bar=payload.pressure.bar if payload.pressure else None,
            pressure_valid=(int(payload.pressure.valid) if payload.pressure else None),
            battery_voltage=payload.battery.voltage if payload.battery else None,
            battery_percent=payload.battery.percent if payload.battery else None,
            signal_rssi=payload.signal.rssi if payload.signal else None,
            raw_payload=raw_payload,
            source="mqtt",
            version="1.0",
            quality_flag=payload.quality_flag,
        )

        with self._sessions() as session:
            try:
                session.add(reading)
                session.commit()
            except IntegrityError:
                session.rollback()
                logger.info(
                    "Ignored duplicate telemetry: device=%s sequence=%s",
                    payload.device_id,
                    payload.sequence,
                )
                return IngestResult(IngestStatus.DUPLICATE, "duplicate_sequence")
            except SQLAlchemyError:
                session.rollback()
                logger.exception("Failed to persist telemetry")
                return IngestResult(IngestStatus.ERROR, "database_error")

        logger.info(
            "Stored telemetry: id=%s device=%s sequence=%s rms=%s current_a=%s pressure_bar=%s quality=%s",
            reading.id,
            reading.device_id,
            reading.sequence,
            reading.imu_rms,
            reading.pump_current_a,
            reading.pressure_bar,
            reading.quality_flag,
        )
        return IngestResult(IngestStatus.STORED, "stored", reading.id)

