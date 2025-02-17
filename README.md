# English Learning Platform

영어 학습을 위한 종합 플랫폼으로, Slack을 통한 자동화된 학습 컨텐츠 전송과 AI 기반의 학습 도구를 제공합니다.

## 🌟 주요 기능

### 1. 자동화된 영어 학습 시스템
- 일일 정해진 시간에 영어 문장 자동 발송 (09:00, 13:00, 17:00, 20:00)
- 사이클 기반의 반복 학습 시스템으로 효율적인 학습 관리
- Slack을 통한 실시간 학습 컨텐츠 전달

### 2. AI 기반 학습 도구
- OpenAI GPT 기반의 대화형 학습 보조
- 영어 일기 작성 및 AI 피드백 시스템
- 맞춤형 프롬프트 템플릿 관리

### 3. 종합 학습 컨텐츠 관리
- 단어장 관리 (과거형, 과거분사, 의미, 예문 포함)
- Small Talk 문장 관리
- OPic 대비 문제은행
- 문법 학습 자료 관리

### 4. 사용자 맞춤 시스템
- 개인화된 학습 설정
- 학습 이력 추적
- 대화 기록 관리

## 🛠 기술 스택

### Backend
- **Framework**: FastAPI
- **Language**: Python 3.12
- **AI Integration**: OpenAI GPT API
- **Database**: MySQL 8.0
- **Cache**: Redis
- **Message Platform**: Slack SDK

### Infrastructure
- **Containerization**: Docker, Docker Compose
- **Task Scheduling**: APScheduler
- **Authentication**: JWT
- **API Documentation**: OpenAPI (Swagger)

## 🚀 시작하기

### 1. 사전 요구사항
- Python 3.12 이상
- Docker 및 Docker Compose
- MySQL 8.0
- Redis (선택사항)
- Slack Workspace 및 Bot Token
- OpenAI API Key

### 2. 환경 설정
```bash
# 저장소 클론
git clone [repository-url]
cd english-bot

# 환경 변수 설정
cp .env.example .env
# .env 파일을 편집하여 필요한 설정값 입력
```

### 3. 실행 방법
```bash
# Docker Compose로 실행
docker-compose up -d

# 로컬 개발 환경 실행
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

## 📝 필수 환경 변수

```env
# MySQL 설정
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=your_user
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=eng_base

# Slack 설정
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_CHANNEL_ID=your-channel-id

# OpenAI 설정
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL_NAME=gpt-4
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=2000

# JWT 설정
JWT_SECRET_KEY=your-secret-key

# Redis 설정 (선택사항)
REDIS_URL=redis://localhost:6379
REDIS_TTL=3600
```

## 🏗 프로젝트 구조

```
english-bot/
├── apis/               # API 엔드포인트 및 모델
│   ├── models/        # Pydantic 모델
│   └── routes/        # API 라우트
├── bots/              # 봇 구현
├── chat/              # 채팅 관련 기능
├── configs/           # 설정 파일
├── diary/             # 일기 관련 기능
├── docker/            # Docker 설정
├── middlewares/       # 미들웨어
├── utils/             # 유틸리티 기능
└── test/              # 테스트 파일
```

## 🔐 보안 기능

- JWT 기반 인증
- CORS 보호
- 비밀번호 해싱 (PBKDF2)
- 환경 변수 기반 설정
- 관리자 권한 시스템

## 📚 주요 API 엔드포인트

### 학습 컨텐츠
- `/api/v1/vocabulary`: 단어 관리
- `/api/v1/small-talk`: Small Talk 관리
- `/api/v1/grammar`: 문법 관리
- `/api/v1/opic`: OPic 문제 관리
- `/api/v1/diary`: 영어 일기 관리

### AI 기능
- `/api/v1/chat`: AI 채팅
- `/api/v1/chat/prompts`: 프롬프트 템플릿 관리
- `/api/v1/diary/{diary_id}/feedback`: AI 일기 피드백

### 시스템 관리
- `/api/v1/bot`: 봇 제어
- `/api/v1/auth`: 인증
- `/health`: 상태 확인

## 💾 데이터베이스 구조

주요 테이블:
- `vocabulary`: 단어 정보
- `vocabulary_meaning`: 단어 의미
- `small_talk`: Small Talk 문장
- `answer`: 답변
- `grammar`: 문법
- `opic`: OPic 문제
- `diary`: 영어 일기
- `chat_history`: 채팅 기록
- `prompt_template`: 프롬프트 템플릿

## 🔄 사이클 시스템

1. 모든 학습 컨텐츠는 사이클 기반으로 관리
2. 한 사이클에서 모든 컨텐츠가 한 번씩 노출
3. 사이클 완료 후 자동으로 새로운 사이클 시작
4. 각 컨텐츠의 노출 이력 추적

## 📊 모니터링

- API 상태: `/health` 엔드포인트
- 봇 상태: `/api/v1/bot/bot-status`
- 스케줄러 상태: 로그 및 API를 통한 모니터링
- 상세 로깅: 각 구성 요소별 로그 기록

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📜 라이선스

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.