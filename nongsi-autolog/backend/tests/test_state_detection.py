from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base
from app.models.device_state import DeviceStateReading
from app.schemas.telemetry import TelemetryPayload
from app.services.event_detection import (
    DeviceConfigRepository,
    StateDetectionService,
    WorkState,
)


def write_config(tmp_path, **overrides: object) -> DeviceConfigRepository:
    default = {
        "window_size": 1,
        "minimum_state_duration_seconds": 1.0,
        "pump_current_on_a": 1.0,
        "pump_current_off_a": 0.6,
        "vibration_moving_on_rms": 0.35,
        "vibration_moving_off_rms": 0.25,
        "pressure_spray_min_bar": 5.0,
        "pressure_fault_recovery_bar": 5.5,
    }
    path = tmp_path / "thresholds.json"
    path.write_text(
        json.dumps(
            {
                "version": "test-1",
                "default": {**default, **overrides},
                "devices": {},
            }
        ),
        encoding="utf-8",
    )
    return DeviceConfigRepository(path)


@pytest.fixture()
def detector(tmp_path) -> tuple[StateDetectionService, sessionmaker]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    return StateDetectionService(sessions, write_config(tmp_path)), sessions


def payload(
    second: int,
    *,
    current: float,
    pressure: float | None,
    vibration: float,
) -> TelemetryPayload:
    timestamp = datetime(2026, 8, 3, tzinfo=timezone.utc) + timedelta(seconds=second)
    document: dict[str, object] = {
        "device_id": "sprayer-001",
        "timestamp": timestamp.isoformat(),
        "sequence": second,
        "imu": {
            "ax": 0,
            "ay": 0,
            "az": 1,
            "gx": 0,
            "gy": 0,
            "gz": 0,
            "rms": vibration,
        },
        "pump": {"current_a": current, "is_running": current >= 1},
        "battery": {"voltage": 4.0, "percent": 80},
        "signal": {"rssi": -55},
    }
    if pressure is not None:
        document["pressure"] = {"bar": pressure, "valid": True}
    return TelemetryPayload.model_validate(document)


def process(
    detector: StateDetectionService,
    second: int,
    *,
    current: float,
    pressure: float | None,
    vibration: float,
):
    return detector.process(
        payload(
            second,
            current=current,
            pressure=pressure,
            vibration=vibration,
        ),
        reading_id=second + 1,
    )


def test_state_transitions_are_stabilized_with_minimum_duration(
    detector: tuple[StateDetectionService, sessionmaker],
) -> None:
    service, sessions = detector

    assert process(service, 0, current=0.1, pressure=0.2, vibration=0.05).state is WorkState.OFFLINE
    idle = process(service, 1, current=0.1, pressure=0.2, vibration=0.05)
    assert idle.state is WorkState.IDLE
    assert idle.changed

    process(service, 2, current=0.1, pressure=0.2, vibration=0.6)
    moving = process(service, 3, current=0.1, pressure=0.2, vibration=0.6)
    assert moving.state is WorkState.MOVING

    process(service, 4, current=2.7, pressure=8.0, vibration=0.6)
    spraying = process(service, 5, current=2.7, pressure=8.0, vibration=0.6)
    assert spraying.state is WorkState.SPRAYING

    process(service, 6, current=2.7, pressure=3.0, vibration=0.6)
    fault = process(service, 7, current=2.7, pressure=3.0, vibration=0.6)
    assert fault.state is WorkState.PRESSURE_FAULT
    assert "below" in fault.reason

    with sessions() as session:
        count = session.scalar(select(func.count()).select_from(DeviceStateReading))
        assert count == 8


def test_pump_hysteresis_keeps_spraying_between_on_and_off_thresholds(
    detector: tuple[StateDetectionService, sessionmaker],
) -> None:
    service, _ = detector
    process(service, 0, current=2.7, pressure=8.0, vibration=0.6)
    process(service, 1, current=2.7, pressure=8.0, vibration=0.6)

    decision = process(service, 2, current=0.8, pressure=8.0, vibration=0.1)

    assert decision.state is WorkState.SPRAYING
    assert decision.raw_state is WorkState.SPRAYING


def test_missing_pressure_transitions_to_sensor_fault(
    detector: tuple[StateDetectionService, sessionmaker],
) -> None:
    service, _ = detector
    process(service, 0, current=0.1, pressure=0.2, vibration=0.05)
    process(service, 1, current=0.1, pressure=0.2, vibration=0.05)
    first_missing = process(service, 2, current=2.7, pressure=None, vibration=0.6)
    fault = process(service, 3, current=2.7, pressure=None, vibration=0.6)

    assert first_missing.state is WorkState.IDLE
    assert fault.state is WorkState.SENSOR_FAULT
    assert fault.quality_flag == "sensor_fault"


def test_invalid_hysteresis_config_is_rejected(tmp_path) -> None:
    repository = write_config(
        tmp_path,
        pump_current_on_a=0.5,
        pump_current_off_a=0.8,
    )

    with pytest.raises(ValueError, match="pump_current_on_a"):
        repository.get("sprayer-001")

