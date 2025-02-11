from typing import AsyncGenerator, Optional, Dict, List
from datetime import datetime
import logging
from openai import AsyncOpenAI
from configs.openai_setting import get_openai_settings
from utils.mysql_connector import MySQLConnector
import redis
import json

# 로깅 설정
logger = logging.getLogger(__name__)

class OpenAIBotException(Exception):
   """OpenAI 봇 관련 기본 예외 클래스"""
   pass

class ConversationNotFound(OpenAIBotException):
   """대화를 찾을 수 없을 때 발생하는 예외"""
   pass

class DatabaseError(OpenAIBotException):
   """데이터베이스 작업 중 발생하는 예외"""
   pass

class RedisCache:
   def __init__(self, redis_url: Optional[str] = None, ttl: int = 3600):
       self.redis_url = redis_url
       self.ttl = ttl
       self._redis = None
       self._is_available = False

       if self.redis_url:
           try:
               self._redis = redis.from_url(self.redis_url)
               self._redis.ping()
               self._is_available = True
               logger.info("Redis cache initialized successfully")
           except redis.RedisError as e:
               logger.warning(f"Failed to initialize Redis cache: {str(e)}")
               self._is_available = False

   @property
   def is_available(self) -> bool:
       return self._is_available

   def json_serial(self, obj):
       """datetime 객체를 JSON으로 직렬화"""
       if isinstance(obj, datetime):
           return obj.isoformat()
       raise TypeError(f"Type {type(obj)} not serializable")

   def get(self, key: str) -> Optional[Dict]:
       if not self.is_available:
           return None
       try:
           data = self._redis.get(key)
           return json.loads(data) if data else None
       except Exception as e:
           logger.error(f"Redis get error: {str(e)}")
           return None

   def set(self, key: str, value: Dict, ttl: Optional[int] = None) -> bool:
       if not self.is_available:
           return False
       try:
           self._redis.setex(
               key,
               ttl or self.ttl,
               json.dumps(value, default=self.json_serial)
           )
           return True
       except Exception as e:
           logger.error(f"Redis set error: {str(e)}")
           return False

   def delete(self, key: str) -> bool:
       if not self.is_available:
           return False
       try:
           self._redis.delete(key)
           return True
       except Exception as e:
           logger.error(f"Redis delete error: {str(e)}")
           return False

   def delete_pattern(self, pattern: str) -> bool:
       if not self.is_available:
           return False
       try:
           keys = self._redis.keys(pattern)
           if keys:
               self._redis.delete(*keys)
           return True
       except Exception as e:
           logger.error(f"Redis delete pattern error: {str(e)}")
           return False

class OpenAIBot:
   def __init__(self):
       self.settings = get_openai_settings()
       self.client = AsyncOpenAI(api_key=self.settings.OPENAI_API_KEY)
       self.db = MySQLConnector()
       self.cache = RedisCache(
           redis_url=self.settings.REDIS_URL,
           ttl=self.settings.REDIS_TTL
       )

   def search_similar_expressions(
           self,
           query: str,
           limit: int = 5
   ) -> List[Dict]:
       """FULLTEXT 검색을 사용하여 유사한 표현 검색"""
       try:
           search_query = """
           SELECT 
               talk_id,
               eng_sentence,
               kor_sentence,
               parenthesis,
               tag,
               MATCH(eng_sentence, kor_sentence, parenthesis, tag) 
               AGAINST(%(query)s IN NATURAL LANGUAGE MODE) as relevance
           FROM small_talk
           WHERE MATCH(eng_sentence, kor_sentence, parenthesis, tag) 
               AGAINST(%(query)s IN NATURAL LANGUAGE MODE)
           ORDER BY relevance DESC
           LIMIT %(limit)s
           """

           results = self.db.execute_raw_query(
               search_query,
               {'query': query, 'limit': limit}
           )
           return results
       except Exception as e:
           logger.error(f"유사 표현 검색 오류: {str(e)}")
           return []

   @staticmethod
   def format_examples_context(examples: List[Dict]) -> str:
       """검색된 예문들을 컨텍스트 형식으로 포맷팅"""
       if not examples:
           return ""

       context = "\n[참고 가능한 실제 표현들]\n"
       for ex in examples:
           context += f"- English: {ex['eng_sentence']}\n"
           if ex['kor_sentence']:
               context += f"  Korean: {ex['kor_sentence']}\n"
           if ex['parenthesis']:
               context += f"  Note: {ex['parenthesis']}\n"
           if ex['tag']:
               context += f"  Tag: {ex['tag']}\n"
           context += "\n"
       return context

   async def generate_stream(
           self,
           user_message: str,
           user_id: int,
           conversation_id: Optional[str] = None
   ) -> AsyncGenerator[str, None]:
       """스트리밍 응답을 생성하는 메서드"""
       try:
           similar_expressions = self.search_similar_expressions(user_message)
           context = self.format_examples_context(similar_expressions)

           user_settings = self.get_user_settings(user_id)
           prompt_template = self.get_prompt_template(
               user_settings.get('default_prompt_template_id')
           ) if user_settings else None

           system_prompt = prompt_template['system_prompt'] if prompt_template else self.settings.SYSTEM_PROMPT

           messages = [
               {"role": "system", "content": system_prompt},
               {"role": "user", "content": f"""다음 실제 사용 예문들을 참고하여 응답해주세요:

{context}

사용자 입력:
{user_message}"""}
           ]

           stream = await self.client.chat.completions.create(
               model=self.settings.MODEL_NAME,
               messages=messages,
               temperature=user_settings.get('temperature', self.settings.TEMPERATURE),
               max_tokens=user_settings.get('max_tokens', self.settings.MAX_TOKENS),
               stream=True
           )

           async for chunk in stream:
               if chunk.choices[0].delta.content:
                   yield chunk.choices[0].delta.content

       except Exception as e:
           logger.error(f"OpenAI API 오류: {str(e)}")
           raise OpenAIBotException(f"응답 생성 중 오류 발생: {str(e)}")

   def get_user_settings(self, user_id: int) -> Optional[Dict]:
       """사용자 설정을 조회하는 메서드"""
       try:
           cache_key = f"user_settings:{user_id}"
           cached_data = self.cache.get(cache_key)
           if cached_data:
               return cached_data

           where = {"user_id": user_id}
           result = self.db.select("user_chat_setting", where=where)
           settings = result[0] if result else None

           if settings:
               self.cache.set(cache_key, settings)
           return settings
       except Exception as e:
           logger.error(f"사용자 설정 조회 오류: {str(e)}")
           return None

   def get_prompt_template(self, template_id: Optional[int]) -> Optional[Dict]:
       """프롬프트 템플릿을 조회하는 메서드"""
       try:
           if not template_id:
               return None

           cache_key = f"prompt_template:{template_id}"
           cached_data = self.cache.get(cache_key)
           if cached_data:
               return cached_data

           where = {
               "prompt_template_id": template_id,
               "is_active": 'Y'
           }
           result = self.db.select("prompt_template", where=where)
           template = result[0] if result else None

           if template:
               self.cache.set(cache_key, template)
           return template
       except Exception as e:
           logger.error(f"프롬프트 템플릿 조회 오류: {str(e)}")
           return None

   def get_conversation_info(self, conversation_id: str) -> Optional[Dict]:
       """대화 세션 정보 조회"""
       try:
           cache_key = f"conversation:{conversation_id}:info"
           cached_data = self.cache.get(cache_key)
           if cached_data:
               return cached_data

           query = """
           SELECT 
               conversation_id,
               user_id,
               title,
               status,
               message_count,
               create_at,
               last_message_at
           FROM conversation_session 
           WHERE conversation_id = %(conversation_id)s
           AND status != 'deleted'
           """
           result = self.db.execute_raw_query(query, {"conversation_id": conversation_id})
           if not result:
               raise ConversationNotFound(f"대화를 찾을 수 없습니다: {conversation_id}")

           conversation = result[0]
           self.cache.set(cache_key, conversation)
           return conversation
       except ConversationNotFound:
           raise
       except Exception as e:
           logger.error(f"대화 세션 조회 오류: {str(e)}")
           raise DatabaseError(f"대화 세션 조회 중 오류 발생: {str(e)}")

   def create_conversation(self, user_id: int, initial_message: str) -> Dict:
       """새 대화를 생성하는 함수."""
       try:
           self.db.begin_transaction()

           # 1. conversation_session 생성
           conv_data = {
               "user_id": user_id,
               "last_message_at": datetime.utcnow()
           }

           # conversation_session INSERT 쿼리 직접 실행하여 ID 확보
           insert_conv_query = """
               INSERT INTO conversation_session 
               (user_id, last_message_at) 
               VALUES (%(user_id)s, %(last_message_at)s)
           """
           self.db.execute_raw_query(insert_conv_query, conv_data)

           # 방금 생성된 conversation_id 조회
           get_conv_id_query = """
               SELECT conversation_id 
               FROM conversation_session 
               WHERE user_id = %(user_id)s 
               ORDER BY create_at DESC 
               LIMIT 1
           """
           conv_result = self.db.execute_raw_query(get_conv_id_query, {"user_id": user_id})

           if not conv_result:
               raise DatabaseError("Failed to create conversation session")

           conversation_id = conv_result[0]['conversation_id']

           # 캐시 무효화
           self.cache.delete_pattern(f"conversation:{conversation_id}:*")
           self.cache.delete_pattern(f"user_conversations:{user_id}")

           self.db.commit_transaction()

           return {
               "conversation_id": conversation_id
           }

       except Exception as e:
           self.db.rollback_transaction()
           logger.error(f"대화 생성 오류: {str(e)}")
           raise DatabaseError(f"대화 생성 중 오류 발생: {str(e)}")

   def save_conversation(
           self,
           user_id: int,
           user_message: str,
           bot_response: str,
           conversation_id: Optional[str] = None
   ) -> Dict:
       """대화 내용 저장"""
       try:
           self.db.begin_transaction()

           if not conversation_id:
               # conversation_id가 없는 경우 새로운 대화 세션 생성
               result = self.create_conversation(user_id, user_message)
               conversation_id = result['conversation_id']

           # conversation_session이 존재하는지 확인
           check_conv_query = """
               SELECT conversation_id 
               FROM conversation_session 
               WHERE conversation_id = %(conversation_id)s 
               AND status != 'deleted'
           """
           conv_exists = self.db.execute_raw_query(check_conv_query, {"conversation_id": conversation_id})

           if not conv_exists:
               raise DatabaseError(f"Conversation session not found: {conversation_id}")

           # chat_history에 저장 (bot_response가 있을 때만)
           if bot_response:
               chat_data = {
                   "conversation_id": conversation_id,
                   "user_id": user_id,
                   "user_message": user_message,
                   "bot_response": bot_response
               }

               insert_chat_query = """
                   INSERT INTO chat_history 
                   (conversation_id, user_id, user_message, bot_response) 
                   VALUES (%(conversation_id)s, %(user_id)s, %(user_message)s, %(bot_response)s)
               """
               result = self.db.execute_raw_query(insert_chat_query, chat_data)

               # conversation_session 업데이트
               update_conv_query = """
                   UPDATE conversation_session 
                   SET last_message_at = CURRENT_TIMESTAMP,
                       message_count = message_count + 1 
                   WHERE conversation_id = %(conversation_id)s
               """
               self.db.execute_raw_query(update_conv_query, {"conversation_id": conversation_id})

               # 캐시 무효화
               self.cache.delete_pattern(f"conversation:{conversation_id}:*")
               self.cache.delete_pattern(f"user_conversations:{user_id}")

               self.db.commit_transaction()

               return {
                   "conversation_id": conversation_id,
                   "chat_history_id": result['lastrowid'] if hasattr(result, 'lastrowid') else None
               }
           else:
               self.db.commit_transaction()
               return {
                   "conversation_id": conversation_id
               }

       except Exception as e:
           self.db.rollback_transaction()
           logger.error(f"대화 저장 오류: {str(e)}")
           raise DatabaseError(f"대화 저장 중 오류 발생: {str(e)}")

   def delete_user_conversation(self, conversation_id: str, user_id: int) -> bool:
       """사용자의 대화 삭제"""
       try:
           conversation = self.get_conversation_info(conversation_id)
           if not conversation or conversation['user_id'] != user_id:
               raise ConversationNotFound("대화를 찾을 수 없거나 접근 권한이 없습니다.")

           self.db.begin_transaction()
           try:
               update_data = {"status": "deleted"}
               where = {"conversation_id": conversation_id}
               self.db.update("conversation_session", update_data, where)

               # 캐시 무효화
               self.cache.delete_pattern(f"conversation:{conversation_id}:*")
               self.cache.delete_pattern(f"user_conversations:{user_id}")

               self.db.commit_transaction()
               return True
           except Exception:
               self.db.rollback_transaction()
               raise

       except ConversationNotFound:
           raise
       except Exception as e:
           logger.error(f"대화 삭제 오류: {str(e)}")
           raise DatabaseError(f"대화 삭제 중 오류 발생: {str(e)}")

   def get_user_conversations(self, user_id: int) -> List[Dict]:
       """사용자의 대화 목록 조회"""
       try:
           cache_key = f"user_conversations:{user_id}"
           cached_data = self.cache.get(cache_key)
           if cached_data:
               return cached_data

           query = """
           SELECT 
               cs.conversation_id,
               cs.title,
               cs.status,
               cs.message_count,
               cs.create_at,
               cs.last_message_at,
               ch.user_message as last_message,
               ch.bot_response as last_response
           FROM conversation_session cs
           LEFT JOIN chat_history ch ON cs.conversation_id = ch.conversation_id
           AND ch.chat_history_id = (
               SELECT MAX(chat_history_id)
               FROM chat_history
               WHERE conversation_id = cs.conversation_id
           )
           WHERE cs.user_id = %(user_id)s
           AND cs.status != 'deleted'
           ORDER BY cs.last_message_at DESC
           """

           conversations = self.db.execute_raw_query(query, {"user_id": user_id})
           self.cache.set(cache_key, conversations)
           return conversations

       except Exception as e:
           logger.error(f"대화 목록 조회 오류: {str(e)}")
           raise DatabaseError(f"대화 목록 조회 중 오류 발생: {str(e)}")

   def update_message_count(self, conversation_id: str):
       """대화 세션의 메시지 수를 업데이트하는 메서드"""
       try:
           query = """
           SELECT COUNT(*) as count 
           FROM chat_history 
           WHERE conversation_id = %(conversation_id)s
           """
           result = self.db.execute_raw_query(query, {"conversation_id": conversation_id})
           count = result[0]['count']

           update_data = {
               "message_count": count,
               "last_message_at": datetime.utcnow()
           }
           where = {"conversation_id": conversation_id}

           self.db.update("conversation_session", update_data, where)

           # 캐시 무효화
           self.cache.delete(f"conversation:{conversation_id}:info")

       except Exception as e:
           logger.error(f"메시지 수 업데이트 오류: {str(e)}")
           raise DatabaseError(f"메시지 수 업데이트 중 오류 발생: {str(e)}")

   def get_chat_history(self, conversation_id: str) -> List[Dict]:
       try:
           # DB 연결이 끊어졌다면 재연결 시도
           if not self.db._connection:
               self.db.connect()

           query = """
                  SELECT 
                      chat_history_id, 
                      conversation_id, 
                      user_id, 
                      user_message, 
                      bot_response, 
                      create_at
                  FROM chat_history
                  WHERE conversation_id = %(conversation_id)s
                  ORDER BY create_at ASC
              """
           # conversation_id를 문자열로 직접 사용
           history = self.db.execute_raw_query(
               query,
               {"conversation_id": conversation_id}
           )
           return history or []
       except Exception as e:
           logger.error("대화 내역 조회 오류: %s", str(e), exc_info=True)
           raise DatabaseError(f"대화 내역 조회 중 오류 발생: {str(e)}")