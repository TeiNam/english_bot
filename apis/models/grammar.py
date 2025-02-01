#apis/models/grammar.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, HttpUrl

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