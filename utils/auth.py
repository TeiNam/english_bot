# utils/auth.py
from datetime import datetime, timedelta
from typing import Optional
import jwt
import os

# 환경 변수에서 시크릿 키 가져오기 (없으면 기본값 사용)
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24시간


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """JWT 액세스 토큰 생성

    Args:
        data (dict): 토큰에 인코딩할 데이터
        expires_delta (timedelta, optional): 만료 시간 델타

    Returns:
        str: 생성된 JWT 토큰
    """
    to_encode = data.copy()

    # 만료 시간 설정
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def verify_token(token: str) -> dict:
    """JWT 토큰 검증

    Args:
        token (str): 검증할 JWT 토큰

    Returns:
        dict: 디코딩된 토큰 데이터

    Raises:
        jwt.InvalidTokenError: 유효하지 않은 토큰
    """
    return jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])