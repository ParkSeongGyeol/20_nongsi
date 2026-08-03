from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Float, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base
from app.db.types import UTCDateTime


class SensorReading(Base):
    __tablename__ = "sensor_readings"
    __table_args__ = (
        UniqueConstraint("device_id", "sequence", name="uq_reading_device_sequence"),
        Index("ix_reading_device_timestamp", "device_id", "recorded_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String(100), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        UTCDateTime(),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    imu_rms: Mapped[float | None] = mapped_column(Float, nullable=True)
    pump_current_a: Mapped[float | None] = mapped_column(Float, nullable=True)
    pressure_bar: Mapped[float | None] = mapped_column(Float, nullable=True)
    pressure_valid: Mapped[int | None] = mapped_column(Integer, nullable=True)
    battery_voltage: Mapped[float | None] = mapped_column(Float, nullable=True)
    battery_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    signal_rssi: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_payload: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="mqtt")
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")
    quality_flag: Mapped[str] = mapped_column(String(50), nullable=False, default="valid")
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
