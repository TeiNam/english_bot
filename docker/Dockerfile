# 빌드 스테이지
FROM python:3.12.8-slim as builder

WORKDIR /build

# 필수 빌드 패키지만 설치하고 캐시 정리를 한 레이어에서 수행
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 의존성 설치를 위한 파일만 먼저 복사하여 캐시 활용
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 런타임 스테이지
FROM python:3.12.8-slim

WORKDIR /app

# 필수 런타임 패키지만 설치하고 시간대 설정을 한 레이어에서 수행
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    tzdata \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && ln -snf /usr/share/zoneinfo/Asia/Seoul /etc/localtime \
    && echo "Asia/Seoul" > /etc/timezone

# 빌더 스테이지에서 파이썬 패키지를 시스템 레벨로 복사
COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# 애플리케이션 소스코드 복사
COPY . /app/

# 보안을 위한 비루트 사용자 생성 및 권한 설정
RUN useradd -r -s /bin/false -m -u 1000 appuser && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app

USER appuser

# 환경 변수 설정
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1

# 헬스체크 최적화
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "8000"]