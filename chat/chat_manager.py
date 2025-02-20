# chat/chat_manager.py
import logging
from datetime import datetime
from typing import Dict, List, Optional

from chat.constants import CACHE_KEYS, DB_TABLES, CACHE_TTL, MAX_HISTORY_PER_CONV, MAX_CONVERSATIONS
from chat.exceptions import (
    ChatBaseException,
    DatabaseError,
    ConversationNotFound
)
from utils.cache_manager import CacheManager
from utils.mysql_connector import MySQLConnector

logger = logging.getLogger(__name__)


class ChatManager:
    def __init__(self):
        self.db = MySQLConnector()
        self.cache = CacheManager()

    def get_user_conversations(self, user_id: int) -> List[Dict]:
        """사용자의 대화 목록 조회"""
        if not user_id:
            logger.error("User ID is required")
            raise ChatBaseException("User ID is required")

        try:
            logger.debug(f"Attempting to get conversations for user: {user_id}")

            # 캐시 확인
            cache_key = CACHE_KEYS["user_conversations"].format(user_id=user_id)
            cached_data = self.cache.get(cache_key)
            if cached_data:
                logger.debug(f"Returning cached conversations for user: {user_id}")
                return cached_data

            # 기본 쿼리 - 최신 대화 목록만 조회
            base_query = f"""
                SELECT 
                    cs.conversation_id,
                    cs.title,
                    cs.status,
                    cs.message_count,
                    cs.create_at,
                    cs.last_message_at,
                    COALESCE(ch.user_message, '') as last_message,
                    COALESCE(ch.bot_response, '') as last_response
                FROM {DB_TABLES['conversation']} cs
                LEFT JOIN (
                    SELECT 
                        conversation_id,
                        user_message,
                        bot_response,
                        create_at,
                        ROW_NUMBER() OVER (PARTITION BY conversation_id ORDER BY create_at DESC) as rn
                    FROM {DB_TABLES['chat_history']}
                ) ch ON cs.conversation_id = ch.conversation_id AND ch.rn = 1
                WHERE cs.user_id = %(user_id)s
                AND cs.status != 'deleted'
                ORDER BY cs.last_message_at DESC
                LIMIT {MAX_CONVERSATIONS}
            """

            logger.debug(f"Executing query for user: {user_id}")
            conversations = self.db.execute_raw_query(base_query, {"user_id": user_id})

            if not conversations:
                logger.info(f"No conversations found for user: {user_id}")
                return []

            # datetime 객체 처리
            for conv in conversations:
                if isinstance(conv['create_at'], datetime):
                    conv['create_at'] = conv['create_at'].replace(tzinfo=None)
                if isinstance(conv['last_message_at'], datetime):
                    conv['last_message_at'] = conv['last_message_at'].replace(tzinfo=None)

            logger.info(f"Found {len(conversations)} conversations for user: {user_id}")

            # 캐시 저장
            self.cache.set(
                cache_key,
                conversations,
                ttl=CACHE_TTL["user_conversations"]
            )

            return conversations

        except Exception as e:
            error_msg = f"Error getting conversations for user {user_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise DatabaseError(error_msg)

    async def get_conversation_info(self, conversation_id: str) -> Optional[Dict]:
        """대화 세션 정보 조회"""
        if not conversation_id:
            raise ConversationNotFound("Conversation ID is required")

        try:
            # 캐시 확인
            cache_key = CACHE_KEYS["conversation_info"].format(conversation_id=conversation_id)
            cached_data = self.cache.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for conversation: {conversation_id}")
                return cached_data

            # DB 조회
            query = f"""
                SELECT 
                    conversation_id,
                    user_id,
                    title,
                    status,
                    message_count,
                    create_at,
                    last_message_at
                FROM {DB_TABLES['conversation']}                WHERE conversation_id = %(conversation_id)s
                AND status != 'deleted'
            """
            result = self.db.execute_raw_query(query, {"conversation_id": conversation_id})

            if not result:
                logger.warning(f"Conversation not found: {conversation_id}")
                raise ConversationNotFound(f"대화를 찾을 수 없습니다: {conversation_id}")

            conversation = result[0]

            # 캐시 저장
            self.cache.set(
                cache_key,
                conversation,
                ttl=CACHE_TTL["conversation_info"]
            )
            return conversation

        except ConversationNotFound:
            raise
        except Exception as e:
            logger.error(f"대화 세션 조회 오류: {str(e)}")
            raise DatabaseError(f"대화 세션 조회 중 오류 발생: {str(e)}")

    def create_conversation(self, user_id: int) -> Dict:
        """새 대화 세션 생성"""
        if not user_id:
            raise ChatBaseException("User ID is required")

        try:
            # 기존 대화 세션 수 확인
            count_query = f"""
                SELECT COUNT(*) as count
                FROM {DB_TABLES['conversation']}            WHERE user_id = %(user_id)s
                AND status != 'deleted'
            """
            count_result = self.db.execute_raw_query(count_query, {"user_id": user_id})
            if count_result and count_result[0]['count'] >= MAX_CONVERSATIONS:
                raise ChatBaseException("Maximum number of conversations reached")

            # 현재 시간 설정
            current_time = datetime.utcnow()

            # 새 대화 세션 생성 쿼리 - uuid_short() 사용
            insert_query = f"""
                INSERT INTO {DB_TABLES['conversation']} 
                (user_id, title, status, message_count, create_at, last_message_at)
                VALUES (%(user_id)s, %(title)s, %(status)s, %(message_count)s, %(create_at)s, %(last_message_at)s)
            """

            # 데이터 준비
            conv_data = {
                "user_id": user_id,
                "title": "New Conversation",
                "status": "active",
                "message_count": 0,
                "create_at": current_time,
                "last_message_at": current_time
            }

            # INSERT 실행
            self.db.execute_raw_query(insert_query, conv_data)

            # 방금 생성된 conversation 조회
            select_query = f"""
                SELECT *
                FROM {DB_TABLES['conversation']}            WHERE user_id = %(user_id)s
                AND create_at = %(create_at)s
                LIMIT 1
            """
            select_params = {
                "user_id": user_id,
                "create_at": current_time
            }

            result = self.db.execute_raw_query(select_query, select_params)

            if not result:
                raise DatabaseError("Failed to get created conversation")

            conversation = result[0]
            conv_id = conversation['conversation_id']

            # 캐시 무효화
            self.invalidate_conversation_cache(conv_id, user_id)

            logger.info(f"Created new conversation: {conv_id} for user: {user_id}")

            return {
                "conversation_id": conv_id,
                "title": conversation["title"],
                "status": conversation["status"],
                "message_count": conversation["message_count"],
                "create_at": conversation["create_at"],
                "last_message_at": conversation["last_message_at"]
            }

        except Exception as e:
            logger.error(f"대화 생성 오류: {str(e)}")
            if isinstance(e, ChatBaseException):
                raise
            raise DatabaseError(f"대화 생성 중 오류 발생: {str(e)}")

    def get_chat_history(self, conversation_id: str) -> List[Dict]:
        """대화 내역 조회"""
        if not conversation_id:
            raise ChatBaseException("Conversation ID is required")

        try:
            cache_key = CACHE_KEYS["conversation_history"].format(conversation_id=conversation_id)
            cached_data = self.cache.get(cache_key)
            if cached_data:
                return cached_data

            query = f"""
                SELECT 
                    chat_history_id, 
                    conversation_id, 
                    user_id, 
                    user_message, 
                    bot_response, 
                    create_at
                FROM {DB_TABLES['chat_history']}
                WHERE conversation_id = %(conversation_id)s
                ORDER BY create_at ASC
                LIMIT {MAX_HISTORY_PER_CONV}
            """
            history = self.db.execute_raw_query(query, {"conversation_id": conversation_id})
            if history:
                self.cache.set(
                    cache_key,
                    history,
                    ttl=CACHE_TTL["conversation_history"]
                )
                logger.info(f"Retrieved {len(history)} messages for conversation: {conversation_id}")
            return history or []

        except Exception as e:
            logger.error(f"대화 내역 조회 오류: {str(e)}")
            raise DatabaseError(f"대화 내역 조회 중 오류 발생: {str(e)}")

    async def save_message(self, user_id: int, user_message: str, bot_response: str,
                           conversation_id: Optional[str] = None) -> Dict:
        """대화 메시지 저장"""
        if not user_id:
            raise ChatBaseException("User ID is required")
        if not user_message:
            raise ChatBaseException("User message is required")

        try:
            # 새 대화 생성이 필요한 경우
            current_conversation_id = conversation_id
            if not current_conversation_id:
                # 대화 생성 쿼리
                insert_query = f"""
                    INSERT INTO {DB_TABLES['conversation']} 
                    (user_id, title, status, message_count, create_at, last_message_at)
                    VALUES (%(user_id)s, %(title)s, %(status)s, %(message_count)s, %(create_at)s, %(last_message_at)s)
                """
                current_time = datetime.utcnow()
                conv_data = {
                    "user_id": user_id,
                    "title": user_message[:50],  # 제목은 메시지 앞부분으로
                    "status": "active",
                    "message_count": 1,
                    "create_at": current_time,
                    "last_message_at": current_time
                }

                # INSERT 실행
                self.db.execute_raw_query(insert_query, conv_data)

                # 방금 생성된 conversation 조회
                select_query = f"""
                    SELECT conversation_id
                    FROM {DB_TABLES['conversation']}                    WHERE user_id = %(user_id)s
                    ORDER BY create_at DESC
                    LIMIT 1
                """
                result = self.db.execute_raw_query(select_query, {"user_id": user_id})

                if not result:
                    raise DatabaseError("Failed to get conversation ID")

                current_conversation_id = result[0]['conversation_id']

            # 메시지 저장
            chat_data = {
                "conversation_id": current_conversation_id,
                "user_id": user_id,
                "user_message": user_message,
                "bot_response": bot_response,
                "create_at": datetime.utcnow()
            }

            insert_query = f"""
                INSERT INTO {DB_TABLES['chat_history']}                (conversation_id, user_id, user_message, bot_response, create_at)
                VALUES (%(conversation_id)s, %(user_id)s, %(user_message)s, %(bot_response)s, %(create_at)s)
            """

            self.db.execute_raw_query(insert_query, chat_data)

            # 대화 세션 업데이트
            update_query = f"""
                UPDATE {DB_TABLES['conversation']}                SET message_count = message_count + 1,
                    last_message_at = %(last_message_at)s
                WHERE conversation_id = %(conversation_id)s
            """

            update_data = {
                "conversation_id": current_conversation_id,
                "last_message_at": datetime.utcnow()
            }

            self.db.execute_raw_query(update_query, update_data)

            # 캐시 무효화
            self.invalidate_conversation_cache(current_conversation_id, user_id)

            return {
                "conversation_id": current_conversation_id,
                "message_saved": True
            }

        except Exception as e:
            logger.error(f"대화 저장 오류: {str(e)}")
            if isinstance(e, (ChatBaseException, DatabaseError)):
                raise
            raise DatabaseError(f"Failed to save message: {str(e)}")

    async def _save_message_to_db(self, chat_data: Dict) -> Dict:
        """메시지를 데이터베이스에 저장"""
        try:
            insert_result = await self.db.ainsert(DB_TABLES['chat_history'], chat_data)
            if not insert_result:
                raise DatabaseError("Failed to save message")
            return insert_result
        except Exception as e:
            logger.error(f"메시지 저장 오류: {str(e)}")
            raise

    async def _update_conversation_status(self, conversation_id: str):
        """대화 세션 상태 업데이트"""
        try:
            update_query = f"""
                UPDATE {DB_TABLES['conversation']}
                SET last_message_at = CURRENT_TIMESTAMP,
                    message_count = message_count + 1 
                WHERE conversation_id = %(conversation_id)s
            """
            update_result = await self.db.aexecute_raw_query(
                update_query,
                {"conversation_id": conversation_id}
            )
            if not update_result:
                raise DatabaseError("Failed to update conversation")
        except Exception as e:
            logger.error(f"대화 상태 업데이트 오류: {str(e)}")

    async def _invalidate_cache_async(self, conversation_id: str, user_id: int):
        """캐시 무효화 (비동기)"""
        try:
            await self.cache.adelete(CACHE_KEYS["conversation_info"].format(
                conversation_id=conversation_id
            ))
            await self.cache.adelete(CACHE_KEYS["conversation_history"].format(
                conversation_id=conversation_id
            ))
            await self.cache.adelete(CACHE_KEYS["user_conversations"].format(
                user_id=user_id
            ))
        except Exception as e:
            logger.warning(f"캐시 무효화 중 오류 발생: {str(e)}")

    async def delete_conversation(self, conversation_id: str, user_id: int) -> bool:
        """대화 삭제"""
        if not conversation_id or not user_id:
            raise ChatBaseException("Conversation ID and User ID are required")

        try:
            # 대화 존재 및 권한 확인 (비동기 함수는 await 사용)
            conversation = await self.get_conversation_info(conversation_id)
            if not conversation or conversation['user_id'] != user_id:
                raise ConversationNotFound("대화를 찾을 수 없거나 접근 권한이 없습니다.")

            self.db.begin_transaction()

            update_data = {"status": "deleted"}
            where = {"conversation_id": conversation_id}
            update_result = self.db.update(DB_TABLES['conversation'], update_data, where)
            if not update_result:
                raise DatabaseError("Failed to delete conversation")

            # 캐시 무효화
            self.invalidate_conversation_cache(conversation_id, user_id)

            self.db.commit_transaction()
            logger.info(f"Deleted conversation: {conversation_id}")
            return True

        except Exception as e:
            self.db.rollback_transaction()
            logger.error(f"대화 삭제 오류: {str(e)}")
            if isinstance(e, (ChatBaseException, DatabaseError)):
                raise
            raise DatabaseError(f"대화 삭제 중 오류 발생: {str(e)}")

    def invalidate_conversation_cache(self, conversation_id: str, user_id: int):
        """대화 관련 캐시 무효화"""
        try:
            if not conversation_id or not user_id:
                logger.warning("Cannot invalidate cache: conversation_id and user_id are required")
                return

            self.cache.delete(CACHE_KEYS["conversation_info"].format(
                conversation_id=conversation_id
            ))
            self.cache.delete(CACHE_KEYS["conversation_history"].format(
                conversation_id=conversation_id
            ))
            self.cache.delete(CACHE_KEYS["user_conversations"].format(
                user_id=user_id
            ))
        except Exception as e:
            logger.warning(f"캐시 무효화 중 오류 발생: {str(e)}")
