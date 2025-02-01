# utils/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from utils.auth import verify_token
from utils.mysql_connector import MySQLConnector
import jwt

security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """현재 인증된 사용자 정보 가져오기

    Args:
        credentials: HTTP Authorization 헤더의 Bearer 토큰

    Returns:
        dict: 사용자 정보

    Raises:
        HTTPException: 인증 실패 시
    """
    try:
        token = credentials.credentials
        payload = verify_token(token)
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 인증 토큰",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_mysql_connection():
    """MySQL 데이터베이스 커넥터 인스턴스 반환"""
    return MySQLConnector()