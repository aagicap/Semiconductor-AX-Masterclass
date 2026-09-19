"""
ax_settings.py
3장 이후 실습이 함께 쓰는 경로와 기준값을 한곳에 모은다.
"""

from pathlib import Path

# 이 파일의 위치에서 저장소 루트를 계산한다.
# ch03 → part1_python_automation → 저장소 루트
REPO_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = REPO_ROOT / "data"
LOG_DIR = DATA_DIR / "logs"
PARSED_DIR = DATA_DIR / "parsed"
PATTERN = "sta_*.log"

THRESHOLD = 0.05  # 교육용 관찰 기준. 실제 규격이 아니다.
