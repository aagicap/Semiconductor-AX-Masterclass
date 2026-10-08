"""
ch06_04_relation.py  (6.4절 미니 프로젝트 해답)
병합한 설계·공정 표에서 장비 변동성과 웨이퍼 수율 하락이
어떻게 함께 움직이는지 단계별로 추적한다.
실행 위치: 저장소 루트
"""

import pandas as pd

from ax_settings import DATA_DIR
from ax_stats import fail_rate
from ax_text import pad

MERGED_PATH = DATA_DIR / "processed" / "design_process.csv"
WAFER_KEY = ["Lot_ID", "Wafer_ID"]
TEMP_BINS = [0, 75, 80, 85, 100]  # 관찰용 구간(℃). 규격이 아니다
GAS_WARN = 88.0  # 경고 코드 기록 기준(sccm). 일러두기 참고


def wafer_table(df: pd.DataFrame) -> pd.DataFrame:
    """웨이퍼마다 장비, 불량률, 온도·유량·슬랙 평균을 만든다."""
    return df.groupby(WAFER_KEY, observed=True).agg(
        equipment=("Equipment_ID", "first"),
        rate=("Pass_Fail", fail_rate),
        temp=("Chamber_Temp", "mean"),
        gas=("Gas_Flow", "mean"),
        slack=("Worst_Slack", "mean"),
    )


def band_table(df: pd.DataFrame) -> pd.DataFrame:
    """온도 구간과 장비로 묶어 다이 수와 불량률을 펼친다."""
    band = pd.cut(df["Chamber_Temp"], TEMP_BINS)
    table = df.groupby([band, "Equipment_ID"], observed=True).agg(
        dies=("Pass_Fail", "size"),
        rate=("Pass_Fail", fail_rate),
    )
    return table.unstack("Equipment_ID")


def show_wafers(wafers: pd.DataFrame) -> None:
    """[1][2] 웨이퍼 단위 요약과 장비별 상관계수를 출력한다."""
    print("  [1] 웨이퍼 단위 요약(장비별 평균, 온도 ℃·유량 sccm)")
    print("  장비        웨이퍼  불량률     온도       유량")
    for name, part in wafers.groupby("equipment"):
        print(
            f"  {pad(str(name), 12)}{len(part):>4}장"
            f"  {part.rate.mean():6.2f}%  {part.temp.mean():7.2f}"
            f"  {part.gas.mean():9.2f}"
        )
    print("-" * 62)
    print("  [2] 웨이퍼 평균값 사이의 상관계수(장비별)")
    for name, part in wafers.groupby("equipment"):
        c = part[["temp", "gas", "rate"]].corr()
        tg, tr = c.loc["temp", "gas"], c.loc["temp", "rate"]
        print(
            f"  {pad(str(name), 12)}온도-유량 {tg:5.2f}"
            f"  온도-불량률 {tr:5.2f}"
        )


def show_bands(df: pd.DataFrame) -> None:
    """[3] 온도 구간별 불량률과 불량이 나타난 온도 범위를 출력한다."""
    print("  [3] 온도 구간(℃) x 장비 불량률(다이 단위)")
    print("  구간            A 다이  A 불량률   B 다이  B 불량률")
    for band, row in band_table(df).iterrows():
        print(
            f"  {pad(str(band), 14)}{int(row[('dies', 'ETCHER_A')]):>6}"
            f"  {row[('rate', 'ETCHER_A')]:7.1f}%"
            f"  {int(row[('dies', 'ETCHER_B')]):>6}"
            f"  {row[('rate', 'ETCHER_B')]:7.1f}%"
        )
    failed = df["Pass_Fail"] == 0
    t = df["Chamber_Temp"]
    low, high = t[failed].min(), t[failed].max()
    print(
        f"  불량 다이 온도 {low:.2f} ~ {high:.2f}"
        f" / 정상 다이 최고 {t[~failed].max():.2f}"
    )
    hot = t > 85
    print(
        f"  85℃ 초과 {int(hot.sum())}행 중 불량"
        f" {int((hot & failed).sum())}행"
    )


def show_clues(df: pd.DataFrame) -> None:
    """[4] 온도와 유량을 떼어 볼 단서와 경고 코드 기록 수를 출력한다."""
    print("  [4] 온도와 유량을 떼어 볼 단서")
    a_hot = (df["Equipment_ID"] == "ETCHER_A") & (
        df["Chamber_Temp"] > 75
    )
    print(
        f"  ETCHER_A 75℃ 초과 {int(a_hot.sum())}행:"
        f" 유량 평균 {df.loc[a_hot, 'Gas_Flow'].mean():.1f},"
        f" 불량률 {fail_rate(df.loc[a_hot, 'Pass_Fail']):.1f}%"
    )
    low_gas = df["Gas_Flow"] < GAS_WARN
    g202 = df["Error_Code"] == "ERR-G202"
    print(
        f"  유량 {GAS_WARN:.0f} 미만 {int(low_gas.sum())}행"
        f" / ERR-G202 기록 {int(g202.sum())}행"
    )


def report() -> None:
    """관계 추적 단계별 결과를 출력한다."""
    if not MERGED_PATH.exists():
        print(f"[FAIL] 병합 결과가 없다 : {MERGED_PATH}")
        print("       6.3절 ch06_03_merge.py 를 먼저 실행한다.")
        return
    df = pd.read_csv(MERGED_PATH)
    print("=" * 62)
    print(" 장비 변동성과 웨이퍼 수율 하락의 관계 추적")
    print("=" * 62)
    show_wafers(wafer_table(df))
    print("-" * 62)
    show_bands(df)
    print("-" * 62)
    show_clues(df)
    print("-" * 62)
    print("  [확인 범위] 관측값이 함께 움직이는 모습만 확인했다")
    print("  어느 값이 다른 값을 바꾸었는지는 판단하지 않았다")
    print("=" * 62)


if __name__ == "__main__":
    report()
