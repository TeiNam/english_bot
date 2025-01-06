FROM python:3.12.8-slim

WORKDIR /app

# 시간대 설정
ENV TZ=Asia/Seoul
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

# 파이썬 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 기본 포트 설정
EXPOSE 8000

# 실행 명령
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]