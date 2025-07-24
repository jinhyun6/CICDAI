from typing import Dict, List, Optional
import os
import httpx
import json

class AIService:
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.api_url = "https://api.anthropic.com/v1/messages"
        self.model = "claude-3-opus-20240229"  # 또는 claude-3-sonnet-20240229
    
    async def analyze_project_structure(self, files_structure: Dict) -> Dict:
        """AI를 사용해 프로젝트 구조를 심층 분석"""
        prompt = f"""
        다음 프로젝트 구조를 분석하고 CI/CD 파이프라인 설정을 위한 상세 정보를 제공해주세요:
        
        파일 구조:
        {json.dumps(files_structure, indent=2)}
        
        다음 정보를 JSON 형식으로 반환해주세요:
        1. project_type: 프로젝트 타입 (frontend, backend, fullstack, mobile, etc.)
        2. detected_frameworks: 감지된 프레임워크들
        3. build_commands: 빌드 명령어
        4. test_commands: 테스트 명령어
        5. deployment_strategy: 추천 배포 전략
        6. environment_variables: 필요한 환경변수
        7. special_considerations: 특별히 고려해야 할 사항
        """
        
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a DevOps expert specializing in CI/CD pipelines."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def generate_optimized_dockerfile(self, project_info: Dict) -> str:
        """프로젝트에 최적화된 Dockerfile 생성"""
        prompt = f"""
        다음 프로젝트 정보를 바탕으로 최적화된 Dockerfile을 생성해주세요:
        
        프로젝트 정보:
        - 타입: {project_info.get('type')}
        - 프레임워크: {project_info.get('framework')}
        - 의존성: {project_info.get('dependencies')}
        - 특별 요구사항: {project_info.get('requirements')}
        
        다음 사항을 고려해주세요:
        1. 멀티스테이지 빌드 사용
        2. 레이어 캐싱 최적화
        3. 보안 best practices
        4. 최소 이미지 크기
        """
        
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a Docker expert. Generate production-ready Dockerfiles."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content
    
    async def generate_github_workflow(self, project_analysis: Dict) -> str:
        """프로젝트에 맞는 GitHub Actions 워크플로우 생성"""
        prompt = f"""
        다음 프로젝트 분석 결과를 바탕으로 GitHub Actions 워크플로우를 생성해주세요:
        
        {json.dumps(project_analysis, indent=2)}
        
        워크플로우는 다음을 포함해야 합니다:
        1. 적절한 트리거 (push, PR 등)
        2. 빌드 및 테스트
        3. Docker 이미지 빌드 및 푸시
        4. GCP Cloud Run 배포
        5. 롤백 전략
        """
        
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a CI/CD expert. Generate production-ready GitHub Actions workflows."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content
    
    async def troubleshoot_deployment_error(self, error_log: str, context: Dict) -> Dict:
        """배포 오류 분석 및 해결책 제시"""
        prompt = f"""
        다음 배포 오류를 분석하고 해결책을 제시해주세요:
        
        에러 로그:
        {error_log}
        
        컨텍스트:
        - 프로젝트 타입: {context.get('project_type')}
        - 배포 환경: {context.get('deployment_env')}
        - 최근 변경사항: {context.get('recent_changes')}
        
        다음 형식으로 응답해주세요:
        1. error_cause: 오류 원인
        2. solution_steps: 해결 단계
        3. prevention_tips: 재발 방지 팁
        """
        
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a DevOps troubleshooting expert."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def optimize_deployment_config(self, current_config: Dict, usage_metrics: Dict) -> Dict:
        """사용 패턴을 분석해 배포 설정 최적화"""
        prompt = f"""
        현재 배포 설정과 사용 지표를 분석해 최적화 방안을 제시해주세요:
        
        현재 설정:
        {json.dumps(current_config, indent=2)}
        
        사용 지표:
        {json.dumps(usage_metrics, indent=2)}
        
        다음 관점에서 최적화해주세요:
        1. 비용 절감
        2. 성능 향상
        3. 가용성 개선
        4. 보안 강화
        """
        
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a cloud optimization expert."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)