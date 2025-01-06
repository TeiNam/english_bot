# English Bot

English Bot은 Slack과 연동된 영어 학습 봇 서비스입니다. FastAPI 기반의 백엔드와 React 기반의 프론트엔드로 구성되어 있습니다.

## 기술 스택

### 백엔드
- Python
- FastAPI
- MySQL
- Slack API

### 프론트엔드
- React
- TypeScript
- Vite
- Tailwind CSS
- ESLint

## 프로젝트 구조

```
english_bot/
├── backend
│   ├── apis/              # API 관련 코드
│   ├── bots/              # 봇 핵심 로직
│   ├── configs/           # 설정 파일
│   ├── middlewares/       # 미들웨어
│   ├── utils/             # 유틸리티 함수
│   └── main.py           # 백엔드 진입점
├── frontend/             # 프론트엔드 애플리케이션
└── docker/              # 도커 설정
```

## 주요 기능

### 백엔드 기능
1. 봇 컨트롤
   - `bots/english_bot.py`: 영어 학습 봇 핵심 로직
   - Slack과의 실시간 통신

2. API 엔드포인트
   - 답변 관리 (`apis/routes/answer.py`)
   - 봇 제어 (`apis/routes/bot.py`)
   - Small Talk 관리 (`apis/routes/small_talk.py`)

3. 데이터베이스 연동
   - MySQL 연결 및 관리
   - 스케줄러 작업

### 프론트엔드 기능
1. 답변 관리
   - 답변 목록 조회
   - 답변 생성 및 수정

2. Small Talk 관리
   - Small Talk 목록 조회
   - Small Talk 생성 및 수정

3. 봇 제어
   - 봇 상태 관리
   - 설정 변경

## 설치 및 실행

### 필수 요구사항
- Python 3.x
- Node.js
- MySQL
- Docker (선택사항)

### 백엔드 설정
1. Python 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. 의존성 설치
```bash
pip install -r requirements.txt
```

3. 환경 변수 설정
- MySQL 설정 (`configs/mysql_setting.py`)
- Slack 설정 (`configs/slack_setting.py`)

4. 서버 실행
```bash
uvicorn main:app --reload
```

### 프론트엔드 설정
1. 의존성 설치
```bash
cd frontend
npm install
```

2. 개발 서버 실행
```bash
npm run dev
```

## API 문서
- API 테스트: `test_main.http` 파일 참조
- Swagger UI: `http://localhost:8000/docs` (서버 실행 시)

## 데이터베이스 구조
- answers: 봇 답변 데이터
- small_talks: Small Talk 데이터

## 기여 방법
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 라이센스
This project is licensed under the MIT License

## 문의사항
프로젝트에 대한 문의사항이나 버그 리포트는 Issues 탭을 통해 제출해 주세요.
