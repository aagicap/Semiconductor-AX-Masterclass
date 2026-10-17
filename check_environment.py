"""
check_environment.py
설치 직후 패키지와 ax_ 공통 모듈 설치 여부를 한눈에 점검한다.
실행 위치: 저장소 루트
"""

import importlib
import sys
import tomllib
from pathlib import Path

REQUIRED = [
    "pandas",
    "numpy",
    "pyarrow",
    "sklearn",
    "faiss",
    "matplotlib",
    "seaborn",
    "openpyxl",
    "pypdf",
    "openai",
    "streamlit",
    "dotenv",
]
PYPROJECT = Path(__file__).resolve().parent / "pyproject.toml"


def check_packages() -> int:
    """requirements의 패키지를 불러와 보고 실패한 수를 돌려준다."""
    failed = 0
    for name in REQUIRED:
        try:
            module = importlib.import_module(name)
        except ImportError:
            print(f"  FAIL {name:14} 설치되지 않았다")
            failed += 1
            continue
        version = getattr(module, "__version__", "(버전 정보 없음)")
        print(f"  OK   {name:14} {version}")
    return failed


def check_ax_modules() -> int:
    """pyproject.toml에 등록된 ax_ 모듈을 불러와 보고 실패한 수를
    돌려준다. 새 모듈 등록 후 재설치를 빠뜨리면 여기서 드러난다."""
    with PYPROJECT.open("rb") as f:
        modules = tomllib.load(f)["tool"]["setuptools"]["py-modules"]
    missing = []
    for name in modules:
        try:
            importlib.import_module(name)
        except ImportError:
            missing.append(name)
    print(f"  등록 {len(modules)}개, 불러오기 실패 {len(missing)}개")
    if missing:
        print(f"  FAIL {', '.join(missing)}")
        print("       저장소 루트에서 pip install -e . 를 실행한다")
    return len(missing)


def main() -> None:
    """세 가지를 점검하고 종합 판정을 출력한다."""
    print(f"[Python] {sys.version.split()[0]}")
    isolated = sys.prefix != sys.base_prefix
    print(f"[가상환경 격리] {'PASS' if isolated else 'FAIL'}")
    print("[패키지]")
    failed = check_packages()
    print("[ax_ 공통 모듈] (4장부터 필요)")
    failed += check_ax_modules()
    print(f"[결과] {'PASS' if failed == 0 else 'FAIL'}")
    print("[확인 범위] 불러오기와 버전만 확인했다")


if __name__ == "__main__":
    main()
