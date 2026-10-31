"""
ch09_02_dataframe_to_excel.py  (9.2절)
8.3절 ETL 데이터베이스를 데이터프레임으로 읽어 웨이퍼별 요약과
설계 지표를 엑셀 시트로 기록한다. 저장한 파일을 다시 읽어 기록 전
표와 대조한다.
실행 위치: 저장소 루트
"""

import pandas as pd
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import PatternFill

from ax_db import DESIGN_COLUMNS, ETL_DB, connect_readonly
from ax_excel import REPORT_DIR, apply_formats, set_widths
from ax_frame import KEY_COLUMNS
from ax_settings import REPO_ROOT
from ax_stats import wafer_summary
from ax_text import pad

OUT_PATH = REPORT_DIR / "ch09_02_wafer_report.xlsx"
# 교육용 경고 기준. 웨이퍼별 불량률이 이 값 이상이면 "해당"이다
WARN_RATE = 0.20
WARN_FILL = PatternFill("solid", fgColor="F8D7DA")

# 요약 열 이름 → 시트 머리 행. 식별자 열은 그대로 둔다
WAFER_NAMES = {
    "dies": "다이 수",
    "fails": "불량 수",
    "fail_ratio": "불량률",
    "last_seen": "마지막 관측",
    "warn": "경고 기준",
}
WAFER_KINDS = ["text", "text", "text", "count", "count", "rate", "time",
               "text"]  # fmt: skip
DESIGN_KINDS = ["text", "text", "count", "count", "value", "text",
                "value3", "value", "value", "text"]  # fmt: skip
SHEETS = {"웨이퍼별 요약": WAFER_KINDS, "설계 지표": DESIGN_KINDS}


def read_tables() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """두 테이블을 읽고, 대조에 쓸 값을 SQL로 따로 센다."""
    order = ", ".join(KEY_COLUMNS)
    con = connect_readonly(ETL_DB)
    try:
        process = pd.read_sql(
            "SELECT * FROM process_die", con, parse_dates=["Timestamp"]
        )
        design = pd.read_sql(
            f"SELECT {', '.join(DESIGN_COLUMNS)} FROM design_die "
            f"ORDER BY {order}",
            con,
        )
        fails, nulls = con.execute(
            "SELECT (SELECT SUM(Pass_Fail = 0) FROM process_die), "
            "(SELECT COUNT(*) - COUNT(Leakage_Power) FROM design_die)"
        ).fetchone()
    finally:
        con.close()
    if process.empty:
        raise RuntimeError(
            "process_die에 행이 없다. 8.3절 배치를 먼저 적재한다"
        )
    return process, design, {"fails": fails, "nulls": nulls}


def wafer_table(process: pd.DataFrame) -> pd.DataFrame:
    """관측 요약에 이 리포트의 규칙(교육용 경고 기준)을 더한다."""
    table = wafer_summary(process)
    hit = table["fail_ratio"] >= WARN_RATE  # 반올림 전 비율로 판정
    table["warn"] = hit.map({True: "해당", False: "미해당"})
    return table.rename(columns=WAFER_NAMES)


def write(tables: dict[str, pd.DataFrame]) -> None:
    """값은 to_excel()이 쓰고, 서식은 기록이 끝난 시트에 덧입힌다."""
    with pd.ExcelWriter(OUT_PATH, engine="openpyxl") as writer:
        for name, frame in tables.items():
            frame.to_excel(writer, sheet_name=name, index=False)
            ws = writer.sheets[name]
            apply_formats(ws, SHEETS[name])
            set_widths(ws, [10] * ws.max_column)
            ws.freeze_panes = "C2"
        ws = writer.sheets["웨이퍼별 요약"]
        rule = CellIsRule(
            operator="greaterThanOrEqual",
            formula=[str(WARN_RATE)],  # 셀 값과 같은 비율 단위
            fill=WARN_FILL,
        )
        ws.conditional_formatting.add(f"F2:F{ws.max_row}", rule)
        set_widths(ws, [10, 10, 12, 9, 9, 9, 18, 10])


def compare(name: str, written: pd.DataFrame) -> pd.DataFrame:
    """저장한 시트를 다시 읽어 값과 빈 셀 위치를 기록 전 표와 맞춘다."""
    back = pd.read_excel(  # 식별자는 문자열로 읽는다
        OUT_PATH,
        sheet_name=name,
        dtype={"Lot_ID": str, "Wafer_ID": str},
    )
    pd.testing.assert_frame_equal(written, back, rtol=1e-12)
    return back


def report(back: dict[str, pd.DataFrame], sql: dict) -> None:
    """다시 읽은 표의 행·열 수와, SQL로 따로 센 값을 나란히 보인다."""
    for name, frame in back.items():
        rows, cols = frame.shape
        print(f"  {pad(name, 16)}{rows:>8}{cols:>8}  일치")
    wafers, dies = back["웨이퍼별 요약"], back["설계 지표"]
    nulls = dies["Leakage_Power"].isna().sum()
    hits = (wafers["경고 기준"] == "해당").sum()
    print("-" * 56)
    print(f"  {pad('다시 읽은 값과 SQL', 24)}    엑셀     SQL")
    print(f"  {pad('불량 수 합계', 24)}"
          f"{wafers['불량 수'].sum():>8}{sql['fails']:>8}")  # fmt: skip
    print(
        f"  {pad('Leakage_Power 빈 셀', 24)}{nulls:>8}{sql['nulls']:>8}"
    )
    print(f"  {pad('경고 기준 해당 웨이퍼', 24)}{hits:>8}"
          f"  (전체 {len(wafers)})")  # fmt: skip


def main() -> None:
    """조회 → 요약 → 기록 → 다시 읽어 대조."""
    process, design, sql = read_tables()
    tables = {
        "웨이퍼별 요약": wafer_table(process),
        "설계 지표": design,
    }
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    write(tables)
    print("=" * 56)
    print(" 9.2 데이터프레임의 엑셀 기록과 대조")
    print("=" * 56)
    print(f"  저장: {OUT_PATH.relative_to(REPO_ROOT).as_posix()}")
    print(f"  {pad('시트', 16)}   행 수   열 수  대조")
    # 다르면 compare()가 AssertionError로 멈춘다
    back = {
        name: compare(name, frame) for name, frame in tables.items()
    }
    report(back, sql)
    print("  [확인 범위] 두 시트의 모든 값과 빈 셀 위치를 기록 전 표와")
    print("              대조했다. 서식은 보지 않았다")
    print("=" * 56)


if __name__ == "__main__":
    main()
