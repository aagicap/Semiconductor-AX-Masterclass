"""
ch08_02_query_index.py  (8.2절)
8.1절의 분석 데이터베이스에 SQL로 질문하고, 인덱스를 만들기 전후의
실행 계획과 조회 시간을 비교한다.
실행 위치: 저장소 루트 (먼저 ch08_01_build_db.py를 실행한다)
"""

import sqlite3
import time

import pandas as pd

from ax_db import ANALYSIS_DB, connect
from ax_frame import load_dataset
from ax_stats import fail_rate
from ax_text import pad

# ① 로트별 불량률. 6.1절의 groupby()와 같은 질문이다
LOT_SQL = """
SELECT Lot_ID,
       COUNT(*)                 AS dies,
       SUM(Pass_Fail = 0)       AS fails,
       100.0 * AVG(Pass_Fail = 0) AS fail_pct
FROM process_die
GROUP BY Lot_ID
ORDER BY Lot_ID
"""
# ② 두 테이블을 네 열 키로 잇고 장비별로 묶는다
JOIN_SQL = """
SELECT p.Equipment_ID,
       COUNT(*)                 AS dies,
       SUM(d.Worst_Slack < 0)   AS neg_slack,
       AVG(d.Worst_Slack)       AS mean_slack
FROM design_die AS d
JOIN process_die AS p USING (Lot_ID, Wafer_ID, Die_X, Die_Y)
GROUP BY p.Equipment_ID
"""
# ③ 장비와 기간 조건. 값은 ?로 넘기고 기간은 [시작, 끝)으로 연다
RANGE_SQL = """
SELECT COUNT(*), AVG(Chamber_Temp), SUM(Pass_Fail = 0)
FROM process_die
WHERE Equipment_ID = ?
  AND Timestamp >= ? AND Timestamp < ?
"""
RANGE_PARAMS = ("ETCHER_B", "2026-01-10", "2026-01-12")
INDEX_SQL = (
    "CREATE INDEX idx_process_equipment_ts "
    "ON process_die (Equipment_ID, Timestamp)"
)


def plan(con: sqlite3.Connection, sql: str, params=()) -> str:
    """EXPLAIN QUERY PLAN의 설명 열만 이어 붙여 돌려준다."""
    rows = con.execute("EXPLAIN QUERY PLAN " + sql, params).fetchall()
    return " / ".join(row[-1] for row in rows)


def used_kb(con: sqlite3.Connection) -> float:
    """빈 페이지를 뺀, 실제로 쓰는 데이터베이스 크기(KB)."""
    pages = con.execute("PRAGMA page_count").fetchone()[0]
    free = con.execute("PRAGMA freelist_count").fetchone()[0]
    size = con.execute("PRAGMA page_size").fetchone()[0]
    return (pages - free) * size / 1024


def best_ms(con: sqlite3.Connection, sql: str, params=()) -> float:
    """200회 조회의 평균 시간(ms)을 5번 재고 가장 작은 값을 고른다."""
    times = []
    for _ in range(5):
        start = time.perf_counter()
        for _ in range(200):
            con.execute(sql, params).fetchall()
        times.append((time.perf_counter() - start) / 200 * 1000)
    return min(times)


def show_queries(con: sqlite3.Connection) -> None:
    """세 질문의 결과를 출력하고 ①을 판다스 계산과 대조한다."""
    lots = pd.read_sql_query(LOT_SQL, con)
    pdf = load_dataset().groupby("Lot_ID", observed=True)["Pass_Fail"]
    diff = (lots["fail_pct"] - pdf.agg(fail_rate).to_numpy()).abs()
    print("  ① 로트별 불량률(%)")
    for row in lots.itertuples(index=False):
        print(
            f"     {row.Lot_ID}  {row.fails:>3} / {row.dies}"
            f"  {row.fail_pct:5.1f}"
        )
    print(f"     판다스(6.1절)와의 최대 차이 {diff.max():.1e}")
    print("  ② 장비별 다이 수, 슬랙 음수, 평균 슬랙(ns)")
    for eq, dies, neg, mean in con.execute(JOIN_SQL):
        print(f"     {eq}  {dies:>5}  {neg:>4}  {mean:.3f}")
    n, temp, fails = con.execute(RANGE_SQL, RANGE_PARAMS).fetchone()
    eq, start, end = RANGE_PARAMS
    print(f"  ③ {eq}, {start} 이상 {end} 미만")
    print(f"     다이 {n}  평균 챔버 온도 {temp:.2f}  불량 {fails}")


def show_index(con: sqlite3.Connection) -> None:
    """인덱스 전후의 실행 계획, 조회 시간, 사용 크기를 비교한다."""
    with con:  # 다시 실행해도 같은 비교가 되도록 먼저 지운다
        con.execute("DROP INDEX IF EXISTS idx_process_equipment_ts")
    size0 = used_kb(con)
    before = plan(con, RANGE_SQL, RANGE_PARAMS)
    t0 = best_ms(con, RANGE_SQL, RANGE_PARAMS)
    with con:
        con.execute(INDEX_SQL)
    size1 = used_kb(con)
    after = plan(con, RANGE_SQL, RANGE_PARAMS)
    t1 = best_ms(con, RANGE_SQL, RANGE_PARAMS)
    for label, text in [("전", before), ("후", after)]:
        head, _, cond = text.partition(" (")
        print(f"  ③의 실행 계획({label}) {head}")
        if cond:  # 인덱스로 좁힌 조건은 다음 줄에 적는다
            print(f"{' ' * 22}({cond}")
    print(
        f"  {pad('1회 조회 시간(ms, 참고)', 26)}"
        f"{t0:.2f} -> {t1:.2f}"
    )
    print(f"  {pad('사용 크기(KB)', 26)}{size0:,.0f} -> {size1:,.0f}")
    print("  키의 앞 열만 쓰는 조건과 쓰지 않는 조건")
    for sql, params in [
        ("SELECT * FROM process_die WHERE Lot_ID = ?", ("LOT_08",)),
        ("SELECT * FROM process_die WHERE Die_X = ?", (3,)),
    ]:
        where = sql.split("WHERE ")[1]
        head = plan(con, sql, params).partition(" (")[0]
        print(f"     {pad(where, 14)}{head}")


def report() -> None:
    """질문 세 개와 인덱스 비교를 출력한다."""
    if not ANALYSIS_DB.exists():
        raise FileNotFoundError(
            "분석 데이터베이스가 없다. "
            "ch08_01_build_db.py를 먼저 실행한다"
        )
    con = connect(ANALYSIS_DB)
    try:
        print("=" * 64)
        print(" SQL 질문과 인덱스")
        print("=" * 64)
        show_queries(con)
        print("-" * 64)
        show_index(con)
    finally:
        con.close()
    print("-" * 64)
    print("  [확인 범위] 실행 계획과 이 환경의 조회 시간만 비교했다")
    print("  시간은 실행 환경에 따라 다르다")
    print("=" * 64)


if __name__ == "__main__":
    report()
