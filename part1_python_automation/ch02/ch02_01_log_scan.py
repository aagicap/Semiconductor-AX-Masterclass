"""
ch02_01_log_scan.py
설계 리포트가 쌓인 디렉터리를 훑어 파일 목록과 규모를 파악한다.
파일을 통째로 읽지 않고 한 줄씩 흘려보내며 집계한다.
"""

import unicodedata
from pathlib import Path

LOG_DIR = Path("data/logs")
PATTERN = "sta_*.log"


def pad(text: str, width: int) -> str:
    """한글은 폭 2, 영문은 폭 1로 계산해 출력 열을 맞춘다."""
    wide = ("W", "F")
    display = sum(
        2 if unicodedata.east_asian_width(ch) in wide else 1
        for ch in text
    )
    return text + " " * max(0, width - display)


def read_lot_id(path: Path) -> str:
    """머리말에서 로트 식별자를 읽는다. 없으면 파일명에서 얻는다."""
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if line.startswith("# Lot:"):
                return line.split()[2]
            if not line.startswith("#"):
                break
    return path.stem.replace("sta_", "").upper()


def count_records(path: Path) -> tuple[int, int]:
    """본문 줄과 머리말 줄을 세어 돌려준다."""
    body = head = 0
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if line.startswith("#"):
                head += 1
            elif line.strip():
                body += 1
    return body, head


def report() -> None:
    """디렉터리 안의 리포트 파일을 훑어 요약한다."""
    print("=" * 62)
    print(" 설계 리포트 디렉터리 스캔")
    print("=" * 62)
    print(f"  대상 경로 : {LOG_DIR.resolve()}")

    if not LOG_DIR.is_dir():
        print("  [FAIL] 디렉터리를 찾을 수 없다.")
        print("         저장소 루트에서 실행했는지 확인하고,")
        print("         data/log_generator.py 를 먼저 실행한다.")
        print("=" * 62)
        return

    files = sorted(LOG_DIR.glob(PATTERN))
    if not files:
        print(f"  [FAIL] {PATTERN} 에 해당하는 파일이 없다.")
        print("=" * 62)
        return

    print(f"  검색 패턴 : {PATTERN}")
    print("-" * 62)
    print(
        f"  {pad('파일명', 20)}{pad('로트', 10)}"
        f"{pad('레코드', 9)}{pad('크기(KB)', 10)}"
    )
    print("-" * 62)

    total_body = 0
    total_size = 0
    for path in files:
        body, _ = count_records(path)
        size_kb = path.stat().st_size / 1024
        total_body += body
        total_size += size_kb
        print(
            f"  {pad(path.name, 20)}{pad(read_lot_id(path), 10)}"
            f"{pad(f'{body:,}', 9)}{size_kb:>8.1f}"
        )

    print("-" * 62)
    print(
        f"  파일 {len(files)}개 / 레코드 {total_body:,}건 "
        f"/ 합계 {total_size:.1f} KB"
    )
    print("=" * 62)


if __name__ == "__main__":
    report()
