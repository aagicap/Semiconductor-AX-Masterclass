import re, os

# 1. 경로 무결성 확보: 현재 실행 파일 기준 절대 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, "address_map.txt")

def parse_address_map(file_path):
    # [설계 패턴] 주소값 내의 언더바(_) 무시 및 데이터 격리
    # - (?P<name>\w+): 레지스터 명칭
    # - (?P<addr>0x[0-9A-Fa-f_]+): 언더바가 포함된 16진수 주소
    # - \[(?P<perm>\w+)\]: 대괄호 내의 접근 권한
    reg_regex = re.compile(r"(?P<name>\w+):\s+(?P<addr>0x[0-9A-Fa-f_]+)\s+\[(?P<perm>\w+)\]")
    
    with open(file_path, 'r') as f:
        for line in f:
            match = reg_regex.search(line)
            if match:
                print(f"Register: {match.group('name'):<15} | Addr: {match.group('addr'):<12} | Access: {match.group('perm')}")

# 실행 및 결과출력
parse_address_map(file_path)