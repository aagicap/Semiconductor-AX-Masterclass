"""
ch01_03_venv_check.py
현재 런타임이 격리된 가상환경 내부인지 시스템 전역 환경인지 진단한다.
라이브러리를 설치하기 전에 실행해 설치 위치를 먼저 확인한다.
"""

import sys
import sysconfig
import unicodedata
from importlib import metadata
from pathlib import Path


def pad(text: str, width: int) -> str:
    """한글은 폭 2, 영문은 폭 1로 계산해 출력 열을 맞춘다."""
    wide = ("W", "F")
    display = sum(
        2 if unicodedata.east_asian_width(ch) in wide else 1
        for ch in text
    )
    return text + " " * max(0, width - display)


def is_isolated() -> bool:
    """실행 경로와 원본 경로가 다르면 격리된 상태로 판정한다."""
    base = getattr(sys, "base_prefix", sys.prefix)
    return sys.prefix != base


def package_count() -> int:
    """현재 환경에 설치된 배포 패키지의 개수를 센다."""
    return len(list(metadata.distributions()))


def report() -> None:
    """격리 무결성 진단 결과를 출력한다."""
    base = getattr(sys, "base_prefix", sys.prefix)
    items = [
        ("실행 엔진", sys.executable),
        ("런타임 경로", sys.prefix),
        ("원본 엔진 경로", base),
        ("패키지 설치 위치", sysconfig.get_paths()["purelib"]),
        ("설치된 패키지 수", f"{package_count()}개"),
    ]

    print("=" * 62)
    print(" AlphaChip_V2 파이프라인 격리 무결성 진단")
    print("=" * 62)
    for key, value in items:
        print(f"  {pad(key, 18)} : {value}")

    print("-" * 62)
    if is_isolated():
        name = Path(sys.prefix).name
        print(f"  [PASS] 가상환경 격리 활성 : {name}")
        print("         이 환경에 설치한 패키지는 시스템 전역을")
        print("         오염시키지 않는다.")
    else:
        print("  [FAIL] 시스템 전역 환경에서 실행 중")
        print("         지금 pip install 을 실행하면 다른 프로젝트에")
        print("         영향을 준다. 가상환경을 활성화한다.")
    print("=" * 62)


if __name__ == "__main__":
    report()
