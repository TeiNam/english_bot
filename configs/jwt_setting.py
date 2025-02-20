# configs/jwt_setting.py
import os
from pathlib import Path

from dotenv import load_dotenv

# 프로젝트 루트 디렉토리 찾기
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = os.path.join(BASE_DIR, '.env')

# .env 파일 로드
load_dotenv(dotenv_path=env_path)

# JWT 설정
JWT_CONFIG = {
    'secret_key': os.getenv('JWT_SECRET_KEY'),
    'algorithm': 'HS256',
}

# 필수 환경변수 확인
if not JWT_CONFIG['secret_key']:
    raise ValueError("Missing required environment variable: JWT_SECRET_KEY")
