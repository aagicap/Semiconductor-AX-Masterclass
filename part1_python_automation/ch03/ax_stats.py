"""
ax_stats.py
6장 이후 실습이 함께 쓰는 불량률과 공정능력지수 계산 함수.
9장부터는 웨이퍼 단위 요약도 여기서 만든다.
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


def wafer_summary(process: pd.DataFrame) -> pd.DataFrame:
    """다이 관측을 (Lot_ID, Wafer_ID)별로 묶어 관측 사실만 요약한다.
    fail_ratio는 0~1 비율이다(fail_rate()는 %를 돌려준다).
    경고 기준·완료일 같은 보고 규칙은 각 리포트가 정한다."""
    marked = process.assign(fail=process["Pass_Fail"].eq(0))
    out = (
        marked.groupby(["Lot_ID", "Wafer_ID"])
        .agg(
            Equipment_ID=("Equipment_ID", "first"),
            equipments=("Equipment_ID", "nunique"),
            dies=("Pass_Fail", "size"),
            fails=("fail", "sum"),
            last_seen=("Timestamp", "max"),
        )
        .reset_index()
    )
    if (out["equipments"] > 1).any():  # 장비는 웨이퍼 단위로 배정된다
        raise ValueError("장비가 둘 이상 기록된 웨이퍼가 있다")
    out.insert(6, "fail_ratio", out["fails"] / out["dies"])
    return out.drop(columns="equipments")
