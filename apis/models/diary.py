from pydantic import BaseModel, ConfigDict, field_validator
from datetime import date, datetime
from typing import Optional


class DiaryCreate(BaseModel):
    date: date  # date 타입 유지
    body: str

    @field_validator('body')
    @classmethod
    def body_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('body must not be empty')
        return v.strip()

    @field_validator('date', mode='before')
    @classmethod
    def validate_date(cls, v: str) -> date:
        """문자열을 date 객체로 변환"""
        if isinstance(v, date):
            return v
        try:
            return datetime.strptime(v, '%Y-%m-%d').date()
        except ValueError:
            raise ValueError('Invalid date format. Use YYYY-MM-DD')

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "date": "2025-02-16",
                "body": "Today I learned..."
            }
        }
    )

class DiaryUpdate(BaseModel):
    body: str
    feedback: Optional[str] = None

    @field_validator('body')
    @classmethod
    def body_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('body must not be empty')
        return v.strip()

class DiaryResponse(BaseModel):
    diary_id: int
    date: date  # date 타입 유지
    body: str
    feedback: Optional[str] = None
    create_at: datetime
    update_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            date: lambda d: d.isoformat(),  # date를 YYYY-MM-DD 문자열로 변환
            datetime: lambda dt: dt.isoformat()  # datetime을 ISO 형식 문자열로 변환
        }
    )