# apis/models/vocabulary.py
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum

class RuleType(str, Enum):
    REGULAR = "규칙"
    IRREGULAR = "불규칙"

class VocabularyMeaningCreate(BaseModel):
    """의미 생성 모델"""
    meaning: str
    classes: str = Field(default="기타")  # 기본값 설정
    example: str = Field(default="예문 없음")     # 기본값 설정
    parenthesis: Optional[str] = None

class VocabularyMeaning(BaseModel):
    """의미 응답 모델"""
    meaning_id: int
    vocabulary_id: int
    meaning: str
    classes: str
    example: str
    parenthesis: Optional[str] = None
    order_no: int
    create_at: datetime
    update_at: datetime

class VocabularyCreate(BaseModel):
    """단어 생성 모델"""
    word: str
    past_tense: Optional[str] = None      # null 허용
    past_participle: Optional[str] = None  # null 허용
    rule: RuleType = RuleType.REGULAR     # 기본값 '규칙'
    meanings: List[VocabularyMeaningCreate]

class VocabularyUpdate(BaseModel):
    """단어 수정 모델"""
    word: Optional[str] = None
    past_tense: Optional[str] = None
    past_participle: Optional[str] = None
    rule: Optional[RuleType] = None
    cycle: Optional[int] = None
    meanings: Optional[List[VocabularyMeaningCreate]] = None

class Vocabulary(BaseModel):
    """단어 응답 모델"""
    vocabulary_id: int
    word: str
    past_tense: Optional[str] = None
    past_participle: Optional[str] = None
    rule: RuleType
    cycle: int = 0
    create_at: datetime
    update_at: datetime
    meanings: List[VocabularyMeaning] = []