"""
ax_engine.py
리포트 형식별 파서 클래스와, 형식을 가려 파서를 고르는 엔진.
"""

import re
from pathlib import Path

from ax_hardware import Die, Lot
from ax_settings import PATTERN, THRESHOLD
from ax_sta import parse_file

RE_V5_LOT = re.compile(r"lot=(?P<lot>\S+)")


class StaParser:
    """TimingSign v4 리포트 파서. 모든 파서의 기반 클래스다."""

    name = "TimingSign v4"
    signature = "(Tool: TimingSign v4"

    def accepts(self, first_line: str) -> bool:
        """머리말 첫 줄을 보고 이 파서가 읽을 형식인지 판단한다."""
        return self.signature in first_line

    def parse(self, path: Path) -> list[Die]:
        """리포트 하나를 다이 목록으로 바꾼다. 2.2절 파서를 쓴다."""
        return [Die(**r) for r in parse_file(path)]


def number(text: str) -> float | None:
    """빈 칸은 결측(None), 나머지는 실수로 바꾼다."""
    return float(text) if text else None


class StaParserV5(StaParser):
    """TimingSign v5 리포트 파서. 쉼표로 구분한 열을 읽는다."""

    name = "TimingSign v5"
    signature = "## TimingSign v5"

    def parse(self, path: Path) -> list[Die]:
        lines = path.read_text(encoding="utf-8").splitlines()
        lot_id = RE_V5_LOT.search(lines[0])["lot"]
        header = lines[1].split(",")
        dies = []
        for line in lines[2:]:
            if line.startswith("#"):
                continue
            row = dict(zip(header, line.split(",")))
            dies.append(
                Die(
                    lot_id=lot_id,
                    wafer_id=row["wafer"],
                    die_x=int(row["x"]),
                    die_y=int(row["y"]),
                    path_id=row["path"],
                    worst_slack=number(row["slack_ns"]),
                    leakage_power=number(row["leak_mw"]),
                    operating_freq=number(row["freq_ghz"]),
                    alarm=row["alarm"] or None,
                )
            )
        return dies


class ParsingEngine:
    """폴더의 리포트를 형식별 파서로 읽어 로트 객체로 조립한다."""

    def __init__(self, parsers: list[StaParser], log_dir: Path):
        self.parsers = parsers
        self.log_dir = log_dir
        self.used: dict[str, str] = {}  # 파일 이름 → 사용한 파서

    def pick(self, path: Path) -> StaParser | None:
        """첫 줄을 읽어 맞는 파서를 고른다. 없으면 None."""
        with path.open(encoding="utf-8") as stream:
            first = stream.readline()
        for parser in self.parsers:
            if parser.accepts(first):
                return parser
        return None

    def run(self) -> dict[str, Lot]:
        """모든 리포트를 읽어 로트 객체 사전을 돌려준다."""
        files = sorted(self.log_dir.glob(PATTERN))
        if not files:
            raise FileNotFoundError(
                f"리포트 파일이 없다 : {self.log_dir}"
            )
        lots: dict[str, Lot] = {}
        for path in files:
            parser = self.pick(path)
            if parser is None:
                self.used[path.name] = "미지원 형식 (건너뜀)"
                continue
            self.used[path.name] = parser.name
            for die in parser.parse(path):
                if die.lot_id not in lots:
                    lots[die.lot_id] = Lot(die.lot_id)
                lots[die.lot_id].add(die)
        return lots


def build_payload(
    lot: Lot, generated_at: str, threshold: float = THRESHOLD
) -> dict:
    """2.4절과 같은 구조의 JSON 자산을 만든다. 순수 함수다."""
    return {
        "lot_id": lot.lot_id,
        "generated_at": generated_at,
        "threshold": threshold,
        "summary": lot.summary(threshold),
        "records": [vars(d) for d in lot.dies],
    }
