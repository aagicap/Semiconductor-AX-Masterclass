"""
ch02_02_log_parse.py
설계 리포트의 각 줄에서 패턴으로 공학 지표를 추출한다.
항목 순서가 바뀌거나 일부 항목이 빠져도 동일하게 동작한다.
"""

import re
from pathlib import Path

LOG_DIR = Path("data/logs")
PATTERN = "sta_*.log"

# 머리말에서 로트 식별자를 찾는다.
RE_LOT = re.compile(r"# Lot:\s+(?P<lot>\S+)")

# 한 줄의 앞부분: 경로 식별자와 다이 좌표
RE_HEAD = re.compile(
    r"Path:\s+(?P<path_id>\S+)\s+"
    r"wafer\s+(?P<wafer>\S+)\s+"
    r"die\s+\((?P<x>\d+),(?P<y>\d+)\)"
)

# 항목별 패턴. 자리와 무관하게 이름으로 찾는다.
RE_SLACK = re.compile(
    r"slack\s+(?P<state>MET|VIOLATED)\s+(?P<ns>-?\d+\.\d+)"
)
RE_LEAK = re.compile(r"leak\s+(?P<mw>\d+\.\d+)")
RE_FREQ = re.compile(r"freq\s+(?P<ghz>\d+\.\d+)")
RE_ALARM = re.compile(r"\((?P<code>[A-Z_]+)\)")


def parse_line(line: str, lot: str) -> dict | None:
    """한 줄을 레코드로 바꾼다. 형식이 아니면 None을 돌려준다."""
    head = RE_HEAD.search(line)
    if head is None:
        return None

    slack = RE_SLACK.search(line)
    leak = RE_LEAK.search(line)
    freq = RE_FREQ.search(line)
    alarm = RE_ALARM.search(line)

    return {
        "lot_id": lot,
        "wafer_id": head["wafer"],
        "die_x": int(head["x"]),
        "die_y": int(head["y"]),
        "path_id": head["path_id"],
        "worst_slack": float(slack["ns"]) if slack else None,
        "leakage_power": float(leak["mw"]) if leak else None,
        "operating_freq": float(freq["ghz"]) if freq else None,
        "alarm": alarm["code"] if alarm else None,
    }


def parse_file(path: Path) -> list[dict]:
    """파일 하나를 레코드 목록으로 바꾼다."""
    records = []
    lot = path.stem.replace("sta_", "").upper()
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if line.startswith("#"):
                found = RE_LOT.search(line)
                if found:
                    lot = found["lot"]
                continue
            record = parse_line(line, lot)
            if record is not None:
                records.append(record)
    return records


def report() -> None:
    """전체 리포트를 파싱하고 결과를 요약한다."""
    print("=" * 62)
    print(" 설계 리포트 패턴 추출")
    print("=" * 62)

    files = sorted(LOG_DIR.glob(PATTERN))
    if not files:
        print("  [FAIL] 리포트 파일이 없다.")
        print("         data/log_generator.py 를 먼저 실행한다.")
        print("=" * 62)
        return

    records = []
    for path in files:
        records.extend(parse_file(path))

    no_leak = sum(1 for r in records if r["leakage_power"] is None)
    alarmed = sum(1 for r in records if r["alarm"] is not None)
    violated = sum(
        1
        for r in records
        if r["worst_slack"] is not None and r["worst_slack"] < 0
    )

    print(f"  파일 {len(files)}개에서 {len(records):,}건 추출")
    print("-" * 62)
    print(f"  누설 전력 항목 없음 : {no_leak:,}건")
    print(f"  상태 경고 표기      : {alarmed:,}건")
    print(f"  슬랙 음수           : {violated:,}건")
    print("-" * 62)
    print("  [샘플] 첫 레코드")
    for key, value in records[0].items():
        print(f"    {key:16}: {value}")
    print("=" * 62)


if __name__ == "__main__":
    report()
