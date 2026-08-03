# API 계약

실행 중 전체 OpenAPI 문서는 http://localhost:8000/docs 에서 확인합니다.

## REST

| Method | Path | 역할 |
|---|---|---|
| GET | `/health` | DB/MQTT readiness |
| GET | `/api/readings?limit=100` | 원본 센서 조회 |
| GET | `/api/devices/{device_id}/snapshot` | 최신 센서·상태 |
| GET | `/api/devices/{device_id}/live` | SSE telemetry stream |
| GET | `/api/catalog` | 농장·필지·장치·투입물·노즐 |
| POST | `/api/sessions` | 작업 시작 |
| GET | `/api/sessions/{session_id}` | 세션·경로 조회 |
| POST | `/api/sessions/{session_id}/locations` | GNSS 포인트 추가 |
| POST | `/api/sessions/{session_id}/finish` | 종료와 이벤트 계산 |
| GET | `/api/sessions/{session_id}/event` | 작업 이벤트 |
| GET | `/api/sessions/{session_id}/export.json` | JSON 파일 |
| GET | `/api/sessions/{session_id}/export.csv` | UTF-8 BOM CSV 파일 |
| POST | `/api/events/{event_id}/confirm` | 농가 확인/수정 메타데이터 |

세션 시작 최소 예시:

```json
{
  "farm_id": "FARM-001",
  "parcel_id": "PARCEL-001",
  "device_id": "sprayer-001",
  "crop": "open_field_citrus",
  "event_type": "spraying",
  "input_material_id": "WATER-DEMO",
  "dilution_ratio": 1,
  "nozzle_id": "nozzle-A",
  "location_mode": "demo"
}
```

위치는 timezone을 포함한 ISO 8601 `timestamp`, 세션 내 유일한 `sequence`, 위·경도, `browser_gnss` 또는 `demo_route` source를 사용합니다. 동일 장치에는 ACTIVE 세션을 하나만 허용합니다.

## MQTT

| Topic | 방향 | 상태 |
|---|---|---|
| `nongsi/devices/{device_id}/telemetry` | 장치 → 서버 | 구현, QoS 1 |
| `nongsi/devices/{device_id}/status` | 장치 → 서버 | 시뮬레이터 online/offline retained 발행 |
| `nongsi/sessions/{session_id}/location` | 서버 → 연계 시스템 | REST 저장 후 QoS 1 발행 |
| `nongsi/sessions/{session_id}/command` | 서버 → 장치 | 확장 계약, 실제 제어 없음 |
| `nongsi/sessions/{session_id}/event` | 서버 → 연계 시스템 | 이벤트 생성/농가 확인 후 QoS 1 발행 |

telemetry의 `(device_id, sequence)`가 중복 키입니다. topic 장치 ID와 payload 장치 ID가 다르거나 timezone 없는 timestamp이면 거부합니다. `command` 토픽은 안전상 실제 장비 제어를 하지 않으며 확장 계약만 예약합니다.
