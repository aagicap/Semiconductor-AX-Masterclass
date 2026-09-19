"""
ch03_02_hardware_model.py
레코드를 로트 > 웨이퍼 > 다이 객체로 조립하고 계층을 점검한다.
"""

from dataclasses import FrozenInstanceError

from ax_hardware import Die, Wafer, build_lots
from ax_settings import LOG_DIR
from ax_sta import load_records
from ax_summary import group_by_lot, summarize
from ax_text import pad


def check_guards(wafer: Wafer, stranger: Die) -> list[str]:
    """객체가 막아 주어야 할 실수 세 가지를 실제로 일으켜 본다."""
    die = wafer.dies[0]
    results = []
    try:
        die.worst_slack = 0.0  # 분석 결과 덮어쓰기
        results.append("[FAIL] 다이 값이 바뀌었다")
    except FrozenInstanceError:
        results.append("[OK] 다이 값 변경 차단 (FrozenInstanceError)")
    try:
        _ = die.worst_slak  # 속성 이름 오타
        results.append("[FAIL] 없는 속성을 읽었다")
    except AttributeError:
        results.append("[OK] 없는 속성 즉시 오류 (AttributeError)")
    try:
        wafer.add(stranger)  # 다른 로트의 같은 번호 웨이퍼
        results.append("[FAIL] 다른 웨이퍼의 다이가 섞였다")
    except ValueError:
        results.append("[OK] 다른 로트 다이 혼입 차단 (ValueError)")
    return results


def report() -> None:
    """계층 규모, 로트별 요약 대조, 보호 장치를 출력한다."""
    print("=" * 62)
    print(" 하드웨어 계층 모델: 로트 > 웨이퍼 > 다이")
    print("=" * 62)

    records = load_records()
    if not records:
        print(f"  [FAIL] 리포트 파일이 없다 : {LOG_DIR}")
        print("         data/log_generator.py 를 먼저 실행한다.")
        print("=" * 62)
        return

    lots = build_lots(records)
    n_wafer = sum(len(lot.wafers) for lot in lots.values())
    n_die = sum(len(lot.dies) for lot in lots.values())
    print(
        f"  로트 {len(lots)}개 / 웨이퍼 {n_wafer}장 / 다이 {n_die:,}개"
    )
    print("-" * 62)
    print(
        f"  {pad('로트', 10)}{pad('웨이퍼', 8)}{pad('다이', 8)}"
        f"{pad('위험 웨이퍼', 13)}3.1절 대조"
    )
    print("-" * 62)

    groups = group_by_lot(records)
    matched = 0
    for lot_id, lot in sorted(lots.items()):
        summary = lot.summary()
        same = summary == summarize(groups[lot_id])
        matched += same
        print(
            f"  {pad(lot_id, 10)}{pad(str(len(lot.wafers)), 8)}"
            f"{pad(str(len(lot.dies)), 8)}"
            f"{pad(str(summary['risky_wafer_count']), 13)}"
            f"{'일치' if same else '불일치'}"
        )
    print("-" * 62)
    print(f"  3.1절 함수 결과와 일치한 로트 : {matched}/{len(lots)}")

    print("-" * 62)
    print("  [보호 장치 점검]")
    wafer = lots["LOT_00"].wafers["W_00"]
    stranger = lots["LOT_01"].wafers["W_00"].dies[0]
    for line in check_guards(wafer, stranger):
        print(f"  {line}")
    print("  [확인 범위] 세 가지 실수만 재현했다. 값의 유효성은 미점검")
    print("=" * 62)


if __name__ == "__main__":
    report()
