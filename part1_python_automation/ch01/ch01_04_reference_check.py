"""
ch01_04_reference_check.py
파이썬 변수가 값을 담는 상자가 아니라 객체를 가리키는 이름표임을
확인한다. 센서 목록을 함수에 넘겨 원본이 함께 바뀌는 과정을 추적한다.
"""


def add_outlier(samples: list) -> None:
    """전달받은 목록에 이상치를 덧붙인다. 반환값은 없다."""
    print(f"  같은 객체인가 : {samples is TEMPS}")
    samples.append(99.9)


def rebind(samples: list) -> None:
    """전달받은 이름에 새 목록을 대입한다. 원본과 연결이 끊긴다."""
    samples = [0.0]
    print(f"  같은 객체인가 : {samples is TEMPS}")


TEMPS = [76.1, 78.4, 80.2]


def report() -> None:
    """참조 공유와 재대입의 차이를 출력한다."""
    print("=" * 62)
    print(" 객체 참조 추적: 목록을 함수에 넘기면 무슨 일이 생기는가")
    print("=" * 62)
    print(f"  시작 시점 원본 : {TEMPS}")

    print("-" * 62)
    print(" [1] 전달받은 목록을 직접 수정한 경우")
    add_outlier(TEMPS)
    print(f"  호출 후 원본   : {TEMPS}")

    print("-" * 62)
    print(" [2] 전달받은 이름에 새 목록을 대입한 경우")
    rebind(TEMPS)
    print(f"  호출 후 원본   : {TEMPS}")

    print("-" * 62)
    print(" [3] 복사본을 만들어 수정한 경우")
    backup = TEMPS[:]
    backup.append(-1.0)
    print(f"  같은 객체인가 : {backup is TEMPS}")
    print(f"  원본           : {TEMPS}")
    print(f"  복사본         : {backup}")
    print("=" * 62)


if __name__ == "__main__":
    report()
