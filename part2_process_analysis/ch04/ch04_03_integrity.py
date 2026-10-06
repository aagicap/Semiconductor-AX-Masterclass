"""
ch04_03_integrity.py
통합 표의 무결성을 점검하고, 결측을 다루는 방식을 비교한다.
실행 위치: 저장소 루트
"""

import numpy as np
import pandas as pd

from ax_frame import check_integrity, load_dataset
from ax_text import pad

TARGET = "Leakage_Power"  # 결측이 있는 유일한 열
SEED = 42  # 가림 검증의 난수 시드


def show_integrity(frame: pd.DataFrame) -> None:
    """점검 결과를 층위별로 출력한다."""
    print(f"  {pad('층위', 6)}{pad('점검 항목', 32)}어긋남")
    for layer, item, count in check_integrity(frame):
        mark = "[OK]" if count == 0 else "[확인]"
        print(f"  {pad(layer, 6)}{pad(item, 32)}{count:>4}  {mark}")


def show_slack_zero(frame: pd.DataFrame) -> None:
    """판정과 슬랙 부호가 어긋난 행의 표시값을 확인한다."""
    failed = frame["Pass_Fail"] == 0
    odd = frame[failed != (frame["Worst_Slack"] < 0)]
    slack = pd.Series(odd["Worst_Slack"])
    negative_zero = int(np.signbit(slack[slack == 0]).sum())
    fails = int((odd["Pass_Fail"] == 0).sum())
    print(f"  불일치 행 : {len(odd)}행 (그중 불량 판정 {fails}행)")
    print(f"  슬랙 표시값이 -0.0인 행 : {negative_zero}행")
    print("  판정 라벨은 고치지 않는다 (반올림 전 슬랙으로 판정)")


def rmse(guess: pd.Series, truth: pd.Series) -> float:
    """두 열의 평균 제곱근 오차."""
    return float(np.sqrt(((guess - truth) ** 2).mean()))


def mask_test(series: pd.Series, seed: int) -> dict[str, float]:
    """관측값을 결측 수만큼 가리고, 방식별로 채운 값의 오차를 잰다."""
    rng = np.random.default_rng(seed)
    size = int(series.isna().sum())
    hidden = rng.choice(series.dropna().index, size=size, replace=False)
    masked = series.copy()
    masked.loc[hidden] = np.nan
    filled = {
        "중앙값 대체": masked.fillna(masked.median()),
        "앞 값 채우기": masked.ffill(),
        "선형 보간": masked.interpolate(),
    }
    truth = series.loc[hidden]
    return {k: rmse(f.loc[hidden], truth) for k, f in filled.items()}


def show_missing(frame: pd.DataFrame) -> None:
    """결측 처리 방식이 결과에 주는 영향을 비교한다."""
    leak = pd.Series(frame[TARGET])
    lost = int(leak.isna().sum())
    kept = frame.dropna()
    fail_all = (frame["Pass_Fail"] == 0).mean() * 100
    fail_kept = (kept["Pass_Fail"] == 0).mean() * 100
    std_fill = leak.fillna(leak.median()).std()
    label = f"불량률(dropna {len(kept):,}행)"
    print(f"  {TARGET} 결측 : {lost}행")
    print(f"  {pad('불량률(원본 5,000행)', 28)}{fail_all:.2f}%")
    print(f"  {pad(label, 28)}{fail_kept:.2f}%")
    print(f"  {pad('표준편차(결측 제외)', 28)}{leak.std():.3f} mW")
    print(f"  {pad('표준편차(중앙값 대체)', 28)}{std_fill:.3f} mW")
    print("-" * 62)
    print(f"  가림 검증 : 관측값 {lost}개를 가리고 복원 (시드 {SEED})")
    errors = mask_test(leak, SEED)
    # 같은 값을 행 순서만 섞어 다시 보간한다
    mixed = leak.sample(frac=1, random_state=SEED)
    mixed = mixed.reset_index(drop=True)
    mixed_error = mask_test(mixed, SEED)["선형 보간"]
    errors["선형 보간(행 순서 섞음)"] = mixed_error
    print(f"  {pad('방식', 28)}오차(RMSE)")
    for name, error in errors.items():
        print(f"  {pad(name, 28)}{error:.2f} mW")


def mark_missing(frame: pd.DataFrame) -> pd.DataFrame:
    """원본은 두고, 결측 위치를 표시한 열을 더한 사본을 돌려준다."""
    out = frame.copy()
    out[f"{TARGET}_Missing"] = out[TARGET].isna()
    return out


def report() -> None:
    """무결성 점검, 불일치 확인, 결측 처리 비교를 출력한다."""
    df = load_dataset()
    print("=" * 62)
    print(" 무결성 점검과 결측 처리")
    print("=" * 62)
    show_integrity(df)
    print("-" * 62)
    show_slack_zero(df)
    print("-" * 62)
    show_missing(df)
    print("-" * 62)
    marked = mark_missing(df)
    count = int(pd.Series(marked[f"{TARGET}_Missing"]).sum())
    print(f"  {pad('표시 열을 더한 사본', 28)}{marked.shape[1]}열")
    print(f"  {pad('원본(바꾸지 않음)', 28)}{df.shape[1]}열")
    print(f"  {pad('표시된 행', 28)}{count}행")
    print("  [확인 범위] 기록 형식·키·관계만 점검했다")
    print("  센서값이 정상 범위인지는 5장에서 판단한다")
    print("=" * 62)


if __name__ == "__main__":
    report()
