import os
from functools import lru_cache
from typing import Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# 환경변수 로드
load_dotenv()


class OpenAISettings(BaseSettings):
    # Required OpenAI settings
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
    MODEL_NAME: str = os.getenv('OPENAI_MODEL_NAME', 'gpt-4')
    TEMPERATURE: float = float(os.getenv('OPENAI_TEMPERATURE', '0.7'))
    MAX_TOKENS: int = int(os.getenv('OPENAI_MAX_TOKENS', '2000'))

    # Redis settings (optional)
    REDIS_URL: Optional[str] = os.getenv('REDIS_URL')
    REDIS_TTL: int = int(os.getenv('REDIS_TTL', '3600'))

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        case_sensitive=True,
        extra='allow'
    )

    def validate_settings(self):
        if not self.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY must be set in environment variables")
        return self


@lru_cache()
def get_openai_settings() -> OpenAISettings:
    """OpenAI 설정을 가져오는 함수"""
    try:
        settings = OpenAISettings()
        return settings.validate_settings()
    except Exception as e:
        raise Exception(f"Failed to load OpenAI settings: {str(e)}")
