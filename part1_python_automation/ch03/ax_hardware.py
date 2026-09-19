"""
ax_hardware.py
로트 > 웨이퍼 > 다이의 하드웨어 계층을 클래스로 표현한다.
판정과 요약은 3.1절의 ax_summary를 그대로 쓴다.
"""

from dataclasses import dataclass, field

from ax_summary import is_risky, summarize


@dataclass(frozen=True)
class Die:
    """다이 하나의 타이밍 분석 결과. 만든 뒤에는 바꿀 수 없다."""

    lot_id: str
    wafer_id: str
    die_x: int
    die_y: int
    path_id: str
    worst_slack: float | None
    leakage_power: float | None
    operating_freq: float | None
    alarm: str | None

    def is_risky(self, threshold: float) -> bool:
        """3.1절 판정 함수에 자신의 속성을 넘긴다."""
        return is_risky(vars(self), threshold)


@dataclass
class Wafer:
    """같은 로트·같은 번호의 다이를 담는 웨이퍼."""

    lot_id: str
    wafer_id: str
    dies: list[Die] = field(default_factory=list)

    @property
    def key(self) -> tuple[str, str]:
        """웨이퍼를 유일하게 가리키는 식별자."""
        return (self.lot_id, self.wafer_id)

    def add(self, die: Die) -> None:
        """다른 웨이퍼의 다이가 섞이지 않게 확인한 뒤 담는다."""
        if (die.lot_id, die.wafer_id) != self.key:
            raise ValueError(f"{self.key} 에 다른 다이: {die.lot_id}")
        self.dies.append(die)

    def risky_dies(self, threshold: float) -> list[Die]:
        """관찰 기준 미만의 다이만 골라낸다."""
        return [d for d in self.dies if d.is_risky(threshold)]


@dataclass
class Lot:
    """웨이퍼를 번호로 찾아 담는 로트."""

    lot_id: str
    wafers: dict[str, Wafer] = field(default_factory=dict)

    def add(self, die: Die) -> None:
        """다이가 속할 웨이퍼를 찾아(없으면 만들어) 담는다."""
        if die.wafer_id not in self.wafers:
            wafer = Wafer(self.lot_id, die.wafer_id)
            self.wafers[die.wafer_id] = wafer
        self.wafers[die.wafer_id].add(die)

    @property
    def dies(self) -> list[Die]:
        """로트에 속한 모든 다이."""
        return [d for w in self.wafers.values() for d in w.dies]

    def summary(self, threshold: float) -> dict:
        """3.1절 요약 함수로 로트 요약을 만든다."""
        return summarize([vars(d) for d in self.dies], threshold)


def build_lots(records: list[dict]) -> dict[str, Lot]:
    """레코드 목록을 로트 객체들로 조립한다."""
    lots: dict[str, Lot] = {}
    for record in records:
        die = Die(**record)
        if die.lot_id not in lots:
            lots[die.lot_id] = Lot(die.lot_id)
        lots[die.lot_id].add(die)
    return lots
