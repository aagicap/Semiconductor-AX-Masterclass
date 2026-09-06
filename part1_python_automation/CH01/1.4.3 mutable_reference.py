import copy

def analyze_mutable_reference():
    # [위험] 가변 객체의 참조 공유 (Netlist Short 현상)
    # ETCHER_B 장비의 초기 상태 레지스터 값 모델링
    reg_a = [0, 0, 0]
    reg_b = reg_a  # 데이터 복사가 아닌 '포인터 이름표'만 전달
    
    reg_b[0] = 1   # B를 수정했으나 A도 오염됨
    print(f"[Warning] reg_b 수정 후 reg_a 상태: {reg_a}")
    print(f"          (두 변수의 메모리 동일 여부: {reg_a is reg_b})\n")

    # [방어] 깊은 복사(Deep Copy)를 통한 메모리 격리
    # AlphaChip_V2의 타이밍 슬랙 데이터베이스(SSOT)
    ssot_log = [["PATH_001", 0.15], ["PATH_002", -0.05]]
    
    # 완전히 분리된 독립적인 물리적 메모리 공간 생성
    isolated_log = copy.deepcopy(ssot_log)
    isolated_log[1][1] = 0.0  # 작업용 변수의 슬랙 값 임의 수정
    
    print(f"[Safe] 원본 SSOT 로그 보존 상태: {ssot_log[1]}")
    print(f"       작업 로그 수정 상태: {isolated_log[1]}")

if __name__ == "__main__":
    analyze_mutable_reference()