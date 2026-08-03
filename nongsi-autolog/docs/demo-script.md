# 1분 발표 시연

## 사전 준비

```powershell
docker compose up -d --build
docker compose ps
```

모든 health가 healthy인지 확인하고 http://localhost:5173 을 엽니다. 화면 상단 `WATER-ONLY DEMO`, 기상 결과의 `MOCK` 표시를 그대로 보여주어 실제 농약/실기상으로 오해되지 않게 합니다.

## 발표 흐름

1. 대시보드에서 전류·압력·진동과 `IDLE/MOVING/SPRAYING/PRESSURE_FAULT` 상태가 센서 원본으로 바뀌는 것을 보여줍니다.
2. `새 작업 시작`을 누르고 농장, 필지, 물, 희석배수, nozzle-A, 데모 경로를 확인합니다.
3. `기록 시작` 후 지도 선이 늘어나고 이동/분사/압력 이상 구간의 색이 달라지는 것을 보여줍니다.
4. `SPRAYING` 뒤 압력이 낮아져 `PRESSURE_FAULT`가 보이면 `작업 종료`를 누릅니다.
5. 결과에서 분사시간, 보정 기반 추정 L, 평균/최저압력, 95분 후 강우 접근과 위험 설명을 확인합니다.
6. `내용 확인`, `JSON 내려받기`, `CSV 내려받기`를 보여줍니다.

상태 주기는 25초입니다. 발표 타이밍을 통제하려면 별도 PowerShell에서 다음을 실행하고 브라우저 결과를 새로 시작합니다.

```powershell
python .\simulator\route_simulator.py --interval 1.5 --points 15
```

## 복구

```powershell
docker compose restart backend simulator frontend
Invoke-RestMethod http://localhost:8000/health
```

ACTIVE 세션 충돌이 발생하면 이전 브라우저 세션에서 `작업 종료`를 누릅니다. DB를 지우는 시연 복구는 데이터 손실이 있으므로 발표 전에만 백업 후 수행합니다.
