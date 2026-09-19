"""
ch03_03_parsing_engine.py
형식이 섞인 리포트 폴더를 파싱 엔진으로 읽어 JSON 자산을 만들고,
2.4절 JSON과 생성 시각을 뺀 전 항목을 대조한다.
"""

import json
from datetime import datetime

from ax_engine import (
    ParsingEngine,
    StaParserV4,
    StaParserV5,
    build_payload,
)
from ax_settings import DATA_DIR, PARSED_DIR, THRESHOLD
from ax_text import pad

MIXED_DIR = DATA_DIR / "logs_mixed"
OUT_DIR = DATA_DIR / "parsed_engine"


def without_time(payload: dict) -> dict:
    """비교에서 실행 시각을 뺀 사본을 만든다."""
    return {k: v for k, v in payload.items() if k != "generated_at"}


def compare(lot_id: str, payload: dict) -> str:
    """2.4절이 저장한 같은 로트의 JSON과 비교한 결과를 돌려준다."""
    path = PARSED_DIR / f"{lot_id.lower()}.json"
    if not path.exists():
        return "비교 대상 없음"
    before = json.loads(path.read_text(encoding="utf-8"))
    if without_time(before) == without_time(payload):
        return "일치"
    return "불일치"


def report() -> None:
    """형식 판별, JSON 저장, 2.4절 대조 결과를 출력한다."""
    print("=" * 62)
    print(" 파싱 엔진: 혼합 형식 리포트 → JSON 자산")
    print("=" * 62)

    parsers = [StaParserV4(), StaParserV5()]  # 새 형식은 여기에 추가
    engine = ParsingEngine(parsers, MIXED_DIR)
    try:
        lots = engine.run()
    except FileNotFoundError as error:
        print(f"  [FAIL] {error}")
        print("         ch03_03_make_v5_logs.py 를 먼저 실행한다.")
        print("=" * 62)
        return

    for name, parser_name in engine.used.items():
        print(f"  {pad(name, 18)}{parser_name}")
    print("-" * 62)

    OUT_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().isoformat(timespec="seconds")
    matched = 0
    for lot_id, lot in sorted(lots.items()):
        payload = build_payload(lot, stamp, THRESHOLD)
        path = OUT_DIR / f"{lot_id.lower()}.json"
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        verdict = compare(lot_id, payload)
        matched += verdict == "일치"
        s = payload["summary"]
        print(
            f"  {pad(lot_id, 10)}레코드 {s['record_count']:>4}"
            f"  결측 {s['missing_leakage']:>3}"
            f"  경고 {s['alarm_count']:>3}  {verdict}"
        )

    print("-" * 62)
    print(f"  2.4절 JSON과 일치한 로트 : {matched}/{len(lots)}")
    print("  [확인 범위] generated_at을 뺀 요약·레코드 전 항목 대조")
    print(f"  저장 경로 : {OUT_DIR}")
    print("=" * 62)


if __name__ == "__main__":
    report()
