# apis/routes/chat_settings.py
from fastapi import APIRouter, Depends, HTTPException, status
import logging
from utils.auth import get_current_user, User
from chat.exceptions import (
    ChatBaseException,
    DatabaseError,
    UserSettingsError
)
from chat.chat_settings import ChatSettingsManager
from apis.models.chat import ChatSettingRequest, ChatSettingResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat/settings", tags=["chat"])

def get_settings_manager():
    return ChatSettingsManager()

@router.get("", response_model=ChatSettingResponse)
async def get_chat_settings(
    current_user: User = Depends(get_current_user)
):
    """사용자의 챗봇 설정 조회"""
    logger.info(f"Fetching chat settings for user {current_user.user_id}")

    if current_user.is_active != 'Y':
        logger.warning(f"Inactive user attempt: {current_user.user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    try:
        manager = get_settings_manager()
        settings = manager.get_user_settings(current_user.user_id)
        if not settings:
            # 기본 설정 생성 및 반환
            settings = manager.update_user_settings(
                current_user.user_id,
                ChatSettingRequest().dict()
            )
        return settings
    except DatabaseError as e:
        logger.error(f"Database error in get_chat_settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_chat_settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching chat settings"
        )

@router.put("", response_model=ChatSettingResponse)
async def update_chat_settings(
    settings: ChatSettingRequest,
    current_user: User = Depends(get_current_user)
):
    """사용자의 챗봇 설정 수정"""
    logger.info(f"Updating chat settings for user {current_user.user_id}")

    if current_user.is_active != 'Y':
        logger.warning(f"Inactive user attempt: {current_user.user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    try:
        manager = get_settings_manager()
        updated_settings = manager.update_user_settings(
            current_user.user_id,
            settings.dict(exclude_unset=True)
        )
        return updated_settings
    except DatabaseError as e:
        logger.error(f"Database error in update_chat_settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in update_chat_settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while updating chat settings"
        )