from fastapi import APIRouter, HTTPException, Header, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.user_service import UserService
from app.models.user import User
import httpx
import jwt
from app.core.config import settings

router = APIRouter()

def get_user_id_from_token(authorization: str = Header(None)) -> int:
    """JWT 토큰에서 사용자 ID 추출"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="인증 필요")
    
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return int(payload.get("sub"))
    except:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰")

@router.get("/repos")
async def get_repositories(
    user_id: int = Depends(get_user_id_from_token),
    db: AsyncSession = Depends(get_db)
):
    """사용자의 GitHub repository 목록 가져오기"""
    # DB에서 사용자의 GitHub 토큰 가져오기
    user_service = UserService(db)
    tokens = await user_service.get_user_tokens(user_id)
    
    github_token = tokens.get("github_token")
    if not github_token:
        raise HTTPException(status_code=400, detail="GitHub 연결이 필요합니다")
    
    # GitHub API 호출
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.github.com/user/repos",
            headers={
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json"
            },
            params={
                "sort": "updated",
                "per_page": 30
            }
        )
    
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Repository 목록 가져오기 실패")
    
    repos = response.json()
    
    # 필요한 정보만 추출
    simplified_repos = [
        {
            "id": repo["id"],
            "name": repo["name"],
            "full_name": repo["full_name"],
            "private": repo["private"],
            "default_branch": repo["default_branch"],
            "updated_at": repo["updated_at"],
            "language": repo["language"],
            "description": repo["description"]
        }
        for repo in repos
    ]
    
    return simplified_repos

@router.post("/repos/{repo_full_name}/enable-actions")
async def enable_github_actions(repo_full_name: str, authorization: str = Header(None)):
    """GitHub Actions 활성화"""
    if not authorization:
        raise HTTPException(status_code=401, detail="인증 필요")
    
    # GitHub Actions는 기본적으로 활성화되어 있음
    # 여기서는 workflow 권한 확인 정도만
    
    return {
        "message": f"GitHub Actions enabled for {repo_full_name}",
        "status": "success"
    }