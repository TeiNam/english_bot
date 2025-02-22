# bots/openai_bot.py
import hashlib
import json
import logging
from typing import List, Dict, Optional, Tuple, Any

from openai import AsyncOpenAI

from chat.chat_settings import ChatSettingsManager
from chat.exceptions import OpenAIError
from chat.prompt_manager import PromptManager
from configs.openai_setting import get_openai_settings
from utils.cache_manager import CacheManager

logger = logging.getLogger(__name__)


class OpenAIBot:
    def __init__(self, cache_manager: Optional[CacheManager] = None):
        settings = get_openai_settings()
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.base_model = settings.MODEL_NAME
        self.base_temperature = settings.TEMPERATURE
        self.base_max_tokens = settings.MAX_TOKENS
        self.prompt_manager = PromptManager()
        self.chat_settings_manager = ChatSettingsManager()

        # 캐시 매니저 초기화
        self.cache_manager = cache_manager or CacheManager(
            redis_url=settings.REDIS_URL,
            ttl=settings.CACHE_TTL if hasattr(settings, 'CACHE_TTL') else 3600
        )
        self.cache_enabled = getattr(settings, 'ENABLE_RESPONSE_CACHE', True)

        # 캐시 접두사 및 TTL 설정
        self.cache_prefix = "openai_response:"
        self.conversation_cache_prefix = "openai_conversation:"

    def _get_user_settings(self, user_id: int) -> Dict:
        """사용자별 설정 조회"""
        # 캐시 키 생성
        cache_key = f"user_settings:{user_id}"

        # 캐시에서 설정 조회
        if self.cache_manager.is_available:
            cached_settings = self.cache_manager.get(cache_key)
            if cached_settings:
                return cached_settings

        try:
            # ChatSettingsManager를 통해 사용자 설정 조회
            # 설정이 없는 경우 기본값 반환됨
            settings = self.chat_settings_manager.get_user_settings(user_id)

            # 캐시에 저장 (TTL 1시간)
            if self.cache_manager.is_available:
                self.cache_manager.set(cache_key, settings, ttl=3600)

            return settings
        except Exception as e:
            logger.error(f"사용자 설정 조회 실패: {str(e)}")
            # 오류 발생시 기본 설정 반환
            default_settings = {
                'model': self.base_model,
                'temperature': self.base_temperature,
                'max_tokens': self.base_max_tokens,
                'default_prompt_template_id': None
            }

            return default_settings

    def _get_template(self, template_id: Optional[int] = None) -> Dict:
        """템플릿 조회 (캐시 적용)"""
        if not template_id:
            # 기본 템플릿이 없는 경우 첫 번째 활성 템플릿 사용
            cache_key = "default_template"
        else:
            cache_key = f"template:{template_id}"

        # 캐시에서 템플릿 조회
        if self.cache_manager.is_available:
            cached_template = self.cache_manager.get(cache_key)
            if cached_template:
                return cached_template

        try:
            if template_id:
                template = self.prompt_manager.get_template_by_id(template_id)
            else:
                templates = self.prompt_manager.get_all_templates()
                if not templates:
                    raise OpenAIError("No active prompt template found")
                template = templates[0]

            # 캐시에 저장 (TTL 1일)
            if self.cache_manager.is_available:
                self.cache_manager.set(cache_key, template, ttl=86400)

            return template
        except Exception as e:
            logger.error(f"템플릿 조회 실패: {str(e)}")
            raise OpenAIError(f"템플릿 조회 실패: {str(e)}")

    def _prepare_messages(self, user_message: str, user_id: int) -> Tuple[List[Dict], Dict]:
        """대화 메시지 준비"""
        # 사용자 설정 조회
        user_settings = self._get_user_settings(user_id)

        # 프롬프트 템플릿 조회
        template = self._get_template(user_settings.get('default_prompt_template_id'))

        messages = [
            {"role": "system", "content": template['system_prompt']},
            {"role": "user", "content": template['user_prompt'].format(user_input=user_message)}
        ]
        return messages, user_settings

    def _generate_cache_key(self, user_message: str, user_id: int, model: str, temperature: float) -> str:
        """캐시 키 생성"""
        # 사용자 설정 조회
        user_settings = self._get_user_settings(user_id)

        # 캐시 키 구성 요소
        key_components = {
            "message": user_message,
            "user_id": user_id,
            "model": model,
            "temperature": temperature,
            "template_id": user_settings.get('default_prompt_template_id')
        }

        # 해시 생성
        key_str = json.dumps(key_components, sort_keys=True)
        hashed = hashlib.md5(key_str.encode()).hexdigest()

        return f"{self.cache_prefix}{hashed}"

    def _get_conversation_cache_key(self, conversation_id: str) -> str:
        """대화 ID에 대한 캐시 키 생성"""
        return f"{self.conversation_cache_prefix}{conversation_id}"

    async def get_cached_response(self, cache_key: str) -> Optional[str]:
        """캐시에서 응답 조회"""
        if not self.cache_enabled or not self.cache_manager.is_available:
            return None

        try:
            return self.cache_manager.get(cache_key)
        except Exception as e:
            logger.warning(f"캐시 조회 중 오류 발생: {str(e)}")
            return None

    async def cache_response(self, cache_key: str, response: str, ttl: Optional[int] = None) -> None:
        """응답을 캐시에 저장"""
        if not self.cache_enabled or not self.cache_manager.is_available:
            return

        try:
            self.cache_manager.set(cache_key, response, ttl=ttl)
        except Exception as e:
            logger.warning(f"캐시 저장 중 오류 발생: {str(e)}")

    async def update_conversation_cache(self, conversation_id: str, user_message: str, ai_response: str) -> None:
        """대화 기록 캐시 업데이트"""
        if not conversation_id or not self.cache_manager.is_available:
            return

        try:
            cache_key = self._get_conversation_cache_key(conversation_id)
            conversation = self.cache_manager.get(cache_key) or []

            # 대화 기록 추가
            conversation.append({
                "role": "user",
                "content": user_message
            })
            conversation.append({
                "role": "assistant",
                "content": ai_response
            })

            # 캐시에 저장 (TTL 1일)
            self.cache_manager.set(cache_key, conversation, ttl=86400)
        except Exception as e:
            logger.warning(f"대화 기록 캐시 업데이트 중 오류 발생: {str(e)}")

    async def generate_stream(self, user_message: str, user_id: int, conversation_id: Optional[str] = None) -> str:
        """스트리밍 방식으로 응답 생성 (캐시 적용)"""
        try:
            # 메시지와 설정 준비
            messages, user_settings = self._prepare_messages(user_message, user_id)

            # 캐시 키 생성
            cache_key = self._generate_cache_key(
                user_message,
                user_id,
                user_settings['model'],
                user_settings['temperature']
            )

            # 캐시에서 응답 조회
            cached_response = await self.get_cached_response(cache_key)
            if cached_response:
                logger.info(f"캐시에서 응답 반환 (키: {cache_key})")

                # 대화 기록 업데이트 (캐시 히트도 기록)
                if conversation_id:
                    await self.update_conversation_cache(conversation_id, user_message, cached_response)

                return cached_response

            # OpenAI API 호출
            response = await self.client.chat.completions.create(
                model=user_settings['model'],
                messages=messages,
                stream=True,
                temperature=user_settings['temperature'],
                max_tokens=user_settings['max_tokens']
            )

            # 전체 응답 수집
            full_response = ""
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content

            if not full_response:
                raise OpenAIError("Empty response from OpenAI")

            # 응답 캐싱
            ttl = getattr(user_settings, 'cache_ttl', None)  # 사용자 별 TTL 설정이 있으면 사용
            await self.cache_response(cache_key, full_response, ttl)

            # 대화 기록 업데이트
            if conversation_id:
                await self.update_conversation_cache(conversation_id, user_message, full_response)

            return full_response

        except Exception as e:
            logger.error(f"응답 생성 중 오류 발생: {str(e)}")
            if isinstance(e, OpenAIError):
                raise
            raise OpenAIError(f"응답 생성 실패: {str(e)}")

    async def invalidate_user_cache(self, user_id: int) -> bool:
        """사용자 관련 캐시 무효화"""
        if not self.cache_manager.is_available:
            return False

        try:
            # 사용자 설정 캐시 삭제
            self.cache_manager.delete(f"user_settings:{user_id}")

            # 사용자 응답 캐시 패턴 삭제
            pattern = f"{self.cache_prefix}*user_id\":{user_id}*"
            self.cache_manager.delete_pattern(pattern)

            return True
        except Exception as e:
            logger.error(f"사용자 캐시 무효화 중 오류 발생: {str(e)}")
            return False

    async def invalidate_conversation_cache(self, conversation_id: str) -> bool:
        """대화 기록 캐시 무효화"""
        if not self.cache_manager.is_available:
            return False

        try:
            cache_key = self._get_conversation_cache_key(conversation_id)
            self.cache_manager.delete(cache_key)
            return True
        except Exception as e:
            logger.error(f"대화 기록 캐시 무효화 중 오류 발생: {str(e)}")
            return False