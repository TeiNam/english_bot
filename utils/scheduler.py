# utils/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from utils.time_utils import KST, get_current_kst, format_kst
from bots.english_bot import english_bot
import logging

logger = logging.getLogger(__name__)


class MessageScheduler:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """스케줄러 초기화"""
        self.scheduler = BackgroundScheduler(timezone=KST)  # 스케줄러의 기본 시간대를 KST로 설정
        self._setup_jobs()
        self._setup_logging()

    def _setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(level=logging.INFO)
        logger.setLevel(logging.INFO)

    def _setup_jobs(self):
        """작업 스케줄 설정"""
        # 실행 시간
        schedule_times = ['08:30','10:00','11:30','13:00','14:30','16:00','17:30','19:00','20:30']

        for time in schedule_times:
            hour, minute = time.split(':')
            self.scheduler.add_job(
                english_bot.process_messages,
                CronTrigger(
                    hour=hour,
                    minute=minute,
                    timezone=KST
                ),
                id=f'send_message_{time}',
                replace_existing=True
            )
            logger.info(f"Scheduled job added for {time} KST")

    def start(self):
        """스케줄러와 봇 시작"""
        try:
            self.scheduler.start()
            english_bot.start()
            current_time = format_kst(get_current_kst())
            logger.info(f"Scheduler and bot started successfully at {current_time}")
        except Exception as e:
            logger.error(f"Failed to start scheduler and bot: {str(e)}")
            self.stop()
            raise

    def stop(self):
        """스케줄러와 봇 종료"""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown()
            if english_bot.is_running():
                english_bot.stop()
            current_time = format_kst(get_current_kst())
            logger.info(f"Scheduler and bot stopped successfully at {current_time}")
        except Exception as e:
            logger.error(f"Failed to stop scheduler and bot: {str(e)}")

    def get_jobs(self):
        """현재 등록된 작업 목록 반환"""
        return [
            {
                'id': job.id,
                'next_run_time': format_kst(job.next_run_time) if job.next_run_time else None
            }
            for job in self.scheduler.get_jobs()
        ]

    def is_running(self):
        """스케줄러 실행 상태 확인"""
        return self.scheduler.running


# 싱글톤 인스턴스 생성
message_scheduler = MessageScheduler()