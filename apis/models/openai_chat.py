from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
    conversation_id: Optional[str] = None

    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    content: str
    conversation_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class ConversationHistory(BaseModel):
    conversation_id: str
    user_message: str
    bot_response: str
    create_at: datetime

    class Config:
        from_attributes = True
