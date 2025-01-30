#utils/scheduler.py
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from utils.time_utils import KST, get_current_kst, format_kst
from bots.english_bot import english_bot

logger = logging.getLogger(__name__)
logging.getLogger("apscheduler").setLevel(logging.WARNING)


class MessageScheduler:
    _instance = None

    # 메시지 전송 시간 일정
    SCHEDULE_TIMES = ['09:00', '13:00', '17:00', '20:00' ]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_scheduler()
        return cls._instance

    def _initialize_scheduler(self):
        """스케줄러 초기화"""
        self.scheduler = BackgroundScheduler(timezone=KST)
        self._setup_logging()
        self._setup_job_schedules()

    def _setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(level=logging.INFO)
        logger.setLevel(logging.INFO)

    def _setup_job_schedules(self):
        """작업 스케줄 설정"""
        for time in self.SCHEDULE_TIMES:
            hour, minute = time.split(':')
            self._add_schedule_job(hour, minute, time)

    def _add_schedule_job(self, hour, minute, job_id_suffix):
        """단일 스케줄 작업 추가"""
        job_id = f'send_message_{job_id_suffix}'

        # 기존 작업 확인 및 로그
        existing_job = self.scheduler.get_job(job_id)
        if existing_job:
            logger.info(f"[작업 교체] ID: {job_id}, 이전 실행 시간: {existing_job.trigger}")
        else:
            logger.info(f"[새 작업 등록] ID: {job_id}, 실행 시간: {hour}:{minute} (KST)")

        # 작업 추가
        self.scheduler.add_job(
            english_bot.process_messages,
            CronTrigger(hour=hour, minute=minute, timezone=KST),
            id=job_id,
            replace_existing=True
        )

    def start(self):
        """스케줄러와 봇 시작"""
        try:
            self.scheduler.start()
            english_bot.start()
            logger.info(f"스케줄러와 봇 시작 성공: {format_kst(get_current_kst())}")
        except Exception as e:
            logger.error(f"스케줄러와 봇 시작 실패: {str(e)}")
            self.stop()
            raise

    def stop(self):
        """스케줄러와 봇 정지"""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown()
            if english_bot.is_running():
                english_bot.stop()
            logger.info(f"스케줄러와 봇 정지 성공: {format_kst(get_current_kst())}")
        except Exception as e:
            logger.error(f"스케줄러와 봇 정지 실패: {str(e)}")

    def get_jobs(self):
        """현재 등록된 스케줄 작업 목록 반환"""
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


# 싱글톤 인스턴스
message_scheduler = MessageScheduler()