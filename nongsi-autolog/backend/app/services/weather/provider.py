from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta, timezone
from typing import Any


class WeatherProvider(ABC):
    name: str

    @abstractmethod
    async def get_current_weather(
        self,
        latitude: float,
        longitude: float,
    ) -> dict[str, Any]: ...

    @abstractmethod
    async def get_short_term_forecast(
        self,
        latitude: float,
        longitude: float,
    ) -> dict[str, Any]: ...

    @abstractmethod
    async def get_rain_approach(
        self,
        latitude: float,
        longitude: float,
    ) -> dict[str, Any]: ...


class MockWeatherProvider(WeatherProvider):
    """Deterministic presentation scenario; values are explicitly simulated."""

    name = "mock"

    async def get_current_weather(
        self,
        latitude: float,
        longitude: float,
    ) -> dict[str, Any]:
        return {
            "latitude": latitude,
            "longitude": longitude,
            "temperature_c": 27.1,
            "wind_speed_ms": 2.8,
            "precipitation_mm": 0.0,
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "simulated": True,
        }

    async def get_short_term_forecast(
        self,
        latitude: float,
        longitude: float,
    ) -> dict[str, Any]:
        return {
            "latitude": latitude,
            "longitude": longitude,
            "forecast_rain_mm": 3.4,
            "maximum_wind_ms": 4.7,
            "forecast_hours": 6,
            "simulated": True,
        }

    async def get_rain_approach(
        self,
        latitude: float,
        longitude: float,
    ) -> dict[str, Any]:
        return {
            "latitude": latitude,
            "longitude": longitude,
            "rain_approach_minutes": 95,
            "simulated": True,
        }


class CachedWeatherProvider(WeatherProvider):
    """Small process cache with stale-on-provider-error behavior."""

    def __init__(
        self,
        provider: WeatherProvider,
        ttl: timedelta = timedelta(minutes=30),
    ) -> None:
        self._provider = provider
        self._ttl = ttl
        self._cache: dict[tuple[str, float, float], tuple[datetime, dict[str, Any]]] = {}
        self.name = provider.name

    async def _get(
        self,
        method: str,
        latitude: float,
        longitude: float,
        loader: Callable[[float, float], Awaitable[dict[str, Any]]],
    ) -> dict[str, Any]:
        key = (method, round(latitude, 3), round(longitude, 3))
        now = datetime.now(timezone.utc)
        cached = self._cache.get(key)
        if cached and now - cached[0] <= self._ttl:
            return {**cached[1], "cache_status": "fresh"}
        try:
            value = await loader(latitude, longitude)
        except Exception:
            if cached:
                return {**cached[1], "cache_status": "stale_fallback"}
            raise
        self._cache[key] = (now, value.copy())
        return {**value, "cache_status": "miss"}

    async def get_current_weather(
        self,
        latitude: float,
        longitude: float,
    ) -> dict[str, Any]:
        return await self._get(
            "current",
            latitude,
            longitude,
            self._provider.get_current_weather,
        )

    async def get_short_term_forecast(
        self,
        latitude: float,
        longitude: float,
    ) -> dict[str, Any]:
        return await self._get(
            "forecast",
            latitude,
            longitude,
            self._provider.get_short_term_forecast,
        )

    async def get_rain_approach(
        self,
        latitude: float,
        longitude: float,
    ) -> dict[str, Any]:
        return await self._get(
            "rain",
            latitude,
            longitude,
            self._provider.get_rain_approach,
        )
