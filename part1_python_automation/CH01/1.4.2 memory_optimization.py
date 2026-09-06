def analyze_memory_optimization():
    print("="*60)
    print(" 파이썬 지능형 메모리 최적화 진단 리포트 ")
    print("="*60)
    
    # 1. 작은 정수 인터닝(Small Integer Interning) 검증
    # ETCHER_B의 정상 기준 온도 파라미터 가정
    temp_a = 65
    temp_b = 65
    
    print(f"temp_a의 물리적 주소: {hex(id(temp_a))}")
    print(f"temp_b의 물리적 주소: {hex(id(temp_b))}")
    print(f"temp_a is temp_b (메모리 주소 동일성): {temp_a is temp_b}\n")
    
    # 2. 임계 범위 초과 데이터의 생성 (드리프트 발생 시점)
    drift_temp_c = 1000
    drift_temp_d = 1000
    
    print(f"drift_temp_c is drift_temp_d (메모리 주소 동일성): {drift_temp_c is drift_temp_d}")
    print(f"drift_temp_c == drift_temp_d (내부 데이터 동등성): {drift_temp_c == drift_temp_d}")
    print("="*60)

if __name__ == "__main__":
    analyze_memory_optimization()