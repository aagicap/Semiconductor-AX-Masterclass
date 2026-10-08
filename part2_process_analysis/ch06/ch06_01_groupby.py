"""
ch06_01_groupby.py
장비별·로트별로 다이를 묶어 불량률을 집계하고,
로트와 장비를 함께 묶으면 무엇이 달라지는지 본다.
실행 위치: 저장소 루트
"""

import pandas as pd

from ax_frame import load_dataset
from ax_stats import fail_rate
from ax_text import pad

# 웨이퍼는 두 열을 함께 써야 유일하다(Wafer_ID는 로트마다 반복)
WAFER_KEY = ["Lot_ID", "Wafer_ID"]


def by_equipment(df: pd.DataFrame) -> pd.DataFrame:
    """장비별 웨이퍼 수, 다이 수, 불량 다이 수, 불량률을 집계한다."""
    dies = df.groupby("Equipment_ID").agg(
        dies=("Pass_Fail", "size"),
        fails=("Pass_Fail", lambda s: int((s == 0).sum())),
        rate=("Pass_Fail", fail_rate),
    )
    wafers = (
        df.drop_duplicates(WAFER_KEY).groupby("Equipment_ID").size()
    )
    return dies.assign(wafers=wafers)


def by_lot_equipment(df: pd.DataFrame) -> pd.DataFrame:
    """로트와 장비를 함께 키로 묶어 웨이퍼 수와 불량률을 펼친다."""
    table = df.groupby(["Lot_ID", "Equipment_ID"]).agg(
        wafers=("Wafer_ID", "nunique"),
        rate=("Pass_Fail", fail_rate),
    )
    return table.unstack("Equipment_ID")  # 장비를 열 방향으로 펼친다


def report() -> None:
    """장비별, 로트별, 로트×장비 집계 결과를 출력한다."""
    df = load_dataset()
    print("=" * 62)
    print(" GroupBy 집계: 장비별·로트별 불량률")
    print("=" * 62)
    eq = by_equipment(df)
    print("  장비        웨이퍼   다이   불량   불량률")
    for row in eq.itertuples():
        print(
            f"  {pad(str(row.Index), 12)}{row.wafers:>4}장"
            f"  {row.dies:>5}  {row.fails:>5}  {row.rate:>6.2f}%"
        )
    fails = int((df["Pass_Fail"] == 0).sum())
    rate = fail_rate(df["Pass_Fail"])
    print(
        f"  {pad('전체', 12)}{int(eq.wafers.sum()):>4}장"
        f"  {len(df):>5}  {fails:>5}  {rate:>6.2f}%"
    )
    print("-" * 62)
    lot = df.groupby("Lot_ID")["Pass_Fail"].agg(fail_rate)
    table = by_lot_equipment(df)
    print("  로트     로트 전체   웨이퍼 A/B   A 불량률   B 불량률")
    for lot_id in table.index:
        w = table.loc[lot_id, "wafers"].fillna(0).astype(int)
        r = table.loc[lot_id, "rate"]
        a = (
            "     -"
            if pd.isna(r["ETCHER_A"])
            else f"{r['ETCHER_A']:5.1f}%"
        )
        print(
            f"  {lot_id}    {lot[lot_id]:5.1f}%"
            f"      {w['ETCHER_A']} / {w['ETCHER_B']}"
            f"      {a}     {r['ETCHER_B']:5.1f}%"
        )
    print("-" * 62)
    print("  [확인 범위] 묶음별 다이 수와 불량 다이 수만 셌다")
    print("  불량이 생긴 원인은 판단하지 않았다")
    print("=" * 62)


if __name__ == "__main__":
    report()
