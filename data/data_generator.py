"""AlphaChip_V2 통합 데이터셋 생성 스크립트.

교재 『반도체 데이터 엔지니어링』의 모든 실습이 사용하는 5,000행 CSV를 생성한다.
난수 시드를 고정해 두었으므로 같은 실행 환경에서는 같은 데이터가 만들어진다.

실행: python data/data_generator.py
"""

from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

N_LOTS, WAFERS_PER_LOT, DIES_PER_WAFER = 10, 5, 100
GRID = 10  # 웨이퍼 1장의 다이 격자 (10 x 10 = 100)

# 스크립트 위치를 기준으로 저장하므로 어느 경로에서 실행해도 data/ 폴더에 생성된다
OUTPUT_PATH = (
    Path(__file__).resolve().parent / "alphachip_v2_integrated_data.csv"
)


def generate_master_semiconductor_data(n_samples=5000):
    np.random.seed(42)
    start_time = datetime(2026, 1, 1, 8, 0, 0)
    timestamps = [
        start_time + timedelta(minutes=5 * i) for i in range(n_samples)
    ]

    lot_ids, wafer_ids, die_x, die_y = [], [], [], []
    for i in range(n_samples):
        lot_ids.append(
            f"LOT_{str(i // (WAFERS_PER_LOT*DIES_PER_WAFER)).zfill(2)}"
        )
        wafer_ids.append(
            f"W_{str((i % (WAFERS_PER_LOT*DIES_PER_WAFER)) // DIES_PER_WAFER).zfill(2)}"
        )
        d = i % DIES_PER_WAFER
        die_x.append(d % GRID)
        die_y.append(d // GRID)

    n_wafers = n_samples // DIES_PER_WAFER
    wafer_equipment = np.random.choice(
        ["ETCHER_A", "ETCHER_B"], n_wafers
    )
    equipment_ids = np.repeat(wafer_equipment, DIES_PER_WAFER)
    path_ids = [
        f"PATH_{str(np.random.randint(1, 50)).zfill(4)}"
        for _ in range(n_samples)
    ]

    chamber_temp = np.zeros(n_samples)
    pressure = np.zeros(n_samples)
    gas_flow = np.zeros(n_samples)
    voltage = np.zeros(n_samples)
    operating_freq = np.zeros(n_samples)
    worst_slack = np.zeros(n_samples)
    leakage_power = np.zeros(n_samples)
    pass_fail = np.zeros(n_samples, dtype=int)
    error_codes = ["NORMAL"] * n_samples

    for i in range(n_samples):
        if equipment_ids[i] == "ETCHER_A":
            if np.random.rand() < 0.03:
                chamber_temp[i] = np.random.normal(79.0, 3.0)
                gas_flow[i] = np.random.normal(95.0, 2.0)
            else:
                chamber_temp[i] = np.random.normal(65.0, 2.0)
                gas_flow[i] = np.random.normal(100.0, 1.5)
        else:
            drift = (i / n_samples) * 20.0
            chamber_temp[i] = np.random.normal(65.0 + drift, 4.0)
            gas_flow[i] = np.random.normal(100.0 - (drift / 2), 5.0)

        pressure[i] = np.random.normal(15.0, 0.5)
        voltage[i] = np.random.uniform(0.7, 1.4)
        operating_freq[i] = voltage[i] * 2.5 + np.random.normal(0, 0.1)
        leakage_power[i] = (
            10.0
            + (chamber_temp[i] - 60) * 0.4
            + (voltage[i] * 5.0)
            + np.random.normal(0, 1.0)
        )
        worst_slack[i] = (
            0.15
            - (chamber_temp[i] - 65) * 0.01
            - (pressure[i] - 15) * 0.005
            + (voltage[i] - 1.0) * 0.1
            + np.random.normal(0, 0.01)
        )

        if worst_slack[i] < 0:
            pass_fail[i] = 0
            error_codes[i] = "ERR-T101"
        else:
            pass_fail[i] = 1
            if gas_flow[i] < 88.0:
                error_codes[i] = "ERR-G202"

    leakage_power = np.round(leakage_power, 2)
    miss_idx = np.random.choice(
        n_samples, size=int(n_samples * 0.025), replace=False
    )
    leakage_power[miss_idx] = np.nan

    df = pd.DataFrame(
        {
            "Timestamp": timestamps,
            "Lot_ID": lot_ids,
            "Wafer_ID": wafer_ids,
            "Die_X": die_x,
            "Die_Y": die_y,
            "Equipment_ID": equipment_ids,
            "Path_ID": path_ids,
            "Voltage": np.round(voltage, 2),
            "Chamber_Temp": np.round(chamber_temp, 2),
            "Pressure": np.round(pressure, 2),
            "Gas_Flow": np.round(gas_flow, 2),
            "Operating_Freq": np.round(operating_freq, 2),
            "Worst_Slack": np.round(worst_slack, 3),
            "Leakage_Power": leakage_power,
            "Pass_Fail": pass_fail,
            "Error_Code": error_codes,
        }
    )
    df.to_csv(OUTPUT_PATH, index=False)
    print(
        f"[Success] {n_samples}행의 AlphaChip_V2 통합 데이터셋이 생성되었습니다."
    )
    print(f"[저장 경로] {OUTPUT_PATH}\n")
    # 원인 단서(장비별·온도별 값)는 6장 전까지 출력하지 않는다.
    fail_rate = (df["Pass_Fail"] == 0).mean() * 100
    print(
        f"[요약] 컬럼 {df.shape[1]}개 / 로트 {df['Lot_ID'].nunique()}개"
    )
    print(f"[요약] 전체 불량률 {fail_rate:.2f}%")
    print(f"[요약] 결측 {int(df.isna().sum().sum())}건")
    return df


if __name__ == "__main__":
    generate_master_semiconductor_data()
