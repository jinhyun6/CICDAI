from typing import Dict, List, Optional
import os
import httpx
import json
import base64

class ClaudeAIService:
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.api_url = "https://api.anthropic.com/v1/messages"
        self.model = "claude-3-5-sonnet-20241022"  # 최신 모델
        print(f"ClaudeAIService initialized. API key exists: {bool(self.api_key)}")
        if self.api_key:
            print(f"API key length: {len(self.api_key)}")
        
    async def _call_claude(self, prompt: str, system_prompt: str = None) -> str:
        """Claude API 호출"""
        print(f"_call_claude called. API key exists: {bool(self.api_key)}")
        
        if not self.api_key:
            raise Exception("ANTHROPIC_API_KEY is not set")
            
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        messages = [{"role": "user", "content": prompt}]
        
        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 4096
        }
        
        if system_prompt:
            data["system"] = system_prompt
        
        print(f"Calling Claude API at {self.api_url}")
        print(f"Request data keys: {data.keys()}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=30.0
            )
            print(f"Claude API response status: {response.status_code}")
            
        if response.status_code != 200:
            raise Exception(f"Claude API error: {response.status_code} - {response.text}")
            
        result = response.json()
        return result["content"][0]["text"]
    
    async def analyze_repository_and_generate_files(
        self, 
        repo_structure: Dict,
        repo_files_content: Dict[str, str]
    ) -> Dict:
        """저장소를 분석하고 필요한 파일들을 생성"""
        
        # 주요 파일들의 내용을 포함한 프롬프트 생성
        files_info = []
        for path, content in repo_files_content.items():
            # 중요한 파일들만 포함 (package.json, requirements.txt, main.py 등)
            if any(name in path for name in ['package.json', 'requirements.txt', 'main.py', 'app.py', 'index.js']):
                files_info.append(f"=== {path} ===\n{content[:1000]}...\n")  # 처음 1000자만
        
        system_prompt = """You are a DevOps expert specializing in containerization and CI/CD pipelines. 
        You analyze code repositories and generate optimized Dockerfiles and GitHub Actions workflows."""
        
        prompt = f"""Please analyze this repository structure and generate appropriate files for CI/CD.

Repository structure:
{json.dumps(repo_structure, indent=2)}

Key files content:
{''.join(files_info)}

Based on this analysis, please generate:

IMPORTANT for services detection:
- If you find package.json with Vue dependencies, it's a "frontend" service with type "vue"
- If you find package.json with React dependencies, it's a "frontend" service with type "react"  
- If you find requirements.txt with FastAPI, it's a "backend" service with type "fastapi"
- If you find requirements.txt with Django, it's a "backend" service with type "django"
- If you find main.py or app.py, it's likely a Python backend service
- If you find index.js or server.js, it's likely a Node.js backend service
- Service names should be descriptive like "frontend", "backend", "api", "web", etc.
- Do NOT use generic names like "main-service" or "unknown"

CRITICAL: If you see /frontend and /backend folders:
- This is a multi-service project
- Create backend/Dockerfile for the backend service
- Create frontend/Dockerfile for the frontend service
- The workflow should build and deploy BOTH services separately

1. An optimized Dockerfile (or multiple if needed)
   - MUST copy actual project files (COPY . . or similar)
   - MUST NOT create test files or dummy applications
   - For Python/FastAPI: install requirements.txt and run actual main.py
   - For Node/Vue: install package.json dependencies and build/serve the actual app
   - If frontend and backend exist in separate folders, create separate Dockerfiles
2. A GitHub Actions workflow file for CI/CD that:
   - CRITICAL: Must use Google Artifact Registry, NOT Container Registry (gcr.io)
   - CRITICAL: Use secrets for all values: ${{{{ secrets.GCP_PROJECT_ID }}}}, ${{{{ secrets.GCP_REGION }}}} 
   - CRITICAL: Region format MUST be: ${{{{ secrets.GCP_REGION }}}}-docker.pkg.dev
   - CRITICAL: For auth use: google-github-actions/auth@v1 with credentials_json: ${{{{ secrets.GCP_SA_KEY }}}}
   - DO NOT use workload_identity_provider, use credentials_json instead
   - Must trigger on push to main branch AND manual workflow_dispatch
   - Must authenticate with: gcloud auth configure-docker REGION-docker.pkg.dev
   - Must create Artifact Registry repository if not exists
   - Must use this exact image format: REGION-docker.pkg.dev/${{{{ secrets.GCP_PROJECT_ID }}}}/cicdai-repo/SERVICE:${{{{ github.sha }}}}
   - MUST include Cloud Run deployment steps after building images
   - Use google-github-actions/deploy-cloudrun@v1 for deployment
   - Deploy backend service with name: cicdai-backend
   - Deploy frontend service with name: cicdai-frontend
   - Add output to show deployment URLs
   - Must have proper newlines at end of file

Please respond with a JSON object in this exact format:
{{
    "analysis": {{
        "project_type": "frontend/backend/fullstack/etc",
        "detected_technologies": ["list", "of", "technologies"],
        "services": [
            {{
                "name": "frontend/backend/api/web/etc",
                "type": "vue/react/fastapi/express/django/etc",
                "path": "/frontend or /backend or /",
                "build_command": "npm run build or python -m build",
                "test_command": "npm test or pytest"
            }}
        ],
        "deployment_strategy": "single-service/multi-service",
        "special_requirements": ["any", "special", "requirements"]
    }},
    "dockerfiles": [
        {{
            "path": "Dockerfile or backend/Dockerfile",
            "content": "FROM node:18-alpine\\n..."
        }}
    ],
    "github_workflow": {{
        "path": ".github/workflows/deploy.yml",
        "content": "FULL GITHUB ACTIONS WORKFLOW HERE - Must be a complete valid workflow that uses Artifact Registry"
    }},
    "environment_variables": [
        {{
            "name": "DATABASE_URL",
            "description": "Database connection string",
            "required": true
        }}
    ]
}}"""
        
        response = await self._call_claude(prompt, system_prompt)
        
        # JSON 파싱
        try:
            # Claude의 응답에서 JSON 부분만 추출
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            json_str = response[json_start:json_end]
            return json.loads(json_str)
        except:
            # JSON 파싱 실패 시 텍스트 응답 반환
            return {
                "error": "Failed to parse AI response",
                "raw_response": response
            }
    
    async def optimize_existing_dockerfile(self, dockerfile_content: str, project_info: Dict) -> str:
        """기존 Dockerfile 최적화"""
        system_prompt = "You are a Docker expert focused on security and optimization."
        
        prompt = f"""Please optimize this Dockerfile for better performance, security, and smaller image size:

Current Dockerfile:
```dockerfile
{dockerfile_content}
```

Project info:
- Type: {project_info.get('type', 'unknown')}
- Technologies: {', '.join(project_info.get('technologies', []))}

Please provide an optimized Dockerfile with:
1. Multi-stage builds where appropriate
2. Security best practices
3. Layer caching optimization
4. Minimal final image size
5. Comments explaining optimizations

Return only the Dockerfile content, no additional explanation."""
        
        return await self._call_claude(prompt, system_prompt)
    
    async def troubleshoot_deployment_error(self, error_log: str, context: Dict) -> Dict:
        """배포 오류 분석 및 해결책 제시"""
        system_prompt = "You are a DevOps troubleshooting expert."
        
        prompt = f"""Analyze this deployment error and provide solutions:

Error log:
```
{error_log}
```

Context:
- Project type: {context.get('project_type')}
- Deployment platform: Google Cloud Run
- Recent changes: {context.get('recent_changes')}

Please provide a JSON response with:
{{
    "error_diagnosis": "Clear explanation of what went wrong",
    "root_cause": "The root cause of the error",
    "solutions": [
        {{
            "description": "Solution description",
            "steps": ["step1", "step2", "..."],
            "code_changes": "Any code that needs to be added/modified"
        }}
    ],
    "prevention": "How to prevent this in the future"
}}"""
        
        response = await self._call_claude(prompt, system_prompt)
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            json_str = response[json_start:json_end]
            return json.loads(json_str)
        except:
            return {
                "error_diagnosis": "Failed to parse AI response",
                "raw_response": response
            }
    
    async def generate_deployment_readme(self, project_analysis: Dict) -> str:
        """프로젝트를 위한 배포 가이드 생성"""
        prompt = f"""Based on this project analysis, generate a comprehensive deployment README:

{json.dumps(project_analysis, indent=2)}

Include:
1. Project overview
2. Prerequisites
3. Local development setup
4. Deployment instructions
5. Environment variables
6. Troubleshooting guide
7. CI/CD pipeline explanation

Format in Markdown."""
        
        return await self._call_claude(prompt)