"""
ch02_04_json_asset.py
설계 리포트를 파싱해 로트별 JSON 자산으로 저장한다.
요약 정보와 레코드를 함께 담아 이후 장에서 바로 읽을 수 있게 한다.
"""

import json
from collections import defaultdict
from datetime import datetime

from ch02_02_log_parse import LOG_DIR, PATTERN, parse_file

OUT_DIR = LOG_DIR.parent / "parsed"
THRESHOLD = 0.05  # 교육용 관찰 기준. 실제 규격이 아니다.


def summarize(records: list[dict]) -> dict:
    """레코드 묶음의 요약 정보를 만든다."""
    risky = [
        r
        for r in records
        if r["worst_slack"] is not None and r["worst_slack"] < THRESHOLD
    ]
    wafers = {(r["lot_id"], r["wafer_id"]) for r in records}
    risky_wafers = {(r["lot_id"], r["wafer_id"]) for r in risky}

    return {
        "record_count": len(records),
        "risky_count": len(risky),
        "wafer_count": len(wafers),
        "risky_wafer_count": len(risky_wafers),
        "missing_leakage": sum(
            1 for r in records if r["leakage_power"] is None
        ),
        "alarm_count": sum(
            1 for r in records if r["alarm"] is not None
        ),
        "path_ids": sorted({r["path_id"] for r in records}),
    }


def save_lot(lot_id: str, records: list[dict]) -> int:
    """로트 하나를 JSON 파일로 저장하고 바이트 수를 돌려준다."""
    payload = {
        "lot_id": lot_id,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "threshold": THRESHOLD,
        "summary": summarize(records),
        "records": records,
    }
    path = OUT_DIR / f"{lot_id.lower()}.json"
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path.stat().st_size


def report() -> None:
    """리포트를 파싱해 로트별 JSON으로 저장한다."""
    print("=" * 62)
    print(" 설계 리포트 JSON 자산화")
    print("=" * 62)

    files = sorted(LOG_DIR.glob(PATTERN))
    if not files:
        print("  [FAIL] 리포트 파일이 없다.")
        print("         data/log_generator.py 를 먼저 실행한다.")
        print("=" * 62)
        return

    by_lot = defaultdict(list)
    for path in files:
        for record in parse_file(path):
            by_lot[record["lot_id"]].append(record)

    OUT_DIR.mkdir(exist_ok=True)
    total_bytes = 0
    total_records = 0
    for lot_id in sorted(by_lot):
        records = by_lot[lot_id]
        size = save_lot(lot_id, records)
        total_bytes += size
        total_records += len(records)
        print(
            f"  {lot_id}  레코드 {len(records):>4}건"
            f"  위험 {summarize(records)['risky_count']:>4}건"
            f"  {size / 1024:>7.1f} KB"
        )

    print("-" * 62)
    print(f"  파일 {len(by_lot)}개 / 레코드 {total_records:,}건")
    print(f"  저장 경로 : {OUT_DIR.resolve()}")
    print("=" * 62)


if __name__ == "__main__":
    report()
