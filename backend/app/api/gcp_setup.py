from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.user_service import UserService
from app.services.gcp_service import GCPService
from app.services.github_service import GitHubService
from app.api.github import get_user_id_from_token
from typing import Dict
import json
import base64

router = APIRouter()

@router.post("/create-service-account-for-cicd")
async def create_service_account_for_cicd(
    data: Dict,
    user_id: int = Depends(get_user_id_from_token),
    db: AsyncSession = Depends(get_db)
):
    """CI/CD를 위한 GCP 서비스 계정 생성 및 GitHub Secret 설정"""
    project_id = data.get("gcp_project_id")
    repo_full_name = data.get("repo_full_name")
    service_name = data.get("service_name", "github-actions")
    
    if not project_id or not repo_full_name:
        raise HTTPException(status_code=400, detail="Project ID and repository name required")
    
    # 토큰 가져오기
    user_service = UserService(db)
    tokens = await user_service.get_user_tokens(user_id)
    
    google_token = tokens.get("google_token")
    github_token = tokens.get("github_token")
    
    if not google_token:
        raise HTTPException(status_code=400, detail="Google Cloud 연결이 필요합니다")
    if not github_token:
        raise HTTPException(status_code=400, detail="GitHub 연결이 필요합니다")
    
    gcp_service = GCPService(google_token)
    github_service = GitHubService(github_token)
    
    try:
        # 1. 필요한 API 활성화
        print("Enabling required APIs...")
        api_results = gcp_service.enable_apis(project_id)
        
        # 2. 서비스 계정 생성
        print(f"Creating service account for project {project_id}...")
        account_id = f"{service_name}-sa"
        service_account = gcp_service.create_service_account(project_id, account_id)
        service_account_email = service_account['email']
        
        # 3. 권한 부여
        print(f"Granting permissions to {service_account_email}...")
        gcp_service.grant_permissions(project_id, service_account_email)
        
        # 4. 서비스 계정 키 생성
        print("Creating service account key...")
        key_data_base64 = gcp_service.create_service_account_key(project_id, service_account_email)
        
        # 5. Base64 디코딩하여 JSON 형식 확인
        key_json_str = base64.b64decode(key_data_base64).decode('utf-8')
        key_json = json.loads(key_json_str)
        
        # 6. GitHub Secret에 저장
        print("Setting up GitHub secrets...")
        secrets_to_create = {
            "GCP_SA_KEY": key_json_str,  # JSON 문자열로 저장
            "GCP_PROJECT_ID": project_id,
            "GCP_SERVICE_ACCOUNT_EMAIL": service_account_email
        }
        
        secret_results = {}
        for secret_name, secret_value in secrets_to_create.items():
            try:
                await github_service.create_or_update_secret(
                    repo_full_name=repo_full_name,
                    secret_name=secret_name,
                    secret_value=secret_value
                )
                secret_results[secret_name] = "✅ Created"
            except Exception as e:
                secret_results[secret_name] = f"❌ Failed: {str(e)}"
        
        return {
            "success": True,
            "service_account": {
                "email": service_account_email,
                "project_id": project_id
            },
            "apis_enabled": api_results,
            "secrets_created": secret_results,
            "message": "서비스 계정이 생성되고 GitHub Secrets가 설정되었습니다.",
            "next_steps": [
                "GitHub Actions 워크플로우가 이제 GCP에 배포할 수 있습니다",
                "첫 배포를 트리거하려면 코드를 push하거나 수동으로 워크플로우를 실행하세요"
            ]
        }
        
    except Exception as e:
        print(f"Error in service account creation: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "서비스 계정 생성 중 오류가 발생했습니다."
        }

@router.post("/verify-gcp-setup")
async def verify_gcp_setup(
    data: Dict,
    user_id: int = Depends(get_user_id_from_token),
    db: AsyncSession = Depends(get_db)
):
    """GCP 설정이 올바른지 확인"""
    project_id = data.get("gcp_project_id")
    repo_full_name = data.get("repo_full_name")
    
    if not project_id or not repo_full_name:
        raise HTTPException(status_code=400, detail="Project ID and repository name required")
    
    # 토큰 가져오기
    user_service = UserService(db)
    tokens = await user_service.get_user_tokens(user_id)
    
    github_token = tokens.get("github_token")
    if not github_token:
        raise HTTPException(status_code=400, detail="GitHub 연결이 필요합니다")
    
    github_service = GitHubService(github_token)
    repo = github_service.get_repo(repo_full_name)
    
    # GitHub Secrets 확인
    required_secrets = ["GCP_SA_KEY", "GCP_PROJECT_ID", "GCP_SERVICE_ACCOUNT_EMAIL", "GCP_SERVICE_NAME", "GCP_REGION"]
    existing_secrets = []
    missing_secrets = []
    
    try:
        secrets = repo.get_secrets()
        secret_names = [s.name for s in secrets]
        
        for secret in required_secrets:
            if secret in secret_names:
                existing_secrets.append(secret)
            else:
                missing_secrets.append(secret)
        
        is_ready = len(missing_secrets) == 0
        
        return {
            "ready": is_ready,
            "existing_secrets": existing_secrets,
            "missing_secrets": missing_secrets,
            "message": "모든 설정이 완료되었습니다!" if is_ready else f"{len(missing_secrets)}개의 Secret이 누락되었습니다."
        }
        
    except Exception as e:
        return {
            "ready": False,
            "error": str(e),
            "message": "설정 확인 중 오류가 발생했습니다."
        }