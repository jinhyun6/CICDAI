from pydantic_settings import BaseSettings
from typing import List

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
    
    # OAuth - GitHub
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GITHUB_REDIRECT_URI: str = "http://localhost:8000/api/auth/github/callback"
    
    # OAuth - Google Cloud
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/google/callback"
    
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