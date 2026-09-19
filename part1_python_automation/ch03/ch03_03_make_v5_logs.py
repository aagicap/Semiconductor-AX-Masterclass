"""
ch03_03_make_v5_logs.py
3.3절 실습용 혼합 리포트 폴더를 만든다.
LOT_00~07은 v4 리포트를 그대로 복사하고, LOT_08~09는 같은 값을
TimingSign v5 형식(쉼표 구분 열)으로 다시 쓴다. 새 난수는 없다.
"""

import re
import shutil

from ax_settings import DATA_DIR, LOG_DIR, PATTERN
from ax_sta import parse_file

MIXED_DIR = DATA_DIR / "logs_mixed"
V5_LOTS = ("LOT_08", "LOT_09")  # 툴을 올린 뒤에 나온 로트
RE_STAMP = re.compile(r"Generated:\s+(?P<d>\S+)\s+(?P<t>\S+)")
COLUMNS = "path,wafer,x,y,state,slack_ns,leak_mw,freq_ghz,alarm"


def fmt(value: float | None) -> str:
    """값이 없으면 빈 칸, 있으면 소수 둘째 자리까지 쓴다."""
    return "" if value is None else f"{value:.2f}"


def to_v5_line(r: dict) -> str:
    """레코드 하나를 v5 형식의 한 줄로 바꾼다."""
    state = "MET" if r["worst_slack"] >= 0 else "VIOLATED"
    return ",".join(
        [
            r["path_id"],
            r["wafer_id"],
            str(r["die_x"]),
            str(r["die_y"]),
            state,
            f"{r['worst_slack']:.3f}",
            fmt(r["leakage_power"]),
            fmt(r["operating_freq"]),
            r["alarm"] or "",
        ]
    )


def write_v5(src, dst, lot_id: str) -> int:
    """v4 리포트 하나를 v5 형식으로 다시 써서 행 수를 돌려준다."""
    stamp = RE_STAMP.search(src.read_text(encoding="utf-8"))
    if stamp is None:
        raise ValueError(f"머리말에 생성 시각이 없다 : {src.name}")
    generated = f"{stamp['d']}T{stamp['t']}"
    records = parse_file(src)
    lines = [
        f"## TimingSign v5.0.0 | lot={lot_id} | generated={generated}",
        COLUMNS,
        *(to_v5_line(r) for r in records),
        f"## end rows={len(records)}",
    ]
    dst.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(records)


def main() -> None:
    """혼합 폴더를 만들고 파일별 형식을 출력한다."""
    files = sorted(LOG_DIR.glob(PATTERN))
    if not files:
        print(f"[FAIL] 리포트 파일이 없다 : {LOG_DIR}")
        return
    MIXED_DIR.mkdir(exist_ok=True)
    for src in files:
        lot_id = src.stem.replace("sta_", "").upper()
        dst = MIXED_DIR / src.name
        if lot_id in V5_LOTS:
            rows = write_v5(src, dst, lot_id)
            print(f"  {src.name}  v5 형식으로 변환 ({rows}행)")
        else:
            shutil.copyfile(src, dst)
            print(f"  {src.name}  v4 원본 복사")
    print(f"저장 경로 : {MIXED_DIR}")


if __name__ == "__main__":
    main()
