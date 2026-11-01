"""
ch09_03_daily_dashboard.py  (9.3절 미니 프로젝트 모범 답안)
8.3절 ETL 데이터베이스로 보고 기준일의 '일일 팹 수율 대시보드'를
엑셀로 만든다. 저장한 파일을 다시 열어 핵심 값을 확인한다.
실행 위치: 저장소 루트. 기준일을 정하려면 --date 2026-01-15처럼 준다
"""

import argparse
import zipfile
from datetime import date, datetime
from pathlib import Path

import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.chart import LineChart, Reference
from openpyxl.drawing.image import Image
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Font, PatternFill

from ax_db import ETL_DB, connect_readonly
from ax_excel import FORMATS, REPORT_DIR, set_widths, write_table
from ax_frame import DIES_PER_WAFER, N_ROWS, N_WAFERS
from ax_settings import DATA_DIR, REPO_ROOT
from ax_stats import wafer_summary
from ax_text import display_width, pad

WARN_RATE = 0.20  # 교육용 경고 기준. 웨이퍼별 불량률 0.20 이상
WARN_FILL = PatternFill("solid", fgColor="F8D7DA")
COCKPIT = DATA_DIR / "processed" / "figures" / "ch07_03_cockpit.png"
DONE_RULE = (
    "웨이퍼별 다이 100개의 관측이 모두 있을 때, 마지막 관측 시각이 "
    "속한 날짜. 보고서 집계용 교육 정의이며 공정 완료 이벤트가 아니다"
)
# 입력 점검(지침 8-2.1). 실패 이력(FAILED)은 판단 근거로 쓰지 않는다
EXPECTED = {
    "process_die 행": N_ROWS,
    "design_die 행": N_ROWS,
    "키로 이은 행": N_ROWS,
    "웨이퍼": N_WAFERS,
    "불량 다이": 804,
    "Leakage_Power NULL": 125,
}
CHECK_SQL = """
SELECT (SELECT COUNT(*) FROM process_die),
       (SELECT COUNT(*) FROM design_die),
       (SELECT COUNT(*) FROM design_die
          JOIN process_die USING (Lot_ID, Wafer_ID, Die_X, Die_Y)),
       (SELECT COUNT(*) FROM (SELECT DISTINCT Lot_ID, Wafer_ID
                              FROM process_die)),
       (SELECT SUM(Pass_Fail = 0) FROM process_die),
       (SELECT COUNT(*) - COUNT(Leakage_Power) FROM design_die)
"""
TREND_ROW = 11  # 일별 추이 표의 머리 행


def load_input() -> pd.DataFrame:
    """입력을 점검하고 제조 관측을 읽는다. 기대와 다르면 멈춘다."""
    con = connect_readonly(ETL_DB)
    try:
        found = dict(zip(EXPECTED, con.execute(CHECK_SQL).fetchone()))
        process = pd.read_sql(
            "SELECT * FROM process_die", con, parse_dates=["Timestamp"]
        )
    finally:
        con.close()
    wrong = {k: v for k, v in found.items() if v != EXPECTED[k]}
    if wrong:
        raise RuntimeError(
            f"입력 점검 실패 {wrong}. 8.3절 적재를 확인한다"
        )
    return process


def wafer_table(process: pd.DataFrame) -> pd.DataFrame:
    """웨이퍼 요약에 완료일과 교육용 경고 기준을 더한다."""
    wafers = wafer_summary(process)  # 장비가 둘 이상이면 여기서 멈춘다
    short = int((wafers["dies"] != DIES_PER_WAFER).sum())
    if short:  # 다이가 모자란 웨이퍼를 완료로 보지 않는다
        raise RuntimeError(
            f"다이가 {DIES_PER_WAFER}개가 아닌 웨이퍼 {short}장"
        )
    wafers["done"] = wafers["last_seen"].dt.normalize()
    hit = wafers["fail_ratio"] >= WARN_RATE  # 반올림 전 비율로 판정
    wafers["warn"] = hit.map({True: "해당", False: "미해당"})
    return wafers


def daily_table(wafers: pd.DataFrame) -> pd.DataFrame:
    """완료일별로 건수를 먼저 합하고, 그다음 비율을 계산한다."""
    days = (
        wafers.groupby("done")
        .agg(
            wafers=("Wafer_ID", "size"),
            dies=("dies", "sum"),
            fails=("fails", "sum"),
        )
        .reset_index()
    )
    days["fail_ratio"] = days["fails"] / days["dies"]
    return days


def pick_day(days: pd.DataFrame) -> tuple[datetime, str]:
    """--date가 없으면 가장 늦은 완료일. 시스템 날짜는 쓰지 않는다."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", type=date.fromisoformat)
    arg = parser.parse_args().date
    if arg is None:
        return max(days["done"]).to_pydatetime(), "가장 늦은 완료일"
    return datetime.combine(arg, datetime.min.time()), "--date로 지정"


def write_info(wb: Workbook, day: datetime) -> None:
    """리포트만 열어도 집계 기준을 알 수 있게 첫 시트에 적는다."""
    ws = wb.worksheets[0]
    ws.title = "정보"
    rule = (
        f"웨이퍼별 불량률 {WARN_RATE:.2f} 이상. 출하 판정 기준이 아니다"
    )
    rows = [
        ("보고 기준일", day),
        ("생성 시각", datetime.now().replace(microsecond=0)),
        ("입력 데이터베이스", ETL_DB.name),
        ("완료일 정의", DONE_RULE),
        ("일일 수율", "완료 웨이퍼의 양품 다이 합계 ÷ 다이 합계"),
        ("교육용 경고 기준", rule),
    ]
    write_table(ws, ["항목", "내용"], rows, ["text", "text"])
    for (cell,) in ws.iter_rows(min_row=2, min_col=2, max_col=2):
        cell.alignment = Alignment(wrap_text=True, vertical="top")
    ws["B2"].number_format = FORMATS["date"]
    ws["B3"].number_format = "yyyy-mm-dd hh:mm:ss"
    set_widths(ws, [18, 60])


def kpi_rows(today: pd.DataFrame) -> list[tuple]:
    """핵심 지표. 완료 웨이퍼가 없으면 비율을 0%로 쓰지 않는다."""
    dies = int(today["dies"].to_numpy().sum())
    fails = int(today["fails"].to_numpy().sum())
    none = "완료 웨이퍼 없음"
    good = (dies - fails) / dies if dies else none
    ratio = fails / dies if dies else none
    hits = int((today["warn"] == "해당").sum())
    return [
        ("완료 웨이퍼 수", len(today), "count"),
        ("다이 수", dies, "count"),
        ("불량 수", fails, "count"),
        ("수율", good, "rate"),
        ("불량률", ratio, "rate"),
        ("경고 기준 해당 웨이퍼 수", hits, "count"),
    ]


def write_dashboard(wb: Workbook, day, today, trend) -> None:
    """핵심 지표, 일별 추이 표와 차트를 한 시트에 둔다."""
    ws = wb.create_sheet("대시보드")
    ws["A1"] = f"일일 팹 수율 대시보드 (기준일 {day:%Y-%m-%d})"
    ws["A1"].font = Font(bold=True, size=14)
    kpi = kpi_rows(today)
    write_table(
        ws, ["지표", "값"], [r[:2] for r in kpi], ["text", "count"], 3
    )
    for row, (_, _, kind) in enumerate(kpi, start=4):
        ws.cell(row=row, column=2).number_format = FORMATS[kind]
    cols = ["done", "wafers", "dies", "fails", "fail_ratio"]
    rows = list(trend[cols].itertuples(index=False, name=None))
    write_table(
        ws,
        ["완료일", "웨이퍼 수", "다이 수", "불량 수", "불량률"],
        rows,
        ["date", "count", "count", "count", "rate"],
        TREND_ROW,
    )
    set_widths(ws, [24, 14, 10, 10, 10])
    if not rows:  # 추이가 없으면 차트를 그리지 않는다
        return
    last = TREND_ROW + len(rows)
    chart = LineChart()
    chart.title = "완료일별 불량률"
    chart.y_axis.number_format = "0%"
    values = Reference(ws, min_col=5, min_row=TREND_ROW, max_row=last)
    chart.add_data(values, titles_from_data=True)
    chart.set_categories(
        Reference(ws, min_col=1, min_row=TREND_ROW + 1, max_row=last)
    )
    chart.varyColors = False  # 구간마다 색을 바꾸지 않는다
    chart.series[0].smooth = False  # 곡선 보간은 없는 값을 그린다
    chart.x_axis.number_format = "mm-dd"
    chart.x_axis.delete = chart.y_axis.delete = False  # 축을 보인다
    chart.legend = None
    chart.width, chart.height = 18, 8
    ws.add_chart(chart, "G3")


def write_detail(wb: Workbook, today: pd.DataFrame) -> None:
    """기준일에 완료된 웨이퍼만 보인다. 경고 기준은 색으로 강조한다."""
    ws = wb.create_sheet("웨이퍼 상세")
    cols = ["Lot_ID", "Wafer_ID", "Equipment_ID", "dies", "fails",
            "fail_ratio", "last_seen", "warn"]  # fmt: skip
    heads = ["Lot_ID", "Wafer_ID", "Equipment_ID", "다이 수", "불량 수",
             "불량률", "마지막 관측", "경고 기준"]  # fmt: skip
    kinds = ["text", "text", "text", "count", "count", "rate", "time",
             "text"]  # fmt: skip
    rows = list(today[cols].itertuples(index=False, name=None))
    write_table(ws, heads, rows, kinds)
    rule = CellIsRule(
        operator="greaterThanOrEqual",
        formula=[str(WARN_RATE)],
        fill=WARN_FILL,
    )
    ws.conditional_formatting.add(f"F2:F{max(2, ws.max_row)}", rule)
    set_widths(ws, [10, 10, 13, 9, 9, 9, 18, 10])
    ws.freeze_panes = "C2"


def write_figure(wb: Workbook) -> None:
    """7.3절 콕핏을 참고 시트에 넣는다. 그림이 없으면 안내만 남긴다."""
    ws = wb.create_sheet("참고 그림")
    ws["A1"] = (
        "전체 Core 50웨이퍼의 누적 분석 참고 그림이며, "
        "보고 기준일의 일일 지표를 나타내지 않는다"
    )
    if not COCKPIT.exists():
        ws["A2"] = "그림 없음: 7.3절 ch07_03을 먼저 실행한다"
        return
    img = Image(str(COCKPIT))
    img.width, img.height = 640, round(640 * img.height / img.width)
    ws.add_image(img, "A3")


def show(label: str, value: object) -> None:
    """한글 이름과 값을 표시 폭에 맞춰 한 줄로 출력한다."""
    text = f"{value:.1%}" if isinstance(value, float) else str(value)
    space = " " * max(0, 12 - display_width(text))
    print(f"  {pad(label, 26)}{space}{text}")


def report(out: Path, day: datetime, how: str, cut: tuple) -> None:
    """저장한 파일을 다시 열어 핵심 지표와 들어간 개체를 보인다."""
    ws = load_workbook(out)["대시보드"]
    print(f"  기준일 {day:%Y-%m-%d} ({how})")
    print(f"  저장: {out.relative_to(REPO_ROOT).as_posix()}")
    print("-" * 60)
    for row in range(4, 10):  # 다시 연 파일의 핵심 지표
        show(str(ws.cell(row=row, column=1).value),
             ws.cell(row=row, column=2).value)  # fmt: skip
    rows, fails = cut
    show("(비교) 날짜로 자른 관측", f"{fails} / {rows}행")
    with zipfile.ZipFile(out) as z:
        names = z.namelist()
    charts = sum(n.startswith("xl/charts/chart") for n in names)
    images = sum(n.startswith("xl/media/") for n in names)
    print("-" * 60)
    print(f"  파일에 든 차트 {charts}개, 그림 {images}장")


def main() -> None:
    """점검 → 웨이퍼 집계 → 완료일 → 기준일 → 기록 → 다시 읽어 확인."""
    process = load_input()
    wafers = wafer_table(process)
    days = daily_table(wafers)
    day, how = pick_day(days)
    today = wafers.loc[wafers["done"] == day]
    trend = days.loc[days["done"] <= day]
    wb = Workbook()
    write_info(wb, day)
    write_dashboard(wb, day, today, trend)
    write_detail(wb, today)
    write_figure(wb)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORT_DIR / f"ch09_03_daily_dashboard_{day:%Y%m%d}.xlsx"
    wb.save(out)
    observed = process.loc[process["Timestamp"].dt.normalize() == day]
    cut = (len(observed), int((observed["Pass_Fail"] == 0).sum()))
    print("=" * 60)
    print(" 9.3 일일 팹 수율 대시보드")
    print("=" * 60)
    print(f"  [PASS] 입력 점검 {len(EXPECTED)}항목 (다이 {N_ROWS}개, "
          f"웨이퍼 {N_WAFERS}장)")  # fmt: skip
    report(out, day, how, cut)
    print(f"  일별 추이 {len(trend)}일, 웨이퍼 상세 {len(today)}행")
    print(
        "  [확인 범위] 다시 연 파일의 핵심 지표와 개체 수만 확인했다."
    )
    print("              차트와 그림의 모양은 엑셀에서 확인한다")
    print("=" * 60)


if __name__ == "__main__":
    main()
