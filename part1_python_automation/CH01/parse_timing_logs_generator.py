import sys
import os

def parse_timing_logs_generator(file_path):
    """
    메모리 고갈(OOM) 방지를 위해 수십 GB의 텍스트 로그를 
    한 줄씩 스트리밍으로 읽어 반환하는 제너레이터 엔진
    """
    # 파일 존재 여부 확인 (방어적 프로그래밍)
    if not os.path.exists(file_path):
        print(f"[Error] 파일을 찾을 수 없습니다: {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as log_file:
        for line in log_file:
            # VIOLATED 키워드가 포함된 라인만 필터링하여 스트리밍 방출
            if "VIOLATED" in line:
                yield line.strip()

def orchestrate_data_pipeline():
    # 실제 분석할 대용량 로그 파일 경로
    target_file = "massive_timing_report.rep"
    
    print("="*60)
    print(" 🚀 대규모 로그 데이터 스트리밍 파이프라인 가동 ")
    print("="*60)
    
    # 제너레이터 객체 생성 (파일 내용이 미리 메모리에 로드되지 않음)
    violation_stream = parse_timing_logs_generator(target_file)
    
    # 객체 자체의 메모리 크기 확인 (데이터 양과 무관하게 O(1))
    print(f"[Memory] 제너레이터 객체 크기: {sys.getsizeof(violation_stream)} Bytes")
    
    # 파이프라인 소비 (Consume) - 1줄씩 처리하여 메모리 부하 제어
    processed_count = 0
    for log in violation_stream:
        processed_count += 1
        # 실제 실무에서는 이곳에서 SQLite 적재(Load)가 이루어짐
        print(f"  -> 추출 데이터 [{processed_count}]: {log}")
            
    print("="*60)
    print(f"[Result] 총 {processed_count}개의 위반 로그를 메모리 부하 없이 파싱 완료했습니다.")
    print("="*60)

if __name__ == "__main__":
    # 스크립트 실행 시 파이프라인 가동
    orchestrate_data_pipeline()
    
    valid_signals = dict(filter(lambda x: x[1] > 0, zip(address_bus, data_bus)))