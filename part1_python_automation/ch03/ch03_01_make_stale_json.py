"""
ch03_01_make_stale_json.py
3.1절 Troubleshooting 실험용. 관찰 기준을 0.03으로 두고 만든
'옛 설정의 자산'을 data/parsed_stale/ 에 저장한다.
2장 파일과 data/parsed/ 는 건드리지 않는다.
"""

import json

from ax_settings import DATA_DIR, LOG_DIR
from ax_sta import load_records
from ax_summary import group_by_lot, summarize

STALE_DIR = DATA_DIR / "parsed_stale"
STALE_THRESHOLD = 0.03  # 다른 설정 버전을 흉내 낸 값


def main() -> None:
    """로트별 요약을 옛 기준으로 계산해 JSON으로 저장한다."""
    records = load_records()
    if not records:
        print(f"[FAIL] 리포트 파일이 없다 : {LOG_DIR}")
        return
    STALE_DIR.mkdir(exist_ok=True)
    groups = group_by_lot(records)
    for lot_id, group in sorted(groups.items()):
        payload = {
            "lot_id": lot_id,
            "threshold": STALE_THRESHOLD,
            "summary": summarize(group, STALE_THRESHOLD),
        }
        path = STALE_DIR / f"{lot_id.lower()}.json"
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    print(f"로트 {len(groups)}개 저장 (기준 {STALE_THRESHOLD})")
    print(f"저장 경로 : {STALE_DIR}")


if __name__ == "__main__":
    main()
