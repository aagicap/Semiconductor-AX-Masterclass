"""
ch05_03_zscore.py
압력의 Z-Score로 이상치를 표시하고, Z-Score가 잘 맞지 않는 경우를 본다.
실행 위치: 저장소 루트
"""

import pandas as pd

from ax_frame import load_dataset
from ax_text import pad

LOW, HIGH = 13.5, 16.5  # 5.1절의 교육용 관리 한계

Z_LIMIT = 3.0  # 평균에서 표준편차의 몇 배 떨어지면 표시할지


def zscore(series: pd.Series) -> pd.Series:
    """평균에서 표준편차의 몇 배 떨어졌는지 계산한다."""
    return (series - series.mean()) / series.std()


def sigma_share(series: pd.Series) -> list[float]:
    """±1σ, ±2σ, ±3σ 안에 든 값의 비율(%)을 돌려준다."""
    z = zscore(series).abs()
    return [float((z <= k).mean() * 100) for k in (1, 2, 3)]


def mark_outliers(frame: pd.DataFrame, column: str) -> pd.DataFrame:
    """원본은 두고, Z-Score와 이상치 표시 열을 더한 사본을 돌려준다."""
    work = frame.copy()
    work[f"{column}_Z"] = zscore(work[column])
    work[f"{column}_Outlier"] = work[f"{column}_Z"].abs() > Z_LIMIT
    return work


def report() -> None:
    """압력의 Z-Score 결과와 온도의 한계 사례를 출력한다."""
    df = load_dataset()
    print("=" * 62)
    print(" Z-Score 이상치 표시: 압력, 그리고 잘 맞지 않는 경우")
    print("=" * 62)
    marked = mark_outliers(df, "Pressure")
    flags = marked["Pressure_Outlier"]
    p = df["Pressure"]
    print(f"  압력 평균 {p.mean():.3f} / 표준편차 {p.std():.3f} mTorr")
    print(f"  |Z| > {Z_LIMIT:.0f} 표시 : {int(flags.sum())}행")
    low = marked.loc[flags & (p < p.mean()), "Pressure"]
    high = marked.loc[flags & (p > p.mean()), "Pressure"]
    print(f"  낮은 쪽 {len(low)}행 : {low.min():.2f} ~ {low.max():.2f}")
    print(f"  높은 쪽 {len(high)}행 : {high.min():.2f} ~ {high.max():.2f}")
    limit_out = ~p.between(LOW, HIGH)
    print(f"  5.1절 한계 밖 {int(limit_out.sum())}행 중"
          f" Z-Score로도 표시 {int((limit_out & flags).sum())}행")
    share = sigma_share(p)
    print(f"  ±1σ / ±2σ / ±3σ 안 : "
          f"{share[0]:.1f}% / {share[1]:.1f}% / {share[2]:.1f}%")
    print("-" * 62)
    t = df["Chamber_Temp"]
    tz = zscore(t).abs() > Z_LIMIT
    half = len(df) // 2
    t_share = sigma_share(t)
    print("  [비교] 챔버 온도에 같은 방법을 적용하면")
    mean, median = t.mean(), t.median()
    print(f"  {pad('평균 / 중앙값', 20)}{mean:.2f} / {median:.2f} ℃")
    print(f"  {pad('1표준편차 이내', 20)}{t_share[0]:.1f}%")
    print(f"  {pad('|Z| > 3 표시', 20)}{int(tz.sum())}행"
          f" (앞 절반 {int(tz.iloc[:half].sum())}"
          f", 뒤 절반 {int(tz.iloc[half:].sum())})")
    print("-" * 62)
    print(f"  표시 열을 더한 사본 {marked.shape[1]}열"
          f" / 원본 {df.shape[1]}열")
    print("  [확인 범위] 값의 통계적 거리만 계산했다")
    print("  표시된 값이 공정 이상인지는 판단하지 않았다")
    print("=" * 62)


if __name__ == "__main__":
    report()
