# 농시 AutoLog

노지감귤 방제기의 센서 상태, 스마트폰 GNSS 경로, 기상 위험을 하나의 추적 가능한 작업 이벤트로 만드는 발표용 MVP입니다. 현재 Phase 1 센서 없는 End-to-End 데모가 완성되어 있으며 실제 농약이 아닌 저전압 물 펌프 시연을 전제로 합니다. 상태 판정과 신뢰도는 학습 AI가 아닌 설명 가능한 규칙 기반 기준모델입니다.

## 1분 실행

요구사항은 Windows 11, Docker Desktop(Compose v2), Git입니다. Docker Desktop을 실행한 뒤 저장소 루트에서 다음 한 명령을 실행합니다.

```powershell
Set-Location .\nongsi-autolog
docker compose up --build
```

서비스가 준비되면 다음 주소를 엽니다.

- PWA/대시보드: http://localhost:5173
- FastAPI 문서: http://localhost:8000/docs
- 상태 확인: http://localhost:8000/health

화면에서 `새 작업 시작` → `데모 경로` → `기록 시작`을 누릅니다. 시뮬레이터가 약 25초 동안 `IDLE → MOVING → SPRAYING → PRESSURE_FAULT`를 순환하며 지도 경로가 2초마다 추가됩니다. `작업 종료`를 누르면 작업 이벤트와 모의 강우 95분 위험, JSON/CSV 다운로드가 생성됩니다.

브라우저 없이 같은 흐름을 실행할 수도 있습니다.

```powershell
python .\simulator\route_simulator.py --interval 2 --points 15
```

## 검증

```powershell
Invoke-RestMethod http://localhost:8000/health | ConvertTo-Json
Invoke-RestMethod 'http://localhost:8000/api/devices/sprayer-001/snapshot' | ConvertTo-Json -Depth 6
docker compose ps
docker compose logs --tail 30 backend simulator
```

백엔드 단위·서비스 테스트와 프론트 프로덕션 빌드는 다음과 같습니다.

```powershell
Set-Location .\backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q

Set-Location ..\frontend
npm install
npm run build
```

현재 테스트는 MQTT payload/중복 sequence/잘못된 timestamp/센서 결측/상태 전환/최소 유지시간/압력 이상/유량 보간/기상 캐시 복구/이벤트/CSV/위치 없음/KMA 격자 변환을 다룹니다.

## 기상 공급자

기본값은 키 없이도 재현 가능한 `MockWeatherProvider`입니다. 기상청 API허브 키가 있으면 `.env.example`을 `.env`로 복사하고 `KMA_AUTH_KEY`를 설정합니다.

```powershell
Copy-Item .env.example .env
# .env의 KMA_AUTH_KEY=... 입력
docker compose up -d --build backend frontend
```

키가 있으면 `KmaWeatherProvider`, 없으면 Mock이 선택됩니다. 두 공급자 모두 30분 캐시로 감싸며 공급자 장애 시 마지막 캐시를 사용합니다. 공식 API 사양과 현재 한계는 [docs/architecture.md](docs/architecture.md)에 기록했습니다.

## 데이터와 안전

- SQLite 원본/결과: `data/nongsi.db`
- 상태 임계값: `backend/config/device_thresholds.json`
- 물 보정표: 시작 시 DB의 `device_calibrations`에 데모 값으로 시드
- 추정 살포량은 `압력별 선형보간 유량 × 분사시간`이며 정밀 계량값이 아닙니다.
- 실제 농약, 고전류 방제기, 실제 배관에는 연결하지 않습니다. 하드웨어 사양 확인 전 회로 연결을 진행하지 마십시오.
- `.env`, DB, 빌드 결과는 Git에 포함되지 않습니다.

## 문서

- [아키텍처와 데이터 흐름](docs/architecture.md)
- [REST/MQTT API](docs/api.md)
- [발표 시연 순서](docs/demo-script.md)
- [하드웨어 안전 및 Phase 2](docs/hardware.md)

종료는 `docker compose down`입니다. 데이터 초기화가 명시적으로 필요할 때만 `docker compose down -v`를 사용하십시오.
