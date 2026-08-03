from __future__ import annotations

from typing import Any


def assess_risk(
    *,
    rain_approach_minutes: int | None,
    maximum_wind_ms: float,
    pressure_fault_seconds: float,
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    explanations: list[dict[str, Any]] = []

    if rain_approach_minutes is None:
        rain_level = "unknown"
        rain_text = "강수 접근시간을 확인하지 못했습니다."
    elif rain_approach_minutes <= 120:
        rain_level = "high"
        rain_text = "작업 종료 후 2시간 이내 강수가 예상되어 재확인이 필요합니다."
    elif rain_approach_minutes <= 360:
        rain_level = "medium"
        rain_text = "작업 종료 후 2~6시간 이내 강수가 예상됩니다."
    else:
        rain_level = "low"
        rain_text = "6시간 이내 강수 접근 가능성이 낮습니다."
    explanations.append({"code": "rain_exposure", "level": rain_level, "text": rain_text})

    if maximum_wind_ms >= 5.0:
        wind_level = "high"
        wind_text = "최대 풍속이 MVP 비산 경계값 5.0 m/s 이상입니다."
    elif maximum_wind_ms >= 3.0:
        wind_level = "medium"
        wind_text = "최대 풍속이 3.0 m/s 이상이므로 비산 가능성을 확인하세요."
    else:
        wind_level = "low"
        wind_text = "최대 풍속이 MVP 비산 주의값 미만입니다."
    explanations.append({"code": "wind_drift", "level": wind_level, "text": wind_text})

    if pressure_fault_seconds >= 60:
        pressure_level = "high"
    elif pressure_fault_seconds >= 10:
        pressure_level = "medium"
    else:
        pressure_level = "low"
    explanations.append(
        {
            "code": "pressure_fault",
            "level": pressure_level,
            "text": f"압력 저하 추정 구간은 {pressure_fault_seconds:.1f}초입니다.",
        }
    )
    return (
        {
            "rain_exposure": rain_level,
            "wind_drift": wind_level,
            "pressure_fault": pressure_level,
        },
        explanations,
    )
