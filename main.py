# main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI

from middlewares.cors import setup_cors_middleware
from middlewares.json_handler import raw_json_middleware
from middlewares.router import setup_routers
from utils.scheduler import message_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    message_scheduler.start()
    yield
    message_scheduler.stop()


app = FastAPI(title="English Bot API", lifespan=lifespan)

# 미들웨어 설정
setup_cors_middleware(app)
app.middleware("http")(raw_json_middleware)

# 라우터 자동 설정
setup_routers(app)


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
