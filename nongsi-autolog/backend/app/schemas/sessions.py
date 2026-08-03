from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class SessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    farm_id: Annotated[str, Field(min_length=1, max_length=50)]
    parcel_id: Annotated[str, Field(min_length=1, max_length=50)]
    device_id: Annotated[str, Field(min_length=1, max_length=100)]
    crop: Annotated[str, Field(min_length=1, max_length=100)] = "open_field_citrus"
    event_type: Annotated[str, Field(min_length=1, max_length=50)] = "spraying"
    input_material_id: str | None = None
    product_name: Annotated[str, Field(max_length=150)] | None = None
    dilution_ratio: Annotated[float, Field(gt=0, le=10000)] | None = None
    nozzle_id: Annotated[str, Field(min_length=1, max_length=80)] = "nozzle-A"
    location_mode: Literal["browser", "demo"] = "demo"
    start_time: AwareDatetime | None = None


class SessionFinishRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    end_time: AwareDatetime | None = None


class LocationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timestamp: AwareDatetime
    sequence: Annotated[int, Field(ge=0)]
    latitude: Annotated[float, Field(ge=-90, le=90, allow_inf_nan=False)]
    longitude: Annotated[float, Field(ge=-180, le=180, allow_inf_nan=False)]
    accuracy_m: Annotated[float, Field(ge=0, allow_inf_nan=False)] | None = None
    source: Literal["browser_gnss", "demo_route"]


class ConfirmationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirmed: bool
    note: Annotated[str, Field(max_length=1000)] | None = None
    corrections: dict[str, Any] | None = None

