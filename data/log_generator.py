"""
log_generator.py
통합 데이터셋의 설계 지표를 STA 타이밍 리포트 형태의 로그로
되돌려 생성한다. 2장 파싱 실습의 입력 자료이며, 파싱 결과는
alphachip_v2_integrated_data.csv의 설계 컬럼과 일치한다.
"""

import random
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent
SOURCE = BASE / "alphachip_v2_integrated_data.csv"
OUT_DIR = BASE / "logs"
TOOL = "TimingSign v4.2.1"


def build_line(row: pd.Series, rng: random.Random) -> str:
    """한 다이의 설계 지표를 리포트 한 줄로 만든다."""
    head = (
        f"Path: {row.Path_ID}  wafer {row.Wafer_ID}  "
        f"die ({row.Die_X},{row.Die_Y})"
    )
    state = "MET" if row.Worst_Slack >= 0 else "VIOLATED"
    slack = f"slack {state}  {row.Worst_Slack:.3f}"
    freq = f"freq {row.Operating_Freq:.2f}"

    # 누설 전력은 결측일 수 있다. 그 행은 항목 자체가 빠진다.
    if pd.isna(row.Leakage_Power):
        parts = [slack, freq]
    else:
        leak = f"leak {row.Leakage_Power:.2f}"
        parts = [slack, leak, freq]
        # 툴 설정에 따라 항목 순서가 바뀌는 상황을 모사한다.
        if rng.random() < 0.10:
            parts = [leak, slack, freq]

    tail = ""
    if row.Error_Code == "ERR-G202":
        tail = "  (CHAMBER_ALARM)"

    gap = " " * rng.choice([1, 2, 3])
    return head + gap + gap.join(parts) + tail


def write_lot(
    lot_id: str, frame: pd.DataFrame, rng: random.Random
) -> Path:
    """로트 하나의 리포트 파일을 만든다."""
    stamp = frame.Timestamp.iloc[0]
    lines = [
        f"# STA Timing Report  (Tool: {TOOL})",
        f"# Lot: {lot_id}   Generated: {stamp}",
        "# " + "-" * 60,
    ]
    for _, row in frame.iterrows():
        lines.append(build_line(row, rng))
    lines.append(f"# End of report   total paths: {len(frame)}")

    path = OUT_DIR / f"sta_{lot_id.lower()}.log"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    """로트별 리포트 파일을 생성한다."""
    if not SOURCE.exists():
        print(f"[FAIL] 원본 데이터 없음 : {SOURCE}")
        print("       먼저 data_generator.py 를 실행한다.")
        return

    df = pd.read_csv(SOURCE)
    OUT_DIR.mkdir(exist_ok=True)
    rng = random.Random(42)

    made = 0
    for lot_id, frame in df.groupby("Lot_ID", sort=True):
        write_lot(lot_id, frame, rng)
        made += 1

    print(f"[Success] {made}개 로트의 STA 리포트를 생성했습니다.")
    print(f"[저장 경로] {OUT_DIR}")


if __name__ == "__main__":
    main()
