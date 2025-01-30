# 빌드 스테이지
FROM python:3.12.8-slim as builder

WORKDIR /build

# 시스템 패키지 및 빌드 도구 설치
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 파이썬 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 런타임 스테이지
FROM python:3.12.8-slim

WORKDIR /app

# 시간대 설정
ENV TZ=Asia/Seoul
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

# 비루트 사용자 생성
RUN useradd -m -u 1000 appuser

# 빌더 스테이지에서 설치된 패키지 복사
COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# 애플리케이션 코드 복사
COPY . .

# 권한 설정
RUN chown -R appuser:appuser /app

# 비루트 사용자로 전환
USER appuser

# 상태 체크를 위한 헬스체크 설정
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 포트 설정
EXPOSE 8000

# 실행 명령
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]