from __future__ import annotations

import json
import logging
import threading
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator

logger = logging.getLogger(__name__)


class DetectionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    window_size: int = Field(ge=1, le=60)
    minimum_state_duration_seconds: float = Field(ge=0, le=60)
    pump_current_on_a: float = Field(ge=0)
    pump_current_off_a: float = Field(ge=0)
    vibration_moving_on_rms: float = Field(ge=0)
    vibration_moving_off_rms: float = Field(ge=0)
    pressure_spray_min_bar: float = Field(ge=0)
    pressure_fault_recovery_bar: float = Field(ge=0)

    @model_validator(mode="after")
    def validate_hysteresis(self) -> "DetectionConfig":
        if self.pump_current_on_a <= self.pump_current_off_a:
            raise ValueError("pump_current_on_a must exceed pump_current_off_a")
        if self.vibration_moving_on_rms <= self.vibration_moving_off_rms:
            raise ValueError(
                "vibration_moving_on_rms must exceed vibration_moving_off_rms"
            )
        if self.pressure_fault_recovery_bar < self.pressure_spray_min_bar:
            raise ValueError(
                "pressure_fault_recovery_bar must be at least pressure_spray_min_bar"
            )
        return self


class DeviceConfigRepository:
    """Load device-specific thresholds and refresh when the JSON file changes."""

    def __init__(self, config_path: str | Path) -> None:
        self._path = Path(config_path)
        self._lock = threading.Lock()
        self._mtime_ns: int | None = None
        self._version = "unknown"
        self._default: dict[str, object] = {}
        self._devices: dict[str, dict[str, object]] = {}

    def get(self, device_id: str) -> tuple[DetectionConfig, str]:
        with self._lock:
            self._reload_if_changed()
            merged = {**self._default, **self._devices.get(device_id, {})}
            return DetectionConfig.model_validate(merged), self._version

    def _reload_if_changed(self) -> None:
        stat = self._path.stat()
        if self._mtime_ns == stat.st_mtime_ns:
            return

        document = json.loads(self._path.read_text(encoding="utf-8"))
        if not isinstance(document.get("default"), dict):
            raise ValueError("device config requires a default object")
        devices = document.get("devices", {})
        if not isinstance(devices, dict):
            raise ValueError("device config devices must be an object")

        default = dict(document["default"])
        DetectionConfig.model_validate(default)
        validated_devices: dict[str, dict[str, object]] = {}
        for device_id, override in devices.items():
            if not isinstance(override, dict):
                raise ValueError(f"device override must be an object: {device_id}")
            DetectionConfig.model_validate({**default, **override})
            validated_devices[str(device_id)] = dict(override)

        self._version = str(document.get("version", "unknown"))
        self._default = default
        self._devices = validated_devices
        self._mtime_ns = stat.st_mtime_ns
        logger.info(
            "Loaded state thresholds: path=%s version=%s devices=%s",
            self._path,
            self._version,
            len(self._devices),
        )

