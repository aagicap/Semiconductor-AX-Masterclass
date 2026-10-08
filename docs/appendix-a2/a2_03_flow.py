"""
a2_03_flow.py
부록 A-2.3 흐름 제어의 예제를 실행한다.
실행 위치: 저장소 루트
"""


def example_01() -> None:
    """if / elif / else."""
    for slack in (0.120, 0.032, -0.021):
        if slack < 0:
            label = "불량"
        elif slack < 0.05:
            label = "위험"
        else:
            label = "여유"
        print(f"{slack:+.3f} {label}")


def example_02() -> None:
    """for: 목록을 차례로, 세면서."""
    lines = ["# header", "PATH_0001 0.178", "PATH_0002 0.032"]
    count = 0
    for line in lines:
        if line.startswith("#"):
            continue
        count += 1
    print(f"기록 {count}줄")
    for number in range(3):
        print(number, end=" ")
    print()


def example_03() -> None:
    """예외 처리와 예외 발생."""
    for text in ("0.032", "abc", "-5.0"):
        try:
            value = float(text)
            if value < -1.0:
                raise ValueError(f"범위 밖 슬랙: {value}")
            print(value)
        except ValueError as error:
            print(f"[건너뜀] {error}")


if __name__ == "__main__":
    for run in (example_01, example_02, example_03):
        print(f"--- {run.__name__}")
        run()
