import sys
import importlib

REQUIRED = ["pandas", "numpy", "sklearn", "faiss", "matplotlib",
            "seaborn", "openpyxl", "pypdf", "openai", "streamlit", "dotenv"]

print(f"[Python] {sys.version.split()[0]}")
print(f"[가상환경 격리] {'PASS' if sys.prefix != sys.base_prefix else 'FAIL'}")

for name in REQUIRED:
    try:
        module = importlib.import_module(name)
        version = getattr(module, "__version__", "(버전 정보 없음)")
        print(f"  OK   {name:14} {version}")
    except ImportError:
        print(f"  FAIL {name:14} 설치되지 않았습니다.")