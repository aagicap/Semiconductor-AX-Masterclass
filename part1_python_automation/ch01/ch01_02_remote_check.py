"""
ch01_02_remote_check.py
현재 코드가 어느 머신에서, 어떤 파이썬으로 실행되고 있는지, 그리고
분석 대상 데이터에 접근 가능한 위치인지를 점검한다.
반도체 망분리(Air-gapped) 환경에서 Remote-SSH 접속 직후 1회 실행한다.
"""

import os
import platform
import socket
import sys
import unicodedata
from pathlib import Path

DATA_PATH = Path("data/alphachip_v2_integrated_data.csv")


def pad(text: str, width: int) -> str:
    """한글은 폭 2, 영문은 폭 1로 계산해 출력 열을 맞춘다."""
    wide = ("W", "F")  # 전각(Wide) / 전각 호환(Fullwidth)
    display = sum(
        2 if unicodedata.east_asian_width(ch) in wide else 1
        for ch in text
    )
    return text + " " * max(0, width - display)


def detect_session() -> str:
    """SSH 환경 변수의 유무로 원격 세션 여부를 판정한다."""
    if os.environ.get("SSH_CONNECTION") or os.environ.get("SSH_CLIENT"):
        return "REMOTE (SSH 세션)"
    return "LOCAL (물리 콘솔 또는 로컬 터미널)"


def detect_venv() -> str:
    """실행 경로와 원본 경로를 비교해 가상환경 활성화를 판정한다."""
    base = getattr(sys, "base_prefix", sys.prefix)
    if sys.prefix != base:
        return f"ACTIVE ({Path(sys.prefix).name})"
    return "INACTIVE (시스템 전역 환경)"


def report() -> None:
    """실행 환경 점검 결과를 표 형태로 출력한다."""
    items = [
        ("세션 유형", detect_session()),
        ("호스트명", socket.gethostname()),
        ("운영체제", f"{platform.system()} {platform.release()}"),
        ("Python 버전", platform.python_version()),
        ("인터프리터 경로", sys.executable),
        ("가상환경", detect_venv()),
        ("작업 디렉터리", str(Path.cwd())),
        ("논리 CPU 코어", str(os.cpu_count())),
    ]

    print("=" * 62)
    print(" AlphaChip_V2 실행 환경 점검 리포트")
    print("=" * 62)
    for key, value in items:
        print(f"  {pad(key, 18)} : {value}")

    print("-" * 62)
    if DATA_PATH.exists():
        mb = DATA_PATH.stat().st_size / (1024**2)
        print(f"  [OK]   데이터 접근 가능 : {DATA_PATH} ({mb:.2f} MB)")
    else:
        print(f"  [FAIL] 데이터 없음      : {DATA_PATH.resolve()}")
        print("         저장소 루트에서 실행했는지 확인한다.")
    print("=" * 62)


if __name__ == "__main__":
    report()
