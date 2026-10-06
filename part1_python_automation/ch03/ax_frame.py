"""
ax_frame.py
통합 CSV를 자료형을 지정한 데이터프레임으로 읽는다.
4장 이후 실습이 함께 쓰는 표준 적재 함수다.
"""

from collections.abc import Hashable
from pathlib import Path

import pandas as pd

from ax_settings import DATA_DIR

CSV_PATH = DATA_DIR / "alphachip_v2_integrated_data.csv"

# 값의 종류가 적은 식별자는 범주형, 격자 좌표와 판정은 작은 정수
DTYPES: dict[Hashable, str] = {
    "Lot_ID": "category",
    "Wafer_ID": "category",
    "Equipment_ID": "category",
    "Path_ID": "category",
    "Error_Code": "category",
    "Die_X": "int8",
    "Die_Y": "int8",
    "Pass_Fail": "int8",
}


def load_dataset(path: Path = CSV_PATH) -> pd.DataFrame:
    """통합 CSV를 자료형과 날짜 형식을 지정해 읽는다."""
    return pd.read_csv(
        path,
        dtype=DTYPES,
        parse_dates=["Timestamp"],
        engine="pyarrow",
    )


# 4.3 무결성 점검 기준. 스키마 문서가 정한 값만 쓴다
COLUMNS = [
    "Timestamp",
    "Lot_ID",
    "Wafer_ID",
    "Die_X",
    "Die_Y",
    "Equipment_ID",
    "Path_ID",
    "Voltage",
    "Chamber_Temp",
    "Pressure",
    "Gas_Flow",
    "Operating_Freq",
    "Worst_Slack",
    "Leakage_Power",
    "Pass_Fail",
    "Error_Code",
]
KEY_COLUMNS = ["Lot_ID", "Wafer_ID", "Die_X", "Die_Y"]
MISSING_ALLOWED = {"Leakage_Power": 125}  # 결측이 예정된 열과 개수
ERROR_CODES = ["NORMAL", "ERR-T101", "ERR-G202"]
N_ROWS, N_LOTS, N_WAFERS, DIES_PER_WAFER = 5000, 10, 50, 100
INTERVAL = pd.Timedelta(minutes=5)  # 수집 간격


def check_integrity(frame: pd.DataFrame) -> list[tuple[str, str, int]]:
    """형식·키·관계를 점검해 (층위, 항목, 어긋난 수)를 돌려준다."""
    absent = [c for c in COLUMNS if c not in frame.columns]
    if absent:  # 열이 빠지면 나머지 점검을 할 수 없다
        return [("형식", "필수 열 16개 중 빠진 열", len(absent))]
    lost = frame.drop(columns=list(MISSING_ALLOWED)).isna().any(axis=1)
    planned = sum(
        abs(int(frame[c].isna().sum()) - n)
        for c, n in MISSING_ALLOWED.items()
    )
    x_ok = frame["Die_X"].between(0, 9)
    y_ok = frame["Die_Y"].between(0, 9)
    volt = ~frame["Voltage"].between(0.7, 1.4)
    judge = ~frame["Pass_Fail"].isin([0, 1])
    code = ~frame["Error_Code"].isin(ERROR_CODES)
    wafers = frame[["Lot_ID", "Wafer_ID"]].value_counts()
    n_lots = int(frame["Lot_ID"].nunique())
    n_wafers = int((wafers > 0).sum())  # 범주형은 빈 조합도 센다
    short = int((wafers != DIES_PER_WAFER).sum())
    dup = frame.duplicated(KEY_COLUMNS)
    gap = frame["Timestamp"].diff().dropna() != INTERVAL
    failed = frame["Pass_Fail"] == 0
    by_code = failed != (frame["Error_Code"] == "ERR-T101")
    by_slack = failed != (frame["Worst_Slack"] < 0)
    rows = [
        ("형식", "필수 열 16개 중 빠진 열", 0),
        ("형식", "허용 외 결측(행)", int(lost.sum())),
        ("형식", "예정 결측 125행과의 차이", planned),
        ("형식", "격자 좌표 0~9 밖(행)", int((~(x_ok & y_ok)).sum())),
        ("형식", "전압 0.7~1.4 V 밖(행)", int(volt.sum())),
        ("형식", "판정/코드 값 정의 밖(행)", int((judge | code).sum())),
        ("키", "전체 행 수와의 차이", abs(len(frame) - N_ROWS)),
        ("키", "로트 수와의 차이", abs(n_lots - N_LOTS)),
        ("키", "웨이퍼 수와의 차이", abs(n_wafers - N_WAFERS)),
        ("키", "복합 키 중복(행)", int(dup.sum())),
        ("키", "다이 100개 아닌 웨이퍼", short),
        ("키", "5분 간격이 아닌 구간", int(gap.sum())),
        ("관계", "판정과 코드 불일치(행)", int(by_code.sum())),
        ("관계", "판정과 슬랙 부호 불일치(행)", int(by_slack.sum())),
    ]
    return rows
