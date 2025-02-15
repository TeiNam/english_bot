# chat/constants.py
from typing import Dict, Any

# 캐시 키 상수
CACHE_KEYS = {
    # 사용자 설정 관련
    "user_settings": "user_chat_settings:{user_id}",

    # 대화 관련
    "conversation_info": "conversation:{conversation_id}:info",
    "conversation_history": "conversation:{conversation_id}:history",
    "user_conversations": "user_conversations:{user_id}",

    # 프롬프트 템플릿 관련
    "prompt_templates": "prompt_templates:active",
    "prompt_template": "prompt_template:{template_id}",

    # 유사 표현 관련
    "similar_expressions": "similar_expressions:{query}:{limit}"
}

# Redis 캐시 TTL 설정
CACHE_TTL = {
    "user_settings": 3600,  # 1시간
    "conversation_info": 1800,  # 30분
    "conversation_history": 1800,  # 30분
    "user_conversations": 300,  # 5분
    "prompt_templates": 3600,  # 1시간
    "prompt_template": 3600,  # 1시간
    "similar_expressions": 300  # 5분
}

# 챗봇 기본 설정
DEFAULT_CHAT_SETTINGS: Dict[str, Any] = {
    "model": "gpt-4o-mini",
    "temperature": 0.7,
    "max_tokens": 1000,
    "default_prompt_template_id": None
}

# 데이터베이스 테이블명
DB_TABLES = {
    "chat_settings": "user_chat_setting",
    "chat_history": "chat_history",
    "conversation": "conversation_session",
    "prompt_template": "prompt_template",
    "small_talk": "small_talk"
}

# 기타 상수
MAX_SIMILAR_EXPRESSIONS = 5  # 유사 표현 검색 최대 개수
MAX_CONVERSATIONS = 50  # 사용자당 최대 대화 개수
MAX_HISTORY_PER_CONV = 100  # 대화당 최대 메시지 개수