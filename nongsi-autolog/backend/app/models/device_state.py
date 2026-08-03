from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base
from app.db.types import UTCDateTime


class DeviceStateReading(Base):
    __tablename__ = "device_states"
    __table_args__ = (
        Index("ix_device_state_device_created", "device_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    reading_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    device_id: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(40), nullable=False)
    raw_state: Mapped[str] = mapped_column(String(40), nullable=False)
    previous_state: Mapped[str] = mapped_column(String(40), nullable=False)
    changed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    reason: Mapped[str] = mapped_column(String(200), nullable=False)
    features_json: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="rule_based")
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")
    quality_flag: Mapped[str] = mapped_column(String(50), nullable=False, default="valid")
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

