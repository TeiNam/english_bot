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


# apis/routes/bot.py
@router.post("/send-now")
async def send_message_now():
    """즉시 메시지 전송"""
    try:
        # english_bot이 실행 중인지 먼저 확인
        if not english_bot.is_running():
            raise HTTPException(
                status_code=400,
                detail="Bot is not running. Please start the bot first."
            )

        current_cycle = english_bot.get_current_cycle()
        logger.info(f"Current cycle before sending: {current_cycle}")

        # process_messages 실행
        result = english_bot.process_messages()

        if result:
            new_cycle = english_bot.get_current_cycle()
            return {
                "status": "success",
                "message": "Message sent successfully",
                "previous_cycle": current_cycle,
                "new_cycle": new_cycle
            }
        else:
            # 실패 원인을 더 구체적으로 파악
            logger.error("process_messages returned False. Possible reasons: no messages to send or processing error")
            raise HTTPException(
                status_code=400,
                detail="No messages to process or processing error occurred. Please check if there are messages available."
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in send_message_now: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while sending message: {str(e)}"
        )

@router.get("/bot-status")
async def get_bot_status():
    """봇 상태 확인"""
    try:
        return {
            "is_running": english_bot.is_running(),
            "current_cycle": english_bot.get_current_cycle(),
            "last_message_time": english_bot.get_last_message_time(),
            "next_message_time": english_bot.get_next_message_time() if hasattr(english_bot, 'get_next_message_time') else None
        }
    except Exception as e:
        logger.error(f"Failed to get bot status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get bot status: {str(e)}"
        )