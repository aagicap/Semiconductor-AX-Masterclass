"""
ax_stats.py
6장 이후 실습이 함께 쓰는 불량률과 공정능력지수 계산 함수.
"""

import pandas as pd


def fail_rate(pass_fail: pd.Series) -> float:
    """불량 다이 비율(%)을 돌려준다. Pass_Fail 0이 불량이다."""
    return float((pass_fail == 0).mean() * 100)


def cp(values: pd.Series, lower: float, upper: float) -> float:
    """규격 폭을 산포 폭(6σ)으로 나눈다. 중심 위치는 보지 않는다."""
    return (upper - lower) / (6 * values.std())


def cpu(values: pd.Series, upper: float) -> float:
    """평균에서 규격 상한까지의 여유를 3σ로 나눈다."""
    return (upper - values.mean()) / (3 * values.std())


def cpl(values: pd.Series, lower: float) -> float:
    """평균에서 규격 하한까지의 여유를 3σ로 나눈다."""
    return (values.mean() - lower) / (3 * values.std())


def cpk(values: pd.Series, lower: float, upper: float) -> float:
    """양쪽 규격 가운데 가까운 쪽의 여유. Cpu와 Cpl 중 작은 값이다."""
    return min(cpu(values, upper), cpl(values, lower))
