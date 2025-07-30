from pydantic_settings import BaseSettings
from typing import List
import os

# Cloud Run 환경 감지 및 BASE_URL 자동 설정
def get_base_url():
    """Cloud Run 또는 로컬 환경에 따라 자동으로 BASE_URL 설정"""
    # 환경변수로 직접 설정된 경우 (Cloud Run에서 자동 설정됨)
    base_url = os.getenv("BASE_URL")
    if base_url:
        return base_url
    
    # 로컬 환경 (BASE_URL이 없는 경우)
    return "http://localhost:8000"

BASE_URL = get_base_url()

class Settings(BaseSettings):
    # 기본 설정
    PROJECT_NAME: str = "CI/CD AI"
    VERSION: str = "0.1.0"
    API_PREFIX: str = "/api"
    
    # 보안
    SECRET_KEY: str = "your-secret-key-change-this"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",  # Vite 기본 포트
        "http://localhost:3000",
    ]
    
    # Frontend URL from environment
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "")
    
    # OAuth - GitHub
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GITHUB_REDIRECT_URI: str = f"{BASE_URL}/api/auth/github/callback"
    
    # OAuth - Google Cloud
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = f"{BASE_URL}/api/auth/google/callback"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost/cicdai"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Encryption key for storing secrets
    ENCRYPTION_KEY: str = ""
    
    # AI API
    ANTHROPIC_API_KEY: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()