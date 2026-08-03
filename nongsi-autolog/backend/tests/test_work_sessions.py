from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base
from app.models.device_state import DeviceStateReading
from app.models.sensor_reading import SensorReading
from app.schemas.sessions import LocationRequest, SessionRequest
from app.services.flow import interpolate_flow_lpm
from app.services.risk import assess_risk
from app.services.weather import CachedWeatherProvider, MockWeatherProvider
from app.services.weather.kma import latitude_longitude_to_grid
from app.services.work_sessions import (
    SessionConflict,
    WorkSessionService,
    seed_demo_data,
)


START = datetime(2026, 8, 3, 7, 0, tzinfo=timezone.utc)


class FailingMockWeatherProvider(MockWeatherProvider):
    fail = False

    async def get_current_weather(self, latitude: float, longitude: float):
        if self.fail:
            raise ConnectionError("weather unavailable")
        return await super().get_current_weather(latitude, longitude)


@pytest.fixture()
def session_service() -> tuple[WorkSessionService, sessionmaker]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    seed_demo_data(sessions)
    return WorkSessionService(sessions, MockWeatherProvider()), sessions


def start_request(**overrides: object) -> SessionRequest:
    document = {
        "farm_id": "FARM-001",
        "parcel_id": "PARCEL-001",
        "device_id": "sprayer-001",
        "crop": "open_field_citrus",
        "event_type": "spraying",
        "input_material_id": "WATER-DEMO",
        "product_name": "물(시연용)",
        "dilution_ratio": 500,
        "nozzle_id": "nozzle-A",
        "location_mode": "demo",
        "start_time": START.isoformat(),
    }
    document.update(overrides)
    return SessionRequest.model_validate(document)


def add_sensor_state_rows(sessions: sessionmaker) -> None:
    values = [
        ("IDLE", 0.1, 0.2),
        ("SPRAYING", 2.7, 5.0),
        ("SPRAYING", 2.7, 7.0),
        ("PRESSURE_FAULT", 2.7, 3.0),
        ("SPRAYING", 2.7, 9.0),
    ]
    with sessions() as session:
        for index, (state, current, pressure) in enumerate(values):
            reading = SensorReading(
                device_id="sprayer-001",
                sequence=1000 + index,
                recorded_at=START + timedelta(seconds=index),
                imu_rms=0.6 if state != "IDLE" else 0.05,
                pump_current_a=current,
                pressure_bar=pressure,
                pressure_valid=1,
                raw_payload="{}",
                quality_flag="valid",
            )
            session.add(reading)
            session.flush()
            session.add(
                DeviceStateReading(
                    reading_id=reading.id,
                    device_id="sprayer-001",
                    state=state,
                    raw_state=state,
                    previous_state=state,
                    changed=0,
                    confidence=0.9,
                    reason="test",
                    features_json="{}",
                    quality_flag="valid",
                )
            )
        session.commit()


def test_linear_flow_interpolation_and_clamping() -> None:
    table = [
        {"pressure_bar": 5.0, "flow_lpm": 2.1},
        {"pressure_bar": 7.0, "flow_lpm": 2.6},
        {"pressure_bar": 9.0, "flow_lpm": 3.0},
    ]

    assert interpolate_flow_lpm(4.0, table) == pytest.approx(2.1)
    assert interpolate_flow_lpm(6.0, table) == pytest.approx(2.35)
    assert interpolate_flow_lpm(10.0, table) == pytest.approx(3.0)


def test_kma_grid_conversion_for_demo_farm() -> None:
    nx, ny = latitude_longitude_to_grid(33.25235, 126.50921)

    assert (nx, ny) == (52, 33)


def test_risk_rules_are_explainable() -> None:
    risk, explanations = assess_risk(
        rain_approach_minutes=95,
        maximum_wind_ms=4.7,
        pressure_fault_seconds=12,
    )

    assert risk == {
        "rain_exposure": "high",
        "wind_drift": "medium",
        "pressure_fault": "medium",
    }
    assert {item["code"] for item in explanations} == {
        "rain_exposure",
        "wind_drift",
        "pressure_fault",
    }


@pytest.mark.asyncio
async def test_weather_cache_returns_stale_data_on_provider_failure() -> None:
    provider = FailingMockWeatherProvider()
    cached = CachedWeatherProvider(provider, ttl=timedelta(seconds=-1))

    first = await cached.get_current_weather(33.25235, 126.50921)
    provider.fail = True
    fallback = await cached.get_current_weather(33.25235, 126.50921)

    assert first["cache_status"] == "miss"
    assert fallback["temperature_c"] == first["temperature_c"]
    assert fallback["cache_status"] == "stale_fallback"


@pytest.mark.asyncio
async def test_session_to_event_json_and_csv(
    session_service: tuple[WorkSessionService, sessionmaker],
) -> None:
    service, sessions = session_service
    started = service.start(start_request())
    session_id = str(started["session_id"])
    add_sensor_state_rows(sessions)

    for sequence, (latitude, longitude) in enumerate(
        [(33.25235, 126.50921), (33.25245, 126.50931), (33.25255, 126.50942)]
    ):
        point = service.add_location(
            session_id,
            LocationRequest(
                timestamp=START + timedelta(seconds=sequence + 1),
                sequence=sequence,
                latitude=latitude,
                longitude=longitude,
                accuracy_m=4.0,
                source="demo_route",
            ),
        )
        assert point["sequence"] == sequence

    with pytest.raises(SessionConflict, match="duplicate location"):
        service.add_location(
            session_id,
            LocationRequest(
                timestamp=START + timedelta(seconds=4),
                sequence=0,
                latitude=33.25,
                longitude=126.5,
                source="demo_route",
            ),
        )

    event = await service.finish(session_id, START + timedelta(seconds=5))

    assert event["event_type"] == "spraying"
    assert event["duration_seconds"] == pytest.approx(5.0)
    assert event["spray_duration_seconds"] == pytest.approx(3.0)
    assert event["estimated_spray_liters"] == pytest.approx(0.128, abs=0.001)
    assert event["geometry"]["type"] == "LineString"
    assert len(event["geometry"]["coordinates"]) == 3
    assert event["weather_summary"]["rain_approach_minutes"] == 95
    assert event["weather_summary"]["simulated"] is True
    assert event["risk"]["rain_exposure"] == "high"
    assert "추정값" in event["estimation_notice"]

    exported_json = json.loads(service.export_json(session_id))
    assert exported_json["event_id"] == event["event_id"]
    rows = list(csv.DictReader(io.StringIO(service.export_csv(session_id))))
    assert len(rows) == 1
    assert rows[0]["session_id"] == session_id
    assert rows[0]["rain_approach_minutes"] == "95"


@pytest.mark.asyncio
async def test_session_without_location_still_generates_event(
    session_service: tuple[WorkSessionService, sessionmaker],
) -> None:
    service, _ = session_service
    started = service.start(start_request())

    event = await service.finish(
        str(started["session_id"]),
        START + timedelta(seconds=2),
    )

    assert event["geometry"]["coordinates"] == []
    assert event["location_quality"] == {"point_count": 0, "available": False}
    assert event["confidence"] == 0.0
