# apis/models/small_talk.py
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class Answer(BaseModel):
    answer_id: int
    eng_sentence: str
    kor_sentence: str
    update_at: datetime


class SmallTalkBase(BaseModel):
    eng_sentence: str = Field(..., description="영어 문장")
    kor_sentence: str = Field(..., description="한국어 문장")
    parenthesis: Optional[str] = Field(None, description="부가 설명")
    tag: Optional[str] = Field(None, description="태그")


class SmallTalkCreate(SmallTalkBase):
    pass


class SmallTalkUpdate(SmallTalkBase):
    pass


class SmallTalkPatch(BaseModel):
    eng_sentence: Optional[str] = None
    kor_sentence: Optional[str] = None
    parenthesis: Optional[str] = None
    tag: Optional[str] = None


class SmallTalk(SmallTalkBase):
    talk_id: int
    create_at: datetime
    update_at: datetime
    answers: List[Answer] = []

    class Config:
        from_attributes = True
