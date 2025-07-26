from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from app.api import auth, github, gcp, cicd, deployment, projects, rollback, analyze, github_actions, gcp_setup
from app.core.config import settings
import os

app = FastAPI(
    title="CI/CD AI",
    description="CI/CD 설정 자동화 플랫폼",
    version="0.1.0"
)

# CORS 설정
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost:8080"
]

# 환경변수에서 프론트엔드 URL 추가
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# 라우터 등록
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(github.router, prefix="/api/github", tags=["github"])
app.include_router(gcp.router, prefix="/api/gcp", tags=["gcp"])
app.include_router(cicd.router, prefix="/api/cicd", tags=["cicd"])
app.include_router(deployment.router, prefix="/api/deployment", tags=["deployment"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(rollback.router, prefix="/api/rollback", tags=["rollback"])
app.include_router(analyze.router, prefix="/api/analyze", tags=["analyze"])
app.include_router(github_actions.router, prefix="/api/github-actions", tags=["github-actions"])
app.include_router(gcp_setup.router, prefix="/api/gcp-setup", tags=["gcp-setup"])

@app.get("/")
async def root():
    return {"message": "CI/CD AI API", "version": "0.1.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/debug/cors")
async def debug_cors():
    return {
        "environment": os.getenv("ENVIRONMENT", "not set"),
        "allowed_origins": origins,
        "cors_settings": {
            "allow_credentials": allow_credentials if 'allow_credentials' in globals() else True,
            "allow_methods": ["*"],
            "allow_headers": ["*"]
        }
    }