"""
ch09_01_workbook_format.py  (9.1절)
8.3절 ETL 데이터베이스에서 로트별 수율 요약을 조회해, 서식 규칙을 입힌
엑셀 워크북으로 저장한다. 저장한 파일을 다시 열어 값과 형식을 확인한다.
실행 위치: 저장소 루트
"""

from datetime import datetime

from openpyxl import Workbook, load_workbook

from ax_db import ETL_DB, connect_readonly
from ax_excel import REPORT_DIR, set_widths, write_table
from ax_settings import REPO_ROOT
from ax_text import pad

OUT_PATH = REPORT_DIR / "ch09_01_lot_summary.xlsx"

LOT_SQL = """
SELECT Lot_ID,
       MIN(Timestamp)                  AS first_seen,
       MAX(Timestamp)                  AS last_seen,
       COUNT(*)                        AS dies,
       SUM(Pass_Fail = 0)              AS fails,
       AVG(Pass_Fail = 0)              AS fail_rate
FROM process_die
GROUP BY Lot_ID
ORDER BY Lot_ID
"""
HEADERS = ["Lot_ID", "첫 관측", "마지막 관측", "다이 수", "불량 수",
           "불량률"]  # fmt: skip
KINDS = ["text", "time", "time", "count", "count", "rate"]
WIDTHS = [10, 18, 18, 9, 9, 9]


def fetch_lots() -> list[tuple]:
    """로트별 요약을 조회하고, 시각 문자열을 datetime으로 바꾼다."""
    con = connect_readonly(ETL_DB)
    try:
        rows = con.execute(LOT_SQL).fetchall()
    finally:
        con.close()
    if not rows:  # 빈 데이터베이스로 빈 리포트를 만들지 않는다
        raise RuntimeError(
            "ETL 데이터베이스가 비어 있다. 8.3절 배치를 먼저 적재한다"
        )
    parse = datetime.fromisoformat
    return [
        (lot, parse(t0), parse(t1), dies, fails, rate)
        for lot, t0, t1, dies, fails, rate in rows
    ]


def build(rows: list[tuple]) -> Workbook:
    """정보 시트와 요약 시트를 가진 워크북을 만든다."""
    wb = Workbook()
    info = wb.active
    info.title = "정보"
    info.append(["항목", "내용"])
    info.append(["입력 데이터베이스", ETL_DB.name])
    info.append(["생성 시각", datetime.now().replace(microsecond=0)])
    info.append(["불량 정의", "Pass_Fail = 0인 다이"])
    info["B3"].number_format = "yyyy-mm-dd hh:mm:ss"
    set_widths(info, [18, 26])

    ws = wb.create_sheet("로트별 요약")
    write_table(ws, HEADERS, rows, KINDS)
    set_widths(ws, WIDTHS)
    ws.freeze_panes = "B2"  # 머리 행과 Lot_ID 열을 고정한다
    return wb


def verify(path) -> None:
    """저장한 파일을 다시 열어 형식과 값의 종류를 확인한다."""
    ws = load_workbook(path)["로트별 요약"]
    last = ws.cell(row=ws.max_row, column=1).value
    rate = ws.cell(row=ws.max_row, column=6)
    print(f"  {pad('데이터 행 수', 18)}{ws.max_row - 1:>8}")
    print(f"  {pad('틀 고정 위치', 18)}{ws.freeze_panes:>8}")
    print(f"  {pad('마지막 행 로트', 18)}{last:>8}")
    print(f"  {pad('불량률 셀 값', 18)}{rate.value:>8.4f}")
    print(f"  {pad('불량률 셀 형식', 18)}{rate.number_format:>8}")
    print(f"  {pad('값의 자료형', 18)}{type(rate.value).__name__:>8}")


def main() -> None:
    """조회 → 워크북 작성 → 저장 → 다시 열어 확인."""
    rows = fetch_lots()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    build(rows).save(OUT_PATH)
    print("=" * 50)
    print(" 9.1 로트별 요약 워크북")
    print("=" * 50)
    print(f"  저장: {OUT_PATH.relative_to(REPO_ROOT).as_posix()}")
    verify(OUT_PATH)
    print("  [확인 범위] 시트 구조·형식·값의 자료형만 확인했다")
    print("=" * 50)


if __name__ == "__main__":
    main()
