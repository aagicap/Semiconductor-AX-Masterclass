"""
ax_engine.py
리포트 형식별 파서 클래스와, 형식을 가려 파서를 고르는 엔진.
"""

import csv
import re
from pathlib import Path

from ax_hardware import Die, Lot
from ax_settings import PATTERN
from ax_sta import parse_file

RE_V5_LOT = re.compile(r"lot=(?P<lot>\S+)")


class BaseStaParser:
    """모든 리포트 파서의 공통 골격. 직접 쓰지 않고 상속해 쓴다."""

    name = "미정"
    marker = ""  # 머리말 첫 줄에 있어야 할 형식 표식

    def accepts(self, first_line: str) -> bool:
        """첫 줄에 자신의 형식 표식이 있으면 True."""
        return bool(self.marker) and self.marker in first_line

    def parse(self, path: Path) -> list[Die]:
        """리포트를 다이 목록으로 바꾼다. 자식 클래스가 정의한다."""
        raise NotImplementedError


class StaParserV4(BaseStaParser):
    """TimingSign v4 리포트 파서. 2.2절 파서를 그대로 쓴다."""

    name = "TimingSign v4"
    marker = "(Tool: TimingSign v4"

    def parse(self, path: Path) -> list[Die]:
        return [Die(**r) for r in parse_file(path)]


def number(text: str) -> float | None:
    """빈 칸은 결측(None), 나머지는 실수로 바꾼다."""
    return float(text) if text else None


class StaParserV5(BaseStaParser):
    """TimingSign v5 리포트 파서. 쉼표로 구분한 열을 읽는다."""

    name = "TimingSign v5"
    marker = "## TimingSign v5"

    def parse(self, path: Path) -> list[Die]:
        with path.open(encoding="utf-8", newline="") as stream:
            found = RE_V5_LOT.search(stream.readline())
            if found is None:
                raise ValueError(
                    f"머리말에 로트 식별자가 없다 : {path.name}"
                )
            lot_id = found["lot"]
            # 머리말 다음 줄부터 CSV. 쉼표 규칙은 csv 모듈에 맡긴다.
            body = (line for line in stream if not line.startswith("#"))
            return [
                self.to_die(lot_id, row) for row in csv.DictReader(body)
            ]

    @staticmethod
    def to_die(lot_id: str, row: dict[str, str]) -> Die:
        """v5 열 이름을 Die 속성 이름으로 옮긴다."""
        return Die(
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


class ParsingEngine:
    """폴더의 리포트를 형식별 파서로 읽어 로트 객체로 조립한다."""

    def __init__(self, parsers: list[BaseStaParser], log_dir: Path):
        self.parsers = parsers
        self.log_dir = log_dir
        self.used: dict[str, str] = {}  # 파일 이름 → 사용한 파서

    def pick(self, path: Path) -> BaseStaParser | None:
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
    lot: Lot, generated_at: str, threshold: float
) -> dict:
    """2.4절과 같은 구조의 JSON 자산을 만든다. 순수 함수다."""
    return {
        "lot_id": lot.lot_id,
        "generated_at": generated_at,
        "threshold": threshold,
        "summary": lot.summary(threshold),
        "records": [vars(d) for d in lot.dies],
    }
