# Build stage
FROM node:20-slim as build

# 시간대 설정
ENV TZ=Asia/Seoul
RUN apt-get update && apt-get install -y \
    tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 의존성 설치
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# 소스 코드 복사 및 빌드
COPY frontend/ .
RUN npm run build

# Production stage
FROM nginx:alpine

# 시간대 설정
ENV TZ=Asia/Seoul
RUN apk add --no-cache tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone

# Nginx 설정
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

# 빌드된 파일 복사
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]