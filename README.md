# 반도체 데이터 엔지니어링 — 반도체 설계·공정 AX 마스터 클래스

**파이썬을 활용한 반도체 데이터 분석과 업무 자동화**

이 저장소는 도서 『반도체 데이터 엔지니어링(가제)』(한빛아카데미)의 공식 실습 코드와 통합 데이터셋을 제공합니다. 교재의 목차와 폴더 구조가 1:1로 대응하므로, 학습 중인 절의 코드를 바로 찾아 실행할 수 있습니다.

---

## AlphaChip_V2 프로젝트 세계관

이 책의 모든 코드는 하나의 시나리오로 이어집니다.

> 완전 자율주행 차량용 NPU **AlphaChip_V2**(3나노 EUV 공정)를 양산하던 중 원인 미상의 수율 급락이 발생했습니다. 교차 분석 결과, 식각 장비 **ETCHER_B**의 노후화로 반응 가스 유량이 흔들리며 챔버 온도가 상승하는 드리프트가 감지되었습니다. 온도 상승은 누설 전력을 폭증시켰고, 크리티컬 패스의 타이밍 슬랙이 마이너스로 무너지며 고온 타이밍 에러(ERR-T101)가 발생하고 있습니다.

독자는 이 프로젝트에 투입된 **반도체 시스템 오케스트레이터**로서, 5,000행 통합 데이터셋을 파싱하고 분석해 원인을 규명하고, 머신러닝으로 고장을 예측하며, 최종적으로 트러블슈팅 AI 코파일럿을 배포합니다.

---

## 폴더 구조 (5부 13장)

```
Semiconductor-AX-Masterclass/
├─ README.md
├─ requirements.txt
├─ check_environment.py          # 설치 직후 환경 점검 도구
├─ data/
│   ├─ data_generator.py         # 통합 데이터셋 생성 스크립트
│   ├─ alphachip_v2_integrated_data.csv
│   └─ manuals/                  # 13장 RAG 실습용 가상 장비 매뉴얼(PDF)
├─ part1_python_automation/      # PART 1. 반도체 데이터와 파이썬 자동화
│   ├─ ch01/                     # 1장 파이썬 에코시스템과 환경 구축
│   ├─ ch02/                     # 2장 비정형 데이터 핸들링과 정규화
│   └─ ch03/                     # 3장 객체 지향과 모듈화
├─ part2_process_analysis/       # PART 2. 공정·장비 데이터 분석
│   ├─ ch04/                     # 4장 Pandas 데이터프레임 아키텍처
│   ├─ ch05/                     # 5장 시계열 센서 제어와 이상치 필터링
│   └─ ch06/                     # 6장 수율 통계와 GroupBy 엔진
├─ part3_visual_db_report/       # PART 3. 시각화·리포트 데이터베이스 자동화
│   ├─ ch07/                     # 7장 데이터 시각화와 병목 추적
│   ├─ ch08/                     # 8장 데이터 자산화와 SQL 연동
│   └─ ch09/                     # 9장 엑셀 리포트 자동 생성
├─ part4_ml_prediction/          # PART 4. 수율·고장 예측 머신러닝
│   ├─ ch10/                     # 10장 회귀 모델과 PPA 추정
│   └─ ch11/                     # 11장 예지 보전(PdM)과 분류 모델
└─ part5_rag_capstone/           # PART 5. 장비 매뉴얼 RAG 통합 캡스톤
    ├─ ch12/                     # 12장 LLM과 프롬프트 엔지니어링
    └─ ch13/                     # 13장 RAG 아키텍처와 AI 코파일럿
```

### 파일명 규칙

`chXX_YY_기능이름.py` — XX는 장, YY는 절 번호입니다.

예: `part1_python_automation/ch01/ch01_03_env_check.py` → 1장 3절 실습 코드

---

## 실습 환경 구축

의존성 충돌을 방지하기 위해 반드시 **파이썬 가상환경(venv)** 위에서 실행합니다.

### 요구 사양

| 항목 | 사양 |
|---|---|
| OS | Windows 10 이상 / Ubuntu 22.04 LTS 이상 (WSL2 권장) |
| Python | **3.14** (최소 3.12 이상) |
| IDE | Visual Studio Code (Python Extension, Remote-SSH) |
| Database | SQLite3 (Python 표준 라이브러리 내장) |

> numpy 2.5 이상이 Python 3.12 이상을 요구하므로, 3.10·3.11 환경에서는 `requirements.txt`의 조합을 그대로 설치할 수 없습니다.

### 설치 절차

```bash
# 1) 저장소 클론
git clone https://github.com/aagicap/Semiconductor-AX-Masterclass.git
cd Semiconductor-AX-Masterclass

# 2) 가상환경 생성 및 활성화
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Linux / macOS

# 3) 의존성 설치
pip install -r requirements.txt

# 4) 설치 확인
python check_environment.py

# 5) 통합 데이터셋 생성
python data/data_generator.py
```

`check_environment.py`가 가상환경 격리와 패키지 설치 상태를 모두 `OK`로 출력하면 준비가 끝난 것입니다.

### API 키 설정 (12~13장 실습)

저장소 루트에 `.env` 파일을 만들고 키를 넣습니다. 이 파일은 `.gitignore`에 등록되어 있으므로 절대 커밋되지 않습니다.

```
OPENAI_API_KEY=sk-...
```

---

## 통합 데이터셋

`data/data_generator.py`를 실행하면 물리적 인과관계가 주입된 5,000행 CSV가 생성됩니다. 난수 시드가 고정되어 있어 **누가 실행해도 동일한 데이터**가 만들어집니다.

### 구조

```
5,000행 = 10 로트 × 5 웨이퍼 × 100 다이
장비는 웨이퍼 단위로 배정됩니다(한 웨이퍼는 한 식각 챔버에서 처리).
```

### 컬럼

| 구분 | 컬럼 |
|---|---|
| 메타데이터 | Timestamp, Lot_ID, Wafer_ID, Die_X, Die_Y, Equipment_ID |
| FDC (공정) | Voltage, Chamber_Temp, Pressure, Gas_Flow |
| EDA (설계) | Path_ID, Operating_Freq, Worst_Slack, Leakage_Power |
| 결과 지표 | Pass_Fail, Error_Code |

`Leakage_Power`에는 센서 통신 유실을 가정한 결측치 2.5%가 포함되어 있습니다. 4장 결측치 제어 실습에 사용합니다.

### 에러 코드

| 코드 | 조건 | 의미 |
|---|---|---|
| `NORMAL` | 정상 | 특이사항 없음 |
| `ERR-T101` | Worst_Slack < 0 | 고온 타이밍 에러 (불량) |
| `ERR-G202` | Gas_Flow < 88 sccm | 가스 유량 저하 경고 (양품이나 장비 노후 신호) |

### 주요 지표

| 항목 | 값 |
|---|---|
| 전체 불량률 | 16.08% |
| ETCHER_A / ETCHER_B 불량률 | 1.04% / 28.89% |
| 로트별 불량률 추이 | LOT_00 0.2% → LOT_09 62.2% |

로트가 진행될수록 불량률이 상승합니다. 이 흐름을 추적해 원인을 밝히는 것이 6장과 11장의 목표입니다.

---

## 온라인 특별 부록

도서 구매자에게 다음 콘텐츠를 별도로 제공합니다.

- **부록 A** AX 실습을 위한 파이썬 코어 문법 브릿지 (입문자용)
- **부록 B** 차세대 AI 확장: GNN 기반 반도체 네트워크 및 디지털 트윈 전망

---

## 문의 및 정오표

코드 실행 오류나 오탈자는 이 저장소의 [Issues](https://github.com/aagicap/Semiconductor-AX-Masterclass/issues)에 등록해 주세요. 확인 후 정오표에 반영합니다.

---

## 라이선스

이 저장소의 코드는 도서 학습 목적으로 자유롭게 사용·수정할 수 있습니다. 코드를 그대로 재배포하거나 상업적 교육 자료로 활용할 경우에는 출처를 밝혀 주세요.

도서 본문의 저작권은 저자에게, 편집·디자인 등 출판 데이터에 관한 권리는 한빛아카데미(주)에 있습니다.

© 2026 김미진
