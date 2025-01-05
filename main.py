# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apis.routes import small_talk, answer, bot
from middlewares.json_handler import raw_json_middleware
from utils.scheduler import message_scheduler
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# CORS origins 설정 가져오기
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:8000").split(",")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시 실행
    message_scheduler.start()
    yield
    # 종료 시 실행
    message_scheduler.stop()

app = FastAPI(title="English Bot API", lifespan=lifespan)

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(raw_json_middleware)
# 라우터 등록
app.include_router(small_talk.router)
app.include_router(answer.router)
app.include_router(bot.router)

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)