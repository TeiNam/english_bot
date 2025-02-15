# chat/small_talk_manager.py
from typing import List, Dict
import logging
from utils.mysql_connector import MySQLConnector
from chat.exceptions import DatabaseError, SmallTalkError
from chat.constants import CACHE_KEYS, DB_TABLES, MAX_SIMILAR_EXPRESSIONS

logger = logging.getLogger(__name__)


class SmallTalkManager:
    def __init__(self):
        self.db = MySQLConnector()

    def search_similar_expressions(
            self,
            query: str,
            limit: int = 5
    ) -> List[Dict]:
        """FULLTEXT 검색을 사용하여 유사한 표현 검색"""
        if not query:
            raise SmallTalkError("Search query is required")
        if not isinstance(limit, int) or limit < 1:
            limit = MAX_SIMILAR_EXPRESSIONS

        try:
            search_query = f"""
            SELECT 
                talk_id,
                eng_sentence,
                kor_sentence,
                parenthesis,
                tag,
                MATCH(eng_sentence, kor_sentence, parenthesis, tag) 
                AGAINST(%(query)s IN NATURAL LANGUAGE MODE) as relevance
            FROM {DB_TABLES['small_talk']}
            WHERE MATCH(eng_sentence, kor_sentence, parenthesis, tag) 
                AGAINST(%(query)s IN NATURAL LANGUAGE MODE)
                AND eng_sentence IS NOT NULL
                AND eng_sentence != ''
            ORDER BY relevance DESC
            LIMIT %(limit)s
            """

            results = self.db.execute_raw_query(
                search_query,
                {'query': query, 'limit': min(limit, MAX_SIMILAR_EXPRESSIONS)}
            )

            if not results:
                logger.debug(f"No similar expressions found for query: {query}")
                return []

            # 필수 필드 검증
            validated_results = []
            for result in results:
                if self._validate_expression(result):
                    validated_results.append(result)

            logger.info(f"Found {len(validated_results)} similar expressions for query: {query}")
            return validated_results

        except Exception as e:
            logger.error(f"유사 표현 검색 오류: {str(e)}")
            if isinstance(e, SmallTalkError):
                raise
            raise DatabaseError(f"유사 표현 검색 중 오류 발생: {str(e)}")

    def _validate_expression(self, expression: Dict) -> bool:
        """표현의 유효성 검사"""
        required_fields = ['eng_sentence']

        # 필수 필드 존재 확인
        if not all(field in expression for field in required_fields):
            logger.warning(f"Missing required fields in expression: {expression.get('talk_id')}")
            return False

        # eng_sentence가 비어있지 않은지 확인
        if not expression['eng_sentence'] or not isinstance(expression['eng_sentence'], str):
            logger.warning(f"Invalid eng_sentence in expression: {expression.get('talk_id')}")
            return False

        return True

    @staticmethod
    def format_examples_context(examples: List[Dict]) -> str:
        """검색된 예문들을 컨텍스트 형식으로 포맷팅"""
        if not examples:
            return ""

        try:
            context = "\n[참고 가능한 실제 표현들]\n"
            for ex in examples:
                # 필수 필드 검증
                if not ex.get('eng_sentence'):
                    continue

                context += f"- English: {ex['eng_sentence']}\n"

                if ex.get('kor_sentence'):
                    context += f"  Korean: {ex['kor_sentence']}\n"
                if ex.get('parenthesis'):
                    context += f"  Note: {ex['parenthesis']}\n"
                if ex.get('tag'):
                    context += f"  Tag: {ex['tag']}\n"
                context += "\n"

            return context
        except Exception as e:
            logger.error(f"컨텍스트 포맷팅 오류: {str(e)}")
            return ""

    def add_expression(self, expression_data: Dict) -> Dict:
        """새로운 표현 추가"""
        if not expression_data:
            raise SmallTalkError("Expression data is required")

        try:
            # 필수 필드 검증
            required_fields = ['eng_sentence']
            missing_fields = [field for field in required_fields if not expression_data.get(field)]
            if missing_fields:
                raise SmallTalkError(f"Required fields missing: {', '.join(missing_fields)}")

            self.db.begin_transaction()

            insert_data = {
                "eng_sentence": expression_data["eng_sentence"],
                "kor_sentence": expression_data.get("kor_sentence"),
                "parenthesis": expression_data.get("parenthesis"),
                "tag": expression_data.get("tag")
            }

            insert_result = self.db.insert(DB_TABLES['small_talk'], insert_data)
            if not insert_result:
                raise DatabaseError("Failed to insert new expression")

            self.db.commit_transaction()
            logger.info(f"Added new expression: {insert_data['eng_sentence'][:50]}...")

            return {
                "talk_id": insert_result.get('id'),
                **insert_data
            }

        except Exception as e:
            self.db.rollback_transaction()
            logger.error(f"표현 추가 오류: {str(e)}")
            if isinstance(e, (SmallTalkError, DatabaseError)):
                raise
            raise DatabaseError(f"표현 추가 중 오류 발생: {str(e)}")

    def update_expression(self, talk_id: int, expression_data: Dict) -> Dict:
        """기존 표현 수정"""
        if not talk_id or not expression_data:
            raise SmallTalkError("Talk ID and expression data are required")

        try:
            self.db.begin_transaction()

            # 기존 표현 확인
            query = f"""
            SELECT * FROM {DB_TABLES['small_talk']}
            WHERE talk_id = %(talk_id)s
            """
            existing = self.db.execute_raw_query(query, {"talk_id": talk_id})
            if not existing:
                raise SmallTalkError(f"Expression not found: {talk_id}")

            # 업데이트할 필드만 선택
            valid_fields = ['eng_sentence', 'kor_sentence', 'parenthesis', 'tag']
            update_data = {
                key: value
                for key, value in expression_data.items()
                if key in valid_fields and value is not None
            }

            if not update_data:
                raise SmallTalkError("No valid fields to update")

            where = {"talk_id": talk_id}
            update_result = self.db.update(DB_TABLES['small_talk'], update_data, where)
            if not update_result:
                raise DatabaseError("Failed to update expression")

            self.db.commit_transaction()
            logger.info(f"Updated expression: {talk_id}")

            # 업데이트된 표현 반환
            updated_query = f"""
            SELECT * FROM {DB_TABLES['small_talk']}
            WHERE talk_id = %(talk_id)s
            """
            result = self.db.execute_raw_query(updated_query, {"talk_id": talk_id})
            if not result:
                raise DatabaseError("Failed to retrieve updated expression")

            return result[0]

        except Exception as e:
            self.db.rollback_transaction()
            logger.error(f"표현 수정 오류: {str(e)}")
            if isinstance(e, (SmallTalkError, DatabaseError)):
                raise
            raise DatabaseError(f"표현 수정 중 오류 발생: {str(e)}")