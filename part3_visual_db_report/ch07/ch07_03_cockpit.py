"""
ch07_03_cockpit.py  (7.3절)
GridSpec으로 설계·공정 지표 다섯 패널을 한 장의 콕핏에 배치한다.
7.1절과 7.2절의 집계 함수를 불러와 다시 쓴다.
실행 위치: 저장소 루트
"""

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.axes import Axes
from matplotlib.gridspec import GridSpec

from ax_frame import load_dataset
from ax_plot import (
    EQUIPMENT_COLORS,
    PAGE_WIDTH,
    configure_plot,
    save_figure,
)
from ax_settings import DATA_DIR
from ax_stats import fail_rate
from ax_text import pad
from ch07_01_trend import daily_table
from ch07_02_distribution import slack_grid

FIG_PATH = DATA_DIR / "processed" / "figures" / "ch07_03_cockpit.png"
WAFER_KEY = ["Lot_ID", "Wafer_ID"]


def kpi_items(df: pd.DataFrame) -> list[str]:
    """콕핏 맨 위의 상태 요약. 원인 판정 없이 관측 수치만 담는다."""
    items = [f"전체 불량률 {fail_rate(df['Pass_Fail']):.2f}%"]
    for name, part in df.groupby("Equipment_ID", observed=True):
        wafers = len(part[WAFER_KEY].drop_duplicates())
        rate = fail_rate(part["Pass_Fail"])
        items.append(f"{name} {rate:.2f}% (웨이퍼 {wafers}장)")
    return items


def die_map(df: pd.DataFrame) -> pd.DataFrame:
    """다이 좌표별 불량률(%). 50웨이퍼를 같은 좌표끼리 누적한다."""
    rate = df.groupby(["Die_Y", "Die_X"])["Pass_Fail"].agg(fail_rate)
    return rate.unstack("Die_X")


def map_spread(df: pd.DataFrame) -> tuple[float, float]:
    """좌표별 불량률의 표준편차와, 위치 차이가 없을 때의 기댓값(%p)."""
    p = df.groupby(WAFER_KEY, observed=True)["Pass_Fail"].agg(fail_rate)
    p = p / 100
    expected = np.sqrt((p * (1 - p)).sum()) / len(p) * 100
    return float(die_map(df).stack().std(ddof=0)), float(expected)


def panel_trend(ax: Axes, df: pd.DataFrame) -> None:
    """① 7.1절의 daily_table()로 장비별 일 평균 온도를 그린다."""
    daily = daily_table(df)
    noon = daily.index + pd.Timedelta(hours=12)
    for name, color in EQUIPMENT_COLORS.items():
        ax.plot(
            noon,
            daily[(name, "temp")],
            color=color,
            marker="o",
            markersize=3,
            label=name,
        )
    ax.set_title("① 장비별 일 평균 챔버 온도(℃)")
    ax.legend(loc="upper left", frameon=False)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))


def panel_lots(ax: Axes, df: pd.DataFrame) -> None:
    """② 로트와 장비의 조합별 불량률. 없는 조합은 막대가 없다."""
    lots = df.groupby(["Lot_ID", "Equipment_ID"], observed=True)
    rates = lots["Pass_Fail"].agg(fail_rate).unstack()
    rates.plot.bar(
        ax=ax, color=EQUIPMENT_COLORS, width=0.8, legend=False
    )
    ax.set_title("② 로트(00~09)·장비별 불량률(%)")
    ax.set_xlabel("")
    ax.set_xticklabels([s[-2:] for s in rates.index], rotation=0)


def panel_heat(ax: Axes, df: pd.DataFrame) -> None:
    """③ 7.2절의 slack_grid()로 구간별 평균 슬랙을 그린다."""
    mean, _ = slack_grid(df)
    sns.heatmap(
        mean.iloc[::-1],
        cmap="RdBu",
        center=0,
        ax=ax,
        cbar_kws={"label": "ns"},
    )
    ax.set_title("③ 평균 슬랙: 전압(V) x 온도(℃)")
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.tick_params(axis="x", rotation=0, labelsize=9)
    ax.tick_params(axis="y", labelsize=9)


def panel_map(ax: Axes, df: pd.DataFrame) -> None:
    """④ 50웨이퍼를 같은 좌표끼리 누적한 다이 좌표별 불량률."""
    sns.heatmap(
        die_map(df),
        cmap="Reds",
        vmin=0,
        square=True,
        ax=ax,
        cbar_kws={"label": "%"},
    )
    ax.set_title("④ 50웨이퍼 누적 다이 좌표별 불량률")
    ax.tick_params(axis="y", rotation=0)


def panel_hist(ax: Axes, df: pd.DataFrame) -> None:
    """⑤ 장비별 Worst_Slack 분포와 슬랙 0 기준선."""
    for name, color in EQUIPMENT_COLORS.items():
        part = df.loc[df["Equipment_ID"] == name, "Worst_Slack"]
        ax.hist(part, bins=30, color=color, alpha=0.5, label=name)
    ax.axvline(0, color="#333333", linestyle="--", linewidth=1)
    ax.set_title("⑤ 장비별 Worst_Slack 분포(ns)")
    ax.set_ylabel("다이 수")


def draw(df: pd.DataFrame) -> plt.Figure:
    """4행 2열 격자. 맨 위는 요약 띠, 둘째 행은 두 칸을 합친다."""
    fig = plt.figure(figsize=(PAGE_WIDTH, 9.8))
    gs = GridSpec(
        4,
        2,
        figure=fig,
        height_ratios=[0.06, 1, 1.1, 1.1],
        width_ratios=[1, 1.2],
        hspace=0.5,
        wspace=0.4,
    )
    ax_kpi = fig.add_subplot(gs[0, :])
    ax_kpi.axis("off")
    ax_kpi.text(
        0.5,
        0.5,
        "   |   ".join(kpi_items(df)),
        ha="center",
        va="center",
        fontsize=10,
        bbox={"boxstyle": "round", "fc": "#F3F5FB", "ec": "#C9D1E8"},
    )
    panel_trend(fig.add_subplot(gs[1, :]), df)
    panel_lots(fig.add_subplot(gs[2, 0]), df)
    panel_heat(fig.add_subplot(gs[2, 1]), df)
    panel_map(fig.add_subplot(gs[3, 0]), df)
    panel_hist(fig.add_subplot(gs[3, 1]), df)
    return fig


def report() -> None:
    """상태 요약과 좌표 맵의 흩어짐을 출력하고 콕핏을 저장한다."""
    configure_plot()
    df = load_dataset()
    spread, expected = map_spread(df)
    rates = die_map(df).stack()
    print("=" * 60)
    print(" 설계·공정 통합 엔지니어링 콕핏")
    print("=" * 60)
    print("  [1] 상태 요약")
    for item in kpi_items(df):
        print(f"      {item}")
    print("-" * 60)
    print("  [2] 50웨이퍼 누적 다이 좌표별 불량률(%)")
    print(
        f"      좌표 {rates.size}개  최소 {rates.min():.1f}"
        f"  최대 {rates.max():.1f}"
    )
    print(f"      {pad('좌표 사이 표준편차', 28)}{spread:.2f}%p")
    print(
        f"      {pad('위치 차이가 없을 때 기댓값', 28)}{expected:.2f}%p"
    )
    print("-" * 60)
    path = save_figure(draw(df), FIG_PATH)
    print(f"  그림 저장: {path.as_posix()}")
    print("  [확인 범위] 패널마다 집계값을 그렸다")
    print("  위치 효과가 없다는 검정은 하지 않았다")
    print("=" * 60)


if __name__ == "__main__":
    report()
