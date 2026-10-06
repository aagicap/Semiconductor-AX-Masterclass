"""
a2_05_files_modules.py
부록 A-2.5 파일과 모듈의 예제를 실행한다.
실행 위치: 저장소 루트
"""

import json
from pathlib import Path

NOTE = Path(__file__).with_name("a2_note.txt")


def example_01() -> None:
    """with: 끝나면 파일을 자동으로 닫는다."""
    with NOTE.open("w", encoding="utf-8") as stream:
        stream.write("LOT_00 W_03 0.032\n")
    with NOTE.open(encoding="utf-8") as stream:
        for line in stream:
            print(line.strip())
    print(stream.closed)
    NOTE.unlink()


def example_02() -> None:
    """import의 세 가지 형태."""
    from math import sqrt
    import statistics as st
    print(json.dumps({"lot_id": "LOT_00"}))
    print(round(sqrt(0.25), 2), st.mean([14.9, 15.0, 15.1]))


def example_03() -> None:
    """__name__: 직접 실행과 불러오기."""
    import a2_01_values_output as other
    print(__name__, other.__name__)


if __name__ == "__main__":
    for run in (example_01, example_02, example_03):
        print(f"--- {run.__name__}")
        run()
