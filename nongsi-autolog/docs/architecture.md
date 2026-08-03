# 아키텍처

## 데이터 흐름

```text
Python sensor simulator / 향후 ESP32
  └─ MQTT nongsi/devices/{id}/telemetry (QoS 1)
       └─ Mosquitto
            └─ FastAPI MQTT subscriber
                 ├─ sensor_readings (원본)
                 ├─ device_states (정제 특징 + 규칙 판정)
                 └─ SSE live snapshot

React PWA / route_simulator.py
  ├─ REST 작업 시작·종료
  └─ Browser GNSS 또는 deterministic demo route
       └─ location_points
            └─ WorkSessionService
                 ├─ 압력-유량 선형보간
                 ├─ Mock/KMA weather + cache
                 ├─ 설명 가능한 위험 규칙
                 └─ work_events + weather_snapshots + risk_assessments
```

원본 센서와 파생 상태, 최종 이벤트를 분리합니다. 도메인 테이블은 `source`, `version`, `quality_flag`, `created_at` 추적 필드를 가지며 SQLite에서 시작하지만 SQLAlchemy 계층을 통해 PostgreSQL/PostGIS로 교체할 수 있습니다.

## 상태 판정

`IDLE`, `MOVING`, `SPRAYING`, `PRESSURE_FAULT`, `SENSOR_FAULT`, `OFFLINE`을 이동평균, on/off 히스테리시스, 최소 유지시간으로 판정합니다. 임계값은 `backend/config/device_thresholds.json`의 기본값 위에 장치별 값을 병합합니다. 표시 신뢰도는 센서 완전성과 규칙 일치도를 설명하기 위한 값이지 학습 모델 정확도가 아닙니다.

## 기상청 연동 확인(2026-08-03)

공식 기상청 API허브의 동네예보 조회 서비스를 기준으로 구현했습니다.

- 인증: API허브에서 활용신청 후 발급되는 `authKey`
- 좌표: WGS84 위·경도를 기상청 5 km 격자 `nx`, `ny`로 변환
- 실황: `getUltraSrtNcst`, `base_date`, `base_time`, `nx`, `ny`
- 초단기예보: `getUltraSrtFcst`, 같은 격자와 발표시각 변수
- 사용 요소: `T1H`, `WSD`, `RN1`, `PTY`
- 공식 단기예보는 02시부터 3시간 간격으로 하루 8회 생산되며, 초단기예보는 최대 6시간 범위를 제공합니다.
- 이용은 무료지만 개발 자동승인/운영 심의와 기관 정책별 트래픽 제한이 있고 공공누리 제1유형 출처표시가 필요합니다.

공식 자료:

- https://apihub.kma.go.kr/apiList.do?apiMov=4.%20동네예보(초단기실황·초단기예보·단기예보)%20조회&seqApi=10&seqApiSub=286
- https://www.data.go.kr/data/15139470/openapi.do

현재 `KmaWeatherProvider`는 공식 JSON REST 응답을 파싱합니다. API 키가 없는 기본 데모는 Mock을 명시적으로 표시합니다. 레이더 HSR 원시 이진자료의 이동벡터 계산은 발표 MVP에 포함하지 않았고, 현재 강우 접근시간은 초단기예보의 최초 `PTY`/`RN1` 발생시각으로 계산합니다.

## 위험 규칙

- 종료 후 120분 이내 강수: high, 120~360분: medium
- 최대 풍속 5 m/s 이상: high, 3 m/s 이상: medium
- 압력 이상 60초 이상: high, 10초 이상: medium

이는 농업 처방이 아닌 재확인용 MVP 지표입니다.
