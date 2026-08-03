from __future__ import annotations

from typing import Annotated

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


FiniteFloat = Annotated[float, Field(allow_inf_nan=False)]
NonNegativeFloat = Annotated[float, Field(ge=0, allow_inf_nan=False)]


class StrictPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ImuPayload(StrictPayload):
    ax: FiniteFloat
    ay: FiniteFloat
    az: FiniteFloat
    gx: FiniteFloat
    gy: FiniteFloat
    gz: FiniteFloat
    rms: NonNegativeFloat


class PumpPayload(StrictPayload):
    current_a: NonNegativeFloat
    is_running: bool


class PressurePayload(StrictPayload):
    bar: Annotated[float, Field(ge=0, le=100, allow_inf_nan=False)]
    valid: bool


class BatteryPayload(StrictPayload):
    voltage: NonNegativeFloat
    percent: Annotated[float, Field(ge=0, le=100, allow_inf_nan=False)]


class SignalPayload(StrictPayload):
    rssi: Annotated[int, Field(ge=-150, le=0)]


class TelemetryPayload(StrictPayload):
    device_id: Annotated[str, Field(min_length=1, max_length=100)]
    timestamp: AwareDatetime
    sequence: Annotated[int, Field(ge=0)]
    imu: ImuPayload | None = None
    pump: PumpPayload | None = None
    pressure: PressurePayload | None = None
    battery: BatteryPayload | None = None
    signal: SignalPayload | None = None

    @property
    def quality_flag(self) -> str:
        missing = [
            name
            for name in ("imu", "pump", "pressure")
            if getattr(self, name) is None
        ]
        return "valid" if not missing else f"missing_{'_'.join(missing)}"

