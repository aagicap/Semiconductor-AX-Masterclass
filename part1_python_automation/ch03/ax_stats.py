"""
ax_stats.py
6장 이후 실습이 함께 쓰는 불량률과 공정능력지수 계산 함수.
"""

import pandas as pd


def fail_rate(pass_fail: pd.Series) -> float:
    """불량 다이 비율(%)을 돌려준다. Pass_Fail 0이 불량이다."""
    return float((pass_fail == 0).mean() * 100)


def cp(values: pd.Series, lower: float, upper: float) -> float:
    """기준 폭을 산포 폭(6σ)으로 나눈다. 중심 위치는 보지 않는다."""
    return (upper - lower) / (6 * values.std())


def cpk(
    values: pd.Series,
    lower: float | None = None,
    upper: float | None = None,
) -> float:
    """평균에서 가까운 기준까지의 거리를 3σ로 나눈다.
    한쪽 기준만 있으면 그쪽만 계산한다."""
    if lower is None and upper is None:
        raise ValueError("기준을 하나 이상 지정해야 한다")
    mean, sigma = values.mean(), values.std()
    gaps = []
    if lower is not None:
        gaps.append(mean - lower)
    if upper is not None:
        gaps.append(upper - mean)
    return min(gaps) / (3 * sigma)
