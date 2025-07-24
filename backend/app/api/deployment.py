from fastapi import APIRouter, HTTPException, Header, Depends
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.user_service import UserService
from app.services.github_service import GitHubService
from app.api.github import get_user_id_from_token
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class WorkflowRun(BaseModel):
    id: int
    name: str
    status: str
    conclusion: Optional[str]
    created_at: datetime
    updated_at: datetime
    html_url: str
    run_number: int
    
class WorkflowStep(BaseModel):
    name: str
    status: str
    conclusion: Optional[str]
    number: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

class DeploymentStatus(BaseModel):
    workflow_runs: List[WorkflowRun]
    current_run: Optional[WorkflowRun]
    steps: List[WorkflowStep]

@router.get("/status/{owner}/{repo}")
async def get_deployment_status(
    owner: str,
    repo: str,
    run_id: Optional[int] = None,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """GitHub Actions workflow 실행 상태 조회"""
    try:
        # JWT 토큰에서 사용자 ID 추출
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Authorization header missing")
        
        token = authorization.split(" ")[1]
        user_id = await get_user_id_from_token(token)
        
        # 사용자 서비스 초기화
        user_service = UserService(db)
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # GitHub 토큰 복호화
        github_token = await user_service.decrypt_token(user.github_token)
        github_service = GitHubService(github_token)
        
        # GitHub API를 통해 workflow runs 조회
        repo_full_name = f"{owner}/{repo}"
        repo_obj = github_service.get_repo(repo_full_name)
        
        # 최근 workflow runs 가져오기
        workflow_runs = []
        runs = repo_obj.get_workflow_runs(actor=user.github_username)
        
        for run in runs[:10]:  # 최근 10개만
            workflow_runs.append(WorkflowRun(
                id=run.id,
                name=run.name,
                status=run.status,
                conclusion=run.conclusion,
                created_at=run.created_at,
                updated_at=run.updated_at,
                html_url=run.html_url,
                run_number=run.run_number
            ))
        
        # 특정 run의 상세 정보 조회
        current_run = None
        steps = []
        
        if run_id:
            for run in runs:
                if run.id == run_id:
                    current_run = WorkflowRun(
                        id=run.id,
                        name=run.name,
                        status=run.status,
                        conclusion=run.conclusion,
                        created_at=run.created_at,
                        updated_at=run.updated_at,
                        html_url=run.html_url,
                        run_number=run.run_number
                    )
                    
                    # Jobs와 steps 조회
                    jobs = run.jobs()
                    for job in jobs:
                        for step in job.steps:
                            steps.append(WorkflowStep(
                                name=step.name,
                                status=step.status,
                                conclusion=step.conclusion,
                                number=step.number,
                                started_at=step.started_at,
                                completed_at=step.completed_at
                            ))
                    break
        
        return DeploymentStatus(
            workflow_runs=workflow_runs,
            current_run=current_run,
            steps=steps
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get deployment status: {str(e)}")

@router.get("/logs/{owner}/{repo}/{run_id}")
async def get_deployment_logs(
    owner: str,
    repo: str,
    run_id: int,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """특정 workflow run의 로그 조회"""
    try:
        # JWT 토큰에서 사용자 ID 추출
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Authorization header missing")
        
        token = authorization.split(" ")[1]
        user_id = await get_user_id_from_token(token)
        
        # 사용자 서비스 초기화
        user_service = UserService(db)
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # GitHub 토큰 복호화
        github_token = await user_service.decrypt_token(user.github_token)
        github_service = GitHubService(github_token)
        
        # 로그 가져오기 (PyGithub가 직접 지원하지 않으므로 raw API 사용)
        import requests
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Jobs 가져오기
        jobs_url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}/jobs"
        jobs_response = requests.get(jobs_url, headers=headers)
        jobs_data = jobs_response.json()
        
        logs = []
        for job in jobs_data.get("jobs", []):
            # 각 job의 로그 URL
            logs_url = job.get("logs_url")
            if logs_url:
                log_response = requests.get(logs_url, headers=headers)
                logs.append({
                    "job_name": job.get("name"),
                    "logs": log_response.text
                })
        
        return {"logs": logs}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get logs: {str(e)}")