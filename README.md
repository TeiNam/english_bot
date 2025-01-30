# English Learning Bot

영어 학습을 위한 자동화된 Slack 메시지 발송 시스템입니다. 지정된 시간에 저장된 영어 문장을 Slack 채널로 자동 발송하여 효율적인 영어 학습을 지원합니다.

## 주요 기능

### 🤖 자동화된 영어 학습
- 하루 9번 정해진 시간에 영어 문장 자동 발송
- 사이클 기반의 문장 반복 학습 시스템
- 한영 번역과 부가 설명 제공

### 🔄 순환 학습 시스템
- 모든 문장이 균등하게 학습될 수 있도록 사이클 관리
- 자동 사이클 리셋 및 진행 상태 추적

### 🛠 관리 시스템
- RESTful API를 통한 문장 관리
- 태그 기반 문장 분류
- 답변 관리 시스템

## 기술 스택

- **Backend Framework**: FastAPI
- **Language**: Python 3.12
- **Database**: MySQL 8.0
- **Message Platform**: Slack
- **Containerization**: Docker, Docker Compose
- **Scheduler**: APScheduler

## 시스템 요구사항

- Python 3.12 이상
- Docker 및 Docker Compose
- MySQL 8.0
- Slack Workspace 및 Bot Token

## 설치 방법

1. 저장소 클론
```bash
git clone [repository-url]
cd english_bot
```

2. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일을 편집하여 필요한 설정 값을 입력
```

3. Docker Compose로 실행
```bash
docker-compose up -d
```

## 환경 변수 설정

`.env` 파일에 다음 환경 변수들을 설정해야 합니다:

```env
# MySQL 설정
MYSQL_ROOT_PASSWORD=your_root_password
MYSQL_DATABASE=eng_base
MYSQL_USER=your_user
MYSQL_PASSWORD=your_password

# Slack 설정
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_CHANNEL_ID=your-channel-id
```

## API 엔드포인트

### 영어 문장 관리

#### 문장 조회
- `GET /small-talk/`: 영어 문장 목록 조회
- `GET /small-talk/{talk_id}`: 특정 문장 상세 조회
- `GET /small-talk/count`: 전체 문장 수 조회

#### 문장 관리
- `POST /small-talk/`: 새로운 문장 추가
- `PUT /small-talk/{talk_id}`: 문장 전체 수정
- `PATCH /small-talk/{talk_id}`: 문장 부분 수정
- `DELETE /small-talk/{talk_id}`: 문장 삭제

### 답변 관리
- `GET /answer/`: 답변 목록 조회
- `POST /answer/`: 새로운 답변 추가
- `PUT /answer/{answer_id}`: 답변 수정
- `DELETE /answer/{answer_id}`: 답변 삭제

## 메시지 발송 시간

매일 다음 시간에 메시지가 자동 발송됩니다:
- 08:30
- 10:00
- 11:30
- 13:00
- 14:30
- 16:00
- 17:30
- 19:00
- 20:30

## 데이터베이스 스키마

### small_talk 테이블
- `talk_id`: 문장 ID (PK)
- `eng_sentence`: 영어 문장
- `kor_sentence`: 한국어 번역
- `parenthesis`: 부가 설명
- `tag`: 태그
- `cycle_number`: 사이클 번호
- `last_sent_at`: 마지막 발송 시간
- `update_at`: 수정 시간

### answer 테이블
- `answer_id`: 답변 ID (PK)
- `talk_id`: 문장 ID (FK)
- `eng_sentence`: 영어 답변
- `kor_sentence`: 한국어 답변
- `update_at`: 수정 시간

## 개발 환경 설정

### 로컬 개발 환경
```bash
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 개발 서버 실행
uvicorn main:app --reload
```

### Docker 개발 환경
```bash
# 개발용 컨테이너 실행
docker-compose up --build

# 로그 확인
docker-compose logs -f

# 컨테이너 중지
docker-compose down
```

## 상태 확인

- API 상태 확인: `GET /health`
- 스케줄러 상태 확인: `GET /bot/status`

## 로깅

로그는 다음 경로에 저장됩니다:
- API 로그: `logs/api.log`
- 봇 로그: `logs/bot.log`
- 스케줄러 로그: `logs/scheduler.log`

## 참고사항

- 모든 시간은 Asia/Seoul 타임존 기준입니다.
- 문장 발송은 사이클 방식으로 진행되며, 모든 문장이 한 번씩 발송된 후 새로운 사이클이 시작됩니다.
- 환경 변수 설정이 올바르지 않으면 서비스가 정상적으로 동작하지 않을 수 있습니다.

## 라이선스

이 프로젝트는 MIT 라이선스 하에 있습니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.