# chat/chat_settings.py
from typing import Dict, Optional
import logging
from utils.mysql_connector import MySQLConnector
from utils.cache_manager import CacheManager
from chat.exceptions import DatabaseError, UserSettingsError
from chat.constants import CACHE_KEYS, DB_TABLES, CACHE_TTL, DEFAULT_CHAT_SETTINGS

logger = logging.getLogger(__name__)


class ChatSettingsManager:
    def __init__(self):
        self.db = MySQLConnector()
        self.cache = CacheManager()

    def get_user_settings(self, user_id: int) -> Optional[Dict]:
        """사용자 설정 조회"""
        if not user_id:
            raise UserSettingsError("User ID is required")

        try:
            cache_key = CACHE_KEYS["user_settings"].format(user_id=user_id)
            cached_data = self.cache.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for user settings: {user_id}")
                return cached_data

            query = f"""
            SELECT 
                user_id,
                default_prompt_template_id,
                model,
                temperature,
                max_tokens,
                create_at,
                update_at
            FROM {DB_TABLES['chat_settings']}
            WHERE user_id = %(user_id)s
            """

            result = self.db.execute_raw_query(query, {"user_id": user_id})
            if not result:
                logger.info(f"No settings found for user: {user_id}, using defaults")
                settings = DEFAULT_CHAT_SETTINGS.copy()
                settings['user_id'] = user_id
                return settings

            settings = result[0]
            self.cache.set(
                cache_key,
                settings,
                ttl=CACHE_TTL["user_settings"]
            )
            return settings

        except Exception as e:
            logger.error(f"사용자 설정 조회 오류: {str(e)}")
            if isinstance(e, UserSettingsError):
                raise
            raise DatabaseError(f"사용자 설정 조회 중 오류 발생: {str(e)}")

    def update_user_settings(self, user_id: int, settings_data: Dict) -> Dict:
        """사용자 설정 생성 또는 수정"""
        if not user_id:
            raise UserSettingsError("User ID is required")
        if not settings_data:
            raise UserSettingsError("Settings data cannot be empty")

        try:
            # 설정값 검증
            self._validate_settings(settings_data)

            self.db.begin_transaction()

            # 기존 설정 확인
            existing_settings = self.get_user_settings(user_id)
            has_existing = existing_settings and 'user_id' in existing_settings

            if has_existing:
                # 업데이트
                valid_fields = ['default_prompt_template_id', 'model', 'temperature', 'max_tokens']
                update_data = {
                    key: value
                    for key, value in settings_data.items()
                    if key in valid_fields and value is not None
                }

                if not update_data:
                    raise UserSettingsError("No valid fields to update")

                where = {"user_id": user_id}
                update_result = self.db.update(DB_TABLES['chat_settings'], update_data, where)
                if not update_result:
                    raise DatabaseError("Failed to update settings")
                logger.info(f"Updated settings for user: {user_id}")
            else:
                # 새로운 설정 생성
                insert_data = {
                    "user_id": user_id,
                    **settings_data
                }
                insert_result = self.db.insert(DB_TABLES['chat_settings'], insert_data)
                if not insert_result:
                    raise DatabaseError("Failed to create settings")
                logger.info(f"Created new settings for user: {user_id}")

            # 캐시 무효화
            self.invalidate_settings_cache(user_id)

            self.db.commit_transaction()

            # 업데이트된 설정 반환
            updated_settings = self.get_user_settings(user_id)
            if not updated_settings:
                raise DatabaseError("Failed to retrieve updated settings")
            return updated_settings

        except Exception as e:
            self.db.rollback_transaction()
            logger.error(f"사용자 설정 저장 오류: {str(e)}")
            if isinstance(e, (UserSettingsError, DatabaseError)):
                raise
            raise DatabaseError(f"사용자 설정 저장 중 오류 발생: {str(e)}")

    def _validate_settings(self, settings: Dict) -> None:
        """설정값 유효성 검사"""
        if not isinstance(settings, dict):
            raise UserSettingsError("Settings must be a dictionary")

        # 온도 검사
        if 'temperature' in settings:
            temp = settings['temperature']
            if not isinstance(temp, (int, float)):
                raise UserSettingsError("Temperature must be a number")
            if temp < 0 or temp > 1:
                raise UserSettingsError("Temperature must be between 0 and 1")

        # 최대 토큰 검사
        if 'max_tokens' in settings:
            tokens = settings['max_tokens']
            if not isinstance(tokens, int):
                raise UserSettingsError("Max tokens must be an integer")
            if tokens < 1 or tokens > 4000:
                raise UserSettingsError("Max tokens must be between 1 and 4000")

        # 모델 검사
        if 'model' in settings:
            model = settings['model']
            if not isinstance(model, str):
                raise UserSettingsError("Model must be a string")
            valid_models = ['gpt-4o-mini', 'gpt-4o']
            if model not in valid_models:
                raise UserSettingsError(f"Invalid model. Must be one of: {', '.join(valid_models)}")

        # 프롬프트 템플릿 ID 검사
        if 'default_prompt_template_id' in settings:
            template_id = settings['default_prompt_template_id']
            if template_id is not None:
                if not isinstance(template_id, int):
                    raise UserSettingsError("Prompt template ID must be an integer")
                if template_id < 1:
                    raise UserSettingsError("Invalid prompt template ID")

    def invalidate_settings_cache(self, user_id: int):
        """사용자 설정 캐시 무효화"""
        try:
            if not user_id:
                logger.warning("Cannot invalidate cache: user_id is required")
                return

            cache_key = CACHE_KEYS["user_settings"].format(user_id=user_id)
            self.cache.delete(cache_key)
        except Exception as e:
            logger.warning(f"캐시 무효화 중 오류 발생: {str(e)}")