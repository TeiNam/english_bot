# bots/openai_bot.py
import logging
from typing import List, Dict, Optional, Tuple

from openai import AsyncOpenAI

from chat.chat_settings import ChatSettingsManager
from chat.exceptions import OpenAIError
from chat.prompt_manager import PromptManager
from configs.openai_setting import get_openai_settings

logger = logging.getLogger(__name__)


class OpenAIBot:
    def __init__(self):
        settings = get_openai_settings()
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.base_model = settings.MODEL_NAME
        self.base_temperature = settings.TEMPERATURE
        self.base_max_tokens = settings.MAX_TOKENS
        self.prompt_manager = PromptManager()
        self.chat_settings_manager = ChatSettingsManager()

    def _get_user_settings(self, user_id: int) -> Dict:
        """사용자별 설정 조회"""
        try:
            # ChatSettingsManager를 통해 사용자 설정 조회
            # 설정이 없는 경우 기본값 반환됨
            return self.chat_settings_manager.get_user_settings(user_id)
        except Exception as e:
            logger.error(f"사용자 설정 조회 실패: {str(e)}")
            # 오류 발생시 기본 설정 반환
            return {
                'model': self.base_model,
                'temperature': self.base_temperature,
                'max_tokens': self.base_max_tokens,
                'default_prompt_template_id': None
            }

    def _prepare_messages(self, user_message: str, user_id: int) -> Tuple[List[Dict], Dict]:
        """대화 메시지 준비"""
        # 사용자 설정 조회
        user_settings = self._get_user_settings(user_id)

        # 프롬프트 템플릿 조회
        template = None
        if user_settings.get('default_prompt_template_id'):
            template = self.prompt_manager.get_template_by_id(
                user_settings['default_prompt_template_id']
            )

        # 기본 템플릿이 없는 경우 첫 번째 활성 템플릿 사용
        if not template:
            templates = self.prompt_manager.get_all_templates()
            if not templates:
                raise OpenAIError("No active prompt template found")
            template = templates[0]

        messages = [
            {"role": "system", "content": template['system_prompt']},
            {"role": "user", "content": template['user_prompt'].format(user_input=user_message)}
        ]
        return messages, user_settings

    async def generate_stream(self, user_message: str, user_id: int, conversation_id: Optional[str] = None) -> str:
        """스트리밍 방식으로 응답 생성"""
        try:
            # 메시지와 설정 준비
            messages, user_settings = self._prepare_messages(user_message, user_id)

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

            return full_response

        except Exception as e:
            logger.error(f"응답 생성 중 오류 발생: {str(e)}")
            if isinstance(e, OpenAIError):
                raise
            raise OpenAIError(f"응답 생성 실패: {str(e)}")
