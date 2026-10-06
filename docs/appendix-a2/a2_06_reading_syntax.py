"""
a2_06_reading_syntax.py
부록 A-2.6 코드 읽기 표기의 예제를 실행한다.
실행 위치: 저장소 루트
"""

from dataclasses import dataclass


def mean_slack(values: list[float]) -> float | None:
    """타입 힌트는 의도를 적을 뿐 실행 중 검사하지 않는다."""
    return sum(values) / len(values) if values else None


@dataclass
class Wafer:
    """데코레이터가 __init__ 등을 덧붙인다."""
    lot_id: str
    wafer_id: str


class Report:
    """부모 클래스."""
    version = "v4"

    def header(self) -> str:
        return f"리포트 {self.version}"


class ReportV5(Report):
    """괄호 안이 부모. 바꾼 것만 적는다."""
    version = "v5"


def example_01() -> None:
    """타입 힌트."""
    print(round(mean_slack([0.1, 0.2]), 3), mean_slack([]))
    print(round(mean_slack((0.1, 0.2)), 3))  # 튜플도 그대로 동작


def example_02() -> None:
    """데코레이터."""
    print(Wafer("LOT_00", "W_03"))


def example_03() -> None:
    """상속 표기."""
    print(Report().header(), ReportV5().header())


if __name__ == "__main__":
    for run in (example_01, example_02, example_03):
        print(f"--- {run.__name__}")
        run()
