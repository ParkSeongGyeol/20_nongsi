from __future__ import annotations

import os
from dataclasses import dataclass


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return default if value is None else int(value)


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
        )


settings = Settings.from_env()
