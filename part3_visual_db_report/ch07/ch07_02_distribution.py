"""
ch07_02_distribution.py  (7.2절)
① 장비별 웨이퍼 수율 분포를 바이올린 플롯으로 그린다.
② 공급 전압 x 챔버 온도 구간별 평균 슬랙을 히트맵으로 그린다.
실행 위치: 저장소 루트
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

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

FIG_DIR = DATA_DIR / "processed" / "figures"
WAFER_KEY = ["Lot_ID", "Wafer_ID"]
# 시각화용 구간. 결과를 보기 전에 정했고 규격·관리 한계가 아니다
VOLT_BINS = [-np.inf, 0.84, 0.98, 1.12, 1.26, np.inf]
VOLT_LABELS = ["~0.84", "0.84~0.98", "0.98~1.12", "1.12~1.26", "1.26~"]
TEMP_BINS = [-np.inf, 70, 75, 80, 85, np.inf]
TEMP_LABELS = ["~70", "70~75", "75~80", "80~85", "85~"]


def wafer_yield(df: pd.DataFrame) -> pd.DataFrame:
    """웨이퍼마다 장비와 수율(%)을 구한다."""
    table = df.groupby(WAFER_KEY, observed=True).agg(
        equipment=("Equipment_ID", "first"),
        fail=("Pass_Fail", fail_rate),
    )
    table["yield_pct"] = 100 - table["fail"]
    return table.reset_index()


def slack_grid(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """전압 x 온도 구간별 평균 슬랙과 다이 수를 함께 돌려준다."""
    volt = pd.cut(df["Voltage"], VOLT_BINS, labels=VOLT_LABELS)
    temp = pd.cut(df["Chamber_Temp"], TEMP_BINS, labels=TEMP_LABELS)
    grouped = df.groupby([volt, temp], observed=False)["Worst_Slack"]
    mean = grouped.mean().unstack()
    count = grouped.size().unstack()
    return mean, count


def draw_violin(wafers: pd.DataFrame) -> plt.Figure:
    """장비별 웨이퍼 수율 분포. 꼬리는 실제 범위에서 자른다."""
    fig, ax = plt.subplots(figsize=(PAGE_WIDTH, 4.2))
    order = list(EQUIPMENT_COLORS)
    sns.violinplot(
        data=wafers,
        x="equipment",
        y="yield_pct",
        order=order,
        hue="equipment",
        palette=EQUIPMENT_COLORS,
        legend=False,
        cut=0,
        dodge=False,
        inner=None,
        density_norm="width",
        alpha=0.35,
        ax=ax,
    )
    sns.stripplot(
        data=wafers,
        x="equipment",
        y="yield_pct",
        order=order,
        hue="equipment",
        palette=EQUIPMENT_COLORS,
        legend=False,
        size=4,
        jitter=0.12,
        dodge=False,
        ax=ax,
    )
    medians = wafers.groupby("equipment")["yield_pct"].median()
    for i, name in enumerate(order):
        ax.hlines(
            medians[name],
            i - 0.25,
            i + 0.25,
            color="#333333",
            linewidth=2,
        )
    counts = wafers["equipment"].value_counts()
    ax.set_xticks(range(len(order)))
    ax.set_xticklabels([f"{n}\n(웨이퍼 {counts[n]}장)" for n in order])
    ax.set_xlabel("")
    ax.set_ylabel("웨이퍼 수율(%)")
    ax.set_ylim(0, 102)  # 0~100%를 모두 보여 차이를 과장하지 않는다
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    return fig


def draw_heatmap(mean: pd.DataFrame) -> plt.Figure:
    """구간별 평균 슬랙. 0을 가운데 색으로 두어 부호가 보이게 한다."""
    fig, ax = plt.subplots(figsize=(PAGE_WIDTH, 4.6))
    sns.heatmap(
        mean.iloc[::-1],
        annot=True,
        fmt=".3f",
        cmap="RdBu",
        center=0,
        linewidths=1,
        linecolor="white",
        cbar_kws={"label": "평균 Worst_Slack(ns)"},
        ax=ax,
    )
    ax.set_xlabel("챔버 온도 구간(℃)")
    ax.set_ylabel("공급 전압 구간(V)")
    ax.tick_params(axis="y", rotation=0)
    fig.tight_layout()
    return fig


def show_wafers(wafers: pd.DataFrame) -> None:
    """[1] 장비별 웨이퍼 수율 요약을 출력한다."""
    print("  [1] 장비별 웨이퍼 수율(%)")
    print("  장비        웨이퍼   최소   중앙값   최대")
    for name in EQUIPMENT_COLORS:
        y = wafers.loc[wafers["equipment"] == name, "yield_pct"]
        print(
            f"  {pad(name, 12)}{len(y):>4}장 {y.min():6.1f}"
            f"  {y.median():7.1f} {y.max():6.1f}"
        )


def show_grid(title: str, table: pd.DataFrame, fmt: str) -> None:
    """[2][3] 전압(행) x 온도(열) 표를 출력한다."""
    print(title)
    head = "".join(f"{c:>9}" for c in table.columns)
    print(f"  {pad('전압(V)', 12)}" + head)
    for volt, row in table.iterrows():
        cells = "".join(f"{v:>9{fmt}}" for v in row)
        print(f"  {str(volt):<12}" + cells)


def report() -> None:
    """수율 분포와 구간별 슬랙을 출력하고 그림 두 장을 저장한다."""
    configure_plot()
    df = load_dataset()
    wafers = wafer_yield(df)
    mean, count = slack_grid(df)
    print("=" * 60)
    print(" 웨이퍼 수율 분포와 전압 x 온도 구간별 평균 슬랙")
    print("=" * 60)
    show_wafers(wafers)
    print("-" * 60)
    show_grid("  [2] 구간별 평균 Worst_Slack(ns)", mean, ".3f")
    print("-" * 60)
    show_grid("  [3] 구간별 다이 수", count, "d")
    print(f"  가장 적은 칸 {int(count.min().min())}개 다이")
    print("-" * 60)
    for name, fig in (
        ("ch07_02_violin.png", draw_violin(wafers)),
        ("ch07_02_heatmap.png", draw_heatmap(mean)),
    ):
        path = save_figure(fig, FIG_DIR / name)
        print(f"  그림 저장: {path.as_posix()}")
    print("  [확인 범위] 구간별 평균과 다이 수만 집계했다")
    print("  구간 경계는 시각화용이며 규격이 아니다")
    print("=" * 60)


if __name__ == "__main__":
    report()
