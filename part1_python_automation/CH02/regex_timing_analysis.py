import re

# 1. 원본 데이터 분석 (STA 리포트 추출 샘플)
# 텍스트 내에서 특정 인스턴스 경로와 슬랙(Slack) 값을 동시에 탐지해야 함
report_line = "Path: u_cpu/u_alu/out_reg_1, Slack: -0.456ns"

# 2. 패턴 설계 및 논리 합성 (re.compile)
# [?P<name>] 구문을 통해 추출된 데이터 필드에 공학적 의미(레이블)를 부여한다.
# - path 필드: [\w/]+ 패턴을 통해 계층 구조(Hierarchy)를 인식
# - slack 필드: [-+]?\d*\.\d+ 패턴을 통해 부동 소수점 무결성 확보
regex_raw = r"Path:\s+(?P<path>[\w/]+),\s+Slack:\s+(?P<slack>[-+]?\d*\.\d+)ns"

# 고속 상태 머신(FSM)으로 변환 (반복 루프 전 수행하여 Throughput 최적화)
pattern = re.compile(regex_raw)

# 3. 매칭 수행 및 데이터 격리
# 검색 수행 결과인 'match' 객체는 상태 머신이 최종 수락 상태에 도달했음을 의미한다.
match = pattern.search(report_line)

if match:
    # 인덱스 번호가 아닌 정의된 그룹 이름으로 데이터에 즉각 접근
    instance_path = match.group('path')
    slack_value = float(match.group('slack')) # 정량적 분석을 위한 수치형 캐스팅
    
    print(f"Detected Instance : {instance_path}")
    print(f"Current Slack (ns): {slack_value}")