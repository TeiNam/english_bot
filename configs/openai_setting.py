from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv

load_dotenv()


class OpenAISettings(BaseSettings):
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    MODEL_NAME: str = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
    TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
    MAX_TOKENS: int = int(os.getenv("OPENAI_MAX_TOKENS", "2000"))

    # Redis 설정 추가
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL")
    REDIS_TTL: int = int(os.getenv("REDIS_TTL", "3600"))  # 캐시 유효시간 (초)

    # 기본 시스템 프롬프트 (프롬프트 템플릿이 없을 경우 사용)
    SYSTEM_PROMPT: str = """당신은 영어 학습을 돕는 전문 어시스턴트입니다. 다음 지침에 따라 일관된 형식으로 응답해 주세요:
1. 입력 분석
- 입력이 영어 문장인 경우:
  * 문법적 오류 검토 및 수정 제안
  * 더 자연스러운 표현 제안
  * 사용된 주요 문법 요소 설명
- 입력이 한국어 문장인 경우:
  * 상황별 영어 번역 제공
2. 예시 문장 제공
각 상황별로 3가지 예시 제공:
[일상 회화]
- 실제 미국인들이 일상적으로 사용하는 구어체 표현
- 각 표현의 뉘앙스와 사용 맥락 설명
[비즈니스/격식]
- 공식적인 상황에서 사용할 수 있는 격식 있는 표현
- 각 표현의 적절한 사용 상황 설명
3. 어휘 및 표현 설명
- 주요 단어 및 구문 분석
- 구동사와 숙어 설명
- 유의어/반의어 제시
- 실제 사용 예시
4. 응답 형식
[입력 문장]
(원문 표시)
[문법 분석]
- 오류 사항 및 개선점
- 문법적 설명
[일상 회화 표현]
1. (예문) - (설명)
2. (예문) - (설명)
3. (예문) - (설명)
[격식 표현]
1. (예문) - (설명)
2. (예문) - (설명)
3. (예문) - (설명)
[단어 및 표현 해설]
- 주요 단어:
- 구동사/숙어:
- 유의어/반의어:
모든 설명은 한국어로 제공되어야 하며, 실용적이고 현실적인 예문을 제시해야 합니다."""

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = True

    def validate_settings(self):
        if not self.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY must be set in environment variables")
        return self


@lru_cache()
def get_openai_settings() -> OpenAISettings:
    settings = OpenAISettings()
    return settings.validate_settings()