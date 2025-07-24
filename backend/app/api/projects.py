from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.project import Project
from app.models.user import User
from app.api.auth import get_current_user
from typing import List
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class ProjectResponse(BaseModel):
    id: int
    github_repo: str
    gcp_project_id: str
    service_name: str
    region: str
    deployment_url: str
    workflow_path: str
    created_at: datetime
    updated_at: datetime

@router.get("/me", response_model=List[ProjectResponse])
async def get_my_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """로그인한 사용자의 프로젝트 목록 조회"""
    result = await db.execute(
        select(Project)
        .where(Project.user_id == current_user.id)
        .order_by(Project.created_at.desc())
    )
    projects = result.scalars().all()
    
    return [
        ProjectResponse(
            id=project.id,
            github_repo=project.github_repo,
            gcp_project_id=project.gcp_project_id,
            service_name=project.service_name,
            region=project.region,
            deployment_url=project.deployment_url,
            workflow_path=project.workflow_path,
            created_at=project.created_at,
            updated_at=project.updated_at
        )
        for project in projects
    ]

@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """프로젝트 삭제"""
    result = await db.execute(
        select(Project)
        .where(Project.id == project_id, Project.user_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    await db.delete(project)
    await db.commit()
    
    return {"message": "Project deleted successfully"}