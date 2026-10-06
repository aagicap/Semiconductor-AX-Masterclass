"""
ch05_02_time_index.py
수집 시각을 인덱스로 두고 시간 구간을 골라 압력을 요약한다.
실행 위치: 저장소 루트
"""

import pandas as pd

from ax_frame import load_dataset
from ax_text import pad


def time_indexed() -> pd.DataFrame:
    """수집 시각을 인덱스로 둔 표를 돌려준다."""
    df = load_dataset().set_index("Timestamp")
    if not df.index.is_monotonic_increasing:
        raise ValueError("수집 시각이 시간순이 아니다")
    return df


def daily_pressure(df: pd.DataFrame) -> pd.DataFrame:
    """하루 단위로 묶어 압력의 개수·평균·표준편차를 구한다."""
    daily = df["Pressure"].resample("D").agg(["count", "mean", "std"])
    return daily.round(3)


def lot_window(df: pd.DataFrame, lot: str) -> tuple[pd.Timestamp, ...]:
    """로트 하나가 처리된 시간 구간(시작, 끝)을 돌려준다."""
    span = df.index[df["Lot_ID"] == lot]
    if span.empty:
        raise ValueError(f"존재하지 않는 Lot_ID: {lot}")
    return span.min(), span.max()


def report() -> None:
    """구간 선택과 리샘플링 결과를 출력한다."""
    df = time_indexed()
    print("=" * 62)
    print(" 시계열 인덱스: 시간 구간 선택과 리샘플링")
    print("=" * 62)
    first, last = df.index.min(), df.index.max()
    print(f"  수집 구간 : {first:%Y-%m-%d %H:%M} ~ {last:%m-%d %H:%M}")
    print(f"  인덱스 자료형 : {df.index.dtype}")
    print("-" * 62)
    day = df.loc["2026-01-03"]
    span = df.loc["2026-01-05 08:00":"2026-01-05 11:55"]
    morning = df.between_time("08:00", "08:55")
    print(f"  {pad('1월 3일 하루', 26)}{len(day):>5}행")
    print(f"  {pad('1월 5일 08:00~11:55', 26)}{len(span):>5}행")
    print(f"  {pad('매일 08:00~08:55', 26)}{len(morning):>5}행")
    start, end = lot_window(df, "LOT_03")
    hours = (end - start) / pd.Timedelta(hours=1)
    print(
        f"  LOT_03 구간 : {start:%m-%d %H:%M} ~ {end:%m-%d %H:%M}"
        f" ({hours:.1f}시간)"
    )
    print("-" * 62)
    daily = daily_pressure(df)
    print("  일별 압력 요약 (mTorr)")
    print(f"  {pad('날짜', 10)}{pad('행', 7)}{pad('평균', 10)}표준편차")
    for when, row in daily.iterrows():
        print(
            f"  {when:%m-%d}{'':5}{int(row['count']):<7}"
            f"{row['mean']:<10.3f}{row['std']:.3f}"
        )
    print("-" * 62)
    print("  [확인 범위] 압력의 시간 구간 요약만 계산했다")
    print("  구간 사이의 차이가 무엇 때문인지는 판단하지 않았다")
    print("=" * 62)


if __name__ == "__main__":
    report()
