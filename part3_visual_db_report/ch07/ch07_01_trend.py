"""
ch07_01_trend.py  (7.1절)
장비별 챔버 온도와 가스 유량을 같은 시간축의 두 Axes에 그린다.
관측이 없는 날은 NaN으로 남겨 선이 그날을 건너뛰지 않게 한다.
실행 위치: 저장소 루트
"""

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from ax_frame import load_dataset
from ax_plot import (
    EQUIPMENT_COLORS,
    PAGE_WIDTH,
    configure_plot,
    save_figure,
)
from ax_settings import DATA_DIR
from ax_text import pad

FIG_PATH = DATA_DIR / "processed" / "figures" / "ch07_01_trend.png"
PANELS = [  # (열 이름, 세로축 이름)
    ("Chamber_Temp", "챔버 온도(℃)"),
    ("Gas_Flow", "가스 유량(sccm)"),
]


def daily_table(df: pd.DataFrame) -> pd.DataFrame:
    """장비별 일 평균과 관측 건수. 관측이 없는 날도 행으로 남긴다."""
    days = pd.date_range(
        df["Timestamp"].min().normalize(),
        df["Timestamp"].max().normalize(),
        freq="D",
    )
    parts = {}
    for name, part in df.groupby("Equipment_ID", observed=True):
        daily = part.resample("D", on="Timestamp").agg(
            temp=("Chamber_Temp", "mean"),
            gas=("Gas_Flow", "mean"),
            n=("Chamber_Temp", "size"),
        )
        daily = daily.reindex(days)  # 없는 날 = NaN
        daily["n"] = daily["n"].fillna(0).astype(int)
        parts[name] = daily
    return pd.concat(parts, axis=1)


def show_table(daily: pd.DataFrame) -> None:
    """날짜별 평균 온도와 관측 건수를 장비별로 출력한다."""
    print("  날짜     A 온도  A 건수   B 온도  B 건수")
    for day, row in daily.iterrows():
        cells = []
        for name in EQUIPMENT_COLORS:
            temp = row[(name, "temp")]
            text = "     -" if pd.isna(temp) else f"{temp:6.2f}"
            cells.append(f"{text}  {int(row[(name, 'n')]):>5}")
        print(f"  {day:%m-%d}  " + "   ".join(cells))
    for name in EQUIPMENT_COLORS:
        empty = daily.index[daily[(name, "n")] == 0]
        dates = ", ".join(f"{d:%m-%d}" for d in empty)
        print(f"  {pad(name, 10)} 관측 없는 날: {dates}")


def draw(df: pd.DataFrame, daily: pd.DataFrame) -> plt.Figure:
    """위는 온도, 아래는 유량. 두 Axes가 시간축을 공유한다."""
    fig, axes = plt.subplots(
        2, 1, figsize=(PAGE_WIDTH, 5.4), sharex=True
    )
    noon = daily.index + pd.Timedelta(hours=12)  # 하루의 가운데
    for ax, (col, label) in zip(axes, PANELS):
        key = "temp" if col == "Chamber_Temp" else "gas"
        for name, color in EQUIPMENT_COLORS.items():
            raw = df[df["Equipment_ID"] == name]
            ax.scatter(
                raw["Timestamp"],
                raw[col],
                s=3,
                color=color,
                alpha=0.15,
                linewidths=0,
            )
            ax.plot(
                noon,
                daily[(name, key)],
                color=color,
                marker="o",
                markersize=3.5,
                linewidth=1.8,
                label=f"{name} 일 평균",
            )
        ax.set_ylabel(label)
        ax.grid(axis="y", alpha=0.3)
    axes[0].legend(loc="upper left", frameon=False)
    axes[1].xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    axes[1].set_xlabel("날짜(2026년 1월)")
    fig.tight_layout()
    return fig


def report() -> None:
    """일별 표를 출력하고 트렌드 그림을 저장한다."""
    font = configure_plot()
    df = load_dataset()
    daily = daily_table(df)
    print("=" * 50)
    print(" 장비별 일 평균 챔버 온도(℃)와 관측 건수")
    print("=" * 50)
    show_table(daily)
    print("-" * 50)
    path = save_figure(draw(df, daily), FIG_PATH)
    print(f"  글꼴: {font}")
    print(f"  그림 저장: {path.as_posix()}")
    print("  [확인 범위] 장비·날짜별 평균과 건수만 집계했다")
    print("  관측 없는 날의 값은 채우지 않았다")
    print("=" * 50)


if __name__ == "__main__":
    report()
