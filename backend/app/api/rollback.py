from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.project import Project
from app.models.user import User
from app.api.auth import get_current_user
from app.services.github_service import GitHubService
from app.services.gcp_service import GCPService
from app.services.user_service import UserService
from pydantic import BaseModel
from typing import Optional
import re

router = APIRouter()

class RollbackRequest(BaseModel):
    project_id: int
    target_version: Optional[str] = None  # 특정 버전으로 롤백, 없으면 이전 버전

class RollbackResponse(BaseModel):
    success: bool
    message: str
    previous_version: str
    current_version: str
    rollback_url: Optional[str] = None

@router.post("/rollback/{project_id}", response_model=RollbackResponse)
async def rollback_deployment(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """배포를 이전 버전으로 롤백"""
    
    # 프로젝트 조회
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # 사용자 토큰 가져오기
    user_service = UserService(db)
    tokens = await user_service.get_user_tokens(current_user.id)
    
    github_token = tokens.get("github_token")
    google_token = tokens.get("google_token")
    
    if not github_token or not google_token:
        raise HTTPException(status_code=401, detail="GitHub and GCP tokens required")
    
    try:
        # GitHub 서비스 초기화
        github_service = GitHubService(github_token)
        
        # GCP 서비스 초기화
        gcp_service = GCPService(google_token)
        
        # 1. 현재 Cloud Run 서비스의 리비전 목록 가져오기
        service_name = project.service_name.lower()
        revisions = gcp_service.get_service_revisions(
            project.gcp_project_id,
            project.region,
            service_name
        )
        
        if len(revisions) < 2:
            raise HTTPException(
                status_code=400,
                detail="No previous revision available for rollback"
            )
        
        # 2. 현재 활성 리비전과 이전 리비전 확인
        current_revision = revisions[0]  # 가장 최신
        previous_revision = revisions[1]  # 이전 버전
        
        # 3. Cloud Run 트래픽을 이전 리비전으로 전환
        rollback_result = gcp_service.update_traffic(
            project.gcp_project_id,
            project.region,
            service_name,
            {previous_revision['name']: 100}  # 100% 트래픽을 이전 버전으로
        )
        
        # 4. GitHub에 롤백 이벤트 기록 (이슈 생성)
        issue_body = f"""
## 🔄 Rollback Performed

**Service:** {service_name}
**Region:** {project.region}
**Previous Version:** {current_revision['name']}
**Rolled back to:** {previous_revision['name']}
**Performed by:** {current_user.email}

### Reason
Production issue detected. Rolled back to stable version.

### Next Steps
1. Investigate the issue in the latest deployment
2. Fix the issue
3. Create a new deployment with the fix
"""
        
        try:
            github_service.create_issue(
                project.github_repo,
                title=f"[Rollback] {service_name} rolled back to {previous_revision['name']}",
                body=issue_body,
                labels=["rollback", "production"]
            )
        except Exception as e:
            # 이슈 생성 실패해도 롤백은 성공한 것으로 처리
            print(f"Failed to create GitHub issue: {e}")
        
        return RollbackResponse(
            success=True,
            message=f"Successfully rolled back to {previous_revision['name']}",
            previous_version=previous_revision['name'],
            current_version=current_revision['name'],
            rollback_url=rollback_result.get('url')
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rollback failed: {str(e)}")

@router.get("/revisions/{project_id}")
async def get_deployment_revisions(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """배포된 리비전 목록 조회"""
    
    # 프로젝트 조회
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # 사용자 토큰 가져오기
    user_service = UserService(db)
    tokens = await user_service.get_user_tokens(current_user.id)
    google_token = tokens.get("google_token")
    
    if not google_token:
        raise HTTPException(status_code=401, detail="GCP token required")
    
    try:
        # GCP 서비스 초기화
        gcp_service = GCPService(google_token)
        
        # Cloud Run 서비스의 리비전 목록 가져오기
        service_name = project.service_name.lower()
        revisions = gcp_service.get_service_revisions(
            project.gcp_project_id,
            project.region,
            service_name
        )
        
        # 리비전 정보 포맷팅
        formatted_revisions = []
        for rev in revisions:
            # 리비전 이름에서 날짜/시간 추출 시도
            created_at = rev.get('metadata', {}).get('creationTimestamp', '')
            
            formatted_revisions.append({
                'name': rev['name'],
                'created_at': created_at,
                'is_active': rev.get('is_active', False),
                'traffic_percent': rev.get('traffic_percent', 0),
                'container_image': rev.get('spec', {}).get('template', {}).get('spec', {}).get('containers', [{}])[0].get('image', 'unknown')
            })
        
        return {
            'project_id': project_id,
            'service_name': service_name,
            'revisions': formatted_revisions
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get revisions: {str(e)}")