"""
ch04_01_load_dataset.py
통합 CSV를 기본 설정과 자료형 지정 두 방식으로 읽어
자료형, 메모리, 적재 시간을 비교한다.
"""

import time
from pathlib import Path
from typing import Literal

import pandas as pd

from ax_frame import CSV_PATH, DTYPES, load_dataset
from ax_settings import DATA_DIR
from ax_text import pad

BENCH_DIR = DATA_DIR / "bench"
REPEAT = 5  # 적재를 반복해 가장 빠른 값을 쓴다


def kib(df: pd.DataFrame) -> float:
    """문자열 내용까지 포함한 메모리 사용량(KiB)."""
    return df.memory_usage(deep=True).sum() / 1024


def best_ms(path: Path, engine: Literal["c", "pyarrow"]) -> float:
    """자료형을 지정해 REPEAT번 읽고 가장 짧은 시간(ms)을 돌려준다."""
    times = []
    for _ in range(REPEAT):
        start = time.perf_counter()
        pd.read_csv(
            path, dtype=DTYPES, parse_dates=["Timestamp"], engine=engine
        )
        times.append(time.perf_counter() - start)
    return min(times) * 1000


def make_bench_file(df: pd.DataFrame, times: int) -> Path:
    """측정용으로 행을 복제한 CSV를 만든다. 분석에는 쓰지 않는다."""
    BENCH_DIR.mkdir(exist_ok=True)
    path = BENCH_DIR / f"integrated_x{times}.csv"
    if not path.exists():
        big = pd.concat([df] * times, ignore_index=True)
        big.to_csv(path, index=False)
    return path


def report() -> None:
    """두 적재 방식의 자료형·메모리·시간을 출력한다."""
    print("=" * 62)
    print(" 통합 CSV 적재: 기본 설정 대 자료형 지정")
    print("=" * 62)
    if not CSV_PATH.exists():
        print(f"  [FAIL] 통합 CSV가 없다 : {CSV_PATH}")
        print("         data/data_generator.py 를 먼저 실행한다.")
        print("=" * 62)
        return

    raw = pd.read_csv(CSV_PATH)
    typed = load_dataset()
    print(f"  크기 : {typed.shape[0]:,}행 × {typed.shape[1]}열")
    print("-" * 62)
    print(f"  {pad('열', 16)}{pad('기본 설정', 18)}자료형 지정")
    for col in ("Timestamp", "Lot_ID", "Die_X", "Pass_Fail"):
        before = str(raw[col].dtype)
        after = str(typed[col].dtype)
        print(f"  {pad(col, 16)}{pad(before, 18)}{after}")
    print(
        f"  {pad('메모리(KiB)', 16)}{pad(f'{kib(raw):.1f}', 18)}"
        f"{kib(typed):.1f}"
    )
    print("-" * 62)

    big = make_bench_file(raw, 100)
    print(f"  적재 시간 (ms, {REPEAT}회 중 최솟값, 자료형 지정)")
    print(f"  {pad('파일', 20)}{pad('C 엔진', 12)}pyarrow 엔진")
    for label, path in (("5,000행", CSV_PATH), ("500,000행", big)):
        c_ms = best_ms(path, "c")
        a_ms = best_ms(path, "pyarrow")
        print(f"  {pad(label, 20)}{pad(f'{c_ms:.1f}', 12)}{a_ms:.1f}")
    print("-" * 62)
    print(
        "  [확인 범위] 시간은 실행 환경(CPU 코어 수 등)에 따라 다르다"
    )
    print("  500,000행은 측정용 복제 파일이며 분석에는 쓰지 않는다")
    print("=" * 62)


if __name__ == "__main__":
    report()
