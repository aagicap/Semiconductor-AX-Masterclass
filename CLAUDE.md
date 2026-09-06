# CLAUDE.md

이 저장소는 도서 『반도체 데이터 엔지니어링(가제)』(한빛아카데미, 5부 13장)의 공식 실습 코드 저장소다.

**이 저장소에서 하는 일은 실습 코드 작성·검증·정리다.** 교재 본문 집필과 원고 검토는 claude.ai 프로젝트에서 별도로 진행하므로, 여기서 원고 문장이나 이미지 프롬프트를 생성하지 않는다.

---

## 개발 환경

- Windows + PowerShell. 터미널 명령은 PowerShell 문법으로 제시한다.
- Python 3.14 (최소 3.12). 항상 `venv` 가상환경을 활성화한 상태에서 실행한다.
- 패키지는 `requirements.txt`에 고정되어 있다. **명세에 없는 패키지를 임의로 추가하지 않는다.** 필요하면 먼저 알린다.

```powershell
.\venv\Scripts\Activate.ps1
python check_environment.py
```

---

## 폴더 및 파일명 규칙

교재 목차와 저장소 구조가 1:1로 대응한다. 폴더명은 **전부 소문자**다.

```
data/                        # 데이터셋과 제너레이터
part1_python_automation/     ch01/ ch02/ ch03/
part2_process_analysis/      ch04/ ch05/ ch06/
part3_visual_db_report/      ch07/ ch08/ ch09/
part4_ml_prediction/         ch10/ ch11/
part5_rag_capstone/          ch12/ ch13/
```

실습 코드 파일명은 `chXX_YY_기능이름.py` 형식이다. XX는 장, YY는 절 번호다.

- 예: `part1_python_automation/ch01/ch01_03_env_check.py` (1장 3절)
- 새 파일을 만들 때 해당 절이 실재하는지 목차로 확인한다. 임의의 절 번호를 만들지 않는다.

---

## 통합 데이터셋 (변경 금지 영역)

`data/data_generator.py`가 생성하는 5,000행 CSV는 교재 전체가 공유하는 단일 데이터셋이다. **생성 규칙을 임의로 바꾸지 않는다.** 수치가 바뀌면 이미 집필된 본문의 실행 결과가 전부 틀어진다.

- 시드 `np.random.seed(42)` 고정. 절대 변경하지 않는다.
- 구조: 10로트 × 5웨이퍼 × 100다이. 장비는 웨이퍼 단위로 배정된다.
- 컬럼 16개: `Timestamp, Lot_ID, Wafer_ID, Die_X, Die_Y, Equipment_ID, Path_ID, Voltage, Chamber_Temp, Pressure, Gas_Flow, Operating_Freq, Worst_Slack, Leakage_Power, Pass_Fail, Error_Code`
- `Leakage_Power`에 결측 2.5%(125행)가 의도적으로 포함되어 있다. 채우거나 제거하지 않는다.
- `Error_Code` 값은 `NORMAL` / `ERR-T101`(슬랙 음수) / `ERR-G202`(가스 유량 저하 경고) 세 가지다.

### 검증 지표

제너레이터를 수정한 뒤에는 아래 값이 그대로 나오는지 반드시 확인한다. 하나라도 달라지면 되돌린다.

| 항목 | 값 |
|---|---|
| 전체 불량률 | 16.08% |
| ETCHER_A / ETCHER_B 불량률 | 1.04% / 28.89% |
| 에러 코드 분포 | NORMAL 4,023 / ERR-T101 804 / ERR-G202 173 |
| Leakage_Power 결측 | 125행 |
| 로트별 불량률 | LOT_00 0.2% → LOT_09 62.2% |

CSV를 직접 편집하지 않는다. 데이터가 필요하면 제너레이터를 실행해 재생성한다.

---

## 코드 작성 규칙

- **작성한 코드는 반드시 실행해 확인한다.** 실행 결과를 추정해서 보고하지 않는다.
- 코드는 두 벌로 관리한다. 저장소에는 **줄 번호 없이 바로 실행되는 `.py`** 만 커밋한다. 지면용(줄 번호 포함) 버전은 원고 쪽에서 따로 만든다.
- API 키는 `.env` + `python-dotenv`로만 다룬다. 하드코딩하지 않으며 `.env`는 커밋하지 않는다.
- matplotlib 사용 시 한글 폰트 설정과 `rcParams["axes.unicode_minus"] = False`를 반드시 포함한다. 이 책은 음수 슬랙이 핵심 결과라 부호가 깨지면 안 된다.
- 파일 순회 중 이름 변경·삭제가 필요하면 `list()`로 감싸 순회 대상을 먼저 확정한다.
- pandas 3.x 기준으로 작성한다. Copy-on-Write가 기본 동작이고 문자열 컬럼의 기본 dtype이 2.x와 다르므로, 옛 관행(`inplace`, 연쇄 대입)을 그대로 쓰지 않는다.
- 포매터는 `black`, 린터는 `pylint`를 따른다.

---

## 커밋

- 메시지는 한국어로, 어느 절의 작업인지 드러나게 쓴다.
  - 예: `1.3절 가상환경 격리 진단 스크립트 추가`
  - 예: `data_generator 저장 경로를 스크립트 기준으로 변경`
- 한 커밋에 여러 절의 변경을 섞지 않는다.
- `venv/`, `.env`, `__pycache__/`는 커밋하지 않는다.
