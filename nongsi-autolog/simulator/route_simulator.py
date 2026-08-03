from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

DEMO_ROUTE = [
    (33.25235, 126.50921),
    (33.25243, 126.50931),
    (33.25252, 126.50944),
    (33.25261, 126.50955),
    (33.25269, 126.50966),
    (33.25277, 126.50954),
    (33.25268, 126.50942),
    (33.25259, 126.50929),
    (33.25249, 126.50917),
    (33.25240, 126.50908),
    (33.25234, 126.50919),
    (33.25242, 126.50930),
    (33.25251, 126.50941),
    (33.25260, 126.50952),
    (33.25268, 126.50963),
]


def request_json(base_url: str, path: str, method: str = "GET", body: object | None = None) -> dict[str, Any]:
    encoded = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    request = Request(
        f"{base_url.rstrip('/')}{path}",
        data=encoded,
        method=method,
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    try:
        with urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"API {exc.code}: {detail}") from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Nongsi demo GNSS and session simulator")
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument("--points", type=int, default=len(DEMO_ROUTE))
    parser.add_argument("--no-finish", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    started = request_json(
        args.api_url,
        "/api/sessions",
        "POST",
        {
            "farm_id": "FARM-001",
            "parcel_id": "PARCEL-001",
            "device_id": "sprayer-001",
            "crop": "open_field_citrus",
            "event_type": "spraying",
            "input_material_id": "WATER-DEMO",
            "product_name": "물(안전 시연용)",
            "dilution_ratio": 1,
            "nozzle_id": "nozzle-A",
            "location_mode": "demo",
        },
    )
    session_id = str(started["session_id"])
    print(f"session started: {session_id}")
    for sequence in range(max(1, args.points)):
        latitude, longitude = DEMO_ROUTE[sequence % len(DEMO_ROUTE)]
        point = request_json(
            args.api_url,
            f"/api/sessions/{session_id}/locations",
            "POST",
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "sequence": sequence,
                "latitude": latitude,
                "longitude": longitude,
                "accuracy_m": 4.5,
                "source": "demo_route",
            },
        )
        print(f"point {sequence + 1}/{args.points}: {point['state']}")
        if sequence + 1 < args.points:
            time.sleep(max(0.05, args.interval))
    if args.no_finish:
        print(f"session remains active: {session_id}")
        return
    event = request_json(
        args.api_url,
        f"/api/sessions/{session_id}/finish",
        "POST",
        {},
    )
    print(json.dumps(event, ensure_ascii=False, indent=2))
    print(f"JSON: {args.api_url}/api/sessions/{session_id}/export.json")
    print(f"CSV : {args.api_url}/api/sessions/{session_id}/export.csv")


if __name__ == "__main__":
    main()
