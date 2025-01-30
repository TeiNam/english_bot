# utils/slack_sender.py
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from configs.slack_setting import get_credentials
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class SlackSender:
    _instance = None

    # Constants for Slack message formatting
    MESSAGE_HEADER = "*오늘의 문장*\n\n"
    NO_SENTENCES_MESSAGE = "No sentences available."
    LOG_PREFIX = "[SlackSender]"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize the Slack client."""
        try:
            credentials = get_credentials()
            self.client = WebClient(token=credentials['bot_token'])
            self.channel_id = credentials['channel_id']
            self.logger = logging.getLogger(self.__class__.__name__)
            self._test_connection()
        except Exception as e:
            self._log_error(f"Slack 초기화 중 오류 발생: {str(e)}")
            raise

    def _test_connection(self):
        """Test Slack connection."""
        try:
            response = self.client.auth_test()
            self._log_info(f"Slack 연결 성공: {response['team']} 팀의 {response['user']} 봇으로 접속")
        except SlackApiError as e:
            self._log_error(f"Slack 연결 테스트 실패: {e.response['error']}")
            raise

    def format_message(self, sentences: List[Dict[str, Any]]) -> str:
        """Format sentences into a Slack message."""
        if not sentences:
            return self.NO_SENTENCES_MESSAGE

        message = self.MESSAGE_HEADER
        for i, sentence in enumerate(sentences, 1):
            message += self._format_sentence(i, sentence)
            if i < len(sentences):
                message += "\n"  # Add spacing between sentences

        self._log_debug(f"Formatted message: {message}")
        return message

    def _format_sentence(self, index: int, sentence: Dict[str, Any]) -> str:
        """Format an individual sentence."""
        tag_part = f" `#{sentence['tag']}`" if sentence.get('tag') else ""
        result = (f"{index}. *\"{sentence['eng_sentence']}\"* - "
                  f"\"{sentence['kor_sentence']}\"{tag_part}\n")
        if sentence.get('parenthesis'):
            result += f"   _- {sentence['parenthesis']}_\n"
        if 'answers' in sentence and sentence['answers']:
            result += self._format_answers(sentence.get('answers', []))
        return result

    def _format_answers(self, answers: List[Dict[str, Any]]) -> str:
        """Format answers for a sentence."""
        result = ""
        for j, answer in enumerate(answers):
            prefix = "└──" if j == len(answers) - 1 else "├──"
            result += (f"   {prefix} *\"{answer['eng_sentence']}\"* - "
                       f"\"{answer['kor_sentence']}\"\n")
        return result

    def send_message(self, sentences: List[Dict[str, Any]]) -> bool:
        """Send a formatted message to Slack."""
        try:
            message = self.format_message(sentences)
            response = self.client.chat_postMessage(
                channel=self.channel_id,
                text=message,
                mrkdwn=True
            )
            if response['ok']:
                self._log_info(f"메시지 전송 성공: {len(sentences)}개 문장")
                return True
            else:
                self._log_error(f"메시지 전송 실패: {response.get('error', 'Unknown error')}")
                return False
        except SlackApiError as e:
            self._log_error(f"Slack API 오류: {e.response['error']}")
        except Exception as e:
            self._log_error(f"메시지 전송 중 오류 발생: {str(e)}")
        return False

    def _log_info(self, message: str):
        """Log informational messages."""
        logger.info(f"{self.LOG_PREFIX} {message}")

    def _log_error(self, message: str):
        """Log error messages."""
        logger.error(f"{self.LOG_PREFIX} {message}")

    def _log_debug(self, message: str):
        """Log debug messages."""
        logger.debug(f"{self.LOG_PREFIX} {message}")
