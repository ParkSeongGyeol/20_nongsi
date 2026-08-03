from __future__ import annotations

import argparse
import json
import logging
import os
import random
import time
from datetime import datetime, timedelta, timezone
from itertools import count

import paho.mqtt.client as mqtt

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("nongsi.simulator")
KST = timezone(timedelta(hours=9), name="KST")


def build_payload(device_id: str, sequence: int) -> dict[str, object]:
    phase = sequence % 25
    if phase < 5:  # idle
        rms, current_a, pressure_bar, running = 0.04, 0.05, 0.2, False
    elif phase < 10:  # moving
        rms, current_a, pressure_bar, running = 0.55, 0.08, 0.2, False
    elif phase < 20:  # spraying
        rms, current_a, pressure_bar, running = 0.65, 2.7, 8.2, True
    else:  # pressure fault scenario for the later state-machine phase
        rms, current_a, pressure_bar, running = 0.63, 2.7, 3.4, True

    jitter = lambda value, width: round(value + random.uniform(-width, width), 3)
    return {
        "device_id": device_id,
        "timestamp": datetime.now(KST).isoformat(timespec="milliseconds"),
        "sequence": sequence,
        "imu": {
            "ax": jitter(0.12, 0.03),
            "ay": jitter(-0.08, 0.03),
            "az": jitter(1.01, 0.02),
            "gx": jitter(1.2, 0.2),
            "gy": jitter(0.4, 0.2),
            "gz": jitter(-0.7, 0.2),
            "rms": jitter(rms, 0.02),
        },
        "pump": {
            "current_a": jitter(current_a, 0.03),
            "is_running": running,
        },
        "pressure": {"bar": jitter(pressure_bar, 0.08), "valid": True},
        "battery": {"voltage": jitter(4.02, 0.01), "percent": 82},
        "signal": {"rssi": random.randint(-65, -50)},
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Nongsi MQTT telemetry simulator")
    parser.add_argument("--host", default=os.getenv("MQTT_HOST", "localhost"))
    parser.add_argument("--port", type=int, default=int(os.getenv("MQTT_PORT", "1883")))
    parser.add_argument(
        "--device-id",
        default=os.getenv("SIMULATOR_DEVICE_ID", "sprayer-001"),
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=float(os.getenv("SIMULATOR_INTERVAL_SECONDS", "1.0")),
    )
    parser.add_argument(
        "--count",
        type=int,
        default=0,
        help="messages to publish; 0 means run continuously",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=f"nongsi-simulator-{args.device_id}",
    )
    client.reconnect_delay_set(min_delay=1, max_delay=30)

    logger.info("Connecting to MQTT broker %s:%s", args.host, args.port)
    client.connect(args.host, args.port, keepalive=60)
    client.loop_start()
    topic = f"nongsi/devices/{args.device_id}/telemetry"
    start_sequence = int(time.time() * 1000)

    try:
        for sent, sequence in enumerate(count(start_sequence), start=1):
            payload = build_payload(args.device_id, sequence)
            encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
            publication = client.publish(topic, encoded, qos=1)
            publication.wait_for_publish(timeout=5)
            if publication.rc != mqtt.MQTT_ERR_SUCCESS:
                raise RuntimeError(f"MQTT publish failed with code {publication.rc}")
            logger.info(
                "Published device=%s sequence=%s current_a=%s pressure_bar=%s",
                args.device_id,
                sequence,
                payload["pump"]["current_a"],
                payload["pressure"]["bar"],
            )
            if args.count > 0 and sent >= args.count:
                break
            time.sleep(max(args.interval, 0.05))
    except KeyboardInterrupt:
        logger.info("Simulator stopped by user")
    finally:
        client.disconnect()
        client.loop_stop()


if __name__ == "__main__":
    main()
