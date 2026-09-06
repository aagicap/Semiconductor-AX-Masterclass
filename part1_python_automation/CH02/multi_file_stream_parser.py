from pathlib import Path
import sys

def parse_single_file_generator(file_path):
    """
    [1.5절 아키텍처] 단일 파일을 한 줄씩 지연 평가(Lazy) 방식으로 읽어내는 엔진
    """
    # 에러 방어: 파일 존재 여부 확인
    if not file_path.exists():
        return

    # with 문: 파일 처리 후 OS 자원(File Descriptor)을 자동으로 완벽히 반납
    with file_path.open('r', encoding='utf-8', errors='ignore') as log_file:
        for line in log_file:
            if "VIOLATED" in line:
                # 파일명(stem)과 해당 결함 로그를 튜플로 묶어서 스트리밍
                yield (file_path.stem, line.strip())

def orchestrate_multi_file_pipeline(root_directory):
    """
    [2.1절 아키텍처] 수천 개의 분산된 파일을 탐색하여 파서를 연속 가동하는 오케스트레이터
    """
    root_path = Path(root_directory)
    print("="*70)
    print(f" 🚀 팹리스 다중 로그 디렉토리 스트리밍 파이프라인 가동 ")
    print(f"    Target Directory: {root_path.resolve()}")
    print("="*70)

    # 1. rglob을 통한 지능형 재귀 탐색 (제너레이터 반환)
    target_files = root_path.rglob("*.rep")
    
    total_violation_count = 0
    
    # 2. 탐색된 파일 경로를 하나씩 꺼내어 단일 파서 엔진에 주입
    for file_path in target_files:
        print(f"\n[Process] 스캐닝 중: {file_path.name}...")
        
        # 3. 개별 파일에 대한 파싱 제너레이터 가동
        violation_stream = parse_single_file_generator(file_path)
        
        for file_name, log_line in violation_stream:
            total_violation_count += 1
            print(f"  -> [추출] {file_name} | {log_line}")
            
    print("="*70)
    print(f"[Result] 전체 디렉토리 탐색 완료. 총 {total_violation_count}개의 위반 로그 무결점 추출.")
    print("="*70)

if __name__ == "__main__":
    # (실무 적용 시 EDA 리포트 최상위 디렉토리 경로 입력)
    # 현재 폴더(".")를 기준으로 테스트 구동
    orchestrate_multi_file_pipeline(".")