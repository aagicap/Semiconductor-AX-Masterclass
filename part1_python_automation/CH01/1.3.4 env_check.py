import sys
import os

def check_venv_isolation():
    """
    현재 런타임이 격리된 가상환경 내부인지, 시스템 전역 환경인지
    sys.prefix 와 sys.executable 아키텍처를 추적하여 진단하는 엔진.
    """
    print("="*60)
    print(" 🛡️ 팹리스 AX 파이프라인 시스템 격리 무결성 진단 ")
    print("="*60)
    
    # 1. 실행 엔진: 파이썬 인터프리터의 물리적 절대 경로 확인
    # 시스템 전역 파이썬인지, 가상환경 폴더 내부의 파이썬인지 확인
    interpreter_path = sys.executable
    print(f"[Interpreter Path] : {interpreter_path}")
    
    # 2. 런타임 경로(sys.prefix)와 원본 경로(sys.base_prefix) 추적
    current_prefix = sys.prefix
    base_prefix = getattr(sys, "base_prefix", sys.prefix)
    
    print(f"[Run-time Prefix]  : {current_prefix}")
    print(f"[Base OS Prefix]   : {base_prefix}")
    print("-" * 60)
    
    # 3. 격리 무결성(Isolation Integrity) 판별 로직
    # 두 경로가 다르면 성공적으로 가상환경으로 우회(Override)된 상태임
    if current_prefix != base_prefix:
        print("[Status] PASS: 가상환경(venv) 샌드박스가 정상 활성화되었습니다.")
        # Windows는 Lib\site-packages, Linux는 lib/python3.x/site-packages 구조를 가짐
        print(f"         독립된 패키지 공간이 글로벌 환경으로부터 보호됩니다.")
    else:
        print("[Status] FAIL: 시스템 전역(Global) 파이썬 환경이 감지되었습니다!")
        print("         경고: 의존성(Dependency) 충돌 리스크가 존재하므로 점검이 필요합니다.")
        
if __name__ == "__main__":
    check_venv_isolation()