import os
from pathlib import Path
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)


class SlackSettings:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """설정 초기화 및 환경변수 로드"""
        # 프로젝트 루트 디렉토리 찾기
        project_root = Path(__file__).parent.parent
        env_path = project_root / '.env'

        # .env 파일 로드
        if env_path.exists():
            load_dotenv(dotenv_path=env_path)
        else:
            logger.warning(f".env 파일을 찾을 수 없습니다: {env_path}")

        # Slack 설정 로드
        self.bot_token = self._get_env_value('SLACK_BOT_TOKEN')
        self.channel_id = self._get_env_value('SLACK_CHANNEL_ID')

        # 필수 설정 검증
        self._validate_settings()

    def _get_env_value(self, key: str) -> str:
        """환경변수 값을 가져오고 정리"""
        value = os.getenv(key, '').strip()
        if value and value[0] in ['"', "'"] and value[-1] in ['"', "'"]:
            value = value[1:-1]
        return value

    def _validate_settings(self):
        """필수 설정값 검증"""
        if not self.bot_token:
            raise ValueError("SLACK_BOT_TOKEN이 설정되지 않았습니다.")

        if not self.bot_token.startswith('xoxb-'):
            raise ValueError("잘못된 SLACK_BOT_TOKEN 형식입니다. Bot User OAuth Token을 사용해주세요.")

        if not self.channel_id:
            raise ValueError("SLACK_CHANNEL_ID가 설정되지 않았습니다.")

        if not self.channel_id.startswith('C'):
            raise ValueError("잘못된 SLACK_CHANNEL_ID 형식입니다. 'C'로 시작하는 채널 ID를 사용해주세요.")

    def get_credentials(self):
        """Slack 인증 정보 반환"""
        return {
            'bot_token': self.bot_token,
            'channel_id': self.channel_id
        }


# 싱글톤 인스턴스 생성
slack_settings = SlackSettings()


def get_credentials():
    """모든 Slack 인증 정보 반환"""
    return slack_settings.get_credentials()