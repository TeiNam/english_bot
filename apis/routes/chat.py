# apis/routes/chat.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import logging
import asyncio

from starlette.responses import Response

from utils.auth import get_current_user, User
from chat.exceptions import (
    ChatBaseException,
    DatabaseError,
    ConversationNotFound,
    OpenAIError
)
from chat.chat_manager import ChatManager
from bots.openai_bot import OpenAIBot
from apis.models.chat import (
    ChatHistoryResponse,
    ConversationResponse,
    ChatStreamRequest
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

# 싱글톤 인스턴스 생성
_chat_manager = None
_openai_bot = None


def get_chat_manager():
    global _chat_manager
    if _chat_manager is None:
        _chat_manager = ChatManager()
    return _chat_manager


def get_openai_bot():
    global _openai_bot
    if _openai_bot is None:
        _openai_bot = OpenAIBot()
    return _openai_bot


@router.get("/conversations", response_model=List[ConversationResponse])
async def get_user_conversations(
        current_user: User = Depends(get_current_user)
):
    """사용자의 대화 목록 조회"""
    try:
        chat_manager = get_chat_manager()
        logger.debug(f"Fetching conversations for user: {current_user.user_id}")

        # 비동기로 실행
        loop = asyncio.get_running_loop()
        try:
            conversations = await loop.run_in_executor(
                None,
                chat_manager.get_user_conversations,
                current_user.user_id
            )
            logger.info(f"Found {len(conversations) if conversations else 0} conversations")
            return conversations or []

        except Exception as e:
            logger.error(f"Error in run_in_executor: {str(e)}", exc_info=True)
            raise

    except ChatBaseException as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DatabaseError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_user_conversations: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch conversations: {str(e)}"
        )


@router.get("/history/{conversation_id}", response_model=List[ChatHistoryResponse])
async def get_chat_history(
    conversation_id: str,
    current_user: User = Depends(get_current_user)
):
    """대화 내역 조회"""
    try:
        chat_manager = get_chat_manager()

        # 대화 접근 권한 확인 (비동기 함수이므로 await로 직접 호출)
        conversation = await chat_manager.get_conversation_info(conversation_id)
        if conversation['user_id'] != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this conversation"
            )

        # 대화 내역 조회: get_chat_history는 동기 함수이므로 run_in_executor를 사용
        loop = asyncio.get_running_loop()
        history = await loop.run_in_executor(
            None,
            chat_manager.get_chat_history,
            conversation_id
        )
        return history

    except ConversationNotFound as e:
        logger.warning(f"Conversation not found: {conversation_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DatabaseError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in get_chat_history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch chat history"
        )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
        conversation_id: str,
        current_user: User = Depends(get_current_user)
):
    """대화 삭제"""
    try:
        chat_manager = get_chat_manager()

        # 대화 존재 및 권한 확인
        try:
            conversation = await loop.run_in_executor(
                None,
                chat_manager.get_conversation_info,
                conversation_id
            )
            if conversation['user_id'] != current_user.user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to delete this conversation"
                )
        except ConversationNotFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

        # 비동기로 실행
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            chat_manager.delete_conversation,
            conversation_id,
            current_user.user_id
        )
        return {"success": result}

    except ConversationNotFound as e:
        logger.warning(f"Conversation not found: {conversation_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DatabaseError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in delete_conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete conversation"
        )


@router.post("/stream")
async def stream_chat(
        message: ChatStreamRequest,
        current_user: User = Depends(get_current_user)
):
    """채팅 응답 생성 및 저장"""
    try:
        chat_manager = get_chat_manager()

        # 1. 대화 ID가 있는 경우 존재 및 권한 확인
        conversation_id = message.conversation_id
        if conversation_id:
            try:
                conversation = await chat_manager.get_conversation_info(conversation_id)
                if conversation['user_id'] != current_user.user_id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You don't have permission to access this conversation"
                    )
            except ConversationNotFound:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found"
                )

        # 2. OpenAI 응답 생성
        bot = get_openai_bot()
        response = await bot.generate_stream(
            user_message=message.content,
            user_id=current_user.user_id,
            conversation_id=conversation_id
        )

        # 3. 메시지 저장 (새 대화 생성 포함)
        try:
            result = await chat_manager.save_message(
                user_id=current_user.user_id,
                user_message=message.content,
                bot_response=response,
                conversation_id=message.conversation_id
            )
            # 새 대화가 생성된 경우 conversation_id를 가져옴
            conversation_id = result.get('conversation_id') or message.conversation_id
        except Exception as e:
            logger.error(f"Failed to save message: {str(e)}")
            # 메시지 저장 실패는 사용자 응답에 영향을 주지 않도록 함
            pass

        # 4. 응답 반환
        return Response(
            content=response,
            media_type="text/plain",
            headers={
                'X-Conversation-ID': str(conversation_id) if conversation_id else ''
            }
        )

    except OpenAIError as e:
        logger.error(f"OpenAI error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in stream_chat: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate response"
        )