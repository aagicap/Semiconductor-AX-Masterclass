from pathlib import Path
import re
import json

def intelligent_log_assetizer(input_file_path, output_json_path):
    """
    비정형 로그 스트림을 분석하여 모듈별 결함 빈도를 구조화하고,
    결과를 정형화된 JSON 파일 데이터베이스로 영구 자산화(SSOT)하는 엔진
    """
    log_path = Path(input_file_path)
    json_output = Path(output_json_path)
    
    # 1. 예외 방어 로직: 파일 무결성 검증
    if not log_path.exists():
        print(f"[Error] 분석 대상 로그 파일이 존재하지 않습니다: {log_path}")
        return None

    # 2. 데이터 적재 공간 정의 (LUT 아키텍처 기반 딕셔너리)
    error_stats = {}

    # 3. 텍스트 논리 회로 사전 합성 (re.compile 및 Named Group 활용)
    error_pattern = re.compile(r"ERROR:\s+(?P<mod>[\w_]+)")

    # 4. 고속 스트림 I/O 자원 제어 및 데이터 추출(Extract) -> 적재(Load)
    with log_path.open('r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            match = error_pattern.search(line)
            if match:
                mod_name = match.group('mod')
                # dict.get(key, default)를 활용한 지능형 카운터 레지스터 구현
                error_stats[mod_name] = error_stats.get(mod_name, 0) + 1

    # 5. [★핵심 보완: 데이터 자산화 단계] 정규화 데이터를 JSON 파일로 영구 적재
    # indent=4 옵션을 통해 가독성이 뛰어난 구조화 파일 포맷 생성
    with json_output.open('w', encoding='utf-8') as json_file:
        json.dump(error_stats, json_file, indent=4, ensure_ascii=False)
        
    print(f"[Assetization Success] 단일 진실 공급원(SSOT) 파일 생성 완료: {json_output.name}")
    return error_stats

def execute_engineering_decision(final_report):
    """
    적재된 데이터베이스를 바탕으로 최우선 디버깅 우선순위(Triage)를 판별하는 엔진
    """
    if not final_report:
        return

    print("="*50)
    print(f"{'지능형 로그 정규화 리포트':^44}")
    print("="*50)
    for mod, count in final_report.items():
        print(f"  Module: {mod:<15} | Error Count: {count:>2}회 발생")
        
    print("-"*50)
    print(f"{'! '*8} Engineering Decision Matrix {' !'*8}")
    
    # [Triage 단계]: 선언적 최댓값 매핑을 활용해 O(1) 속도로 병목 모듈 특정
    worst_module = max(final_report, key=final_report.get)
    
    print(f"  최우선 디버깅 대상 (Worst Module): [{worst_module}]")
    print(f"  시스템적 집중 분석 근거         : 결함 발생 밀도 최대 ({final_report[worst_module]}회)")
    print("!"*50)

if __name__ == "__main__":
    # 프로젝트 환경 내의 공통 리포트 폴더 경로 지정
    target_log = "mixed_eda_system.log"
    output_db = "ssot_error_report.json"
    
    # 파이프라인 가동
    report_db = intelligent_log_assetizer(target_log, output_db)
    execute_engineering_decision(report_db)