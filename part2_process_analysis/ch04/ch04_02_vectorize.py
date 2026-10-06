"""
ch04_02_vectorize.py
같은 판정을 반복문과 벡터화로 각각 계산해 결과와 시간을 비교하고,
Copy-on-Write 동작을 점검한다.
"""

import timeit
import warnings

import numpy as np
import pandas as pd

from ax_frame import DTYPES, load_dataset
from ax_settings import DATA_DIR, THRESHOLD
from ax_text import pad

BENCH_PATH = DATA_DIR / "bench" / "integrated_x100.csv"
REPEAT = 5  # 반복 측정 횟수. 가장 짧은 값을 쓴다


def by_iterrows(frame: pd.DataFrame, limit: float) -> pd.Series:
    """행을 하나씩 돌며 판정한다. 2~3장 방식에 가장 가깝다."""
    flags = []
    for _, row in frame.iterrows():
        flags.append(row["Worst_Slack"] < limit)
    return pd.Series(flags, index=frame.index)


def by_apply(frame: pd.DataFrame, limit: float) -> pd.Series:
    """열 하나에 파이썬 함수를 행마다 적용한다."""
    return frame["Worst_Slack"].apply(lambda value: value < limit)


def by_vector(frame: pd.DataFrame, limit: float) -> pd.Series:
    """열 전체를 한 번에 비교한다."""
    return frame["Worst_Slack"] < limit


def best_ms(func, frame: pd.DataFrame, limit: float, n: int) -> float:
    """n번 실행해 가장 짧은 시간(ms)을 돌려준다."""
    runs = timeit.repeat(lambda: func(frame, limit), number=1, repeat=n)
    return min(runs) * 1000


def add_columns(frame: pd.DataFrame, limit: float) -> pd.DataFrame:
    """관찰 기준 판정과 단위 변환 열을 벡터화로 추가한다."""
    out = frame.copy()
    out["Is_Risky"] = out["Worst_Slack"] < limit
    out["Leakage_W"] = out["Leakage_Power"] / 1000
    out["Temp_Band"] = np.select(
        [out["Chamber_Temp"] < 70, out["Chamber_Temp"] < 80],
        ["70 미만", "70~80"],
        default="80 이상",
    )
    return out


def check_copy_rules(frame: pd.DataFrame) -> list[str]:
    """값을 바꾸는 세 가지 방식의 결과를 확인한다."""
    results = []
    work = frame.copy()
    before = work["Pressure"].iloc[0]

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        work[work["Pressure"] > 0]["Pressure"] = 0.0
    changed = work["Pressure"].iloc[0] != before
    name = caught[0].category.__name__ if caught else "경고 없음"
    results.append(
        f"[{'FAIL' if changed else 'OK'}] 연쇄 대입은 원본 미변경"
        f" ({name})"
    )

    part = work[work["Pressure"] > 0]
    part.loc[part.index[0], "Pressure"] = 0.0
    kept = work["Pressure"].iloc[0] == before
    results.append(
        f"[{'OK' if kept else 'FAIL'}] 골라낸 결과를 고쳐도 원본 유지"
    )

    work.loc[work.index[0], "Pressure"] = 0.0
    applied = work["Pressure"].iloc[0] == 0.0
    results.append(
        f"[{'OK' if applied else 'FAIL'}] .loc 대입은 원본에 반영"
    )

    label = work
    same = label is work
    results.append(
        f"[{'OK' if same else 'FAIL'}] 새 이름은 같은 객체를 가리킴"
    )
    return results


def show_columns(wide: pd.DataFrame) -> None:
    """파생 열을 추가한 결과를 요약해 출력한다."""
    band = pd.Series(wide["Temp_Band"]).value_counts().sort_index()
    print(
        f"  파생 열 추가 후 : {wide.shape[0]:,}행 × {wide.shape[1]}열"
    )
    risky = pd.Series(wide["Is_Risky"]).sum()
    missing = pd.Series(wide["Leakage_W"]).isna().sum()
    print(f"  위험 판정 : {risky:,}건")
    print(f"  누설 전력 단위 변환 결측 : {missing}건")
    for name, value in band.items():
        print(f"  온도 구간 {pad(str(name), 10)}{value:,}행")
    print("-" * 62)


def report() -> None:
    """결과 일치, 처리 시간, 파생 열, 복사 규칙을 출력한다."""
    print("=" * 62)
    print(" 벡터화 연산: 같은 판정을 세 가지 방식으로")
    print("=" * 62)
    df = load_dataset()

    flags = {
        "iterrows": by_iterrows(df, THRESHOLD),
        "apply": by_apply(df, THRESHOLD),
        "벡터화": by_vector(df, THRESHOLD),
    }
    counts = {name: int(series.sum()) for name, series in flags.items()}
    same = len(set(counts.values())) == 1
    print(f"  관찰 기준 : 슬랙 {THRESHOLD} ns 미만")
    for name, value in counts.items():
        print(f"  {pad(name, 12)}위험 {value:,}건")
    verdict = "모두 같다" if same else "서로 다르다"
    print(f"  세 방식의 판정 결과는 {verdict}")
    print("-" * 62)

    print(f"  {pad('방법', 12)}{pad('5,000행(ms)', 16)}500,000행(ms)")
    if BENCH_PATH.exists():
        big = pd.read_csv(
            BENCH_PATH,
            dtype=DTYPES,
            parse_dates=["Timestamp"],
            engine="pyarrow",
        )
    else:
        big = None
        print(
            "  (500,000행 파일이 없다. 4.1절 스크립트를 먼저 실행한다)"
        )
    for name, func in (
        ("iterrows", by_iterrows),
        ("apply", by_apply),
        ("벡터화", by_vector),
    ):
        small_ms = best_ms(func, df, THRESHOLD, REPEAT)
        big_ms = None  # 파일이 없으면 재지 않는다
        if big is not None:
            # 500,000행 반복문은 수 초가 걸리므로 한 번만 잰다
            big_n = 1 if name == "iterrows" else REPEAT
            big_ms = best_ms(func, big, THRESHOLD, big_n)
        print(
            f"  {pad(name, 12)}{pad(f'{small_ms:,.2f}', 16)}"
            f"{'-' if big_ms is None else f'{big_ms:,.2f}'}"
        )
    print(f"  [확인 범위] {REPEAT}회 측정 중 최솟값")
    print("  500,000행 iterrows만 1회. 시간은 실행 환경에 따라 다르다")
    print("-" * 62)

    show_columns(add_columns(df, THRESHOLD))

    print("  [복사 규칙 점검]")
    for line in check_copy_rules(df):
        print(f"  {line}")
    print(
        "  [확인 범위] 값을 바꾸는 방식만 확인했다. 값의 타당성은 4.3절"
    )
    print("=" * 62)


if __name__ == "__main__":
    report()
