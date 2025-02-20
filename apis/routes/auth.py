# apis/routes/auth.py
from datetime import timedelta

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr

from apis.models.auth_service import AuthService
from utils.auth import create_access_token, get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["인증"])


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    user_id: int
    username: str
    email: str


@router.post("/login", response_model=dict)
async def login(user_data: UserLogin):
    """로그인 API

    Args:
        user_data: 사용자 로그인 정보

    Returns:
        dict: 액세스 토큰과 사용자 정보

    Raises:
        HTTPException: 인증 실패 시
    """
    auth_service = AuthService()
    user = auth_service.authenticate_user(user_data.email, user_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다."
        )

    # 토큰 생성
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.user_id},  # user_id도 토큰에 포함
        expires_delta=timedelta(minutes=1440)  # 24시간
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email
        }
    }


@router.post("/refresh", response_model=dict)
async def refresh_token(current_user=Depends(get_current_user)):
    """토큰 갱신 API"""
    try:
        new_access_token = create_access_token(
            data={"sub": current_user.email, "user_id": current_user.user_id},
            expires_delta=timedelta(minutes=1440)  # 24시간
        )

        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "user": {
                "user_id": current_user.user_id,
                "username": current_user.username,
                "email": current_user.email
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰 갱신에 실패했습니다."
        )
