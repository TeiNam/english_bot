from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class SectionType(str, Enum):
    GENERAL = "General-Topics"
    ROLEPLAY = "Role-Play"


class OpicBase(BaseModel):
    section: SectionType
    survey: str
    question: str


class OpicCreate(OpicBase):
    pass


class OpicUpdate(OpicBase):
    section: Optional[SectionType] = None
    survey: Optional[str] = None
    question: Optional[str] = None


class Opic(OpicBase):
    opic_id: int
    create_at: datetime
    update_at: datetime

    class Config:
        from_attributes = True


class OpicResponse(BaseModel):
    """페이지네이션 응답 모델"""
    items: List[Opic]
    total: int
    page: int
    size: int
    total_pages: int
    has_next: bool
    has_prev: bool
