"""
ch08_01_build_db.py  (8.1절)
설계 레코드(3.3절 JSON)와 제조 관측(통합 CSV)을 SQLite 분석
데이터베이스의 두 테이블에 적재하고, SQL로 다시 세어 원본과 대조한다.
실행 위치: 저장소 루트
"""

import sqlite3

from ax_db import (
    ANALYSIS_DB,
    DESIGN_COLUMNS,
    PROCESS_COLUMNS,
    connect,
    create_tables,
    design_table,
    insert_sql,
    load_design,
    process_table,
    to_rows,
)
from ax_frame import load_dataset
from ax_settings import REPO_ROOT
from ax_text import pad

# (항목, 원본에서 기대하는 값, 데이터베이스에 묻는 SQL)
CHECKS = [
    ("design_path 행 수", 5000, "SELECT COUNT(*) FROM design_path"),
    ("process_die 행 수", 5000, "SELECT COUNT(*) FROM process_die"),
    (
        "Leakage_Power NULL",
        125,
        "SELECT COUNT(*) FROM design_path WHERE Leakage_Power IS NULL",
    ),
    (
        "불량(Pass_Fail = 0)",
        804,
        "SELECT COUNT(*) FROM process_die WHERE Pass_Fail = 0",
    ),
    (
        "웨이퍼 수",
        50,
        "SELECT COUNT(*) FROM "
        "(SELECT DISTINCT Lot_ID, Wafer_ID FROM process_die)",
    ),
    (
        "키로 이은 행 수",
        5000,
        "SELECT COUNT(*) FROM design_path "
        "JOIN process_die USING (Lot_ID, Wafer_ID, Die_X, Die_Y)",
    ),
]


def build(con: sqlite3.Connection) -> tuple[int, int]:
    """두 테이블을 만들고 한 번의 트랜잭션으로 적재한다."""
    core = load_dataset()
    design = to_rows(design_table(core, load_design()))
    process = to_rows(process_table(core))
    create_tables(con)
    with con:  # 성공하면 commit, 예외가 나면 rollback
        con.executemany(
            insert_sql("design_path", DESIGN_COLUMNS), design
        )
        con.executemany(
            insert_sql("process_die", PROCESS_COLUMNS), process
        )
    return len(design), len(process)


def verify(con: sqlite3.Connection) -> bool:
    """원본에서 기대하는 값과 SQL로 다시 센 값을 나란히 출력한다."""
    ok = True
    print(f"  {pad('항목', 22)}  기대      DB  판정")
    for name, expected, sql in CHECKS:
        got = con.execute(sql).fetchone()[0]
        mark = "PASS" if got == expected else "FAIL"
        ok = ok and got == expected
        print(f"  {pad(name, 22)}{expected:>6}{got:>8}  {mark}")
    return ok


def report() -> None:
    """기존 파일을 지우고 새로 만든 뒤 대조 결과를 출력한다."""
    ANALYSIS_DB.unlink(missing_ok=True)  # 8.1절은 전체를 새로 만든다
    con = connect(ANALYSIS_DB)
    try:
        n_design, n_process = build(con)
        print("=" * 56)
        print(" SQLite 분석 데이터베이스 적재")
        print("=" * 56)
        print(
            f"  적재 design_path {n_design:,}행 / "
            f"process_die {n_process:,}행"
        )
        print("-" * 56)
        ok = verify(con)
    finally:
        con.close()  # 트랜잭션과 별개로 연결은 직접 닫는다
    print("-" * 56)
    size = ANALYSIS_DB.stat().st_size / 1024
    path = ANALYSIS_DB.relative_to(REPO_ROOT).as_posix()
    print(f"  파일 {path} ({size:,.0f} KB)")
    print(f"  [판정] {'PASS' if ok else 'FAIL'}")
    print("  [확인 범위] 행 수·NULL·키 연결만 대조했다")
    print("=" * 56)


if __name__ == "__main__":
    report()
