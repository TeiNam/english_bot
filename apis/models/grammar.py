from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class GrammarBase(BaseModel):
    title: str
    body: Optional[str] = None
    url: Optional[str] = None


class GrammarCreate(GrammarBase):
    pass


class GrammarUpdate(GrammarBase):
    title: Optional[str] = None
    body: Optional[str] = None
    url: Optional[str] = None


class Grammar(GrammarBase):
    grammar_id: int
    create_at: datetime
    update_at: datetime

    class Config:
        from_attributes = True


class GrammarResponse(BaseModel):
    """페이지네이션 응답 모델"""
    items: List[Grammar]
    total: int
    page: int
    size: int
    total_pages: int
    has_next: bool
    has_prev: bool
