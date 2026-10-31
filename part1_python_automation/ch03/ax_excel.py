"""
ax_excel.py
9장 실습이 함께 쓰는 엑셀 서식 규칙. 리포트마다 서식을 따로 정하지
않고 이 모듈의 규칙을 불러 쓴다. 불러오기만 해서는 파일을 만들지 않는다.
"""

from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from ax_settings import DATA_DIR

REPORT_DIR = DATA_DIR / "processed" / "reports"

# 값의 종류별 표시 형식. 값은 숫자로 두고 보이는 모양만 정한다
FORMATS = {
    "count": "#,##0",  # 다이 수, 불량 수
    "rate": "0.0%",  # 비율. 0.2는 20.0%로 보인다
    "value": "0.00",  # 측정·분석 값
    "time": "yyyy-mm-dd hh:mm",  # 관측 시각
    "date": "yyyy-mm-dd",  # 완료일 같은 날짜
    "text": "@",  # 식별자
}

HEADER_FONT = Font(bold=True, color="FFFFFF")
HEADER_FILL = PatternFill("solid", fgColor="203D80")
THIN = Side(style="thin", color="BFBFBF")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def write_table(
    ws: Worksheet,
    headers: list[str],
    rows: list[tuple],
    kinds: list[str],
    start_row: int = 1,
) -> None:
    """머리 행과 데이터 행을 쓰고, 열마다 같은 형식을 입힌다.
    kinds는 열마다 FORMATS의 키 하나를 고른다."""
    if len(headers) != len(kinds):
        raise ValueError("머리 행과 형식의 열 수가 다르다")
    for col, name in enumerate(headers, start=1):
        cell = ws.cell(row=start_row, column=col, value=name)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal="center")
        cell.border = BOX
    for r, values in enumerate(rows, start=start_row + 1):
        for col, (value, kind) in enumerate(zip(values, kinds), 1):
            cell = ws.cell(row=r, column=col, value=value)
            cell.number_format = FORMATS[kind]
            cell.border = BOX


def set_widths(ws: Worksheet, widths: list[float]) -> None:
    """열 너비를 앞에서부터 차례로 정한다(단위: 글자 수)."""
    for col, width in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(col)].width = width
