from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base
from app.db.types import UTCDateTime


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TraceableMixin:
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="system")
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")
    quality_flag: Mapped[str] = mapped_column(String(50), nullable=False, default="valid")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False, default=utc_now)


class Farm(TraceableMixin, Base):
    __tablename__ = "farms"

    farm_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    center_latitude: Mapped[float] = mapped_column(Float, nullable=False)
    center_longitude: Mapped[float] = mapped_column(Float, nullable=False)


class Parcel(TraceableMixin, Base):
    __tablename__ = "parcels"

    parcel_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    farm_id: Mapped[str] = mapped_column(ForeignKey("farms.farm_id"), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    crop: Mapped[str] = mapped_column(String(100), nullable=False)
    boundary_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class Device(TraceableMixin, Base):
    __tablename__ = "devices"

    device_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    device_type: Mapped[str] = mapped_column(String(80), nullable=False)
    active: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class DeviceCalibration(TraceableMixin, Base):
    __tablename__ = "device_calibrations"
    __table_args__ = (
        UniqueConstraint("device_id", "nozzle_id", name="uq_calibration_device_nozzle"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(ForeignKey("devices.device_id"), nullable=False)
    nozzle_id: Mapped[str] = mapped_column(String(80), nullable=False)
    calibration_json: Mapped[str] = mapped_column(Text, nullable=False)


class InputMaterial(TraceableMixin, Base):
    __tablename__ = "input_materials"

    material_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class WorkSession(TraceableMixin, Base):
    __tablename__ = "work_sessions"
    __table_args__ = (
        Index("ix_session_device_status", "device_id", "status"),
    )

    session_id: Mapped[str] = mapped_column(String(60), primary_key=True)
    farm_id: Mapped[str] = mapped_column(ForeignKey("farms.farm_id"), nullable=False)
    parcel_id: Mapped[str] = mapped_column(ForeignKey("parcels.parcel_id"), nullable=False)
    device_id: Mapped[str] = mapped_column(ForeignKey("devices.device_id"), nullable=False)
    crop: Mapped[str] = mapped_column(String(100), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, default="spraying")
    input_material_id: Mapped[str | None] = mapped_column(
        ForeignKey("input_materials.material_id"),
        nullable=True,
    )
    product_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    dilution_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    nozzle_id: Mapped[str] = mapped_column(String(80), nullable=False)
    location_mode: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="ACTIVE")
    start_time: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    end_time: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)


class LocationPoint(TraceableMixin, Base):
    __tablename__ = "location_points"
    __table_args__ = (
        UniqueConstraint("session_id", "sequence", name="uq_location_session_sequence"),
        Index("ix_location_session_timestamp", "session_id", "recorded_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("work_sessions.session_id"),
        nullable=False,
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    accuracy_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    state: Mapped[str] = mapped_column(String(40), nullable=False)
    is_spraying: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pressure_fault: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class WorkEvent(TraceableMixin, Base):
    __tablename__ = "work_events"

    event_id: Mapped[str] = mapped_column(String(60), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("work_sessions.session_id"),
        unique=True,
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    start_time: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    end_time: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    spray_duration_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    estimated_spray_liters: Mapped[float] = mapped_column(Float, nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    farmer_confirmed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class WeatherSnapshot(TraceableMixin, Base):
    __tablename__ = "weather_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("work_sessions.session_id"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    observed_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    raw_response_json: Mapped[str] = mapped_column(Text, nullable=False)


class RiskAssessment(TraceableMixin, Base):
    __tablename__ = "risk_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("work_sessions.session_id"),
        nullable=False,
    )
    event_id: Mapped[str] = mapped_column(ForeignKey("work_events.event_id"), nullable=False)
    rain_exposure: Mapped[str] = mapped_column(String(20), nullable=False)
    wind_drift: Mapped[str] = mapped_column(String(20), nullable=False)
    pressure_fault: Mapped[str] = mapped_column(String(20), nullable=False)
    explanation_json: Mapped[str] = mapped_column(Text, nullable=False)


class UserConfirmation(TraceableMixin, Base):
    __tablename__ = "user_confirmations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(ForeignKey("work_events.event_id"), nullable=False)
    confirmed: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    correction_json: Mapped[str | None] = mapped_column(Text, nullable=True)
