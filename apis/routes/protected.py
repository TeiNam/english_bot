# apis/routes/protected.py
from fastapi import APIRouter, Depends
from utils.dependencies import get_current_user

router = APIRouter(
    prefix="/api/v1/protected",
    tags=["보호된 리소스"]
)


@router.get("/me")
async def read_current_user(current_user: dict = Depends(get_current_user)):
    """현재 인증된 사용자 정보 조회

    Args:
        current_user: 현재 인증된 사용자 정보

    Returns:
        dict: 사용자 정보
    """
    return current_user