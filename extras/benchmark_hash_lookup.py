"""
benchmark_hash_lookup.py
표 2-4의 탐색 비용 측정을 재현한다.
리스트의 순차 탐색과 집합의 해시 기반 탐색을 자료 크기별로 비교한다.

실행: python extras/benchmark_hash_lookup.py
"""

import platform
import sys
import timeit

SIZES = (5_000, 50_000, 500_000)
REPEAT = 5  # 같은 조건을 몇 번 반복해 최솟값을 취할지


def make_data(n: int) -> tuple[list, set, list]:
    """크기 n의 리스트와 집합, 조회할 값 세 개를 만든다."""
    ids = [f"PATH_{i:06d}" for i in range(n)]
    targets = [ids[-1], ids[n // 2], f"PATH_{n + 1:06d}"]
    return ids, set(ids), targets


def measure(container, targets: list, loops: int) -> float:
    """조회 1회당 걸린 시간을 마이크로초로 돌려준다."""
    timer = timeit.Timer(lambda: [t in container for t in targets])
    best = min(timer.repeat(repeat=REPEAT, number=loops))
    return best / (loops * len(targets)) * 1e6


def report() -> None:
    """자료 크기별 측정 결과를 표로 출력한다."""
    print("=" * 62)
    print(" 탐색 비용 측정: 순차 탐색과 해시 기반 탐색")
    print("=" * 62)
    print(f"  Python {platform.python_version()} / {platform.system()}")
    print(f"  반복 {REPEAT}회 중 최솟값, 조회 1회당 마이크로초")
    print("-" * 62)
    head = f"  {'레코드 수':>10}  {'리스트':>12}"
    print(f"{head}  {'집합':>10}  {'배수':>10}")
    print("-" * 62)

    for n in SIZES:
        ids, id_set, targets = make_data(n)
        loops = max(3, 200_000 // n)
        seq = measure(ids, targets, loops)
        hashed = measure(id_set, targets, loops * 50)
        print(
            f"  {n:>10,}  {seq:>12.1f}  {hashed:>10.3f}"
            f"  {seq / hashed:>9,.0f}배"
        )

    print("-" * 62)
    print("  리스트는 자료가 늘면 비용도 함께 늘고,")
    print("  집합은 자료 개수에 비례해 늘지 않는다.")
    print("  절대값은 실행 환경에 따라 달라진다.")
    print("=" * 62)


if __name__ == "__main__":
    if sys.version_info < (3, 12):
        print("[WARN] Python 3.12 이상에서 측정하기를 권한다.")
    report()
