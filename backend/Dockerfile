# Python 3.11 slim 이미지 사용
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Python 종속성 파일 복사
COPY requirements.txt .

# Python 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# Cloud Run은 PORT 환경변수를 자동으로 설정
# 기본값은 8080

# 프로덕션 시작 스크립트 생성
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Get port from environment variable\n\
PORT=${PORT:-8080}\n\
\n\
# Start the application with gunicorn for production\n\
exec gunicorn main:app \\\n\
    --bind 0.0.0.0:$PORT \\\n\
    --workers 2 \\\n\
    --worker-class uvicorn.workers.UvicornWorker \\\n\
    --timeout 0 \\\n\
    --access-logfile - \\\n\
    --error-logfile -' > startup.sh && chmod +x startup.sh

# 시작 명령
CMD ["./startup.sh"]