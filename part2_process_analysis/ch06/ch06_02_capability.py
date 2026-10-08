"""
ch06_02_capability.py
압력과 슬랙의 산포를 요약하고, 교육용 가상 규격으로 Cp·Cpk를 계산한다.
기간 전체로 낸 지수와 로트별로 나눈 지수를 비교한다.
실행 위치: 저장소 루트
"""

import pandas as pd

from ax_frame import load_dataset
from ax_stats import cp, cpk
from ax_text import pad

# 교육용 가상 규격: Cp·Cpk 계산을 위해 합성 시나리오에서 가정한 값.
# 실제 장비·제품의 검증 규격이 아니며, 5.1절 확인 범위와 다르다.
P_LSL, P_USL = 13.0, 17.5  # 압력(mTorr)
SLACK_LSL = 0.0  # 슬랙(ns). 양불 판정 규칙과 같은 값, 상한 없음


def spread(values: pd.Series) -> dict[str, float]:
    """산포를 평균, 표준편차, 5%·50%·95% 분위수로 요약한다."""
    q = values.quantile([0.05, 0.5, 0.95])
    return {
        "mean": values.mean(),
        "std": values.std(),
        "p05": q[0.05],
        "p50": q[0.5],
        "p95": q[0.95],
    }


def slack_cpk_by(df: pd.DataFrame, key: list[str]) -> pd.Series:
    """묶음별로 슬랙의 하한 Cpk를 계산한다."""
    return df.groupby(key, observed=True)["Worst_Slack"].agg(
        lambda s: cpk(s, lower=SLACK_LSL)
    )


def report() -> None:
    """압력·슬랙의 산포와 Cp·Cpk를 출력한다."""
    df = load_dataset()
    print("=" * 62)
    print(" 산포 요약과 공정능력지수 (교육용 가상 규격)")
    print("=" * 62)
    p = df["Pressure"]
    print(f"  압력  가상 규격 {P_LSL} ~ {P_USL} mTorr")
    print(
        f"  {pad('평균 / 표준편차', 18)}{p.mean():.3f} / {p.std():.3f}"
    )
    print(
        f"  {pad('Cp / Cpk', 18)}{cp(p, P_LSL, P_USL):.2f}"
        f" / {cpk(p, P_LSL, P_USL):.2f}"
    )
    print("-" * 62)
    print(f"  슬랙  가상 규격 하한 {SLACK_LSL} ns (상한 없음, Cpk만)")
    print(
        "  장비         평균  표준편차       5%     50%     95%    Cpk"
    )
    by_eq = slack_cpk_by(df, ["Equipment_ID"])
    groups = df.groupby("Equipment_ID", observed=True)
    for name, part in groups["Worst_Slack"]:
        s = spread(part)
        print(
            f"  {pad(str(name), 10)}{s['mean']:7.3f}  {s['std']:8.3f}"
            f"  {s['p05']:7.3f} {s['p50']:7.3f} {s['p95']:7.3f}"
            f"  {by_eq[name]:5.2f}"
        )
    below = int((df["Worst_Slack"] < SLACK_LSL).sum())
    fails = int((df["Pass_Fail"] == 0).sum())
    print(f"  하한 미만 {below}행 / Pass_Fail 불량 {fails}행")
    print("-" * 62)
    print("  로트별 슬랙 Cpk")
    print("  로트      ETCHER_A   ETCHER_B")
    table = slack_cpk_by(df, ["Lot_ID", "Equipment_ID"])
    table = table.unstack("Equipment_ID")
    for lot_id, row in table.iterrows():
        a = row["ETCHER_A"]
        a_text = "-" if pd.isna(a) else f"{a:.2f}"
        print(f"  {lot_id}  {a_text:>10} {row['ETCHER_B']:>10.2f}")
    print("-" * 62)
    print("  [확인 범위] 교육용 가상 규격으로 지수를 계산했다")
    print("  공정이 안정 상태인지는 확인하지 않았다")
    print("=" * 62)


if __name__ == "__main__":
    report()
