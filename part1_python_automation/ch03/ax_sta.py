"""
ax_sta.py
STA 타이밍 리포트를 레코드로 바꾼다. 3장 이후의 표준 파서다.
패턴과 parse_line, parse_file은 2.2절 코드를 그대로 옮겼다.
"""

import re
from pathlib import Path

from ax_settings import LOG_DIR, PATTERN

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


def load_records(
    log_dir: Path = LOG_DIR, pattern: str = PATTERN
) -> list[dict]:
    """디렉터리의 리포트를 모두 읽어 레코드 목록으로 만든다."""
    records = []
    for path in sorted(log_dir.glob(pattern)):
        records.extend(parse_file(path))
    return records
