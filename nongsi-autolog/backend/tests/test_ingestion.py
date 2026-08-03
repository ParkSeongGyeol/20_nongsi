from __future__ import annotations

import json

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.models.sensor_reading import SensorReading
from app.services.telemetry import IngestStatus, TelemetryIngestor


@pytest.fixture()
def ingestor() -> TelemetryIngestor:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    return TelemetryIngestor(sessions)


def valid_payload(sequence: int = 101) -> str:
    return json.dumps(
        {
            "device_id": "sprayer-001",
            "timestamp": "2026-08-03T09:00:00+09:00",
            "sequence": sequence,
            "imu": {
                "ax": 0.12,
                "ay": -0.08,
                "az": 1.01,
                "gx": 1.2,
                "gy": 0.4,
                "gz": -0.7,
                "rms": 0.31,
            },
            "pump": {"current_a": 2.7, "is_running": True},
            "pressure": {"bar": 8.4, "valid": True},
            "battery": {"voltage": 4.02, "percent": 82},
            "signal": {"rssi": -58},
        }
    )


def test_valid_payload_is_stored(ingestor: TelemetryIngestor) -> None:
    result = ingestor.ingest_json(valid_payload(), topic_device_id="sprayer-001")

    assert result.status is IngestStatus.STORED
    with ingestor._sessions() as session:
        reading = session.scalar(select(SensorReading))
        assert reading is not None
        assert reading.pressure_bar == pytest.approx(8.4)
        assert reading.quality_flag == "valid"
        assert reading.recorded_at.utcoffset() is not None
        assert reading.recorded_at.isoformat() == "2026-08-03T00:00:00+00:00"


def test_duplicate_device_sequence_is_ignored(ingestor: TelemetryIngestor) -> None:
    first = ingestor.ingest_json(valid_payload())
    duplicate = ingestor.ingest_json(valid_payload())

    assert first.status is IngestStatus.STORED
    assert duplicate.status is IngestStatus.DUPLICATE
    with ingestor._sessions() as session:
        count = session.scalar(select(func.count()).select_from(SensorReading))
        assert count == 1


def test_timestamp_without_timezone_is_rejected(ingestor: TelemetryIngestor) -> None:
    payload = json.loads(valid_payload())
    payload["timestamp"] = "2026-08-03T09:00:00"

    result = ingestor.ingest_json(json.dumps(payload))

    assert result.status is IngestStatus.INVALID


def test_topic_device_mismatch_is_rejected(ingestor: TelemetryIngestor) -> None:
    result = ingestor.ingest_json(valid_payload(), topic_device_id="sprayer-999")

    assert result.status is IngestStatus.INVALID


def test_missing_pressure_is_stored_with_quality_flag(
    ingestor: TelemetryIngestor,
) -> None:
    payload = json.loads(valid_payload())
    del payload["pressure"]

    result = ingestor.ingest_json(json.dumps(payload))

    assert result.status is IngestStatus.STORED
    with ingestor._sessions() as session:
        reading = session.scalar(select(SensorReading))
        assert reading is not None
        assert reading.pressure_bar is None
        assert reading.quality_flag == "missing_pressure"
