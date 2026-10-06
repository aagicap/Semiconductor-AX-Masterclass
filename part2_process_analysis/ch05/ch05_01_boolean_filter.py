"""
ch05_01_boolean_filter.py
교육용 확인 범위를 벗어난 압력 기록을 불리언 마스크로 골라낸다.
실행 위치: 저장소 루트
"""

import pandas as pd

from ax_frame import load_dataset
from ax_text import pad

# 교육용 확인 범위(15.0 ± 1.5 mTorr). 검증 규격도 관리 한계도 아니다
CENTER, MARGIN = 15.0, 1.5
LOW, HIGH = CENTER - MARGIN, CENTER + MARGIN
SHOW = ["Timestamp", "Lot_ID", "Wafer_ID", "Die_X", "Die_Y", "Pressure"]


def pressure_masks(frame: pd.DataFrame) -> dict[str, pd.Series]:
    """범위 아래, 범위 위, 범위 밖을 참·거짓 열로 돌려준다."""
    pressure = frame["Pressure"]
    below = pressure < LOW
    above = pressure > HIGH
    return {"below": below, "above": above, "out": below | above}


def mark_out(frame: pd.DataFrame) -> pd.DataFrame:
    """원본은 두고, 범위 밖 표시 열을 더한 사본을 돌려준다."""
    work = frame.copy()
    work["Pressure_Out"] = ~work["Pressure"].between(LOW, HIGH)
    return work


def report() -> None:
    """마스크 결과와 골라낸 행을 출력한다."""
    df = load_dataset()
    masks = pressure_masks(df)
    out = masks["out"]
    print("=" * 62)
    print(" 불리언 인덱싱: 압력 교육용 확인 범위 밖 기록 격리")
    print("=" * 62)
    print(f"  확인 범위 : {LOW:.1f} ~ {HIGH:.1f} mTorr (교육용)")
    print(f"  {pad('범위 아래', 14)}{int(masks['below'].sum()):>5}행")
    print(f"  {pad('범위 위', 14)}{int(masks['above'].sum()):>5}행")
    print(
        f"  {pad('범위 밖 합계', 14)}{int(out.sum()):>5}행"
        f"  ({out.mean() * 100:.2f}%)"
    )
    print("-" * 62)
    picked = df.loc[out, SHOW]
    print("  골라낸 기록 (앞 5행)")
    for row in picked.head(5).itertuples(index=False):
        when = row.Timestamp.strftime("%m-%d %H:%M")
        print(
            f"  {when}  {row.Lot_ID}  {row.Wafer_ID}"
            f"  ({row.Die_X},{row.Die_Y})  {row.Pressure:.2f}"
        )
    print("-" * 62)
    lot = df["Lot_ID"] == "LOT_03"
    both = out & lot
    print(f"  조건 결합 : 범위 밖 & LOT_03  {int(both.sum())}행")
    marked = mark_out(df)
    print(
        f"  표시 열을 더한 사본 {marked.shape[1]}열"
        f" / 원본 {df.shape[1]}열"
    )
    print("  [확인 범위] 교육용 범위 밖인 기록을 골라 표시만 했다")
    print("  규격 위반이나 공정 이상 여부는 판단하지 않았다")
    print("=" * 62)


if __name__ == "__main__":
    report()
