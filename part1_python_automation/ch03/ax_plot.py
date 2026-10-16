"""
ax_plot.py
7장 이후 그래프가 함께 쓰는 한글 글꼴 설정과 그림 저장 함수.
불러오기만 해서는 아무 설정도 바꾸지 않는다.
configure_plot()을 호출해야 설정이 적용된다.
"""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.figure import Figure

from ax_settings import REPO_ROOT

# 윈도우 → macOS → 리눅스 순으로 찾는다
FONT_CANDIDATES = [
    "Malgun Gothic",
    "AppleGothic",
    "NanumGothic",
    "Noto Sans CJK KR",
]
# 지면 본문 폭(약 14.8cm)에 맞춘 그림 가로 길이(인치)
PAGE_WIDTH = 7.5
# 장비 색. 같은 장비는 모든 그림에서 같은 색으로 그린다
EQUIPMENT_COLORS = {"ETCHER_A": "#2F6BDB", "ETCHER_B": "#D6457A"}


def find_korean_font() -> str | None:
    """설치된 글꼴 가운데 첫 번째 한글 글꼴 이름을 돌려준다."""
    installed = {f.name for f in font_manager.fontManager.ttflist}
    for name in FONT_CANDIDATES:
        if name in installed:
            return name
    return None


def configure_plot() -> str:
    """한글 글꼴과 음수 부호를 설정하고 글꼴 이름을 돌려준다."""
    name = find_korean_font()
    if name is None:
        raise RuntimeError(
            "한글 글꼴을 찾지 못했다. 다음 중 하나를 설치한다: "
            + ", ".join(FONT_CANDIDATES)
        )
    plt.rcParams["font.family"] = name
    plt.rcParams["font.size"] = 11  # 본문 폭으로 줄여도 8pt 이상
    plt.rcParams["axes.unicode_minus"] = False  # 마이너스 깨짐 방지
    return name


def save_figure(fig: Figure, path: Path, dpi: int = 300) -> Path:
    """그림을 저장하고 저장소 루트 기준 상대 경로를 돌려준다."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return path.relative_to(REPO_ROOT)
