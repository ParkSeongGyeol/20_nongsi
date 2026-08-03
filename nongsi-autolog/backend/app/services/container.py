from app.db.database import session_factory
from app.core.config import settings
from app.services.weather import (
    CachedWeatherProvider,
    KmaWeatherProvider,
    MockWeatherProvider,
)
from app.services.work_sessions import WorkSessionService

base_weather_provider = (
    KmaWeatherProvider(settings.kma_auth_key, settings.kma_api_base_url)
    if settings.kma_auth_key
    else MockWeatherProvider()
)
weather_provider = CachedWeatherProvider(base_weather_provider)
work_session_service = WorkSessionService(session_factory, weather_provider)

__all__ = ["weather_provider", "work_session_service"]
