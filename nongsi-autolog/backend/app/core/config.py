from __future__ import annotations

import os
from dataclasses import dataclass


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return default if value is None else int(value)


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    return default if value is None else float(value)


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str
    log_level: str
    database_url: str
    mqtt_host: str
    mqtt_port: int
    mqtt_keepalive_seconds: int
    mqtt_client_id: str
    mqtt_topic: str
    device_config_path: str
    device_online_timeout_seconds: int
    state_stream_poll_seconds: float
    cors_origins: tuple[str, ...]
    kma_auth_key: str | None
    kma_api_base_url: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            app_name=os.getenv("APP_NAME", "Nongsi AutoLog API"),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            database_url=os.getenv("DATABASE_URL", "sqlite:///../data/nongsi.db"),
            mqtt_host=os.getenv("MQTT_HOST", "localhost"),
            mqtt_port=_env_int("MQTT_PORT", 1883),
            mqtt_keepalive_seconds=_env_int("MQTT_KEEPALIVE_SECONDS", 60),
            mqtt_client_id=os.getenv("MQTT_CLIENT_ID", "nongsi-backend"),
            mqtt_topic=os.getenv("MQTT_TOPIC", "nongsi/devices/+/telemetry"),
            device_config_path=os.getenv(
                "DEVICE_CONFIG_PATH",
                "./config/device_thresholds.json",
            ),
            device_online_timeout_seconds=_env_int(
                "DEVICE_ONLINE_TIMEOUT_SECONDS",
                10,
            ),
            state_stream_poll_seconds=_env_float(
                "STATE_STREAM_POLL_SECONDS",
                0.5,
            ),
            cors_origins=tuple(
                origin.strip()
                for origin in os.getenv(
                    "CORS_ORIGINS",
                    "http://localhost:5173,http://127.0.0.1:5173",
                ).split(",")
                if origin.strip()
            ),
            kma_auth_key=os.getenv("KMA_AUTH_KEY") or None,
            kma_api_base_url=os.getenv(
                "KMA_API_BASE_URL",
                "https://apihub.kma.go.kr/api/typ02/openApi/VilageFcstInfoService_2.0",
            ),
        )


settings = Settings.from_env()
