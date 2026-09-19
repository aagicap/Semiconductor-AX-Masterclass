"""
ch01_05_env_check.py
API 자격 증명을 코드에서 분리해 .env 파일로 관리하는 구조를 점검한다.
확인하는 것은 값을 읽어 왔는지와 형식이 키답게 생겼는지까지다.
키가 실제로 유효한지는 12장에서 API를 호출해 확인한다.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

ENV_PATH = Path(".env")
KEY_NAME = "OPENAI_API_KEY"
MIN_LENGTH = 20


def mask(secret: str) -> str:
    """앞 3자와 뒤 4자만 남기고 가린다. 로그 유출을 막는다."""
    if len(secret) <= 7:
        return "*" * len(secret)
    return f"{secret[:3]}{'*' * 10}{secret[-4:]}"


def looks_like_key(value: str) -> bool:
    """키의 형식만 검사한다. 유효성 검증이 아니다."""
    if len(value) < MIN_LENGTH:
        return False
    if any(ch.isspace() for ch in value):
        return False
    return value.isascii()


def report() -> None:
    """자격 증명 캡슐화 상태를 점검해 출력한다."""
    loaded = load_dotenv(ENV_PATH)
    key = os.environ.get(KEY_NAME)

    print("=" * 62)
    print(" 자격 증명 캡슐화 점검")
    print("=" * 62)
    found = "발견" if ENV_PATH.exists() else "없음"
    print(f"  .env 파일        : {found}")
    print(f"  파일 적재        : {'성공' if loaded else '건너뜀'}")
    print("-" * 62)

    if not key:
        print(f"  [WAIT] {KEY_NAME} 미설정")
        print("         저장소 루트에 .env 파일을 만들고 아래 한 줄을")
        print(f"         적는다.  {KEY_NAME}=발급받은_키")
        print("         키 발급 절차는 온라인 부록 B에서 안내한다.")
    elif not looks_like_key(key):
        print(f"  [WARN] {KEY_NAME} 값의 형식이 키와 다르다")
        print(f"         읽어 온 값 : {mask(key)}")
        print("         안내 문구를 그대로 두었거나 공백이 섞였는지")
        print("         확인한다. 발급받은 키로 교체한다.")
    else:
        print(f"  [OK]   {KEY_NAME} 읽기 성공 : {mask(key)}")
        print("         형식 점검까지 통과했다. 키가 실제로 유효한지는")
        print("         12장에서 API를 호출해 확인한다.")
        print("         값은 마스킹해 출력한다. 원문을 화면이나")
        print("         로그에 남기지 않는다.")
    print("=" * 62)


if __name__ == "__main__":
    report()
