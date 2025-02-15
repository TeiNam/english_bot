# apis/models/chat.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# Chat Settings Models
class ChatSettingRequest(BaseModel):
    default_prompt_template_id: Optional[int] = None
    model: str = Field(default="gpt-4o-mini", pattern="^(gpt-4o-mini|gpt-4o)$")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    max_tokens: int = Field(default=1000, ge=1, le=4000)

class ChatSettingResponse(BaseModel):
    user_id: int
    default_prompt_template_id: Optional[int]
    model: str
    temperature: float
    max_tokens: int
    create_at: datetime
    update_at: datetime

    class Config:
        from_attributes = True

# Prompt Template Models
class PromptTemplateResponse(BaseModel):
    prompt_template_id: int
    name: str
    description: Optional[str]
    system_prompt: str
    user_prompt: str
    is_active: str
    create_at: datetime
    update_at: datetime

    class Config:
        from_attributes = True

class PromptTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    system_prompt: str
    user_prompt: str
    is_active: str = "Y"

class PromptTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    user_prompt: Optional[str] = None
    is_active: Optional[str] = None

# Chat History Models
class ChatHistoryResponse(BaseModel):
    chat_history_id: int
    conversation_id: str
    user_id: int
    user_message: str
    bot_response: str
    create_at: datetime

    class Config:
        from_attributes = True

class ConversationResponse(BaseModel):
    conversation_id: str
    title: Optional[str]
    status: str
    message_count: int
    create_at: datetime
    last_message_at: datetime
    last_message: Optional[str]
    last_response: Optional[str]

    class Config:
        from_attributes = True

class SaveMessageRequest(BaseModel):
    user_message: str
    bot_response: str
    conversation_id: Optional[str] = None

class ChatStreamRequest(BaseModel):
    """스트리밍 채팅 요청 모델"""
    content: str
    conversation_id: Optional[str] = None

class PromptTemplateDeleteResponse(BaseModel):
    prompt_template_id: int
    deleted: bool