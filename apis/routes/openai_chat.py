from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import List, Dict
from ..models.openai_chat import ChatMessage, ChatResponse, ConversationHistory
from utils.auth import get_current_user, User
from bots.openai_bot import OpenAIBot

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


def get_bot():
    return OpenAIBot()


@router.post("/stream", response_model=None)
async def chat_stream(
        message: ChatMessage,
        current_user: User = Depends(get_current_user)
):
    """채팅 스트리밍 응답"""
    if current_user.is_active != 'Y':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    bot = get_bot()
    try:
        async def stream_generator():
            collected_response = []
            async for content in bot.generate_stream(
                    message.content,
                    current_user.user_id,
                    message.conversation_id
            ):
                collected_response.append(content)
                yield content

            # 전체 응답 저장
            full_response = "".join(collected_response)
            bot.save_conversation(
                current_user.user_id,
                message.content,
                full_response,
                message.conversation_id
            )

        return StreamingResponse(
            stream_generator(),
            media_type='text/event-stream'
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{conversation_id}", response_model=List[ConversationHistory])
async def get_chat_history(
        conversation_id: str,
        current_user: User = Depends(get_current_user)
):
    """대화 히스토리 조회"""
    try:
        bot = get_bot()
        # 대화 소유자 확인
        conversation = bot.get_conversation_info(conversation_id)
        if not conversation or conversation['user_id'] != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

        history = bot.get_conversation_history(conversation_id)
        return history
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/conversation/{conversation_id}")
async def delete_conversation(
        conversation_id: str,
        current_user: User = Depends(get_current_user)
):
    """대화 삭제"""
    try:
        bot = get_bot()
        # 대화 소유자 확인 및 삭제
        result = bot.delete_user_conversation(conversation_id, current_user.user_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        return {"message": "Conversation deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations", response_model=List[Dict])
async def get_user_conversations(
        current_user: User = Depends(get_current_user)
):
    """사용자의 대화 목록 조회"""
    try:
        bot = get_bot()
        conversations = bot.get_user_conversations(current_user.user_id)
        return conversations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))