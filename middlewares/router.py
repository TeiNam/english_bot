# middlewares/router.py
from fastapi import FastAPI
from pathlib import Path
from importlib import import_module
from typing import List
import logging

logger = logging.getLogger(__name__)

API_DIRECTORY = "apis/routes"  # apis 디렉토리 이름 상수화
EXCLUDED_FILES = "__"  # 제외 파일 조건


def get_router_modules() -> List[str]:
    """apis 디렉토리에서 라우터 모듈 목록 반환"""
    api_dir = Path(API_DIRECTORY)
    if not api_dir.exists():
        raise FileNotFoundError(f"{API_DIRECTORY} 디렉토리를 찾을 수 없습니다.")

    def handle_module_path(path: Path) -> str:
        """모듈 경로 포맷팅"""
        return ".".join(path.with_suffix('').parts)  # .py 확장자 제거 및 경로 포맷

    module_paths = [
        handle_module_path(path)
        for path in api_dir.rglob("*.py")
        if not path.name.startswith(EXCLUDED_FILES)
    ]
    return module_paths


def setup_routers(app: FastAPI) -> None:
    """FastAPI 애플리케이션에 라우터 자동 등록"""
    router_modules = get_router_modules()
    for module_path in router_modules:
        try:
            module = import_module(module_path)
            if hasattr(module, "router"):
                app.include_router(module.router)
                logger.info(f"✓ 라우터 등록 성공: {module_path}")
            else:
                logger.warning(f"⚠ 라우터가 없음: {module_path}")
        except Exception as e:
            logger.error(f"❌ {module_path} 모듈 로드 실패: {e}")
