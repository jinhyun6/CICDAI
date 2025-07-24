from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.user_service import UserService
from app.services.github_service import GitHubService
from app.services.gcp_service import GCPService
from app.api.github import get_user_id_from_token
from app.models.project import Project
import base64
import hashlib
import json

router = APIRouter()

def generate_hash(text: str) -> str:
    """프로젝트 ID를 해시하여 짧은 문자열 생성"""
    return hashlib.md5(text.encode()).hexdigest()

class CICDSetupRequest(BaseModel):
    github_repo: str  # owner/repo 형식
    gcp_project_id: str
    service_name: str
    region: str = "asia-northeast3"
    environment_variables: Dict[str, str] = {}

class WorkflowTemplate(BaseModel):
    name: str
    content: str
    path: str

@router.post("/setup")
async def setup_cicd(
    request: CICDSetupRequest,
    user_id: int = Depends(get_user_id_from_token),
    db: AsyncSession = Depends(get_db)
):
    """GitHub repo와 GCP 프로젝트를 연결하고 CI/CD 설정"""
    
    # 사용자 토큰 가져오기
    user_service = UserService(db)
    tokens = await user_service.get_user_tokens(user_id)
    
    github_token = tokens.get("github_token")
    google_token = tokens.get("google_token")
    
    if not github_token or not google_token:
        raise HTTPException(status_code=401, detail="GitHub과 GCP 모두 연결이 필요합니다")
    
    try:
        # GitHub 서비스 초기화
        github_service = GitHubService(github_token)
        
        # GCP 서비스 초기화
        gcp_service = GCPService(google_token)
        
        # 1. GCP API 활성화
        print("Enabling required GCP APIs...")
        api_results = gcp_service.enable_apis(request.gcp_project_id)
        
        # 2. GCP 서비스 계정 생성
        print("Creating GCP service account...")
        service_account = gcp_service.create_service_account(request.gcp_project_id)
        service_account_email = service_account['email']
        
        # IAM API 동기화를 위해 잠시 대기
        import time
        print("Waiting for IAM API to sync...")
        time.sleep(5)
        
        # 3. 권한 부여 (실패해도 계속 진행)
        print("Granting permissions...")
        try:
            gcp_service.grant_permissions(request.gcp_project_id, service_account_email)
        except Exception as e:
            print(f"Permission grant failed (continuing anyway): {e}")
        
        # 권한 설정 후 추가 대기
        time.sleep(3)
        
        # 4. 서비스 계정 키 생성
        print("Creating service account key...")
        service_account_key_base64 = gcp_service.create_service_account_key(
            request.gcp_project_id, 
            service_account_email
        )
        
        # Base64 디코딩하여 JSON 문자열로 변환
        import base64
        service_account_key_json = base64.b64decode(service_account_key_base64).decode('utf-8')
        
        # 디버깅: JSON 확인
        print(f"Service account key (first 100 chars): {service_account_key_json[:100]}...")
        
        # JSON 유효성 검증
        try:
            import json
            json.loads(service_account_key_json)
            print("Service account key is valid JSON")
        except Exception as e:
            print(f"Invalid JSON: {e}")
        
        # 디버깅: 받은 환경변수 출력
        print(f"Environment variables received: {request.environment_variables}")
        
        # 5. GitHub Secrets 설정 (서비스 계정 키만)
        secrets_to_create = {
            "GCP_SA_KEY": service_account_key_json,
        }
        
        # 사용자 정의 환경변수 추가
        if request.environment_variables:
            secrets_to_create.update(request.environment_variables)
        
        print(f"Secrets to create: {list(secrets_to_create.keys())}")
        
        # Secrets 일괄 생성
        secret_results = github_service.setup_secrets_batch(
            request.github_repo,
            secrets_to_create
        )
        
        # 6. Dockerfile과 Workflow 파일 생성/업데이트 (한 번의 커밋으로)
        dockerfile_content = generate_dockerfile_template(request.service_name)
        workflow = generate_workflow_template(
            request.service_name,
            request.region,
            request.gcp_project_id
        )
        
        # 여러 파일을 하나의 커밋으로 생성
        files_to_create = {
            "Dockerfile": dockerfile_content,
            workflow.path: workflow.content
        }
        
        try:
            batch_result = github_service.create_multiple_files(
                request.github_repo,
                files_to_create,
                "Setup CI/CD with Cloud Run deployment"
            )
            print(f"Files created/updated: {batch_result}")
            files_created = files_to_create
        except Exception as e:
            print(f"Failed to create files: {e}")
            raise  # 에러를 다시 발생시켜 정확한 문제 파악
        
        # 배포 URL 생성 (예상 URL)
        expected_url = f"https://{request.service_name.lower()}-{generate_hash(request.gcp_project_id)[:8]}-{request.region}.a.run.app"
        
        # Project 레코드 생성 또는 업데이트
        project = Project(
            user_id=user_id,
            github_repo=request.github_repo,
            gcp_project_id=request.gcp_project_id,
            service_name=request.service_name,
            region=request.region,
            deployment_url=expected_url,
            workflow_path=workflow.path
        )
        
        db.add(project)
        await db.commit()
        await db.refresh(project)
        
        return {
            "status": "success",
            "message": "CI/CD 설정 완료",
            "details": {
                "service_account": service_account_email,
                "apis_enabled": api_results,
                "secrets_created": secret_results,
                "files_created": files_created,
                "deployment_info": {
                    "service_name": request.service_name.lower(),
                    "region": request.region,
                    "project_id": request.gcp_project_id,
                    "expected_url": expected_url,
                    "github_repo": request.github_repo
                },
                "next_steps": [
                    "main 브랜치에 push하면 자동 배포가 시작됩니다",
                    "GitHub Actions 탭에서 진행 상황을 확인하세요",
                    f"배포 완료 후 URL: {expected_url}"
                ]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"CI/CD 설정 실패: {str(e)}")

async def create_service_account(project_id: str, gcp_token: str) -> str:
    """GCP 서비스 계정 생성"""
    # TODO: 실제 구현
    # google-cloud-iam 라이브러리 사용
    service_account_id = "github-actions-sa"
    return f"{service_account_id}@{project_id}.iam.gserviceaccount.com"

async def grant_permissions(project_id: str, service_account_email: str, gcp_token: str):
    """서비스 계정에 필요한 권한 부여"""
    # TODO: 실제 구현
    # 필요한 역할:
    # - roles/run.admin (Cloud Run 관리)
    # - roles/storage.admin (Artifact Registry)
    # - roles/cloudbuild.builds.builder (Cloud Build)
    pass

async def create_service_account_key(
    project_id: str, 
    service_account_email: str, 
    gcp_token: str
) -> str:
    """서비스 계정 키 생성"""
    # TODO: 실제 구현
    # JSON 키 생성하여 반환
    mock_key = {
        "type": "service_account",
        "project_id": project_id,
        "private_key_id": "key123",
        "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
        "client_email": service_account_email,
        "client_id": "123456789",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token"
    }
    return json.dumps(mock_key)

async def create_github_secrets(repo: str, secrets: Dict[str, str], github_token: str):
    """GitHub repository에 secrets 생성"""
    # TODO: 실제 구현
    # PyGithub 라이브러리 사용하여 secrets 생성
    pass

def generate_dockerfile_template(service_name: str) -> str:
    """기본 Dockerfile 템플릿 생성"""
    return """FROM python:3.9-slim

WORKDIR /app

RUN pip install Flask

# Create app.py file with proper escaping
RUN echo 'from flask import Flask' > app.py && \
    echo 'import os' >> app.py && \
    echo '' >> app.py && \
    echo 'app = Flask(__name__)' >> app.py && \
    echo '' >> app.py && \
    echo '@app.route("/")' >> app.py && \
    echo 'def hello():' >> app.py && \
    echo '    return "<h1>🎉 CI/CD Success! Your app is deployed on Cloud Run!</h1>"' >> app.py && \
    echo '' >> app.py && \
    echo 'if __name__ == "__main__":' >> app.py && \
    echo '    port = int(os.environ.get("PORT", 8080))' >> app.py && \
    echo '    app.run(host="0.0.0.0", port=port)' >> app.py

EXPOSE 8080

CMD ["python", "app.py"]
"""

def generate_workflow_template(
    service_name: str, 
    region: str, 
    project_id: str
) -> WorkflowTemplate:
    """GitHub Actions workflow 파일 생성 - 값을 직접 포함"""
    
    # Docker 이미지 이름은 소문자여야 함
    service_name_lower = service_name.lower()
    
    workflow_content = f"""name: Deploy to Cloud Run

on:
  push:
    branches:
      - main
    paths-ignore:
      - '.github/workflows/**'
      - '*.md'
      - 'LICENSE'
  workflow_dispatch:  # 수동 실행 가능

env:
  PROJECT_ID: {project_id}
  SERVICE_NAME: {service_name}
  SERVICE_NAME_LOWER: {service_name_lower}
  REGION: {region}

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Authenticate to Google Cloud
      uses: google-github-actions/auth@v1
      with:
        credentials_json: ${{{{ secrets.GCP_SA_KEY }}}}

    - name: Set up Cloud SDK
      uses: google-github-actions/setup-gcloud@v1

    - name: Configure Docker
      run: |
        gcloud auth configure-docker

    - name: Build Docker image
      run: |
        docker build -t gcr.io/$PROJECT_ID/$SERVICE_NAME_LOWER:${{{{ github.sha }}}} .

    - name: Push Docker image
      run: |
        docker push gcr.io/$PROJECT_ID/$SERVICE_NAME_LOWER:${{{{ github.sha }}}}

    - name: Deploy to Cloud Run
      run: |
        gcloud run deploy $SERVICE_NAME_LOWER \\
          --image gcr.io/$PROJECT_ID/$SERVICE_NAME_LOWER:${{{{ github.sha }}}} \\
          --region $REGION \\
          --platform managed \\
          --allow-unauthenticated \\
          --format json > deployment-output.json
        
        # Extract service URL
        SERVICE_URL=$(cat deployment-output.json | jq -r '.status.url')
        echo "SERVICE_URL=$SERVICE_URL" >> $GITHUB_ENV
        echo "🚀 Deployed to: $SERVICE_URL"
    
    - name: Update deployment status
      if: always()
      uses: actions/github-script@v6
      with:
        script: |
          const status = '${{{{ job.status }}}}';
          const serviceUrl = '${{{{ env.SERVICE_URL }}}}';
          
          await github.rest.repos.createCommitStatus({{
            owner: context.repo.owner,
            repo: context.repo.repo,
            sha: context.sha,
            state: status === 'success' ? 'success' : 'failure',
            target_url: serviceUrl || '',
            description: status === 'success' ? `Deployed to ${{serviceUrl}}` : 'Deployment failed',
            context: 'Cloud Run Deployment'
          }})
"""
    
    return WorkflowTemplate(
        name="deploy.yml",
        content=workflow_content,
        path=".github/workflows/deploy.yml"
    )

async def create_workflow_file(
    repo: str, 
    workflow: WorkflowTemplate, 
    github_token: str
):
    """GitHub repository에 workflow 파일 생성"""
    # TODO: 실제 구현
    # PyGithub 라이브러리 사용하여 파일 생성
    pass

@router.get("/templates")
async def get_workflow_templates():
    """사용 가능한 workflow 템플릿 목록"""
    templates = [
        {
            "id": "cloudrun-docker",
            "name": "Cloud Run (Docker)",
            "description": "Docker 이미지를 빌드하고 Cloud Run에 배포"
        },
        {
            "id": "appengine-standard",
            "name": "App Engine Standard",
            "description": "App Engine Standard 환경에 배포"
        },
        {
            "id": "firebase-hosting",
            "name": "Firebase Hosting",
            "description": "정적 웹사이트를 Firebase Hosting에 배포"
        }
    ]
    return templates