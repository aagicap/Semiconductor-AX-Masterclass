"""
ch02_03_aggregate.py
파싱한 레코드를 딕셔너리와 집합으로 집계한다.
탐색 비용이 자료 구조에 따라 어떻게 달라지는지 함께 확인한다.
"""

import unicodedata
from collections import Counter, defaultdict

from ch02_02_log_parse import LOG_DIR, PATTERN, parse_file

THRESHOLD = 0.05  # 교육용 관찰 기준. 실제 규격이 아니다.


def pad(text: str, width: int) -> str:
    """한글은 폭 2, 영문은 폭 1로 계산해 출력 열을 맞춘다."""
    wide = ("W", "F")
    display = sum(
        2 if unicodedata.east_asian_width(ch) in wide else 1
        for ch in text
    )
    return text + " " * max(0, width - display)


def load_records() -> list[dict]:
    """리포트 전체를 읽어 레코드 목록으로 만든다."""
    records = []
    for path in sorted(LOG_DIR.glob(PATTERN)):
        records.extend(parse_file(path))
    return records


def summarize_by_lot(records: list[dict]) -> dict[str, dict]:
    """로트별 건수와 위험 건수를 한 번의 순회로 집계한다."""
    summary = defaultdict(lambda: {"total": 0, "risky": 0})
    for record in records:
        slot = summary[record["lot_id"]]
        slot["total"] += 1
        slack = record["worst_slack"]
        if slack is not None and slack < THRESHOLD:
            slot["risky"] += 1
    return dict(summary)


def report() -> None:
    """집계 결과를 출력한다."""
    records = load_records()
    if not records:
        print(
            "[FAIL] 레코드가 없다. log_generator.py 를 먼저 실행한다."
        )
        return

    print("=" * 62)
    print(" 설계 리포트 집계")
    print("=" * 62)
    print(f"  레코드 {len(records):,}건")

    # 1) 로트별 집계
    print("-" * 62)
    print(f"  {pad('로트', 10)}{pad('건수', 8)}{pad('위험', 8)}비율")
    print("-" * 62)
    for lot, slot in sorted(summarize_by_lot(records).items()):
        ratio = slot["risky"] / slot["total"] * 100
        print(
            f"  {pad(lot, 10)}{pad(str(slot['total']), 8)}"
            f"{pad(str(slot['risky']), 8)}{ratio:5.1f}%"
        )

    # 2) 경로별 등장 빈도
    counter = Counter(r["path_id"] for r in records)
    print("-" * 62)
    print("  경로별 등장 빈도 상위 5건")
    for path_id, count in counter.most_common(5):
        print(f"    {pad(path_id, 14)}{count:>5}회")

    # 3) 집합 연산: 웨이퍼를 어떻게 세는가
    only_wafer = {r["wafer_id"] for r in records}
    full_key = {(r["lot_id"], r["wafer_id"]) for r in records}

    print("-" * 62)
    print(f"  웨이퍼 번호만으로 센 개수 : {len(only_wafer)}개")
    print(f"  로트와 함께 센 개수       : {len(full_key)}개")

    risky_wafers = {
        (r["lot_id"], r["wafer_id"])
        for r in records
        if r["worst_slack"] is not None and r["worst_slack"] < THRESHOLD
    }
    leak_wafers = {
        (r["lot_id"], r["wafer_id"])
        for r in records
        if r["leakage_power"] is None
    }

    print("-" * 62)
    print(f"  위험 구간이 나온 웨이퍼   : {len(risky_wafers)}개")
    print(f"  누설 결측이 있는 웨이퍼   : {len(leak_wafers)}개")
    both = risky_wafers & leak_wafers
    clean = full_key - risky_wafers
    print(f"  두 조건 모두 해당         : {len(both)}개")
    print(f"  위험이 한 번도 없던 웨이퍼: {len(clean)}개")
    print("=" * 62)


if __name__ == "__main__":
    report()
