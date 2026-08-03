from __future__ import annotations

import csv
import io
import json
import logging
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from statistics import fmean
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.models.device_state import DeviceStateReading
from app.models.domain import (
    Device,
    DeviceCalibration,
    Farm,
    InputMaterial,
    LocationPoint,
    Parcel,
    RiskAssessment,
    UserConfirmation,
    WeatherSnapshot,
    WorkEvent,
    WorkSession,
)
from app.models.sensor_reading import SensorReading
from app.schemas.sessions import ConfirmationRequest, LocationRequest, SessionRequest
from app.services.flow import interpolate_flow_lpm
from app.services.risk import assess_risk
from app.services.weather import WeatherProvider

logger = logging.getLogger(__name__)


class SessionError(ValueError):
    pass


class SessionNotFound(SessionError):
    pass


class SessionConflict(SessionError):
    pass


def seed_demo_data(sessions: sessionmaker[Session]) -> None:
    with sessions() as session:
        if session.get(Farm, "FARM-001") is None:
            session.add(
                Farm(
                    farm_id="FARM-001",
                    name="서귀포 감귤 실증농장",
                    center_latitude=33.25235,
                    center_longitude=126.50921,
                    source="demo_seed",
                )
            )
        if session.get(Parcel, "PARCEL-001") is None:
            session.add(
                Parcel(
                    parcel_id="PARCEL-001",
                    farm_id="FARM-001",
                    name="노지감귤 1번 필지",
                    crop="open_field_citrus",
                    boundary_json=None,
                    source="demo_seed",
                )
            )
        if session.get(Device, "sprayer-001") is None:
            session.add(
                Device(
                    device_id="sprayer-001",
                    name="물 펌프 방제 데모 장치",
                    device_type="low_voltage_demo_sprayer",
                    active=1,
                    source="demo_seed",
                )
            )
        if session.get(InputMaterial, "WATER-DEMO") is None:
            session.add(
                InputMaterial(
                    material_id="WATER-DEMO",
                    event_type="spraying",
                    name="물(안전 시연용)",
                    description="실제 농약이 아닌 저전압 물 펌프 시연용",
                    source="demo_seed",
                )
            )
        calibration = session.scalar(
            select(DeviceCalibration).where(
                DeviceCalibration.device_id == "sprayer-001",
                DeviceCalibration.nozzle_id == "nozzle-A",
            )
        )
        if calibration is None:
            session.add(
                DeviceCalibration(
                    device_id="sprayer-001",
                    nozzle_id="nozzle-A",
                    calibration_json=json.dumps(
                        [
                            {"pressure_bar": 5.0, "flow_lpm": 2.1},
                            {"pressure_bar": 7.0, "flow_lpm": 2.6},
                            {"pressure_bar": 9.0, "flow_lpm": 3.0},
                        ],
                        separators=(",", ":"),
                    ),
                    source="water_calibration_demo",
                    quality_flag="estimated_demo",
                )
            )
        session.commit()


class WorkSessionService:
    def __init__(
        self,
        sessions: sessionmaker[Session],
        weather: WeatherProvider,
    ) -> None:
        self._sessions = sessions
        self._weather = weather
        self._event_publisher: Callable[[str, dict[str, object]], None] | None = None

    def set_event_publisher(
        self,
        publisher: Callable[[str, dict[str, object]], None] | None,
    ) -> None:
        self._event_publisher = publisher

    def _publish(self, topic: str, payload: dict[str, object]) -> None:
        if self._event_publisher is None:
            return
        try:
            self._event_publisher(topic, payload)
        except Exception:
            logger.exception("Non-fatal MQTT event publish failure: topic=%s", topic)

    def catalog(self) -> dict[str, object]:
        with self._sessions() as session:
            farms = session.scalars(select(Farm).order_by(Farm.farm_id)).all()
            parcels = session.scalars(select(Parcel).order_by(Parcel.parcel_id)).all()
            devices = session.scalars(
                select(Device).where(Device.active == 1).order_by(Device.device_id)
            ).all()
            materials = session.scalars(
                select(InputMaterial).order_by(InputMaterial.material_id)
            ).all()
            calibrations = session.scalars(
                select(DeviceCalibration).order_by(DeviceCalibration.id)
            ).all()
        return {
            "farms": [
                {
                    "farm_id": item.farm_id,
                    "name": item.name,
                    "center": [item.center_longitude, item.center_latitude],
                }
                for item in farms
            ],
            "parcels": [
                {
                    "parcel_id": item.parcel_id,
                    "farm_id": item.farm_id,
                    "name": item.name,
                    "crop": item.crop,
                }
                for item in parcels
            ],
            "devices": [
                {
                    "device_id": item.device_id,
                    "name": item.name,
                    "device_type": item.device_type,
                }
                for item in devices
            ],
            "input_materials": [
                {
                    "material_id": item.material_id,
                    "event_type": item.event_type,
                    "name": item.name,
                    "description": item.description,
                }
                for item in materials
            ],
            "nozzles": [
                {"device_id": item.device_id, "nozzle_id": item.nozzle_id}
                for item in calibrations
            ],
        }

    def start(self, request: SessionRequest) -> dict[str, object]:
        start_time = (request.start_time or datetime.now(timezone.utc)).astimezone(
            timezone.utc
        )
        with self._sessions() as session:
            farm = session.get(Farm, request.farm_id)
            parcel = session.get(Parcel, request.parcel_id)
            device = session.get(Device, request.device_id)
            if farm is None:
                raise SessionError("farm not found")
            if parcel is None or parcel.farm_id != farm.farm_id:
                raise SessionError("parcel not found in farm")
            if device is None or not device.active:
                raise SessionError("active device not found")
            if request.input_material_id and session.get(
                InputMaterial,
                request.input_material_id,
            ) is None:
                raise SessionError("input material not found")
            active = session.scalar(
                select(WorkSession).where(
                    WorkSession.device_id == request.device_id,
                    WorkSession.status == "ACTIVE",
                )
            )
            if active is not None:
                raise SessionConflict(
                    f"device already has active session: {active.session_id}"
                )

            session_id = f"SES-{start_time:%Y%m%d}-{uuid4().hex[:8].upper()}"
            work_session = WorkSession(
                session_id=session_id,
                farm_id=request.farm_id,
                parcel_id=request.parcel_id,
                device_id=request.device_id,
                crop=request.crop,
                event_type=request.event_type,
                input_material_id=request.input_material_id,
                product_name=request.product_name,
                dilution_ratio=request.dilution_ratio,
                nozzle_id=request.nozzle_id,
                location_mode=request.location_mode,
                status="ACTIVE",
                start_time=start_time,
                source="pwa",
            )
            session.add(work_session)
            session.commit()
            return self._session_dict(work_session, [], None)

    def add_location(
        self,
        session_id: str,
        request: LocationRequest,
    ) -> dict[str, object]:
        with self._sessions() as session:
            work_session = session.get(WorkSession, session_id)
            if work_session is None:
                raise SessionNotFound("session not found")
            if work_session.status != "ACTIVE":
                raise SessionConflict("locations can only be added to an active session")
            state_row = session.scalar(
                select(DeviceStateReading)
                .where(DeviceStateReading.device_id == work_session.device_id)
                .order_by(DeviceStateReading.id.desc())
                .limit(1)
            )
            state = state_row.state if state_row else "OFFLINE"
            point = LocationPoint(
                session_id=session_id,
                sequence=request.sequence,
                recorded_at=request.timestamp,
                latitude=request.latitude,
                longitude=request.longitude,
                accuracy_m=request.accuracy_m,
                state=state,
                is_spraying=int(state == "SPRAYING"),
                pressure_fault=int(state == "PRESSURE_FAULT"),
                source=request.source,
                quality_flag=(
                    "low_accuracy"
                    if request.accuracy_m is not None and request.accuracy_m > 50
                    else "valid"
                ),
            )
            try:
                session.add(point)
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                raise SessionConflict("duplicate location sequence") from exc
            result = self._location_dict(point)
        self._publish(f"nongsi/sessions/{session_id}/location", result)
        return result

    def get(self, session_id: str) -> dict[str, object]:
        with self._sessions() as session:
            work_session = session.get(WorkSession, session_id)
            if work_session is None:
                raise SessionNotFound("session not found")
            points = session.scalars(
                select(LocationPoint)
                .where(LocationPoint.session_id == session_id)
                .order_by(LocationPoint.sequence)
            ).all()
            event = session.scalar(
                select(WorkEvent).where(WorkEvent.session_id == session_id)
            )
            return self._session_dict(work_session, points, event)

    async def finish(
        self,
        session_id: str,
        end_time: datetime | None = None,
    ) -> dict[str, object]:
        with self._sessions() as session:
            work_session = session.get(WorkSession, session_id)
            if work_session is None:
                raise SessionNotFound("session not found")
            existing = session.scalar(
                select(WorkEvent).where(WorkEvent.session_id == session_id)
            )
            if existing is not None:
                return self._event_dict(existing)
            if work_session.status != "ACTIVE":
                raise SessionConflict("session is not active")
            finished_at = (end_time or datetime.now(timezone.utc)).astimezone(timezone.utc)
            if finished_at <= work_session.start_time:
                raise SessionError("end_time must be after start_time")

            state_rows = session.execute(
                select(DeviceStateReading, SensorReading)
                .join(SensorReading, DeviceStateReading.reading_id == SensorReading.id)
                .where(
                    DeviceStateReading.device_id == work_session.device_id,
                    SensorReading.recorded_at >= work_session.start_time,
                    SensorReading.recorded_at <= finished_at,
                )
                .order_by(SensorReading.recorded_at)
            ).all()
            points = session.scalars(
                select(LocationPoint)
                .where(LocationPoint.session_id == session_id)
                .order_by(LocationPoint.sequence)
            ).all()
            calibration_row = session.scalar(
                select(DeviceCalibration).where(
                    DeviceCalibration.device_id == work_session.device_id,
                    DeviceCalibration.nozzle_id == work_session.nozzle_id,
                )
            )
            parcel = session.get(Parcel, work_session.parcel_id)
            farm = session.get(Farm, work_session.farm_id)

        calibration = (
            json.loads(calibration_row.calibration_json) if calibration_row else []
        )
        metrics = self._calculate_metrics(state_rows, finished_at, calibration)
        if points:
            latitude = points[-1].latitude
            longitude = points[-1].longitude
        elif farm:
            latitude = farm.center_latitude
            longitude = farm.center_longitude
        else:
            latitude, longitude = 33.25235, 126.50921

        current = await self._weather.get_current_weather(latitude, longitude)
        forecast = await self._weather.get_short_term_forecast(latitude, longitude)
        rain = await self._weather.get_rain_approach(latitude, longitude)
        weather_summary = {
            "provider": self._weather.name,
            "simulated": bool(forecast.get("simulated", False)),
            "rain_approach_minutes": rain.get("rain_approach_minutes"),
            "forecast_rain_mm": forecast.get("forecast_rain_mm", 0.0),
            "maximum_wind_ms": forecast.get("maximum_wind_ms", 0.0),
            "observed_at": current.get("observed_at"),
        }
        risk, explanations = assess_risk(
            rain_approach_minutes=weather_summary["rain_approach_minutes"],
            maximum_wind_ms=float(weather_summary["maximum_wind_ms"]),
            pressure_fault_seconds=metrics["pressure_fault_seconds"],
        )
        event_id = f"EVT-{finished_at:%Y%m%d}-{uuid4().hex[:8].upper()}"
        coordinates = [[point.longitude, point.latitude] for point in points]
        event_payload = {
            "event_id": event_id,
            "session_id": session_id,
            "farm_id": work_session.farm_id,
            "parcel_id": work_session.parcel_id,
            "device_id": work_session.device_id,
            "crop": work_session.crop,
            "event_type": work_session.event_type,
            "input_material": {
                "material_id": work_session.input_material_id,
                "product_name": work_session.product_name,
                "dilution_ratio": work_session.dilution_ratio,
                "nozzle_id": work_session.nozzle_id,
            },
            "start_time": work_session.start_time.isoformat(),
            "end_time": finished_at.isoformat(),
            "duration_seconds": round(
                (finished_at - work_session.start_time).total_seconds(),
                1,
            ),
            "spray_duration_seconds": round(metrics["spray_seconds"], 1),
            "estimated_spray_liters": round(metrics["estimated_liters"], 3),
            "estimation_notice": "물 보정표 기반 추정값이며 정밀 계량값이 아닙니다.",
            "geometry": {"type": "LineString", "coordinates": coordinates},
            "location_quality": {
                "point_count": len(points),
                "available": bool(points),
            },
            "sensor_evidence": metrics["sensor_evidence"],
            "pressure_summary": {
                "average_bar": metrics["average_pressure_bar"],
                "minimum_bar": metrics["minimum_pressure_bar"],
                "fault_duration_seconds": round(metrics["pressure_fault_seconds"], 1),
            },
            "weather_summary": weather_summary,
            "risk": risk,
            "risk_explanations": explanations,
            "confidence": metrics["confidence"],
            "confidence_notice": "규칙 기반 설명 지표이며 학습 AI 정확도가 아닙니다.",
            "farmer_confirmed": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        with self._sessions() as session:
            persisted_session = session.get(WorkSession, session_id)
            if persisted_session is None:
                raise SessionNotFound("session not found")
            persisted_session.status = "FINISHED"
            persisted_session.end_time = finished_at
            event = WorkEvent(
                event_id=event_id,
                session_id=session_id,
                event_type=persisted_session.event_type,
                start_time=persisted_session.start_time,
                end_time=finished_at,
                duration_seconds=event_payload["duration_seconds"],
                spray_duration_seconds=event_payload["spray_duration_seconds"],
                estimated_spray_liters=event_payload["estimated_spray_liters"],
                payload_json=json.dumps(event_payload, ensure_ascii=False),
                farmer_confirmed=0,
                source="rule_based",
                quality_flag="estimated",
            )
            session.add(event)
            weather_payload = {
                "current": current,
                "forecast": forecast,
                "rain_approach": rain,
            }
            session.add(
                WeatherSnapshot(
                    session_id=session_id,
                    provider=self._weather.name,
                    latitude=latitude,
                    longitude=longitude,
                    observed_at=datetime.now(timezone.utc),
                    expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
                    payload_json=json.dumps(weather_payload, ensure_ascii=False),
                    raw_response_json=json.dumps(weather_payload, ensure_ascii=False),
                    source=self._weather.name,
                    quality_flag="simulated" if weather_summary["simulated"] else "valid",
                )
            )
            session.add(
                RiskAssessment(
                    session_id=session_id,
                    event_id=event_id,
                    rain_exposure=risk["rain_exposure"],
                    wind_drift=risk["wind_drift"],
                    pressure_fault=risk["pressure_fault"],
                    explanation_json=json.dumps(explanations, ensure_ascii=False),
                    source="mvp_rule_v1",
                )
            )
            session.commit()
            result = self._event_dict(event)
        self._publish(f"nongsi/sessions/{session_id}/event", result)
        return result

    def get_event(self, session_id: str) -> dict[str, object]:
        with self._sessions() as session:
            event = session.scalar(
                select(WorkEvent).where(WorkEvent.session_id == session_id)
            )
            if event is None:
                raise SessionNotFound("work event not found")
            return self._event_dict(event)

    def confirm(
        self,
        event_id: str,
        request: ConfirmationRequest,
    ) -> dict[str, object]:
        with self._sessions() as session:
            event = session.get(WorkEvent, event_id)
            if event is None:
                raise SessionNotFound("work event not found")
            event.farmer_confirmed = int(request.confirmed)
            payload = json.loads(event.payload_json)
            payload["farmer_confirmed"] = request.confirmed
            event.payload_json = json.dumps(payload, ensure_ascii=False)
            session.add(
                UserConfirmation(
                    event_id=event_id,
                    confirmed=int(request.confirmed),
                    note=request.note,
                    correction_json=(
                        json.dumps(request.corrections, ensure_ascii=False)
                        if request.corrections
                        else None
                    ),
                    source="farmer_pwa",
                )
            )
            session.commit()
            result = self._event_dict(event)
        self._publish(f"nongsi/sessions/{event.session_id}/event", result)
        return result

    def export_json(self, session_id: str) -> str:
        return json.dumps(
            self.get_event(session_id),
            ensure_ascii=False,
            indent=2,
        )

    def export_csv(self, session_id: str) -> str:
        event = self.get_event(session_id)
        pressure = event["pressure_summary"]
        weather = event["weather_summary"]
        risk = event["risk"]
        row = {
            "event_id": event["event_id"],
            "session_id": event["session_id"],
            "farm_id": event["farm_id"],
            "parcel_id": event["parcel_id"],
            "device_id": event["device_id"],
            "event_type": event["event_type"],
            "start_time": event["start_time"],
            "end_time": event["end_time"],
            "duration_seconds": event["duration_seconds"],
            "spray_duration_seconds": event["spray_duration_seconds"],
            "estimated_spray_liters": event["estimated_spray_liters"],
            "average_pressure_bar": pressure["average_bar"],
            "minimum_pressure_bar": pressure["minimum_bar"],
            "pressure_fault_duration_seconds": pressure["fault_duration_seconds"],
            "rain_approach_minutes": weather["rain_approach_minutes"],
            "maximum_wind_ms": weather["maximum_wind_ms"],
            "rain_exposure_risk": risk["rain_exposure"],
            "wind_drift_risk": risk["wind_drift"],
            "pressure_fault_risk": risk["pressure_fault"],
            "farmer_confirmed": event["farmer_confirmed"],
            "geometry_geojson": json.dumps(event["geometry"], ensure_ascii=False),
        }
        buffer = io.StringIO(newline="")
        writer = csv.DictWriter(buffer, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)
        return buffer.getvalue()

    @staticmethod
    def _calculate_metrics(
        rows: list[tuple[DeviceStateReading, SensorReading]],
        end_time: datetime,
        calibration: list[dict[str, float]],
    ) -> dict[str, object]:
        spray_seconds = 0.0
        fault_seconds = 0.0
        estimated_liters = 0.0
        pressure_values: list[float] = []
        confidence_values: list[float] = []
        for index, (state_row, reading) in enumerate(rows):
            next_time = rows[index + 1][1].recorded_at if index + 1 < len(rows) else end_time
            seconds = min(2.0, max(0.0, (next_time - reading.recorded_at).total_seconds()))
            if reading.pressure_bar is not None and reading.pressure_valid:
                pressure_values.append(reading.pressure_bar)
            confidence_values.append(state_row.confidence)
            if state_row.state == "SPRAYING":
                spray_seconds += seconds
                if calibration and reading.pressure_bar is not None:
                    flow_lpm = interpolate_flow_lpm(reading.pressure_bar, calibration)
                    estimated_liters += flow_lpm * seconds / 60
            elif state_row.state == "PRESSURE_FAULT":
                fault_seconds += seconds
        evidence: list[str] = []
        if rows:
            evidence.extend(["imu", "pump_current", "pressure"])
        return {
            "spray_seconds": spray_seconds,
            "pressure_fault_seconds": fault_seconds,
            "estimated_liters": estimated_liters,
            "average_pressure_bar": (
                round(fmean(pressure_values), 3) if pressure_values else None
            ),
            "minimum_pressure_bar": (
                round(min(pressure_values), 3) if pressure_values else None
            ),
            "confidence": (
                round(fmean(confidence_values), 2) if confidence_values else 0.0
            ),
            "sensor_evidence": evidence,
        }

    @staticmethod
    def _location_dict(point: LocationPoint) -> dict[str, object]:
        return {
            "id": point.id,
            "session_id": point.session_id,
            "sequence": point.sequence,
            "timestamp": point.recorded_at.isoformat(),
            "latitude": point.latitude,
            "longitude": point.longitude,
            "accuracy_m": point.accuracy_m,
            "state": point.state,
            "is_spraying": bool(point.is_spraying),
            "pressure_fault": bool(point.pressure_fault),
            "source": point.source,
            "quality_flag": point.quality_flag,
        }

    def _session_dict(
        self,
        work_session: WorkSession,
        points: list[LocationPoint],
        event: WorkEvent | None,
    ) -> dict[str, object]:
        return {
            "session_id": work_session.session_id,
            "farm_id": work_session.farm_id,
            "parcel_id": work_session.parcel_id,
            "device_id": work_session.device_id,
            "crop": work_session.crop,
            "event_type": work_session.event_type,
            "input_material_id": work_session.input_material_id,
            "product_name": work_session.product_name,
            "dilution_ratio": work_session.dilution_ratio,
            "nozzle_id": work_session.nozzle_id,
            "location_mode": work_session.location_mode,
            "status": work_session.status,
            "start_time": work_session.start_time.isoformat(),
            "end_time": (
                work_session.end_time.isoformat() if work_session.end_time else None
            ),
            "locations": [self._location_dict(point) for point in points],
            "event": self._event_dict(event) if event else None,
        }

    @staticmethod
    def _event_dict(event: WorkEvent) -> dict[str, object]:
        payload = json.loads(event.payload_json)
        payload["farmer_confirmed"] = bool(event.farmer_confirmed)
        return payload
