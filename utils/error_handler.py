# utils/error_handler.py
from functools import wraps
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)

def handle_errors(func):
    """공통 에러 처리 데코레이터"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            raise
        except Exception as e:
            operation = func.__doc__ or func.__name__
            logger.error(f"{operation} 실패: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    return wrapper