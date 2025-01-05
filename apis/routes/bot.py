# apis/routes/bot.py
from fastapi import APIRouter, HTTPException
from bots.english_bot import english_bot
from utils.scheduler import message_scheduler
import logging

# 로거 설정
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bot", tags=["bot"])


@router.post("/start")
async def start_scheduler():
    """스케줄러 시작"""
    try:
        if message_scheduler.is_running():
            logger.warning("Scheduler is already running")
            raise HTTPException(status_code=400, detail="Scheduler is already running")

        message_scheduler.start()
        logger.info("Scheduler started successfully")
        return {
            "message": "Scheduler started successfully",
            "jobs": message_scheduler.get_jobs()
        }
    except Exception as e:
        logger.error(f"Failed to start scheduler: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start scheduler: {str(e)}")


@router.post("/stop")
async def stop_scheduler():
    """스케줄러 종료"""
    try:
        if not message_scheduler.is_running():
            logger.warning("Scheduler is not running")
            raise HTTPException(status_code=400, detail="Scheduler is not running")

        message_scheduler.stop()
        logger.info("Scheduler stopped successfully")
        return {"message": "Scheduler stopped successfully"}
    except Exception as e:
        logger.error(f"Failed to stop scheduler: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to stop scheduler: {str(e)}")


@router.get("/status")
async def get_scheduler_status():
    """스케줄러 상태 확인"""
    try:
        is_running = message_scheduler.is_running()
        response = {
            "running": is_running,
        }

        # 실행 중일 경우 스케줄된 작업 정보도 포함
        if is_running:
            response["jobs"] = message_scheduler.get_jobs()

        logger.info(f"Scheduler status checked - running: {is_running}")
        return response
    except Exception as e:
        logger.error(f"Failed to get scheduler status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get scheduler status: {str(e)}")


@router.post("/send-now")
async def send_message_now():
    """즉시 메시지 전송"""
    try:
        # 현재 사이클 정보 로깅
        current_cycle = english_bot.get_current_cycle()
        logger.info(f"Attempting immediate message send (Current cycle: {current_cycle})")

        if english_bot.process_messages():
            new_cycle = english_bot.get_current_cycle()
            logger.info(f"Message sent successfully (New cycle: {new_cycle})")
            return {
                "message": "Message sent successfully",
                "cycle": new_cycle
            }

        logger.error("Failed to send message")
        raise HTTPException(status_code=500, detail="Failed to send message")
    except Exception as e:
        logger.error(f"Failed to send message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")