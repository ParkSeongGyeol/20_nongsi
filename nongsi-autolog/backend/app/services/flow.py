from __future__ import annotations


def interpolate_flow_lpm(
    pressure_bar: float,
    calibration: list[dict[str, float]],
) -> float:
    """Linearly interpolate calibrated water flow; clamp outside the table."""

    if not calibration:
        raise ValueError("calibration table must not be empty")
    points = sorted(calibration, key=lambda point: point["pressure_bar"])
    if pressure_bar <= points[0]["pressure_bar"]:
        return points[0]["flow_lpm"]
    if pressure_bar >= points[-1]["pressure_bar"]:
        return points[-1]["flow_lpm"]

    for lower, upper in zip(points, points[1:]):
        if lower["pressure_bar"] <= pressure_bar <= upper["pressure_bar"]:
            span = upper["pressure_bar"] - lower["pressure_bar"]
            ratio = (pressure_bar - lower["pressure_bar"]) / span
            return lower["flow_lpm"] + ratio * (
                upper["flow_lpm"] - lower["flow_lpm"]
            )
    raise RuntimeError("pressure interpolation interval not found")

