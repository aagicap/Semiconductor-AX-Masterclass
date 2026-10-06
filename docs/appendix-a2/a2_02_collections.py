"""
a2_02_collections.py
부록 A-2.2 자료 구조의 예제를 실행한다.
실행 위치: 저장소 루트
"""


def example_01() -> None:
    """리스트와 튜플."""
    slacks = [0.178, 0.032, -0.021]
    slacks.append(0.090)
    key = ("LOT_00", "W_03")
    print(len(slacks), slacks[0], slacks[-1], key[1])


def example_02() -> None:
    """집합: 중복 제거와 집합 연산."""
    seen = {("LOT_00", "W_00"), ("LOT_00", "W_01"), ("LOT_00", "W_00")}
    risky = {("LOT_00", "W_01"), ("LOT_01", "W_02")}
    print(len(seen))
    print(sorted(seen & risky), sorted(risky - seen))
    print(("LOT_01", "W_02") in risky)


def example_03() -> None:
    """딕셔너리 조회: 대괄호와 get."""
    record = {"lot_id": "LOT_00", "worst_slack": 0.032}
    print(record["worst_slack"])
    print(record.get("leakage_power"))
    print(record.get("worst_slak", "키 없음"))


def example_04() -> None:
    """내포 표기: 리스트·집합·딕셔너리."""
    records = [
        {"lot_id": "LOT_00", "wafer_id": "W_00", "worst_slack": 0.031},
        {"lot_id": "LOT_00", "wafer_id": "W_00", "worst_slack": 0.120},
        {"lot_id": "LOT_00", "wafer_id": "W_01", "worst_slack": 0.044},
    ]
    slacks = [r["worst_slack"] for r in records]
    risky = {(r["lot_id"], r["wafer_id"])
             for r in records if r["worst_slack"] < 0.05}
    by_wafer = {r["wafer_id"]: r["worst_slack"] for r in records}
    print(slacks)
    print(sorted(risky))
    print(by_wafer)


if __name__ == "__main__":
    for run in (example_01, example_02, example_03, example_04):
        print(f"--- {run.__name__}")
        run()
