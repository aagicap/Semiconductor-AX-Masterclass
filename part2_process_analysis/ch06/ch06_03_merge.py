"""
ch06_03_merge.py
3.3절 파싱 엔진의 설계 레코드(JSON)와 통합 CSV의 제조 관측·결과 열을
제조 식별자로 병합하고, 병합이 맞게 되었는지 확인한다.
실행 위치: 저장소 루트
"""

import json

import pandas as pd
from pandas.errors import MergeError

from ax_frame import KEY_COLUMNS, load_dataset
from ax_settings import DATA_DIR, REPO_ROOT
from ax_text import pad

DESIGN_DIR = DATA_DIR / "parsed_engine"  # 3.3절 산출물
OUT_PATH = DATA_DIR / "processed" / "design_process.csv"

# JSON 속성 이름 → 통합 CSV 열 이름
RENAME = {
    "lot_id": "Lot_ID",
    "wafer_id": "Wafer_ID",
    "die_x": "Die_X",
    "die_y": "Die_Y",
    "path_id": "Path_ID",
    "worst_slack": "Worst_Slack",
    "leakage_power": "Leakage_Power",
    "operating_freq": "Operating_Freq",
    "alarm": "Alarm",
}
# 제조 관측·결과 열. Voltage는 설계 리포트에 없어 여기서 다루지 않는다
PROCESS_COLUMNS = [
    "Timestamp",
    "Equipment_ID",
    "Chamber_Temp",
    "Pressure",
    "Gas_Flow",
    "Pass_Fail",
    "Error_Code",
]
DESIGN_VALUES = ["Worst_Slack", "Leakage_Power", "Operating_Freq"]
# 현재 log_generator.py가 쓰는 경고 문자열(ERR-G202에 대응)
KNOWN_ALARMS = {"GAS_FLOW_WARN"}


def load_design() -> pd.DataFrame:
    """로트별 JSON 자산의 레코드를 하나의 표로 모은다."""
    files = sorted(DESIGN_DIR.glob("lot_*.json"))
    if not files:
        raise FileNotFoundError(f"설계 자산이 없다 : {DESIGN_DIR}")
    records = []
    for path in files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        records.extend(payload["records"])
    return pd.DataFrame(records).rename(columns=RENAME)


def unknown_alarms(design: pd.DataFrame) -> list[str]:
    """현재 생성기가 쓰지 않는 경고 문자열을 찾는다.
    있으면 설계 자산이 예전 리포트로 만들어진 것이다."""
    found = set(design["Alarm"].dropna().unique())
    return sorted(found - KNOWN_ALARMS)


def has_stale_alarms(design: pd.DataFrame) -> bool:
    """예전 경고 문자열이 있으면 다시 만드는 순서를 출력한다."""
    stale = unknown_alarms(design)
    if not stale:
        return False
    names = ", ".join(stale)
    print(f"  [FAIL] 예전 경고 문자열이 남아 있다 : {names}")
    print("         리포트와 설계 자산을 다시 만든다(저장소 루트).")
    for step in (
        "data/log_generator.py",
        "part1_python_automation/ch03/ch03_03_make_v5_logs.py",
        "part1_python_automation/ch03/ch03_03_parsing_engine.py",
    ):
        print(f"         python {step}")
    print("=" * 62)
    return True


def merge_design_process(
    design: pd.DataFrame, process: pd.DataFrame
) -> pd.DataFrame:
    """제조 식별자로 1:1 병합한다. 짝이 없는 행도 남겨 표시한다."""
    return design.merge(
        process,
        on=KEY_COLUMNS,
        how="outer",
        validate="one_to_one",
        indicator=True,
    )


def wrong_key_rows(frame: pd.DataFrame, key: list[str]) -> int:
    """자기 자신과 key로 병합할 때 생기는 행 수를 계산한다."""
    counts = frame.groupby(key, observed=True).size()
    return int((counts**2).sum())


def count_mismatch(
    merged: pd.DataFrame, csv: pd.DataFrame
) -> dict[str, int]:
    """병합한 설계 값이 통합 CSV의 같은 열과 다른 행 수를 센다.
    양쪽이 모두 결측이면 같은 것으로 본다."""
    base = merged.merge(csv, on=KEY_COLUMNS, suffixes=("", "_csv"))
    result = {}
    for col in DESIGN_VALUES:
        same = base[col].eq(base[f"{col}_csv"])
        both_na = base[col].isna() & base[f"{col}_csv"].isna()
        result[col] = int((~(same | both_na)).sum())
    warn = base["Alarm"].eq("GAS_FLOW_WARN")
    g202 = base["Error_Code"].eq("ERR-G202")
    result["경고 대응"] = int((warn != g202).sum())
    return result


def show_wrong_keys(
    csv: pd.DataFrame, design: pd.DataFrame, process: pd.DataFrame
) -> None:
    """키를 잘못 고르면 행이 얼마나 불어나는지, validate가
    어떻게 막는지 보여 준다."""
    print("  [잘못된 키] 같은 표를 병합하면 생기는 행 수")
    for key in (["Wafer_ID"], ["Lot_ID", "Wafer_ID"], ["Path_ID"]):
        rows = wrong_key_rows(csv, key)
        print(f"  {pad(' + '.join(key), 20)}{rows:>10,}행")
    try:
        design.merge(
            process, on=["Lot_ID", "Wafer_ID"], validate="one_to_one"
        )
    except MergeError as error:
        print("  validate가 웨이퍼 키 병합을 멈춤: MergeError")
        head = str(error).splitlines()[0]  # 중복 행 목록은 뺀다
        for part in head.split("; "):
            print(f"    {part}")


def report() -> None:
    """병합 결과와 검증 항목을 출력한다."""
    print("=" * 62)
    print(" 설계 레코드(JSON) + 제조 관측·결과(CSV) 병합")
    print("=" * 62)
    try:
        design = load_design()
    except FileNotFoundError as error:
        print(f"  [FAIL] {error}")
        print(
            "         3.3절 ch03_03_parsing_engine.py 를 먼저 실행한다."
        )
        print("=" * 62)
        return
    if has_stale_alarms(design):
        return
    csv = load_dataset()
    process = csv[KEY_COLUMNS + PROCESS_COLUMNS]
    for name, part in (
        ("설계 레코드", design),
        ("제조 관측·결과", process),
    ):
        rows, cols = part.shape
        print(f"  {pad(name, 16)}{rows:>6}행 {cols:>3}열")

    for name, part in (("설계", design), ("제조", process)):
        dup = int(part.duplicated(KEY_COLUMNS).sum())
        print(f"  {pad(name + ' 복합 키 중복', 16)}{dup:>6}행")
    merged = merge_design_process(design, process)
    sides = merged["_merge"].value_counts()
    print(
        f"  {pad('병합 결과', 16)}{len(merged):>6}행"
        f" {merged.shape[1] - 1:>3}열"
    )
    print(
        f"  {pad('짝 확인', 16)}양쪽 {sides['both']}"
        f" / 설계만 {sides['left_only']} / 제조만 {sides['right_only']}"
    )
    print("-" * 62)
    print("  [대조] 병합한 설계 값과 통합 CSV의 같은 열")
    for item, count in count_mismatch(merged, csv).items():
        print(f"  {pad(item, 16)}불일치 {count}행")
    print("-" * 62)
    show_wrong_keys(csv, design, process)
    print("-" * 62)
    OUT_PATH.parent.mkdir(exist_ok=True)
    merged.drop(columns="_merge").to_csv(OUT_PATH, index=False)
    print(f"  저장 경로 : {OUT_PATH.relative_to(REPO_ROOT)}")
    print("  [확인 범위] 키의 짝과 값의 일치만 확인했다")
    print("  설계 값과 공정 값의 관계는 판단하지 않았다")
    print("=" * 62)


if __name__ == "__main__":
    report()
