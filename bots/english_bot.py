# bots/english_bot.py
import logging
import os
import threading
from typing import Optional, List, Dict, Any, Tuple

from dotenv import load_dotenv

from utils.mysql_connector import MySQLConnector
from utils.slack_sender import SlackSender
from utils.time_utils import (
    get_current_utc, format_utc, format_kst
)

logger = logging.getLogger(__name__)

load_dotenv()


class EnglishBot:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """봇 초기화"""
        self.db = MySQLConnector()
        self.sentences_per_message = int(os.getenv('SENTENCES_PER_MESSAGE', 1))
        self._running = False
        self._thread = None
        self.logger = logging.getLogger(self.__class__.__name__)
        self._last_message_time = None

    def get_current_cycle(self) -> int:
        """현재 사이클 번호를 가져옵니다."""
        try:
            query = """
                SELECT COALESCE(MAX(cycle_number), 0) as current_cycle
                FROM small_talk
                WHERE last_sent_at IS NOT NULL
            """
            result = self.db.execute_raw_query(query)
            current_cycle = result[0]['current_cycle'] if result and result[0]['current_cycle'] is not None else 0
            self.logger.info(f"Current cycle: {current_cycle}")
            return current_cycle
        except Exception as e:
            self.logger.error(f"현재 사이클 조회 중 오류 발생: {str(e)}")
            return 0

    def check_cycle_completion(self) -> Tuple[bool, int]:
        """사이클 완료 여부를 확인하고 새로운 사이클 번호를 반환합니다."""
        try:
            current_cycle = self.get_current_cycle()

            query = """
                SELECT 
                    total.count as total_sentences,
                    COALESCE(sent.count, 0) as sent_sentences
                FROM 
                    (SELECT COUNT(*) as count FROM small_talk) total
                    LEFT JOIN 
                    (SELECT COUNT(*) as count 
                     FROM small_talk 
                     WHERE cycle_number = %(current_cycle)s) sent ON 1=1
            """

            result = self.db.execute_raw_query(query, {'current_cycle': current_cycle})

            if not result:
                return False, current_cycle

            total = result[0]['total_sentences']
            sent = result[0]['sent_sentences']

            self.logger.info(f"Total sentences: {total}, Sent in current cycle: {sent}")

            if sent >= total:
                return True, current_cycle + 1

            return False, current_cycle

        except Exception as e:
            self.logger.error(f"사이클 완료 확인 중 오류 발생: {str(e)}")
            return False, current_cycle

    def get_random_sentences(self) -> Optional[List[Dict[str, Any]]]:
        """랜덤 영어 문장을 가져옵니다."""
        try:
            cycle_completed, current_cycle = self.check_cycle_completion()

            if current_cycle == 0 or cycle_completed:
                current_cycle = 1
                self.logger.info(f"Starting new cycle: {current_cycle}")

            collected_talk_ids = []
            needed_count = self.sentences_per_message

            # 1단계: cycle 0 문장 조회
            zero_cycle_query = """
                SELECT talk_id
                FROM small_talk
                WHERE (cycle_number = 0 OR cycle_number IS NULL OR last_sent_at IS NULL)
                ORDER BY RAND()
                LIMIT %(limit)s
            """

            zero_cycle_result = self.db.execute_raw_query(
                zero_cycle_query,
                {'limit': needed_count}
            )

            if zero_cycle_result:
                collected_talk_ids.extend([row['talk_id'] for row in zero_cycle_result])
                needed_count -= len(collected_talk_ids)
                self.logger.info(f"Found {len(collected_talk_ids)} messages with cycle 0, need {needed_count} more")

            # 2단계: cycle 0 문장이 부족한 경우 처리
            if needed_count > 0 and collected_talk_ids:
                collected_ids_str = ','.join(map(str, collected_talk_ids))
                reset_query = f"""
                    UPDATE small_talk
                    SET last_sent_at = NULL,
                        cycle_number = 0
                    WHERE talk_id NOT IN ({collected_ids_str})
                """
                self.db.execute_raw_query(reset_query)
                self.logger.info("Reset cycle for remaining messages: last_sent_at to NULL and cycle_number to 0")

                # 추가 문장 선택
                additional_query = f"""
                    SELECT talk_id
                    FROM small_talk
                    WHERE talk_id NOT IN ({collected_ids_str})
                    AND last_sent_at IS NULL
                    ORDER BY RAND()
                    LIMIT %(limit)s
                """

                additional_result = self.db.execute_raw_query(
                    additional_query,
                    {'limit': needed_count}
                )

                if additional_result:
                    collected_talk_ids.extend([row['talk_id'] for row in additional_result])
                    self.logger.info(f"Added {len(additional_result)} additional messages")

            # 3단계: cycle 0 문장이 없는 경우 일반 로직으로 처리
            if not collected_talk_ids:
                regular_query = """
                    SELECT talk_id
                    FROM small_talk
                    WHERE cycle_number < %(cycle_number)s
                    ORDER BY RAND()
                    LIMIT %(limit)s
                """

                regular_result = self.db.execute_raw_query(
                    regular_query,
                    {
                        'cycle_number': current_cycle,
                        'limit': self.sentences_per_message
                    }
                )

                if regular_result:
                    collected_talk_ids = [row['talk_id'] for row in regular_result]
                elif cycle_completed:
                    self.reset_cycle()
                    return self.get_random_sentences()

            # 4단계: 선택된 문장이 있으면 상세 정보 조회
            if collected_talk_ids:
                talk_ids_str = ','.join(map(str, collected_talk_ids))

                detail_query = f"""
                    SELECT 
                        st.talk_id,
                        st.eng_sentence,
                        st.kor_sentence,
                        st.parenthesis,
                        st.tag,
                        st.update_at,
                        a.answer_id,
                        a.eng_sentence as answer_eng_sentence,
                        a.kor_sentence as answer_kor_sentence,
                        a.update_at as answer_update_at
                    FROM small_talk st
                    LEFT JOIN answer a ON st.talk_id = a.talk_id
                    WHERE st.talk_id IN ({talk_ids_str})
                    ORDER BY st.talk_id, a.answer_id
                """

                result = self.db.execute_raw_query(detail_query)

                if result:
                    # 디버깅용 로그 추가
                    self.logger.info(f"Raw query result count: {len(result)}")

                    # 결과를 SmallTalk 모델 형식으로 재구성
                    sentences_dict = {}
                    for row in result:
                        talk_id = row['talk_id']
                        if talk_id not in sentences_dict:
                            sentences_dict[talk_id] = {
                                'talk_id': talk_id,
                                'eng_sentence': row['eng_sentence'],
                                'kor_sentence': row['kor_sentence'],
                                'parenthesis': row['parenthesis'],
                                'tag': row['tag'],
                                'update_at': row['update_at'],
                                'answers': []
                            }

                        # answer_id가 있는 경우에만 answers 배열에 추가
                        if row.get('answer_id'):
                            sentences_dict[talk_id]['answers'].append({
                                'answer_id': row['answer_id'],
                                'eng_sentence': row['answer_eng_sentence'],
                                'kor_sentence': row['answer_kor_sentence'],
                                'update_at': row['answer_update_at']
                            })

                    # 딕셔너리를 리스트로 변환
                    formatted_result = list(sentences_dict.values())
                    self.logger.info(f"Formatted result count: {len(formatted_result)}")

                    success = self.update_sent_status(collected_talk_ids, current_cycle)
                    if success:
                        self.logger.info(f"{len(formatted_result)}개의 문장을 가져왔습니다. (사이클: {current_cycle})")
                        for sentence in formatted_result:
                            self.logger.info(
                                f"Sentence ID: {sentence['talk_id']}, Answers count: {len(sentence['answers'])}")
                        return formatted_result

            self.logger.warning("데이터베이스에서 문장을 찾을 수 없습니다.")
            return None

        except Exception as e:
            self.logger.error(f"문장 조회 중 오류 발생: {str(e)}")
            return None

    def update_sent_status(self, talk_ids: List[int], cycle_number: int) -> bool:
        """발송된 문장들의 상태를 업데이트합니다."""
        try:
            if not talk_ids:
                return False

            talk_ids_str = ','.join(map(str, talk_ids))

            # last_sent_at과 cycle_number 모두 업데이트
            query = f"""
                UPDATE small_talk
                SET last_sent_at = CURRENT_TIMESTAMP,
                    cycle_number = %(cycle_number)s
                WHERE talk_id IN ({talk_ids_str})
            """

            params = {
                'cycle_number': cycle_number
            }

            result = self.db.execute_raw_query(query, params)
            self.logger.info(f"Updated {len(talk_ids)} sentences to cycle {cycle_number} with current timestamp")
            return True

        except Exception as e:
            self.logger.error(f"발송 상태 업데이트 중 오류 발생: {str(e)}")
            return False

    def reset_cycle(self) -> bool:
        """새로운 사이클을 위해 모든 문장의 상태를 초기화합니다."""
        try:
            query = """
                UPDATE small_talk
                SET last_sent_at = NULL,
                    cycle_number = 0
            """
            self.db.execute_raw_query(query)
            self.logger.info("Reset all sentences: last_sent_at to NULL and cycle_number to 0")
            return True
        except Exception as e:
            self.logger.error(f"사이클 초기화 중 오류 발생: {str(e)}")
            return False

    def process_messages(self) -> bool:
        """메시지 처리 및 전송"""
        try:
            sentences = self.get_random_sentences()
            if not sentences:
                self.logger.error("메시지를 가져오는데 실패했습니다.")
                return False

            # 디버깅을 위한 로그 추가
            self.logger.info(f"Retrieved sentences: {sentences}")

            # SlackSender 인스턴스 생성 및 메시지 전송
            slack_sender = SlackSender()
            success = slack_sender.send_message(sentences)

            if success:
                self.logger.info(
                    f"메시지 전송 성공: {len(sentences)}개 문장, "
                    f"시간: {format_utc(get_current_utc())}"
                )
            else:
                self.logger.error("Slack 메시지 전송 실패")

            return success

        except Exception as e:
            self.logger.error(f"메시지 처리 중 오류 발생: {str(e)}", exc_info=True)
            return False

    def start(self) -> bool:
        """봇 시작"""
        with self._lock:
            if self._running:
                self.logger.warning("봇이 이미 실행 중입니다.")
                return False

            self._running = True
            self.logger.info("봇이 시작되었습니다.")
            return True

    def stop(self) -> bool:
        """봇 종료"""
        with self._lock:
            if not self._running:
                self.logger.warning("봇이 이미 종료되었습니다.")
                return False

            self._running = False
            self.logger.info("봇이 종료되었습니다.")
            return True

    def is_running(self) -> bool:
        """봇 실행 상태 확인"""
        return self._running

    def get_last_message_time(self) -> Optional[str]:
        """마지막 메시지 전송 시간 반환 (KST)"""
        try:
            query = """
                SELECT MAX(last_sent_at) as last_sent
                FROM small_talk
                WHERE last_sent_at IS NOT NULL
            """
            result = self.db.execute_raw_query(query)
            if result and result[0]['last_sent']:
                # UTC 시간을 KST로 변환하여 문자열로 반환
                return format_kst(result[0]['last_sent'])
            return None
        except Exception as e:
            self.logger.error(f"마지막 전송 시간 조회 중 오류 발생: {str(e)}")
            return None


# 싱글톤 인스턴스
english_bot = EnglishBot()
