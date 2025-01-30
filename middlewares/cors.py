from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from enum import Enum


class Environment(str, Enum):
    DEV = "dev"
    PRD = "prd"


ALLOWED_METHODS = ["*"]
ALLOWED_HEADERS = ["*"]


def get_environment() -> str:
    """ENV 환경 변수를 가져오거나 기본값(dev)을 반환."""
    return os.getenv("ENV", "dev")


def validate_environment(env: str) -> None:
    """환경 변수가 유효한지 검사."""
    if env not in Environment._value2member_map_:
        valid_values = [e.value for e in Environment]
        raise ValueError(f"유효하지 않은 환경입니다. 가능한 값: {valid_values}")


def get_cors_origins(env: str) -> list[str]:
    """CORS 허용 origins 추출."""
    if env == Environment.DEV:
        return ["*"]  # 개발 환경은 모든 origin 허용
    origins = os.getenv("CORS_ORIGINS", "").strip().split(",")
    origins = [origin.strip() for origin in origins if origin.strip()]
    if not origins:
        raise ValueError("Production 환경에서는 CORS_ORIGINS 환경변수 설정이 필요합니다.")
    return origins


def setup_cors_middleware(app: FastAPI) -> None:
    """CORS 미들웨어 설정."""
    # 1. ENV 값 가져오기
    env = get_environment()

    # 2. ENV 값 검증
    validate_environment(env)

    # 3. CORS origins 설정
    origins = get_cors_origins(env)

    # 4. 미들웨어 추가
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=ALLOWED_METHODS,
        allow_headers=ALLOWED_HEADERS,
    )
