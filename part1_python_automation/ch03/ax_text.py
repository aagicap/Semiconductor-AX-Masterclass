"""
ax_text.py
터미널 출력용 문자열 도구. 1장과 2장에서 반복한 함수를 모았다.
"""

import unicodedata

WIDE = ("W", "F")


def display_width(text: str) -> int:
    """한글은 폭 2, 영문은 폭 1로 센 표시 폭을 돌려준다."""
    return sum(
        2 if unicodedata.east_asian_width(ch) in WIDE else 1
        for ch in text
    )


def pad(text: str, width: int) -> str:
    """표시 폭 기준으로 오른쪽을 공백으로 채운다."""
    return text + " " * max(0, width - display_width(text))
