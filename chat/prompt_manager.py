# chat/prompt_manager.py
import logging
from typing import List, Dict, Optional

from chat.constants import CACHE_KEYS, DB_TABLES, CACHE_TTL
from chat.exceptions import DatabaseError, PromptTemplateError
from utils.cache_manager import CacheManager
from utils.mysql_connector import MySQLConnector

logger = logging.getLogger(__name__)


class PromptManager:
    def __init__(self):
        self.db = MySQLConnector()
        self.cache = CacheManager()

    def get_template_by_id(self, template_id: int) -> Optional[Dict]:
        """특정 프롬프트 템플릿 조회 (활성/비활성 상관없이)"""
        try:
            cache_key = CACHE_KEYS["prompt_template"].format(template_id=template_id)
            cached_data = self.cache.get(cache_key)
            if cached_data:
                return cached_data

            query = f"""
            SELECT 
                prompt_template_id,
                name,
                description,
                system_prompt,
                user_prompt,
                is_active,
                create_at,
                update_at
            FROM {DB_TABLES['prompt_template']}
            WHERE prompt_template_id = %(template_id)s
            """
            result = self.db.execute_raw_query(query, {"template_id": template_id})
            if not result:
                logger.debug(f"No template found for ID: {template_id}")
                return None

            template = result[0]
            self.cache.set(cache_key, template, ttl=CACHE_TTL["prompt_template"])
            return template

        except Exception as e:
            logger.error(f"프롬프트 템플릿 조회 오류: {str(e)}")
            raise DatabaseError(f"프롬프트 템플릿 조회 중 오류 발생: {str(e)}")

    def get_all_templates(self) -> List[Dict]:
        """모든 프롬프트 템플릿 조회 (활성/비활성 모두 포함)"""
        try:
            cache_key = CACHE_KEYS["prompt_templates"]
            cached_data = self.cache.get(cache_key)
            if cached_data:
                return cached_data

            query = f"""
            SELECT 
                prompt_template_id,
                name,
                description,
                system_prompt,
                user_prompt,
                is_active,
                create_at,
                update_at
            FROM {DB_TABLES['prompt_template']}
            ORDER BY prompt_template_id
            """
            templates = self.db.execute_raw_query(query)
            if not templates:
                logger.debug("No templates found")
                return []

            self.cache.set(cache_key, templates, ttl=CACHE_TTL["prompt_templates"])
            return templates

        except Exception as e:
            logger.error(f"프롬프트 템플릿 목록 조회 오류: {str(e)}")
            raise DatabaseError(f"프롬프트 템플릿 목록 조회 중 오류 발생: {str(e)}")

    def create_template(self, template_data: Dict) -> Dict:
        """새로운 프롬프트 템플릿 생성"""
        try:
            if not template_data:
                raise PromptTemplateError("Template data cannot be empty")

            # 필수 필드 검증
            required_fields = ['name', 'system_prompt', 'user_prompt']
            missing_fields = [field for field in required_fields if not template_data.get(field)]
            if missing_fields:
                raise PromptTemplateError(f"필수 필드가 누락되었습니다: {', '.join(missing_fields)}")

            self.db.begin_transaction()

            insert_data = {
                "name": template_data["name"],
                "description": template_data.get("description"),
                "system_prompt": template_data["system_prompt"],
                "user_prompt": template_data["user_prompt"],
                "is_active": template_data.get("is_active", "Y")
            }

            insert_result = self.db.insert(DB_TABLES['prompt_template'], insert_data)
            if not insert_result:
                raise DatabaseError("Failed to insert new template")

            # 방금 생성된 템플릿 조회
            query = f"""
            SELECT 
                prompt_template_id,
                name,
                description,
                system_prompt,
                user_prompt,
                is_active,
                create_at,
                update_at
            FROM {DB_TABLES['prompt_template']}
            WHERE name = %(name)s
            ORDER BY create_at DESC
            LIMIT 1
            """
            result = self.db.execute_raw_query(query, {"name": template_data["name"]})
            if not result:
                raise DatabaseError("Failed to retrieve created template")

            template = result[0]

            # 캐시 무효화
            self.invalidate_template_cache()

            self.db.commit_transaction()
            logger.info(f"Created new template: {template['name']} (ID: {template['prompt_template_id']})")

            return template

        except Exception as e:
            self.db.rollback_transaction()
            logger.error(f"프롬프트 템플릿 생성 오류: {str(e)}")
            if isinstance(e, (PromptTemplateError, DatabaseError)):
                raise
            raise DatabaseError(f"프롬프트 템플릿 생성 중 오류 발생: {str(e)}")

    def update_template(self, template_id: int, template_data: Dict) -> Dict:
        """프롬프트 템플릿 수정 (활성/비활성 상태 변경 포함)"""
        try:
            if not template_data:
                raise PromptTemplateError("Update data cannot be empty")

            self.db.begin_transaction()

            # 기존 템플릿 확인 (활성/비활성 상관없이 조회)
            existing = self.get_template_by_id(template_id)
            if not existing:
                raise PromptTemplateError(f"Template not found: {template_id}")

            valid_fields = ['name', 'description', 'system_prompt', 'user_prompt', 'is_active']
            update_data = {
                key: value
                for key, value in template_data.items()
                if key in valid_fields and value is not None
            }

            if not update_data:
                raise PromptTemplateError("No valid fields to update")

            where = {"prompt_template_id": template_id}
            update_result = self.db.update(DB_TABLES['prompt_template'], update_data, where)
            if not update_result:
                raise DatabaseError("Failed to update template")

            self.invalidate_template_cache(template_id)
            self.db.commit_transaction()
            logger.info(f"Updated template ID: {template_id}")

            updated = self.get_template_by_id(template_id)
            if not updated:
                raise DatabaseError("Failed to retrieve updated template")
            return updated

        except Exception as e:
            self.db.rollback_transaction()
            logger.error(f"프롬프트 템플릿 수정 오류: {str(e)}")
            if isinstance(e, (PromptTemplateError, DatabaseError)):
                raise
            raise DatabaseError(f"프롬프트 템플릿 수정 중 오류 발생: {str(e)}")

    def delete_template(self, template_id: int) -> dict:
        """프롬프트 템플릿 삭제 (실제 로우 삭제)"""
        template = self.get_template_by_id(template_id)
        if not template:
            raise PromptTemplateError(f"Prompt template not found: {template_id}")

        self.db.begin_transaction()
        try:
            # 실제 삭제: DELETE 쿼리 실행
            delete_result = self.db.delete(DB_TABLES['prompt_template'], {"prompt_template_id": template_id})
            if not delete_result:
                raise DatabaseError("Failed to delete prompt template")

            self.invalidate_template_cache(template_id)
            self.db.commit_transaction()
            logger.info(f"Deleted template: {template_id}")
            return {"prompt_template_id": template_id, "deleted": True}

        except Exception as e:
            self.db.rollback_transaction()
            logger.error(f"프롬프트 템플릿 삭제 오류: {str(e)}")
            raise DatabaseError(f"프롬프트 템플릿 삭제 중 오류 발생: {str(e)}")

    def invalidate_template_cache(self, template_id: Optional[int] = None):
        """프롬프트 템플릿 캐시 무효화"""
        try:
            self.cache.delete(CACHE_KEYS["prompt_templates"])
            if template_id:
                self.cache.delete(CACHE_KEYS["prompt_template"].format(template_id=template_id))
        except Exception as e:
            logger.warning(f"캐시 무효화 중 오류 발생: {str(e)}")


# 외부 모듈에서 PromptException을 참조할 수 있도록 별칭 제공
PromptException = PromptTemplateError
