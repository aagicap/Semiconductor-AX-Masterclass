"""
benchmark_sqlite_index.py  (8.2절 온라인 심화 자료의 측정 재현)
process_die를 행 수만 늘린 측정용 복제 데이터베이스로 만들어,
(Equipment_ID, Timestamp) 인덱스 전후의 조회 시간을 행 수별로 잰다.
복제 행은 Lot_ID에 복제 번호를 붙여 키만 겹치지 않게 한 것이다.
분석에는 쓰지 않는다.
실행 위치: 저장소 루트 (먼저 ch08_01_build_db.py를 실행한다)
"""

import sqlite3
import time

from ax_db import ANALYSIS_DB
from ax_settings import DATA_DIR

BENCH_DB = DATA_DIR / "bench" / "bench_index.db"
COPIES = [1, 10, 100]  # 5,000행, 50,000행, 500,000행
RANGE_SQL = (
    "SELECT COUNT(*), AVG(Chamber_Temp) FROM process_die "
    "WHERE Equipment_ID = ? AND Timestamp >= ? AND Timestamp < ?"
)
PARAMS = ("ETCHER_B", "2026-01-10", "2026-01-12")


def best_ms(con: sqlite3.Connection, repeat: int = 20) -> float:
    """repeat회 조회의 평균 시간(ms)을 5번 재고 가장 작은 값."""
    times = []
    for _ in range(5):
        start = time.perf_counter()
        for _ in range(repeat):
            con.execute(RANGE_SQL, PARAMS).fetchall()
        times.append((time.perf_counter() - start) / repeat * 1000)
    return min(times)


def build(copies: int) -> sqlite3.Connection:
    """원본 process_die를 copies배로 복제한 측정용 파일을 만든다."""
    BENCH_DB.parent.mkdir(parents=True, exist_ok=True)
    BENCH_DB.unlink(missing_ok=True)
    con = sqlite3.connect(BENCH_DB, autocommit=False)
    with con:
        con.execute("ATTACH DATABASE ? AS src", (str(ANALYSIS_DB),))
        con.execute(
            "CREATE TABLE process_die AS "
            "SELECT * FROM src.process_die WHERE 0"
        )
        for k in range(copies):
            con.execute(
                "INSERT INTO process_die SELECT Lot_ID || '_' || ?, "
                "Wafer_ID, Die_X, Die_Y, Timestamp, Equipment_ID, "
                "Chamber_Temp, Pressure, Gas_Flow, Pass_Fail, "
                "Error_Code "
                "FROM src.process_die",
                (k,),
            )
    con.execute("DETACH DATABASE src")
    return con


def main() -> None:
    """행 수별로 인덱스 전후 시간을 출력한다."""
    print("=" * 56)
    print(" 행 수별 인덱스 전후 조회 시간(ms, 5회 중 최솟값)")
    print("=" * 56)
    print(f"  {'rows':>9}  {'SCAN':>8}  {'SEARCH':>8}  {'ratio':>6}")
    for copies in COPIES:
        con = build(copies)
        try:
            rows = con.execute(
                "SELECT COUNT(*) FROM process_die"
            ).fetchone()[0]
            t0 = best_ms(con)
            with con:
                con.execute(
                    "CREATE INDEX idx_eq_ts "
                    "ON process_die (Equipment_ID, Timestamp)"
                )
            t1 = best_ms(con)
        finally:
            con.close()
        print(f"  {rows:>9,}  {t0:>8.2f}  {t1:>8.2f}  {t0 / t1:>6.1f}")
    BENCH_DB.unlink(missing_ok=True)
    print("-" * 56)
    print("  [확인 범위] 이 환경에서 한 가지 조회의 시간만 쟀다")
    print("=" * 56)


if __name__ == "__main__":
    main()
