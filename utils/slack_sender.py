# utils/slack_sender.py
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from configs.slack_setting import get_credentials
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class SlackSender:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Slack client 초기화"""
        try:
            credentials = get_credentials()
            self.client = WebClient(token=credentials['bot_token'])
            self.channel_id = credentials['channel_id']
            self.logger = logging.getLogger(self.__class__.__name__)
            self._test_connection()
        except Exception as e:
            logger.error(f"Slack 초기화 중 오류 발생: {str(e)}")
            raise

    def _test_connection(self):
        """Slack 연결 테스트"""
        try:
            response = self.client.auth_test()
            logger.info(f"Slack 연결 성공: {response['team']} 팀의 {response['user']} 봇으로 접속")
        except SlackApiError as e:
            logger.error(f"Slack 연결 테스트 실패: {e.response['error']}")
            raise

    def group_answers(self, sentences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """답변들을 메인 문장별로 그룹화"""
        if not sentences:
            return []

        result = []

        try:
            # 디버깅을 위한 로깅 추가
            self.logger.info(f"Grouping sentences input: {sentences}")

            for sentence in sentences:
                # 기본 문장 정보
                main_sentence = {
                    'talk_id': sentence['talk_id'],
                    'eng_sentence': sentence['eng_sentence'],
                    'kor_sentence': sentence['kor_sentence'],
                    'parenthesis': sentence['parenthesis'],
                    'tag': sentence.get('tag', ''),
                    'answers': sentence.get('answers', [])  # 답변 배열을 직접 사용
                }
                result.append(main_sentence)

                # 디버깅을 위한 로깅 추가
                self.logger.info(
                    f"Processed sentence: talk_id={sentence['talk_id']}, answers_count={len(main_sentence['answers'])}")

        except Exception as e:
            self.logger.error(f"답변 그룹화 중 오류 발생: {str(e)}")
            raise

        return result

    def format_message(self, sentences: List[Dict[str, Any]]) -> str:
        """메시지를 포매팅"""
        try:
            if not sentences:
                return "No sentences available."

            message = "*오늘의 문장*\n\n"

            # group_answers 호출하지 않고 직접 처리
            for i, sentence in enumerate(sentences, 1):
                # 디버깅을 위한 로깅 추가
                self.logger.info(f"Formatting sentence {i}: {sentence}")

                # 메인 문장 (태그 포함)
                tag_str = f" `#{sentence['tag']}`" if sentence.get('tag') else ""
                message += (f"{i}. *\"{sentence['eng_sentence']}\"* - "
                            f"\"{sentence['kor_sentence']}\"{tag_str}\n")

                # 부가 설명
                if sentence.get('parenthesis'):
                    message += f"   _- {sentence['parenthesis']}_\n"

                # 답변이 있는 경우에만 트리 구조 표시
                answers = sentence.get('answers', [])
                if answers:
                    self.logger.info(f"Processing {len(answers)} answers for sentence {i}")
                    for j, answer in enumerate(answers):
                        prefix = "└──" if j == len(answers) - 1 else "├──"
                        message += (f"   {prefix} *\"{answer['eng_sentence']}\"* - "
                                    f"\"{answer['kor_sentence']}\"\n")

                # 문장 사이 공백
                if i < len(sentences):
                    message += "\n"

        except Exception as e:
            self.logger.error(f"메시지 포매팅 중 오류 발생: {str(e)}")
            raise

        # 최종 메시지 로깅
        self.logger.info(f"Final formatted message:\n{message}")
        return message

    def send_message(self, sentences: List[Dict[str, Any]]) -> bool:
        """슬랙으로 메시지 전송"""
        try:
            message = self.format_message(sentences)
            response = self.client.chat_postMessage(
                channel=self.channel_id,
                text=message,
                mrkdwn=True
            )

            if response['ok']:
                logger.info(f"메시지 전송 성공: {len(sentences)}개 문장")
                return True
            else:
                logger.error(f"메시지 전송 실패: {response.get('error', 'Unknown error')}")
                return False

        except SlackApiError as e:
            logger.error(f"Slack API 오류: {e.response['error']}")
            return False
        except Exception as e:
            logger.error(f"메시지 전송 중 예상치 못한 오류: {str(e)}")
            return False


# 싱글톤 인스턴스 생성
slack_sender = SlackSender()