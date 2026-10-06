"""
a2_04_functions.py
부록 A-2.4 함수의 예제를 실행한다.
실행 위치: 저장소 루트
"""


def is_risky(slack: float, threshold: float) -> bool:
    """슬랙이 기준보다 작으면 참을 돌려준다."""
    return slack < threshold


def show(slack: float) -> None:
    """출력만 하고 값을 돌려주지 않는다."""
    print(f"슬랙 {slack}")


def describe(lot_id: str, wafer_id: str, worst_slack: float) -> str:
    """이름 붙은 인자로 받아 한 줄로 만든다."""
    return f"{lot_id}/{wafer_id} 슬랙 {worst_slack}"


def example_01() -> None:
    """def와 return, 반환이 없는 함수."""
    print(is_risky(0.032, 0.05))
    result = show(0.032)
    print(result)


def example_02() -> None:
    """키워드 인자와 ** 풀어 넘기기."""
    print(describe(wafer_id="W_03", lot_id="LOT_00", worst_slack=0.032))
    record = {"lot_id": "LOT_00", "wafer_id": "W_03",
              "worst_slack": 0.032}
    print(describe(**record))
    try:
        describe(**{"lot_id": "LOT_00", "wafer_id": "W_03",
                    "worst_slak": 0.032})
    except TypeError as error:
        print(f"TypeError: {error}")


def example_03() -> None:
    """lambda: 이름 없는 한 줄 함수."""
    threshold = 0.05
    check = lambda slack: slack < threshold  # noqa
    print(check(0.032), check(0.120))
    slacks = [0.120, -0.021, 0.032]
    print(sorted(slacks, key=lambda value: abs(value)))


if __name__ == "__main__":
    for run in (example_01, example_02, example_03):
        print(f"--- {run.__name__}")
        run()
