"""
a2_01_values_output.py
부록 A-2.1 값·연산과 출력의 예제를 실행한다.
실행 위치: 저장소 루트
"""


def example_01() -> None:
    """진리값: 슬랙 0.0과 None을 구분한다."""
    slack = 0.0
    print(bool(slack))
    print(slack is not None)
    missing = None
    print(bool(missing))
    print(missing is not None)


def example_02() -> None:
    """나눗셈 세 가지와 비교."""
    dies = 5000
    per_wafer = 100
    print(dies / per_wafer, dies // per_wafer, 437 % per_wafer)
    print(5 // 2, -5 // 2, 5.0 // 2)
    print(dies // 2, 0.032 < 0.05, 15.0 <= 15.0)


def example_03() -> None:
    """is와 ==: 같은 값인가, 같은 객체인가."""
    temps = [65.2, 66.0]
    alias = temps
    copied = list(temps)  # 같은 내용의 새 리스트
    print(alias == temps, alias is temps)
    print(copied == temps, copied is temps)


def example_04() -> None:
    """f-문자열과 서식 지정자."""
    lot = "LOT_09"
    risky = 1501
    slack = -0.0004
    rate = 0.1608
    print(f"{lot} 위험 {risky:,}건")
    print(f"슬랙 {slack:.3f} / 불량률 {rate:.2%}")
    print(f"[{lot:<8}] [{risky:>6}]")


if __name__ == "__main__":
    for run in (example_01, example_02, example_03, example_04):
        print(f"--- {run.__name__}")
        run()
