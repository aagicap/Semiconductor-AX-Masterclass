"""
ch08_03_etl_pipeline.py  (8.3절 미니 프로젝트 모범 답안)
입고 배치 단위로 설계 자산(JSON)과 통합 CSV를 읽어 검증한 뒤 SQLite에
적재한다. 같은 배치를 다시 실행해도 행이 늘지 않고, 배치 안에서 하나라도
실패하면 그 배치 전체를 취소하고 실패 이력만 남긴다. 스키마 준비는
배치보다 먼저 따로 확정하므로 첫 배치가 실패해도 테이블과 이력이 남는다.
실행 위치: 저장소 루트
실행 예: python part3_visual_db_report/ch08/ch08_03_etl_pipeline.py
         batch_1 --reset
"""

import argparse
import sqlite3
from datetime import datetime

import pandas as pd

from ax_db import (
    DESIGN_COLUMNS,
    ETL_DB,
    PROCESS_COLUMNS,
    connect,
    create_tables,
    design_table,
    load_design,
    process_table,
    to_rows,
)
from ax_frame import KEY_COLUMNS, load_dataset
from ax_text import pad

# 입고 배치. Timestamp의 달력 날짜와 섞이지 않게 배치 이름으로 부른다
BATCHES = {
    "batch_1": [f"LOT_{i:02d}" for i in range(8)],
    "batch_2": ["LOT_08", "LOT_09"],
}
HISTORY_SCHEMA = """
CREATE TABLE IF NOT EXISTS etl_history (
    run_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at     TEXT    NOT NULL,
    batch          TEXT    NOT NULL,
    rows_attempted INTEGER NOT NULL,
    rows_inserted  INTEGER NOT NULL,
    status         TEXT    NOT NULL
        CHECK (status IN ('SUCCESS', 'FAILED')),
    message        TEXT
);
"""


def upsert_sql(table: str, columns: list[str]) -> str:
    """기본 키가 겹치는 행만 건너뛰는 INSERT 문. 다른 제약 위반은
    그대로 오류가 난다(INSERT OR IGNORE와 다른 점)."""
    names = ", ".join(columns)
    marks = ", ".join("?" for _ in columns)
    keys = ", ".join(KEY_COLUMNS)
    return (
        f"INSERT INTO {table} ({names}) VALUES ({marks}) "
        f"ON CONFLICT ({keys}) DO NOTHING"
    )


def extract(lots: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """배치에 속한 로트만 두 원천에서 읽는다."""
    core = load_dataset()
    core = core.loc[core["Lot_ID"].isin(lots)]
    design = load_design().query("Lot_ID in @lots")
    if design.empty or core.empty:
        raise ValueError(f"원천 자료가 없다: {lots}")
    return core, design


def transform(
    core: pd.DataFrame, design: pd.DataFrame, fail_lot: str | None
) -> tuple[list[tuple], list[tuple]]:
    """짝·경고 대응을 확인하고 적재할 행으로 바꾼다."""
    dtab = design_table(core, design)  # 짝이 없으면 여기서 멈춘다
    ptab = process_table(core).copy()
    warn = dtab.set_index(KEY_COLUMNS)["Alarm"].eq("GAS_FLOW_WARN")
    code = ptab.set_index(KEY_COLUMNS)["Error_Code"].eq("ERR-G202")
    mismatch = int((warn.sort_index() != code.sort_index()).sum())
    if mismatch:
        raise ValueError(f"경고와 에러 코드가 다른 행 {mismatch}개")
    if fail_lot:  # 실패 실험: 메모리의 사본 한 행만 바꾼다
        row = ptab.index[ptab["Lot_ID"] == fail_lot][0]
        ptab.loc[row, "Pass_Fail"] = 2
    return to_rows(dtab), to_rows(ptab)


def prepare(con) -> None:
    """세 테이블을 준비하고 배치와 별개로 먼저 확정한다."""
    with con:
        create_tables(con)
        con.executescript(HISTORY_SCHEMA)


def load(con, name, design, process) -> int:
    """한 배치를 하나의 트랜잭션으로 적재하고 새로 들어간 행 수를
    돌려준다. 성공 이력도 같은 트랜잭션 안에서 남긴다."""
    with con:
        before = con.total_changes
        con.executemany(
            upsert_sql("design_die", DESIGN_COLUMNS), design
        )
        con.executemany(
            upsert_sql("process_die", PROCESS_COLUMNS), process
        )
        inserted = con.total_changes - before
        con.execute(
            "INSERT INTO etl_history (started_at, batch, "
            "rows_attempted, rows_inserted, status) "
            "VALUES (?, ?, ?, ?, 'SUCCESS')",
            (now(), name, len(design) + len(process), inserted),
        )
    return inserted


def record_failure(con, name: str, attempted: int, error: Exception):
    """적재가 취소된 뒤, 새 트랜잭션에서 실패 이력만 남긴다."""
    with con:
        con.execute(
            "INSERT INTO etl_history (started_at, batch, "
            "rows_attempted, rows_inserted, status, message) "
            "VALUES (?, ?, ?, 0, 'FAILED', ?)",
            (
                now(),
                name,
                attempted,
                f"{type(error).__name__}: {error}",
            ),
        )


def now() -> str:
    """적재 시각. 데이터의 Timestamp와 같은 ISO 8601 형식."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def count(con, sql: str) -> int:
    """행 하나, 열 하나를 돌려주는 집계 질문의 값."""
    return con.execute(sql).fetchone()[0]


def summary(con) -> None:
    """테이블별 행 수, 키 연결, 결측, 적재 이력을 출력한다."""
    checks = [
        ("design_die 행 수", "SELECT COUNT(*) FROM design_die"),
        ("process_die 행 수", "SELECT COUNT(*) FROM process_die"),
        (
            "키로 이은 행 수",
            "SELECT COUNT(*) FROM design_die JOIN process_die "
            "USING (Lot_ID, Wafer_ID, Die_X, Die_Y)",
        ),
        (
            "Leakage_Power NULL",
            "SELECT COUNT(*) FROM design_die "
            "WHERE Leakage_Power IS NULL",
        ),
    ]
    for name, sql in checks:
        print(f"  {pad(name, 24)}{count(con, sql):>6}")
    print("  적재 이력 (run, batch, 시도, 새로 들어간 행, 상태)")
    for row in con.execute(
        "SELECT run_id, batch, rows_attempted, rows_inserted, "
        "status "
        "FROM etl_history ORDER BY run_id"
    ):
        print(
            f"     {row[0]:>2}  {row[1]}  {row[2]:>5}  {row[3]:>5}"
            f"  {row[4]}"
        )


def main() -> None:
    """명령줄에서 배치 이름을 받아 ETL을 한 번 실행한다."""
    parser = argparse.ArgumentParser()
    parser.add_argument("batch", choices=list(BATCHES))
    parser.add_argument("--fail-lot", help="실패 실험용 로트 이름")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="ETL 데이터베이스를 지우고 시작한다",
    )
    args = parser.parse_args()
    if args.reset:
        ETL_DB.unlink(missing_ok=True)
    lots = BATCHES[args.batch]
    con = connect(ETL_DB)
    prepare(con)
    attempted = 0
    print("=" * 60)
    print(f" ETL 적재: {args.batch} ({lots[0]} ~ {lots[-1]})")
    print("=" * 60)
    try:
        core, design = extract(lots)
        drows, prows = transform(core, design, args.fail_lot)
        attempted = len(drows) + len(prows)
        inserted = load(con, args.batch, drows, prows)
        print(
            f"  [PASS] 적재 시도 {attempted:,}행, 새로 들어간 행 "
            f"{inserted:,}행"
        )
    except (ValueError, sqlite3.IntegrityError) as error:
        record_failure(con, args.batch, attempted, error)
        print(f"  [FAIL] {type(error).__name__}: {error}")
        print("         배치 전체를 취소했다")
    try:
        print("-" * 60)
        summary(con)
    finally:
        con.close()
    print("  [확인 범위] 행 수·키 연결·NULL·적재 이력만 확인했다")
    print("=" * 60)


if __name__ == "__main__":
    main()
