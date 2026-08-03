# 농시 AutoLog

현재 구현 범위는 Phase 1의 첫 체크포인트입니다. Python 시뮬레이터가 실제 ESP32와 동일한 JSON 구조로 MQTT telemetry를 발행하고, FastAPI 백엔드가 payload를 검증한 뒤 콘솔과 SQLite `sensor_readings` 테이블에 저장합니다. React, 작업 상태 판정, GNSS, 기상 결합, ESP32 펌웨어는 아직 구현하지 않았습니다.

## Phase 0 — Windows 개발환경 확인

PowerShell에서 다음 명령으로 설치 여부와 버전을 확인합니다.

```powershell
Get-ComputerInfo | Select-Object WindowsProductName, WindowsVersion, OsArchitecture
docker --version
docker compose version
docker info
python --version
py -0p
node --version
npm --version
git --version
code --version
pio --version
```

필수: Docker Desktop(Compose v2 포함), Python 3.11 이상, Git. Node.js와 PlatformIO는 이후 프론트엔드/ESP32 단계에서 사용합니다. `docker info`가 오류를 내면 Docker Desktop을 시작한 뒤 다시 확인합니다.

## 저장소 디렉터리 생성 명령

이 저장소는 이미 생성되어 있습니다. 같은 구조를 수동으로 다시 만들 때의 PowerShell 명령은 다음과 같습니다.

```powershell
$project = Join-Path (Get-Location) 'nongsi-autolog'
$directories = @(
  'firmware/esp32-sprayer/src',
  'backend/app/api', 'backend/app/core', 'backend/app/db',
  'backend/app/models', 'backend/app/schemas',
  'backend/app/services/mqtt', 'backend/app/services/event_detection',
  'backend/app/services/weather', 'backend/app/services/risk', 'backend/tests',
  'frontend/src', 'simulator/scenarios', 'mosquitto/config',
  'data/samples', 'docs'
)
$directories | ForEach-Object {
  New-Item -ItemType Directory -Force -Path (Join-Path $project $_) | Out-Null
}
```

## 한 명령으로 실행

Docker Desktop이 실행 중인 상태에서 저장소 루트에서 실행합니다.

```powershell
Set-Location .\nongsi-autolog
docker compose up --build
```

기본값은 `.env` 없이도 동작합니다. 값을 바꾸려면 먼저 `Copy-Item .env.example .env`를 한 번 실행합니다. Compose는 Mosquitto, FastAPI, 시뮬레이터를 순서대로 시작합니다. 시뮬레이터는 1초마다 telemetry를 전송합니다. 개발용 Mosquitto 설정은 익명 접속을 허용하므로 외부 네트워크에 그대로 배포하지 마십시오.

## 저장 결과 검증

별도 PowerShell 창에서 실행합니다.

```powershell
Invoke-RestMethod http://localhost:8000/health | ConvertTo-Json
Invoke-RestMethod 'http://localhost:8000/api/readings?limit=3' | ConvertTo-Json -Depth 5
docker compose logs --tail 30 backend
docker compose logs --tail 10 simulator
```

정상이라면 `/health`의 HTTP 상태가 200이고 `status`가 `ok`, `mqtt_connected`가 `true`이며 `/api/readings`의 `total`이 계속 증가합니다. DB 또는 MQTT가 준비되지 않으면 `/health`는 의도적으로 HTTP 503과 `degraded`를 반환합니다. SQLite 파일은 `data/nongsi.db`에 생성됩니다. 종료 명령은 다음과 같습니다.

```powershell
docker compose down
```

`docker compose down -v`는 broker 볼륨까지 삭제하므로 데이터 초기화가 명시적으로 필요할 때만 사용합니다.

## Docker 없이 백엔드 테스트

MQTT broker 연결까지 확인하려면 Docker가 필요합니다. payload 검증과 SQLite 저장 로직은 로컬에서 독립적으로 테스트할 수 있습니다.

```powershell
Set-Location .\nongsi-autolog\backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

broker만 Docker로 실행하고 백엔드·시뮬레이터를 로컬 Python으로 실행하려면 각각 별도 PowerShell 창에서 다음을 사용합니다.

```powershell
# 창 1: 저장소 루트
docker compose up mosquitto

# 창 2: backend
$env:MQTT_HOST = 'localhost'
$env:DATABASE_URL = 'sqlite:///../data/nongsi.db'
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000

# 창 3: 저장소 루트
.\backend\.venv\Scripts\python.exe .\simulator\sensor_simulator.py --count 10
```

## 현재 MQTT 계약

- 구독 토픽: `nongsi/devices/{device_id}/telemetry`
- QoS: 1
- 중복 기준: `(device_id, sequence)`
- timestamp: timezone이 포함된 ISO 8601만 허용
- topic의 `device_id`와 payload의 `device_id`가 다르면 거부
- IMU, pump, pressure 결측은 저장하되 `quality_flag`에 기록

API 문서는 실행 후 `http://localhost:8000/docs`에서 확인할 수 있습니다.
