import sys

def trace_garbage_collection():
    print("="*60)
    print(" 파이썬 참조 카운팅(Reference Counting) 진단 ")
    print("="*60)

    # 1. 5,000행 AlphaChip_V2 통합 데이터 적재 객체 생성
    csv_data_block = ["ETCHER_B_Drift_Log_5000_Rows"]
    
    # sys.getrefcount() 함수로 인자를 전달할 때 임시 참조가 1 추가됨
    print(f"[Step 1] 객체 선언 직후 참조 횟수: {sys.getrefcount(csv_data_block)}")

    # 2. 참조 공유 증가
    backup_ptr = csv_data_block
    print(f"[Step 2] 'backup_ptr' 할당 이후 참조 횟수: {sys.getrefcount(csv_data_block)}")

    # 3. 참조 해제 (Garbage Collection 트리거)
    csv_data_block = None
    backup_ptr = None
    
    print("[Step 3] 변수의 참조를 모두 해제했습니다. (Reference Count = 0)")
    print("         -> 백그라운드 가비지 컬렉터(GC)가 메모리를 즉시 OS에 반환합니다.")
    print("="*60)

if __name__ == "__main__":
    trace_garbage_collection()