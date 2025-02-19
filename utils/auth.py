# utils/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from configs.jwt_setting import JWT_CONFIG
from utils.mysql_connector import MySQLConnector
from apis.deps import get_db
from pydantic import BaseModel

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=True)


class User(BaseModel):
    user_id: int
    email: str
    username: str
    is_active: str = 'Y'
    is_admin: bool = False


def create_access_token(data: dict, expires_delta: timedelta = timedelta(days=7)) -> str:
    """액세스 토큰 생성"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_CONFIG['secret_key'], algorithm=JWT_CONFIG['algorithm'])
    return encoded_jwt


async def verify_token(token: str = Depends(oauth2_scheme)) -> dict:
    """토큰 검증"""
    try:
        payload = jwt.decode(token, JWT_CONFIG['secret_key'], algorithms=[JWT_CONFIG['algorithm']])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: MySQLConnector = Depends(get_db)
) -> User:
   """현재 사용자 정보 조회"""
   credentials_exception = HTTPException(
       status_code=status.HTTP_401_UNAUTHORIZED,
       detail="Could not validate credentials",
       headers={"WWW-Authenticate": "Bearer"},
   )

   try:
       payload = jwt.decode(
           token,
           JWT_CONFIG['secret_key'],
           algorithms=[JWT_CONFIG['algorithm']]
       )

       email: str = payload.get("sub")
       user_id: int = payload.get("user_id")
       if email is None or user_id is None:
           raise credentials_exception

       query = """
                   SELECT user_id, email, username, is_active, is_admin  # is_admin 필드 추가
                   FROM `user` 
                   WHERE user_id = %(user_id)s 
                   AND email = %(email)s
                   AND is_active = 'Y'
               """
       result = db.execute_raw_query(query, {"user_id": user_id, "email": email})

       if not result:
           raise credentials_exception

       return User(**result[0])

   except JWTError:
       raise credentials_exception
   except Exception:
       raise credentials_exception