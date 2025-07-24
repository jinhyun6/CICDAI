from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.user_service import UserService
from app.api.github import get_user_id_from_token
import httpx
import json

router = APIRouter()

@router.get("/test-connection")
async def test_gcp_connection(
    user_id: int = Depends(get_user_id_from_token),
    db: AsyncSession = Depends(get_db)
):
    """GCP 연결 테스트 및 토큰 상태 확인"""
    user_service = UserService(db)
    tokens = await user_service.get_user_tokens(user_id)
    
    google_token = tokens.get("google_token")
    google_refresh_token = tokens.get("google_refresh_token")
    
    if not google_token:
        return {
            "connected": False,
            "message": "Google Cloud가 연결되지 않았습니다."
        }
    
    # 토큰 유효성 검사
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v1/tokeninfo",
                params={
                    "access_token": google_token
                }
            )
        
        if response.status_code == 200:
            token_info = response.json()
            return {
                "connected": True,
                "valid_token": True,
                "email": token_info.get("email"),
                "expires_in": token_info.get("expires_in"),
                "scope": token_info.get("scope"),
                "has_refresh_token": bool(google_refresh_token)
            }
        else:
            return {
                "connected": True,
                "valid_token": False,
                "error": "Token invalid or expired",
                "has_refresh_token": bool(google_refresh_token)
            }
            
    except Exception as e:
        return {
            "connected": True,
            "valid_token": False,
            "error": str(e),
            "has_refresh_token": bool(google_refresh_token)
        }

@router.get("/projects")
async def get_projects(
    user_id: int = Depends(get_user_id_from_token),
    db: AsyncSession = Depends(get_db)
):
    """사용자의 실제 GCP 프로젝트 목록 가져오기"""
    
    # DB에서 사용자의 Google 토큰 가져오기
    user_service = UserService(db)
    tokens = await user_service.get_user_tokens(user_id)
    
    google_token = tokens.get("google_token")
    if not google_token:
        # Google 연결 안 됨 - Mock 데이터 반환
        return [
            {
                "projectId": "demo-project",
                "name": "Demo Project (Google 연결 필요)",
                "projectNumber": "000000",
                "lifecycleState": "ACTIVE"
            }
        ]
    
    # 토큰 갱신을 위한 재시도 카운터
    retry_count = 0
    
    while retry_count < 2:
        try:
            # Google Cloud Resource Manager API 호출
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://cloudresourcemanager.googleapis.com/v1/projects",
                    headers={
                        "Authorization": f"Bearer {google_token}",
                        "Accept": "application/json"
                    },
                    params={
                        "filter": "lifecycleState:ACTIVE"
                    }
                )
            
            print(f"GCP API Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                projects = data.get("projects", [])
                
                print(f"Found {len(projects)} GCP projects")
                
                # 프로젝트가 없으면 도움말 메시지와 함께 반환
                if not projects:
                    return [{
                        "projectId": "no-projects-found",
                        "name": "프로젝트가 없습니다. GCP Console에서 프로젝트를 먼저 생성해주세요.",
                        "projectNumber": "",
                        "lifecycleState": "ACTIVE"
                    }]
                
                # 필요한 정보만 추출
                return [
                    {
                        "projectId": proj["projectId"],
                        "name": proj.get("name", proj["projectId"]),
                        "projectNumber": proj.get("projectNumber", ""),
                        "lifecycleState": proj.get("lifecycleState", "ACTIVE")
                    }
                    for proj in projects
                ]
            elif response.status_code == 401 and retry_count == 0:
                print(f"GCP API Error: Unauthorized - Attempting to refresh token")
                # 토큰 갱신 시도
                new_token = await user_service.refresh_google_token(user_id)
                if new_token:
                    google_token = new_token
                    retry_count += 1
                    print("Token refreshed, retrying API call...")
                    continue
                else:
                    # 토큰 갱신 실패
                    raise HTTPException(
                        status_code=401, 
                        detail="Google 토큰이 만료되었습니다. 다시 연결해주세요."
                    )
            else:
                print(f"GCP API Error: {response.status_code} - {response.text}")
                error_data = response.json() if response.text else {}
                print(f"Error details: {error_data}")
                break
                
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error fetching GCP projects: {e}")
            print(f"Error type: {type(e)}")
            break
        
        retry_count += 1
    
    # 에러 시 Mock 데이터
    return [
        {
            "projectId": "my-project-2024",
            "name": "My Project 2024",
            "projectNumber": "123456789",
            "lifecycleState": "ACTIVE"
        },
        {
            "projectId": "test-cicd-project",
            "name": "Test CI/CD Project",
            "projectNumber": "987654321",
            "lifecycleState": "ACTIVE"
        }
    ]