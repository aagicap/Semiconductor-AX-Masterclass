"""
ch03_01_module_pipeline.py
공통 모듈을 조립해 로트별 요약을 만들고 2.4절 결과와 대조한다.
"""

import json

from ax_settings import LOG_DIR, PARSED_DIR, THRESHOLD
from ax_sta import load_records
from ax_summary import group_by_lot, summarize
from ax_text import pad


def load_previous(lot_id: str) -> dict | None:
    """2.4절이 저장한 로트 요약을 읽는다. 파일이 없으면 None."""
    path = PARSED_DIR / f"{lot_id.lower()}.json"
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload["summary"]


def report() -> None:
    """로트별 요약을 출력하고 이전 결과와 비교한다."""
    print("=" * 62)
    print(" 모듈 조립 파이프라인: 로트별 요약과 2.4절 대조")
    print("=" * 62)

    records = load_records()
    if not records:
        print(f"  [FAIL] 리포트 파일이 없다 : {LOG_DIR}")
        print("         data/log_generator.py 를 먼저 실행한다.")
        print("=" * 62)
        return

    print(f"  관찰 기준 : 슬랙 {THRESHOLD} ns 미만")
    print("-" * 62)
    print(f"  {pad('로트', 10)}{pad('건수', 8)}{pad('위험', 8)}대조")
    print("-" * 62)

    compared = matched = 0
    for lot_id, group in sorted(group_by_lot(records).items()):
        summary = summarize(group)
        before = load_previous(lot_id)
        if before is None:
            verdict = "비교 대상 없음"
        else:
            compared += 1
            if summary == before:
                matched += 1
                verdict = "일치"
            else:
                verdict = f"불일치 (이전 위험 {before['risky_count']})"
        count = pad(str(summary["record_count"]), 8)
        risky = pad(str(summary["risky_count"]), 8)
        print(f"  {pad(lot_id, 10)}{count}{risky}{verdict}")

    print("-" * 62)
    print(f"  대조한 로트 {compared}개 중 일치 {matched}개")
    print("  [확인 범위] 요약 항목만 대조했다. 레코드 본문은 3.3절")
    print("=" * 62)


if __name__ == "__main__":
    report()
