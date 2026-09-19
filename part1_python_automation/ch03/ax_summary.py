"""
ax_summary.py
레코드 묶음을 판정하고 요약한다. 모든 함수가 순수 함수다.
관찰 기준은 호출하는 쪽이 인자로 넘긴다.
"""


def is_risky(record: dict, threshold: float) -> bool:
    """슬랙이 관찰 기준 미만이면 True. 값이 없으면 False."""
    slack = record["worst_slack"]
    return slack is not None and slack < threshold


def group_by_lot(records: list[dict]) -> dict[str, list[dict]]:
    """레코드를 로트별 목록으로 나눈다. 입력은 바꾸지 않는다."""
    groups: dict[str, list[dict]] = {}
    for record in records:
        groups.setdefault(record["lot_id"], []).append(record)
    return groups


def summarize(records: list[dict], threshold: float) -> dict:
    """레코드 묶음의 요약 정보를 만든다."""
    risky = [r for r in records if is_risky(r, threshold)]
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
