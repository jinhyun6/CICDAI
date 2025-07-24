# CI/CD AI - 원클릭 배포 자동화 플랫폼

AI 기반 CI/CD 파이프라인 자동 생성 및 Google Cloud Run 배포 플랫폼

## 🚀 주요 기능

- **AI 기반 자동 분석**: Claude AI가 저장소를 분석하여 최적화된 Dockerfile과 GitHub Actions 워크플로우 자동 생성
- **원클릭 배포**: GitHub 저장소를 Google Cloud Run에 자동 배포
- **OAuth 통합**: GitHub 및 Google Cloud 계정 연동
- **자동 설정**: GCP 서비스 계정, GitHub Secrets, 필요한 API 자동 설정
- **롤백 기능**: 이전 버전으로 빠른 롤백 지원
- **다중 서비스 지원**: 모노레포 내 여러 서비스 자동 감지 및 배포

## 설정 방법

### 1. 환경 설정

```bash
# 백엔드 환경 설정
cd backend
cp .env.example .env
# .env 파일을 열어 필요한 값들을 설정하세요
```

### 2. GitHub OAuth 설정

1. [GitHub Developer Settings](https://github.com/settings/developers)로 이동
2. "New OAuth App" 클릭
3. 다음 정보 입력:
   - Application name: CI/CD AI (원하는 이름)
   - Homepage URL: http://localhost:5173
   - Authorization callback URL: http://localhost:8000/api/auth/github/callback
4. 생성된 Client ID와 Client Secret을 `.env` 파일에 추가

### 3. Google Cloud OAuth 설정

1. [Google Cloud Console](https://console.cloud.google.com/apis/credentials)로 이동
2. "Create Credentials" > "OAuth client ID" 선택
3. Application type: Web application
4. Authorized redirect URIs에 추가: http://localhost:8000/api/auth/google/callback
5. 생성된 Client ID와 Client Secret을 `.env` 파일에 추가

### 4. 데이터베이스 설정

```bash
# PostgreSQL 설치 및 실행
# macOS (Homebrew)
brew install postgresql
brew services start postgresql

# 데이터베이스 생성
createdb cicdai

# 마이그레이션 실행
cd backend
alembic upgrade head
```

### 5. 실행

```bash
# 백엔드 실행
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# 프론트엔드 실행 (새 터미널)
cd frontend
npm install
npm run dev
```

## 사용 방법

1. http://localhost:5173 접속
2. 회원가입/로그인
3. GitHub 및 Google Cloud 계정 연결
4. CI/CD 설정 시작!

## 문제 해결

### "연결 중..." 에서 멈추는 경우

1. `.env` 파일에 OAuth 클라이언트 ID와 시크릿이 올바르게 설정되었는지 확인
2. 브라우저 개발자 도구 콘솔에서 에러 메시지 확인
3. 백엔드 서버 로그 확인

### OAuth 연결 실패

1. Redirect URI가 정확히 일치하는지 확인
2. OAuth 앱의 권한 범위(scope)가 올바른지 확인
3. 토큰이 만료되지 않았는지 확인