# apis/routes/bot.py
from fastapi import APIRouter, HTTPException
from bots.english_bot import english_bot
from utils.mysql_connector import MySQLConnector
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


@router.post("/send-now")
async def send_message_now():
    """즉시 메시지 전송"""
    try:
        if not english_bot.is_running():
            raise HTTPException(
                status_code=400,
                detail="Bot is not running. Please start the bot first."
            )

        # 데이터 존재 여부 체크
        db = MySQLConnector()
        count_result = db.execute_raw_query("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN cycle_number IS NULL OR cycle_number = 0 THEN 1 ELSE 0 END) as available
            FROM small_talk
        """)

        total = count_result[0]['total']
        available = count_result[0]['available']

        if total == 0:
            raise HTTPException(
                status_code=400,
                detail="No messages found in database. Please add some messages first."
            )

        if available == 0:
            raise HTTPException(
                status_code=400,
                detail=f"All {total} messages have been sent in current cycle. Consider resetting the cycle."
            )

        current_cycle = english_bot.get_current_cycle()
        logger.info(f"Current cycle: {current_cycle}, Total messages: {total}, Available messages: {available}")

        result = english_bot.process_messages()

        if result:
            new_cycle = english_bot.get_current_cycle()
            return {
                "status": "success",
                "message": "Message sent successfully",
                "previous_cycle": current_cycle,
                "new_cycle": new_cycle,
                "stats": {
                    "total_messages": total,
                    "available_messages": available
                }
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to process messages. Total: {total}, Available: {available}"
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
        status = {
            "is_running": english_bot.is_running(),
            "current_cycle": english_bot.get_current_cycle(),
            "last_message_time": english_bot.get_last_message_time(),
            "scheduler": {
                "is_running": message_scheduler.is_running(),
                "jobs": message_scheduler.get_jobs() if message_scheduler.is_running() else []
            }
        }
        return status
    except Exception as e:
        logger.error(f"Failed to get bot status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get bot status: {str(e)}"
        )