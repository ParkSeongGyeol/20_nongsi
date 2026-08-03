from __future__ import annotations

import asyncio
import json
import math
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen

from app.services.weather.provider import WeatherProvider

KST = timezone(timedelta(hours=9), name="KST")


def latitude_longitude_to_grid(latitude: float, longitude: float) -> tuple[int, int]:
    """Convert WGS84 coordinates to the KMA 5 km village-forecast grid."""
    re = 6371.00877 / 5.0
    slat1 = math.radians(30.0)
    slat2 = math.radians(60.0)
    olon = math.radians(126.0)
    olat = math.radians(38.0)
    sn = math.log(math.cos(slat1) / math.cos(slat2)) / math.log(
        math.tan(math.pi * 0.25 + slat2 * 0.5)
        / math.tan(math.pi * 0.25 + slat1 * 0.5)
    )
    sf = (
        math.tan(math.pi * 0.25 + slat1 * 0.5) ** sn
        * math.cos(slat1)
        / sn
    )
    ro = re * sf / math.tan(math.pi * 0.25 + olat * 0.5) ** sn
    ra = re * sf / math.tan(
        math.pi * 0.25 + math.radians(latitude) * 0.5
    ) ** sn
    theta = math.radians(longitude) - olon
    if theta > math.pi:
        theta -= 2.0 * math.pi
    if theta < -math.pi:
        theta += 2.0 * math.pi
    theta *= sn
    return int(ra * math.sin(theta) + 43.0 + 0.5), int(
        ro - ra * math.cos(theta) + 136.0 + 0.5
    )


def _number(value: object) -> float:
    text = str(value).strip()
    if text in {"강수없음", "없음", "-"}:
        return 0.0
    if "미만" in text:
        return 0.5
    numeric = "".join(character for character in text if character in "0123456789.-")
    try:
        return float(numeric)
    except ValueError:
        return 0.0


class KmaWeatherProvider(WeatherProvider):
    """KMA API Hub village-forecast adapter (authKey authentication)."""

    name = "kma_api_hub"

    def __init__(
        self,
        auth_key: str,
        base_url: str = "https://apihub.kma.go.kr/api/typ02/openApi/VilageFcstInfoService_2.0",
        timeout_seconds: float = 10.0,
    ) -> None:
        if not auth_key:
            raise ValueError("KMA auth key is required")
        self._auth_key = auth_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds

    def _request_sync(self, endpoint: str, params: dict[str, object]) -> list[dict[str, Any]]:
        query = urlencode(
            {
                "pageNo": 1,
                "numOfRows": 1000,
                "dataType": "JSON",
                **params,
                "authKey": self._auth_key,
            }
        )
        with urlopen(f"{self._base_url}/{endpoint}?{query}", timeout=self._timeout) as response:
            document = json.loads(response.read().decode("utf-8"))
        api_response = document.get("response", {})
        header = api_response.get("header", {})
        if str(header.get("resultCode")) not in {"00", "0"}:
            raise RuntimeError(f"KMA API error: {header.get('resultMsg', 'unknown')}")
        items = api_response.get("body", {}).get("items", {}).get("item", [])
        return items if isinstance(items, list) else [items]

    async def _request(self, endpoint: str, params: dict[str, object]) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._request_sync, endpoint, params)

    @staticmethod
    def _current_base(now: datetime) -> datetime:
        return (now.astimezone(KST) - timedelta(minutes=40)).replace(
            minute=0,
            second=0,
            microsecond=0,
        )

    @staticmethod
    def _forecast_base(now: datetime) -> datetime:
        return (now.astimezone(KST) - timedelta(minutes=45)).replace(
            minute=30,
            second=0,
            microsecond=0,
        )

    async def get_current_weather(
        self,
        latitude: float,
        longitude: float,
    ) -> dict[str, Any]:
        nx, ny = latitude_longitude_to_grid(latitude, longitude)
        base = self._current_base(datetime.now(timezone.utc))
        items = await self._request(
            "getUltraSrtNcst",
            {
                "base_date": base.strftime("%Y%m%d"),
                "base_time": base.strftime("%H%M"),
                "nx": nx,
                "ny": ny,
            },
        )
        values = {str(item.get("category")): item.get("obsrValue") for item in items}
        return {
            "latitude": latitude,
            "longitude": longitude,
            "grid": {"nx": nx, "ny": ny},
            "temperature_c": _number(values.get("T1H")),
            "wind_speed_ms": _number(values.get("WSD")),
            "precipitation_mm": _number(values.get("RN1")),
            "observed_at": base.isoformat(),
            "simulated": False,
        }

    async def _forecast(self, latitude: float, longitude: float) -> list[dict[str, Any]]:
        nx, ny = latitude_longitude_to_grid(latitude, longitude)
        base = self._forecast_base(datetime.now(timezone.utc))
        return await self._request(
            "getUltraSrtFcst",
            {
                "base_date": base.strftime("%Y%m%d"),
                "base_time": base.strftime("%H%M"),
                "nx": nx,
                "ny": ny,
            },
        )

    async def get_short_term_forecast(
        self,
        latitude: float,
        longitude: float,
    ) -> dict[str, Any]:
        items = await self._forecast(latitude, longitude)
        wind = [_number(item.get("fcstValue")) for item in items if item.get("category") == "WSD"]
        rain = [_number(item.get("fcstValue")) for item in items if item.get("category") == "RN1"]
        return {
            "latitude": latitude,
            "longitude": longitude,
            "forecast_rain_mm": round(sum(rain), 2),
            "maximum_wind_ms": max(wind, default=0.0),
            "forecast_hours": 6,
            "simulated": False,
        }

    async def get_rain_approach(
        self,
        latitude: float,
        longitude: float,
    ) -> dict[str, Any]:
        items = await self._forecast(latitude, longitude)
        groups: dict[tuple[str, str], dict[str, object]] = {}
        for item in items:
            key = (str(item.get("fcstDate", "")), str(item.get("fcstTime", "")))
            groups.setdefault(key, {})[str(item.get("category"))] = item.get("fcstValue")
        now = datetime.now(KST)
        approaches: list[int] = []
        for (date, time), values in groups.items():
            if _number(values.get("PTY")) <= 0 and _number(values.get("RN1")) <= 0:
                continue
            try:
                forecast_at = datetime.strptime(date + time, "%Y%m%d%H%M").replace(tzinfo=KST)
            except ValueError:
                continue
            approaches.append(max(0, round((forecast_at - now).total_seconds() / 60)))
        return {
            "latitude": latitude,
            "longitude": longitude,
            "rain_approach_minutes": min(approaches) if approaches else None,
            "simulated": False,
        }


__all__ = ["KmaWeatherProvider", "latitude_longitude_to_grid"]
