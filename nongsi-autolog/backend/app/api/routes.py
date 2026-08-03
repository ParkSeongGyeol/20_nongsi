from __future__ import annotations

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.db.database import session_factory
from app.models.sensor_reading import SensorReading

router = APIRouter(prefix="/api")


def _reading_response(reading: SensorReading) -> dict[str, object]:
    return {
        "id": reading.id,
        "device_id": reading.device_id,
        "sequence": reading.sequence,
        "timestamp": reading.recorded_at.isoformat(),
        "received_at": reading.received_at.isoformat(),
        "imu_rms": reading.imu_rms,
        "pump_current_a": reading.pump_current_a,
        "pressure_bar": reading.pressure_bar,
        "pressure_valid": (
            bool(reading.pressure_valid)
            if reading.pressure_valid is not None
            else None
        ),
        "battery_voltage": reading.battery_voltage,
        "battery_percent": reading.battery_percent,
        "signal_rssi": reading.signal_rssi,
        "source": reading.source,
        "version": reading.version,
        "quality_flag": reading.quality_flag,
    }


@router.get("/readings")
def list_readings(
    limit: int = Query(default=20, ge=1, le=500),
) -> dict[str, object]:
    with session_factory() as session:
        total = session.scalar(select(func.count()).select_from(SensorReading)) or 0
        readings = session.scalars(
            select(SensorReading)
            .order_by(SensorReading.id.desc())
            .limit(limit)
        ).all()
    return {
        "total": total,
        "items": [_reading_response(reading) for reading in readings],
    }


@router.get("/readings/latest")
def latest_reading() -> dict[str, object] | None:
    with session_factory() as session:
        reading = session.scalar(
            select(SensorReading).order_by(SensorReading.id.desc()).limit(1)
        )
    return None if reading is None else _reading_response(reading)

