from __future__ import annotations

import json
import logging
from typing import Any

import paho.mqtt.client as mqtt

from app.core.config import Settings
from app.services.telemetry import TelemetryIngestor

logger = logging.getLogger(__name__)


class MQTTSubscriber:
    def __init__(self, settings: Settings, ingestor: TelemetryIngestor) -> None:
        self._settings = settings
        self._ingestor = ingestor
        self._connected = False
        self._client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=settings.mqtt_client_id,
        )
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message
        self._client.reconnect_delay_set(min_delay=1, max_delay=30)

    @property
    def connected(self) -> bool:
        return self._connected

    def start(self) -> None:
        logger.info(
            "Starting MQTT subscriber: broker=%s:%s topic=%s",
            self._settings.mqtt_host,
            self._settings.mqtt_port,
            self._settings.mqtt_topic,
        )
        self._client.connect_async(
            self._settings.mqtt_host,
            self._settings.mqtt_port,
            self._settings.mqtt_keepalive_seconds,
        )
        self._client.loop_start()

    def stop(self) -> None:
        self._client.disconnect()
        self._client.loop_stop()
        self._connected = False

    def publish_json(self, topic: str, payload: dict[str, Any]) -> None:
        if not self._connected:
            raise RuntimeError("MQTT publisher is not connected")
        result = self._client.publish(
            topic,
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
            qos=1,
        )
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            raise RuntimeError(f"MQTT publish failed with code {result.rc}")

    def _on_connect(
        self,
        client: mqtt.Client,
        userdata: object,
        flags: mqtt.ConnectFlags,
        reason_code: mqtt.ReasonCode,
        properties: mqtt.Properties | None,
    ) -> None:
        del userdata, flags, properties
        if reason_code.is_failure:
            logger.error("MQTT connection failed: %s", reason_code)
            return
        self._connected = True
        client.subscribe(self._settings.mqtt_topic, qos=1)
        logger.info("MQTT connected and subscribed: %s", self._settings.mqtt_topic)

    def _on_disconnect(
        self,
        client: mqtt.Client,
        userdata: object,
        disconnect_flags: mqtt.DisconnectFlags,
        reason_code: mqtt.ReasonCode,
        properties: mqtt.Properties | None,
    ) -> None:
        del client, userdata, disconnect_flags, properties
        self._connected = False
        if reason_code.is_failure:
            logger.warning("Unexpected MQTT disconnect: %s", reason_code)
        else:
            logger.info("MQTT disconnected")

    def _on_message(
        self,
        client: mqtt.Client,
        userdata: object,
        message: mqtt.MQTTMessage,
    ) -> None:
        del client, userdata
        try:
            raw_payload = message.payload.decode("utf-8")
        except UnicodeDecodeError:
            logger.warning("Rejected non-UTF-8 MQTT message on %s", message.topic)
            return

        topic_parts = message.topic.split("/")
        topic_device_id = topic_parts[2] if len(topic_parts) >= 4 else None
        result = self._ingestor.ingest_json(
            raw_payload,
            topic_device_id=topic_device_id,
        )
        logger.debug("MQTT ingestion result: %s", result)
