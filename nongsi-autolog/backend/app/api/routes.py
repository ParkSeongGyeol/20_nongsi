from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select

from app.core.config import settings
from app.db.database import session_factory
from app.models.device_state import DeviceStateReading
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


def _device_snapshot(device_id: str) -> dict[str, object] | None:
    with session_factory() as session:
        reading = session.scalar(
            select(SensorReading)
            .where(SensorReading.device_id == device_id)
            .order_by(SensorReading.id.desc())
            .limit(1)
        )
        if reading is None:
            return None
        state_row = session.scalar(
            select(DeviceStateReading)
            .where(DeviceStateReading.device_id == device_id)
            .order_by(DeviceStateReading.id.desc())
            .limit(1)
        )

    now = datetime.now(timezone.utc)
    received_at = reading.received_at
    if received_at.tzinfo is None:
        received_at = received_at.replace(tzinfo=timezone.utc)
    age_seconds = max(0.0, (now - received_at).total_seconds())
    online = age_seconds <= settings.device_online_timeout_seconds

    state = state_row.state if state_row else "OFFLINE"
    reason = state_row.reason if state_row else "state decision is not available"
    if not online:
        state = "OFFLINE"
        reason = (
            f"no telemetry for {age_seconds:.1f} seconds "
            f"(timeout {settings.device_online_timeout_seconds}s)"
        )

    return {
        "device_id": device_id,
        "online": online,
        "last_seen_seconds": round(age_seconds, 1),
        "state": state,
        "raw_state": state_row.raw_state if state_row else "OFFLINE",
        "previous_state": state_row.previous_state if state_row else "OFFLINE",
        "state_changed": bool(state_row.changed) if state_row else False,
        "confidence": state_row.confidence if state_row else 0.0,
        "reason": reason,
        "features": json.loads(state_row.features_json) if state_row else {},
        "state_source": state_row.source if state_row else "rule_based",
        "state_version": state_row.version if state_row else "unknown",
        "state_id": state_row.id if state_row else None,
        "reading": _reading_response(reading),
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


@router.get("/devices/{device_id}/snapshot")
def device_snapshot(device_id: str) -> dict[str, object]:
    snapshot = _device_snapshot(device_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="device telemetry not found")
    return snapshot


@router.get("/devices/{device_id}/live")
async def device_live(device_id: str, request: Request) -> StreamingResponse:
    async def event_stream():
        last_signature: tuple[object, object] | None = None
        last_keepalive = 0.0
        loop = asyncio.get_running_loop()
        while not await request.is_disconnected():
            snapshot = await asyncio.to_thread(_device_snapshot, device_id)
            now = loop.time()
            if snapshot is not None:
                reading = snapshot["reading"]
                signature = (reading["id"], snapshot["state_id"])
                if signature != last_signature:
                    yield (
                        "event: telemetry\n"
                        f"data: {json.dumps(snapshot, ensure_ascii=False)}\n\n"
                    )
                    last_signature = signature
                    last_keepalive = now
            if now - last_keepalive >= 15:
                yield ": keep-alive\n\n"
                last_keepalive = now
            await asyncio.sleep(settings.state_stream_poll_seconds)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
