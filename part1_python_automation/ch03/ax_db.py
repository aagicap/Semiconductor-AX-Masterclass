"""
ax_db.py
8장 이후 실습이 함께 쓰는 분석 데이터베이스(SQLite) 스키마와 변환 함수.
열 이름은 통합 CSV와 같게 둔다. 불러오기만 해서는 파일을 만들지 않는다.
"""

import json
import sqlite3
from pathlib import Path

import pandas as pd

from ax_frame import KEY_COLUMNS
from ax_settings import DATA_DIR

DB_DIR = DATA_DIR / "processed"
ANALYSIS_DB = DB_DIR / "alphachip_analysis.db"  # 8.1·8.2절
ETL_DB = DB_DIR / "alphachip_etl.db"  # 8.3절 증분 적재
DESIGN_DIR = DATA_DIR / "parsed_engine"  # 3.3절 설계 자산

# 설계 조건과 설계 분석 결과. Voltage는 통합 CSV에서 가져온다
DESIGN_COLUMNS = [
    "Lot_ID", "Wafer_ID", "Die_X", "Die_Y", "Voltage",
    "Path_ID", "Worst_Slack", "Leakage_Power", "Operating_Freq",
    "Alarm",
]  # fmt: skip
# 제조 관측과 결과. 순수 센서 테이블이 아니라 판정까지 담는다
PROCESS_COLUMNS = [
    "Lot_ID", "Wafer_ID", "Die_X", "Die_Y", "Timestamp",
    "Equipment_ID", "Chamber_Temp", "Pressure", "Gas_Flow",
    "Pass_Fail", "Error_Code",
]  # fmt: skip

# JSON 속성 이름 → 통합 CSV 열 이름
JSON_TO_CSV = {
    "lot_id": "Lot_ID",
    "wafer_id": "Wafer_ID",
    "die_x": "Die_X",
    "die_y": "Die_Y",
    "path_id": "Path_ID",
    "worst_slack": "Worst_Slack",
    "leakage_power": "Leakage_Power",
    "operating_freq": "Operating_Freq",
    "alarm": "Alarm",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS design_die (
    Lot_ID         TEXT    NOT NULL,
    Wafer_ID       TEXT    NOT NULL,
    Die_X          INTEGER NOT NULL,
    Die_Y          INTEGER NOT NULL,
    Voltage        REAL    NOT NULL,
    Path_ID        TEXT    NOT NULL,
    Worst_Slack    REAL    NOT NULL,
    Leakage_Power  REAL,               -- 결측은 NULL로 둔다
    Operating_Freq REAL    NOT NULL,
    Alarm          TEXT,               -- 경고가 없으면 NULL
    PRIMARY KEY (Lot_ID, Wafer_ID, Die_X, Die_Y)
);
CREATE TABLE IF NOT EXISTS process_die (
    Lot_ID         TEXT    NOT NULL,
    Wafer_ID       TEXT    NOT NULL,
    Die_X          INTEGER NOT NULL,
    Die_Y          INTEGER NOT NULL,
    Timestamp      TEXT    NOT NULL,   -- ISO 8601 문자열
    Equipment_ID   TEXT    NOT NULL,
    Chamber_Temp   REAL    NOT NULL,
    Pressure       REAL    NOT NULL,
    Gas_Flow       REAL    NOT NULL,
    Pass_Fail      INTEGER NOT NULL CHECK (Pass_Fail IN (0, 1)),
    Error_Code     TEXT    NOT NULL
        CHECK (Error_Code IN ('NORMAL', 'ERR-T101', 'ERR-G202')),
    PRIMARY KEY (Lot_ID, Wafer_ID, Die_X, Die_Y)
);
"""


def connect(path: Path) -> sqlite3.Connection:
    """데이터베이스 파일을 연다. 없으면 폴더와 파일을 만든다.
    트랜잭션 동작을 환경 기본값에 맡기지 않고 직접 정한다."""
    path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(path, autocommit=False)


def connect_readonly(path: Path) -> sqlite3.Connection:
    """조회 전용으로 연다. 파일이 없으면 새로 만들지 않고 오류를 낸다.
    경로를 잘못 주었을 때 빈 데이터베이스를 읽는 일을 막는다."""
    uri = path.resolve().as_uri() + "?mode=ro"
    return sqlite3.connect(uri, uri=True, autocommit=False)


def create_tables(con: sqlite3.Connection) -> None:
    """두 테이블을 만든다. 이미 있으면 그대로 둔다."""
    con.executescript(SCHEMA)


def to_rows(frame: pd.DataFrame) -> list[tuple]:
    """데이터프레임을 SQLite에 넣을 튜플 목록으로 바꾼다.
    NaN은 None(SQL의 NULL)으로, 시각은 ISO 8601 문자열로 바꾼다."""
    out = frame.copy()
    for col in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[col]):
            out[col] = out[col].dt.strftime("%Y-%m-%d %H:%M:%S")
    out = out.astype(object).where(out.notna(), None)
    return list(out.itertuples(index=False, name=None))


def insert_sql(table: str, columns: list[str]) -> str:
    """값 자리를 ?로 비워 둔 INSERT 문을 만든다."""
    names = ", ".join(columns)
    marks = ", ".join("?" for _ in columns)
    return f"INSERT INTO {table} ({names}) VALUES ({marks})"


def load_design(design_dir: Path = DESIGN_DIR) -> pd.DataFrame:
    """3.3절 JSON 자산의 레코드를 통합 CSV 열 이름의 표로 모은다."""
    files = sorted(design_dir.glob("lot_*.json"))
    if not files:
        raise FileNotFoundError(f"설계 자산이 없다 : {design_dir}")
    records = []
    for path in files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        records.extend(payload["records"])
    return pd.DataFrame(records).rename(columns=JSON_TO_CSV)


def design_table(
    core: pd.DataFrame, design: pd.DataFrame
) -> pd.DataFrame:
    """설계 레코드에 통합 CSV의 Voltage(설계 분석 조건)를 붙인다.
    validate는 키 중복을, _merge는 짝 누락을 확인한다."""
    volt = core[KEY_COLUMNS + ["Voltage"]].astype(
        {"Lot_ID": str, "Wafer_ID": str}
    )
    table = design.merge(
        volt,
        on=KEY_COLUMNS,
        how="outer",
        validate="one_to_one",
        indicator=True,
    )
    unmatched = int((table["_merge"] != "both").sum())
    if unmatched:
        raise ValueError(f"짝이 없는 키가 {unmatched}개 있다")
    return table[DESIGN_COLUMNS]


def process_table(core: pd.DataFrame) -> pd.DataFrame:
    """통합 CSV에서 제조 관측과 결과 열만 고른다."""
    return core[PROCESS_COLUMNS]
