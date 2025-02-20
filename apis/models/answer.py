# apis/models/answer.py
from datetime import datetime

from pydantic import BaseModel, Field


class AnswerBase(BaseModel):
    eng_sentence: str = Field(..., description="영어 답변")
    kor_sentence: str = Field(..., description="한국어 답변")


class AnswerCreate(AnswerBase):
    talk_id: int = Field(..., description="스몰톡 ID")


class AnswerUpdate(AnswerBase):
    pass


class Answer(AnswerBase):
    answer_id: int
    talk_id: int
    update_at: datetime

    class Config:
        from_attributes = True
