from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import List, Dict, Optional
from pydantic import BaseModel
from datetime import datetime
import logging
from apis.models.openai_chat import ChatMessage, ChatResponse, ConversationHistory
from utils.auth import get_current_user, User
from bots.openai_bot import OpenAIBot, DatabaseError, ConversationNotFound

# 로깅 설정
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


# 요청 및 응답 모델 정의
class CreateConversationRequest(BaseModel):
    initial_message: str


class ConversationResponse(BaseModel):
    conversation_id: str
    chat_history_id: int


class ConversationListResponse(BaseModel):
    conversation_id: str
    title: Optional[str]
    status: str
    message_count: int
    create_at: datetime
    last_message_at: datetime
    last_message: Optional[str]
    last_response: Optional[str]


def get_bot():
    return OpenAIBot()


@router.post("/stream", response_model=None)
async def chat_stream(
        message: ChatMessage,
        current_user: User = Depends(get_current_user)
):
    """채팅 스트리밍 응답"""
    logger.info(f"Starting chat stream for user {current_user.user_id}")

    if current_user.is_active != 'Y':
        logger.warning(f"Inactive user attempt: {current_user.user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    bot = get_bot()
    try:
        # conversation_id가 없는 경우 새로운 대화 세션만 생성
        if not message.conversation_id:
            result = bot.create_conversation(current_user.user_id, message.content)
            message.conversation_id = result['conversation_id']
        else:
            # conversation_id가 유효한지 확인
            try:
                conversation = bot.get_conversation_info(message.conversation_id)
                if not conversation or conversation['user_id'] != current_user.user_id:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Conversation not found"
                    )
            except ConversationNotFound:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found"
                )

        async def stream_generator():
            collected_response = []
            async for content in bot.generate_stream(
                    message.content,
                    current_user.user_id,
                    message.conversation_id
            ):
                collected_response.append(content)
                yield content

            # 전체 응답만 한 번 저장
            full_response = "".join(collected_response)
            logger.info(f"Saving conversation for user {current_user.user_id}")
            try:
                bot.save_conversation(
                    current_user.user_id,
                    message.content,
                    full_response,
                    message.conversation_id
                )
            except DatabaseError as e:
                logger.error(f"Failed to save conversation: {str(e)}")

        return StreamingResponse(
            stream_generator(),
            media_type='text/event-stream'
        )

    except DatabaseError as e:
        logger.error(f"Database error in chat_stream: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in chat_stream: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during chat processing"
        )


@router.get("/history/{conversation_id}", response_model=List[ConversationHistory])
async def get_chat_history(
        conversation_id: str,
        current_user: User = Depends(get_current_user)
):
    """대화 히스토리 조회"""
    logger.info(f"Fetching chat history for conversation {conversation_id}")
    try:
        bot = get_bot()
        # 대화 소유자 확인
        conversation = bot.get_conversation_info(conversation_id)
        if not conversation or conversation['user_id'] != current_user.user_id:
            logger.warning(
                f"Unauthorized access attempt to conversation {conversation_id} by user {current_user.user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

        # 메서드 이름 수정: get_conversation_history -> get_chat_history
        history = bot.get_chat_history(conversation_id)
        return history
    except ConversationNotFound as e:
        logger.warning(f"Conversation not found: {conversation_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DatabaseError as e:
        logger.error(f"Database error in get_chat_history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_chat_history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching chat history"
        )


@router.delete("/conversation/{conversation_id}", status_code=status.HTTP_200_OK)
async def delete_conversation(
        conversation_id: str,
        current_user: User = Depends(get_current_user)
):
    """대화 삭제"""
    logger.info(f"Deleting conversation {conversation_id} for user {current_user.user_id}")
    try:
        bot = get_bot()
        result = bot.delete_user_conversation(conversation_id, current_user.user_id)
        if not result:
            logger.warning(f"Conversation not found for deletion: {conversation_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        return {"message": "Conversation deleted successfully"}
    except ConversationNotFound as e:
        logger.warning(f"Conversation not found: {conversation_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DatabaseError as e:
        logger.error(f"Database error in delete_conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in delete_conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while deleting the conversation"
        )


@router.get("/conversations", response_model=List[ConversationListResponse])
async def get_user_conversations(
        current_user: User = Depends(get_current_user)
):
    """사용자의 대화 목록 조회"""
    logger.info(f"Fetching conversations for user {current_user.user_id}")
    try:
        bot = get_bot()
        conversations = bot.get_user_conversations(current_user.user_id)
        return conversations
    except DatabaseError as e:
        logger.error(f"Database error in get_user_conversations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_user_conversations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching conversations"
        )


@router.post("/conversation", response_model=ConversationResponse)
async def create_conversation_endpoint(
        request: CreateConversationRequest,
        current_user: User = Depends(get_current_user)
):
    """새 대화를 생성하고, 최초 메시지를 저장하는 엔드포인트"""
    logger.info(f"Creating new conversation for user {current_user.user_id}")
    try:
        bot = get_bot()
        result = bot.create_conversation(current_user.user_id, request.initial_message)
        return ConversationResponse(
            conversation_id=result['conversation_id'],
            chat_history_id=result['chat_history_id']
        )
    except DatabaseError as e:
        logger.error(f"Database error in create_conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in create_conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating the conversation"
        )