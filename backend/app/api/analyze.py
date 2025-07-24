from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.user_service import UserService
from app.api.github import get_user_id_from_token
import httpx
from typing import Dict, List, Optional
import base64
from app.services.claude_ai_service import ClaudeAIService

router = APIRouter()
claude_ai = ClaudeAIService()

@router.post("/analyze-repo")
async def analyze_repository(
    repo_data: Dict,
    user_id: int = Depends(get_user_id_from_token),
    db: AsyncSession = Depends(get_db)
):
    """GitHub 저장소를 분석하여 프로젝트 구조와 배포 설정 제안"""
    repo_full_name = repo_data.get("repo_full_name")
    if not repo_full_name:
        raise HTTPException(status_code=400, detail="Repository name required")
    
    # GitHub 토큰 가져오기
    user_service = UserService(db)
    tokens = await user_service.get_user_tokens(user_id)
    github_token = tokens.get("github_token")
    
    if not github_token:
        raise HTTPException(status_code=400, detail="GitHub 연결이 필요합니다")
    
    analysis = {
        "repo_full_name": repo_full_name,
        "project_type": "unknown",
        "has_dockerfile": False,
        "has_docker_compose": False,
        "detected_services": [],
        "deployment_suggestions": []
    }
    
    # 저장소 루트 파일 목록 가져오기
    async with httpx.AsyncClient() as client:
        # 루트 디렉토리 파일 목록
        response = await client.get(
            f"https://api.github.com/repos/{repo_full_name}/contents/",
            headers={
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Repository 분석 실패")
        
        root_files = response.json()
        file_names = [f["name"] for f in root_files]
        
        # Dockerfile 확인
        if "Dockerfile" in file_names:
            analysis["has_dockerfile"] = True
        
        # Docker Compose 확인
        if "docker-compose.yml" in file_names or "docker-compose.yaml" in file_names:
            analysis["has_docker_compose"] = True
            
        # package.json 확인 (Node.js/Frontend)
        if "package.json" in file_names:
            # package.json 내용 읽기
            pkg_response = await client.get(
                f"https://api.github.com/repos/{repo_full_name}/contents/package.json",
                headers={
                    "Authorization": f"token {github_token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            if pkg_response.status_code == 200:
                pkg_content = base64.b64decode(pkg_response.json()["content"]).decode()
                if "vue" in pkg_content or "react" in pkg_content:
                    analysis["detected_services"].append({
                        "name": "frontend",
                        "type": "vue" if "vue" in pkg_content else "react",
                        "path": "/"
                    })
        
        # requirements.txt 확인 (Python/Backend)
        if "requirements.txt" in file_names:
            req_response = await client.get(
                f"https://api.github.com/repos/{repo_full_name}/contents/requirements.txt",
                headers={
                    "Authorization": f"token {github_token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            if req_response.status_code == 200:
                req_content = base64.b64decode(req_response.json()["content"]).decode()
                if "fastapi" in req_content:
                    analysis["detected_services"].append({
                        "name": "backend",
                        "type": "fastapi",
                        "path": "/"
                    })
        
        # 하위 디렉토리 확인 (frontend, backend 폴더)
        for dir_name in ["frontend", "backend"]:
            if dir_name in file_names and root_files[[f["name"] for f in root_files].index(dir_name)]["type"] == "dir":
                dir_response = await client.get(
                    f"https://api.github.com/repos/{repo_full_name}/contents/{dir_name}",
                    headers={
                        "Authorization": f"token {github_token}",
                        "Accept": "application/vnd.github.v3+json"
                    }
                )
                if dir_response.status_code == 200:
                    dir_files = [f["name"] for f in dir_response.json()]
                    
                    if dir_name == "frontend" and "package.json" in dir_files:
                        analysis["detected_services"].append({
                            "name": "frontend",
                            "type": "vue/react",
                            "path": f"/{dir_name}",
                            "has_dockerfile": "Dockerfile" in dir_files
                        })
                    elif dir_name == "backend" and ("requirements.txt" in dir_files or "main.py" in dir_files):
                        analysis["detected_services"].append({
                            "name": "backend",
                            "type": "python/fastapi",
                            "path": f"/{dir_name}",
                            "has_dockerfile": "Dockerfile" in dir_files
                        })
    
    # 프로젝트 타입 결정
    if len(analysis["detected_services"]) > 1:
        analysis["project_type"] = "fullstack"
    elif len(analysis["detected_services"]) == 1:
        service = analysis["detected_services"][0]
        if service["type"] in ["vue", "react", "vue/react"]:
            analysis["project_type"] = "frontend"
        else:
            analysis["project_type"] = "backend"
    
    # 배포 제안
    if analysis["has_docker_compose"]:
        analysis["deployment_suggestions"].append({
            "type": "docker-compose",
            "description": "Docker Compose를 사용한 다중 서비스 배포",
            "services": ["frontend", "backend"],
            "recommended": True
        })
    
    if analysis["has_dockerfile"] or any(s.get("has_dockerfile") for s in analysis["detected_services"]):
        analysis["deployment_suggestions"].append({
            "type": "cloud-run",
            "description": "Google Cloud Run을 사용한 컨테이너 배포",
            "services": [s["name"] for s in analysis["detected_services"]],
            "recommended": not analysis["has_docker_compose"]
        })
    
    # Dockerfile이 없는 경우 자동 생성 제안
    for service in analysis["detected_services"]:
        if not service.get("has_dockerfile") and not analysis["has_dockerfile"]:
            analysis["deployment_suggestions"].append({
                "type": "auto-dockerfile",
                "description": f"{service['name']} 서비스를 위한 Dockerfile 자동 생성",
                "service": service["name"],
                "path": service["path"]
            })
    
    return analysis

@router.post("/generate-dockerfile")
async def generate_dockerfile(
    config: Dict,
    user_id: int = Depends(get_user_id_from_token)
):
    """서비스 타입에 따른 Dockerfile 자동 생성"""
    service_type = config.get("service_type")
    service_path = config.get("service_path", "/")
    
    dockerfiles = {
        "vue/react": """FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]""",
        
        "python/fastapi": """FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]""",
        
        "node/express": """FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 3000
CMD ["node", "index.js"]"""
    }
    
    dockerfile_content = dockerfiles.get(service_type, dockerfiles["python/fastapi"])
    
    return {
        "dockerfile": dockerfile_content,
        "path": f"{service_path}/Dockerfile",
        "service_type": service_type
    }

@router.post("/ai-analyze-and-generate")
async def ai_analyze_and_generate(
    repo_data: Dict,
    user_id: int = Depends(get_user_id_from_token),
    db: AsyncSession = Depends(get_db)
):
    """Claude AI를 사용해 저장소를 분석하고 Dockerfile 및 워크플로우 생성"""
    repo_full_name = repo_data.get("repo_full_name")
    if not repo_full_name:
        raise HTTPException(status_code=400, detail="Repository name required")
    
    # GitHub 토큰 가져오기
    user_service = UserService(db)
    tokens = await user_service.get_user_tokens(user_id)
    github_token = tokens.get("github_token")
    
    if not github_token:
        raise HTTPException(status_code=400, detail="GitHub 연결이 필요합니다")
    
    # 저장소 구조 및 주요 파일 내용 가져오기
    repo_structure = {}
    repo_files_content = {}
    
    async with httpx.AsyncClient() as client:
        # 저장소 파일 목록 가져오기 (재귀적)
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # 루트 디렉토리 파일 목록
        response = await client.get(
            f"https://api.github.com/repos/{repo_full_name}/contents/",
            headers=headers
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Repository 접근 실패")
        
        root_items = response.json()
        
        # 중요한 파일들의 내용 가져오기
        important_files = [
            'package.json', 'requirements.txt', 'Dockerfile', 'docker-compose.yml',
            'main.py', 'app.py', 'index.js', 'server.js', 'pom.xml', 'build.gradle',
            'pyproject.toml', 'setup.py', 'Cargo.toml', 'go.mod'
        ]
        
        print(f"Analyzing repository: {repo_full_name}")
        print(f"Root items count: {len(root_items)}")
        
        async def get_file_content(path: str):
            """파일 내용 가져오기"""
            try:
                resp = await client.get(
                    f"https://api.github.com/repos/{repo_full_name}/contents/{path}",
                    headers=headers
                )
                if resp.status_code == 200:
                    content_data = resp.json()
                    if content_data.get("content"):
                        return base64.b64decode(content_data["content"]).decode('utf-8')
            except:
                pass
            return None
        
        # 루트 디렉토리의 중요 파일들
        for item in root_items:
            if item["type"] == "file" and item["name"] in important_files:
                print(f"Found important file: {item['name']}")
                content = await get_file_content(item["path"])
                if content:
                    repo_files_content[item["path"]] = content
                    print(f"Got content for {item['name']}, length: {len(content)}")
            
            # 하위 디렉토리 확인
            if item["type"] == "dir" and item["name"] in ["frontend", "backend", "src", "app", ".github"]:
                dir_resp = await client.get(
                    f"https://api.github.com/repos/{repo_full_name}/contents/{item['path']}",
                    headers=headers
                )
                if dir_resp.status_code == 200:
                    dir_items = dir_resp.json()
                    print(f"Checking directory {item['name']}, found {len(dir_items)} items")
                    for dir_item in dir_items:
                        if dir_item["type"] == "file" and dir_item["name"] in important_files:
                            print(f"Found important file in {item['name']}: {dir_item['name']}")
                            content = await get_file_content(dir_item["path"])
                            if content:
                                repo_files_content[dir_item["path"]] = content
                                print(f"Got content for {dir_item['path']}, length: {len(content)}")
        
        # 저장소 구조 생성
        def build_structure(items, path=""):
            structure = {}
            for item in items:
                if item["type"] == "file":
                    structure[item["name"]] = "file"
                elif item["type"] == "dir":
                    structure[item["name"]] = "dir"
            return structure
        
        repo_structure = build_structure(root_items)
    
    # Claude AI로 분석 및 파일 생성
    try:
        print(f"\nSending to AI:")
        print(f"- Repository structure keys: {list(repo_structure.keys())}")
        print(f"- Files with content: {list(repo_files_content.keys())}")
        print(f"- Total content size: {sum(len(c) for c in repo_files_content.values())} chars")
        
        ai_result = await claude_ai.analyze_repository_and_generate_files(
            repo_structure=repo_structure,
            repo_files_content=repo_files_content
        )
        
        # 에러 체크
        if "error" in ai_result:
            # 에러가 있어도 기본 분석은 반환
            return {
                "ai_analysis": None,
                "error": ai_result.get("error"),
                "raw_response": ai_result.get("raw_response", ""),
                "basic_analysis": await analyze_repository(repo_data, user_id, db)
            }
        
        return {
            "ai_analysis": ai_result,
            "repo_full_name": repo_full_name,
            "generated_files": {
                "dockerfiles": ai_result.get("dockerfiles", []),
                "workflow": ai_result.get("github_workflow", {}),
                "environment_variables": ai_result.get("environment_variables", [])
            }
        }
        
    except Exception as e:
        # AI 분석 실패 시 기본 분석 반환
        import traceback
        print(f"AI analysis error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return {
            "ai_analysis": None,
            "error": str(e),
            "error_traceback": traceback.format_exc(),
            "basic_analysis": await analyze_repository(repo_data, user_id, db)
        }