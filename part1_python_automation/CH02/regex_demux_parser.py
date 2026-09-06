import re

def analyze_log_with_regex():
    print("="*70)
    print(" 🔬 팹리스 지능형 Regex 디먹스(De-MUX) 파싱 엔진 가동 ")
    print("="*70)

    # 1. 텍스트 논리 회로 사전 합성 (Pre-synthesis)
    # 파이썬이 이스케이프(\)를 오해하지 않도록 반드시 Raw String(r"")을 사용한다.
    regex_pattern = r"Slack\s*:\s*([-\d\.]+)\s*\((VIOLATED|MET)\)"
    
    # 패턴을 파이썬 내부 C 엔진에 '미리 컴파일'하여 반복 매칭 속도를 극대화한다.
    parser_engine = re.compile(regex_pattern)

    # 2. 비정형 원시 데이터(Raw Data) 샘플 (공백 지터 및 노이즈 혼재 상황)
    raw_logs = [
        "Slack : 0.045 (MET)               # 공백 1개 정상 로그",
        "Slack  :  -0.125 (VIOLATED)      # 다중 공백 지터 로그",
        "Slack:-0.300   (VIOLATED)        # 공백 누락 및 혼합 지터 로그",
        "Temp   :  128.5 (VIOLATED)       # Slack 패턴에 부합하지 않는 이질적 노이즈"
    ]

    # 3. 파이프라인 추출(Extract) 처리
    for i, log_line in enumerate(raw_logs):
        # 컴파일된 엔진에 텍스트를 통과시켜 패턴 매칭을 수행한다.
        match = parser_engine.search(log_line)
        
        if match:
            # 매칭 성공 시, 괄호()로 묶은 그룹(Group) 데이터를 인덱스로 추출한다.
            slack_value = float(match.group(1)) # Group 1: 수치 추출 (float 형변환)
            status = match.group(2)             # Group 2: 상태값 추출
            
            print(f"[Line {i+1} 매칭 성공] 상태: {status:8} | Slack 수치: {slack_value:7.3f}")
        else:
            # 패턴과 일치하지 않는 데이터는 노이즈로 간주하고 에러 없이 안전하게 드롭(Drop)한다.
            print(f"[Line {i+1} 필터 드롭] 매칭 실패 (노이즈 데이터 격리)")

    print("="*70)

if __name__ == "__main__":
    analyze_log_with_regex()