# apis/models/vocabulary.py
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class RuleType(str, Enum):
    """단어 규칙성 타입 Enum"""
    REGULAR = "규칙"
    IRREGULAR = "불규칙"
    NO_RULE = "규칙없음"  # 테이블 정의에 맞게 추가


class VocabularyMeaningCreate(BaseModel):
    """의미 생성 모델"""
    meaning: str
    classes: str = Field(default="기타")  # 기본값 설정
    example: str = Field(default="예문 없음")  # 기본값 설정
    parenthesis: Optional[str] = None

    @field_validator('classes')
    @classmethod
    def validate_classes(cls, v: str) -> str:
        """'분류없음'을 '기타'로 변환"""
        if not v or v == "" or v == "분류없음":
            return "기타"
        return v


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
    past_tense: Optional[str] = None  # null 허용
    past_participle: Optional[str] = None  # null 허용
    rule: RuleType = RuleType.NO_RULE  # 기본값 '규칙없음'으로 변경
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