from github import Github
from github import GithubException
import base64
from nacl import encoding, public
from typing import Dict, Any, Optional
import requests
import httpx

class GitHubService:
    def __init__(self, access_token: str):
        self.github = Github(access_token)
        self.access_token = access_token
    
    def get_repo(self, repo_full_name: str):
        """Repository 객체 가져오기"""
        try:
            return self.github.get_repo(repo_full_name)
        except GithubException as e:
            raise Exception(f"Repository not found: {repo_full_name}")
    
    def create_or_update_secret(self, repo_full_name: str, secret_name: str, secret_value: str):
        """GitHub Repository Secret 생성 또는 업데이트"""
        repo = self.get_repo(repo_full_name)
        
        # GCP_SA_KEY는 특별 처리 (이미 base64 인코딩되어 있을 수 있음)
        if secret_name == "GCP_SA_KEY":
            print(f"Processing GCP_SA_KEY - checking if it's already base64 encoded")
            # JSON인지 확인
            try:
                import json
                json.loads(secret_value)
                print("GCP_SA_KEY is valid JSON, will encrypt")
                # JSON이면 정상적으로 암호화
            except:
                print("GCP_SA_KEY is not JSON, might be already encrypted")
                # JSON이 아니면 문제가 있음
        
        # Repository의 public key 가져오기
        public_key = repo.get_public_key()
        
        # Secret 값 암호화
        encrypted_value = self._encrypt_secret(public_key.key, secret_value)
        
        # Secret 생성 또는 업데이트
        try:
            # 먼저 기존 secret 삭제 시도 (있으면)
            try:
                repo.delete_secret(secret_name)
                print(f"Deleted existing secret: {secret_name}")
            except:
                pass  # 없으면 무시
            
            # 새로 생성
            repo.create_secret(secret_name, encrypted_value)
            return f"Secret '{secret_name}' created successfully"
            
        except Exception as e:
            raise Exception(f"Failed to create secret: {e}")
    
    def create_or_update_secret_direct(self, repo_full_name: str, secret_name: str, secret_value: str):
        """GitHub REST API를 직접 사용하여 Secret 생성"""
        # Repository 정보 파싱
        owner, repo = repo_full_name.split('/')
        
        # Headers
        headers = {
            'Authorization': f'token {self.access_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # Public key 조회
        key_response = requests.get(
            f'https://api.github.com/repos/{owner}/{repo}/actions/secrets/public-key',
            headers=headers
        )
        
        if key_response.status_code != 200:
            raise Exception(f"Failed to get public key: {key_response.text}")
            
        public_key_data = key_response.json()
        
        # 값 암호화
        encrypted_value = self._encrypt_secret(public_key_data['key'], secret_value)
        
        # Secret 생성/업데이트
        secret_response = requests.put(
            f'https://api.github.com/repos/{owner}/{repo}/actions/secrets/{secret_name}',
            headers=headers,
            json={
                'encrypted_value': encrypted_value,
                'key_id': public_key_data['key_id']
            }
        )
        
        if secret_response.status_code in [201, 204]:
            print(f"Successfully created/updated secret: {secret_name}")
            return f"Secret '{secret_name}' created successfully"
        else:
            raise Exception(f"Failed to create secret: {secret_response.text}")
    
    def _encrypt_secret(self, public_key: str, secret_value: str) -> str:
        """GitHub의 public key로 secret 암호화"""
        # 디버깅
        print(f"Encrypting secret, value starts with: {secret_value[:50]}...")
        
        public_key_bytes = base64.b64decode(public_key)
        sealed_box = public.SealedBox(public.PublicKey(public_key_bytes))
        encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
        return base64.b64encode(encrypted).decode("utf-8")
    
    def create_workflow_file(self, repo_full_name: str, workflow_content: str, 
                           workflow_path: str = ".github/workflows/deploy.yml",
                           commit_message: str = "Add CI/CD workflow"):
        """Workflow 파일 생성"""
        repo = self.get_repo(repo_full_name)
        
        # 디버깅: repo 정보 출력
        print(f"Creating workflow for repo: {repo.full_name}")
        print(f"Repo private: {repo.private}")
        
        try:
            # .github/workflows 디렉토리가 있는지 먼저 확인
            try:
                repo.get_contents(".github")
            except:
                # .github 폴더가 없으면 먼저 README 생성 (폴더 생성용)
                try:
                    repo.create_file(
                        ".github/README.md",
                        "Create .github folder",
                        "# GitHub folder\n"
                    )
                except:
                    pass
            
            # 파일이 이미 존재하는지 확인
            try:
                existing_file = repo.get_contents(workflow_path)
                # 파일이 존재하면 업데이트
                repo.update_file(
                    workflow_path,
                    commit_message,
                    workflow_content,
                    existing_file.sha
                )
                return f"Workflow file updated: {workflow_path}"
            except:
                # 파일이 없으면 생성
                repo.create_file(
                    workflow_path,
                    commit_message,
                    workflow_content
                )
                return f"Workflow file created: {workflow_path}"
                
        except Exception as e:
            print(f"Error details: {e}")
            raise Exception(f"Failed to create workflow file: {e}")
    
    def setup_secrets_batch(self, repo_full_name: str, secrets: Dict[str, str]) -> Dict[str, str]:
        """여러 secrets를 한번에 설정"""
        results = {}
        
        print(f"Setting up secrets for repo: {repo_full_name}")
        print(f"Secrets to create: {list(secrets.keys())}")
        
        for secret_name, secret_value in secrets.items():
            try:
                # GCP_SA_KEY는 특별히 주의해서 처리
                if secret_name == "GCP_SA_KEY":
                    result = self.create_or_update_secret_direct(repo_full_name, secret_name, secret_value)
                else:
                    result = self.create_or_update_secret(repo_full_name, secret_name, secret_value)
                results[secret_name] = "✅ " + result
                print(f"Created secret: {secret_name}")
            except Exception as e:
                results[secret_name] = f"❌ Failed: {str(e)}"
                print(f"Failed to create secret {secret_name}: {e}")
        
        return results
    
    def create_multiple_files(self, repo_full_name: str, files_to_create: Dict[str, str], commit_message: str = "Add multiple files"):
        """여러 파일을 한 번의 커밋으로 생성"""
        repo = self.get_repo(repo_full_name)
        
        try:
            # 현재 main 브랜치의 최신 커밋 SHA 가져오기
            main_branch = repo.get_branch("main")
            main_sha = main_branch.commit.sha
            
            # 트리 요소들 생성
            tree_elements = []
            
            for file_path, content in files_to_create.items():
                # 각 파일을 blob으로 생성
                blob = repo.create_git_blob(content, "utf-8")
                tree_elements.append(
                    repo.create_git_tree_element(
                        path=file_path,
                        mode="100644",  # 일반 파일
                        type="blob",
                        sha=blob.sha
                    )
                )
            
            # 기존 트리 가져오기
            base_tree = repo.get_git_tree(main_sha)
            
            # 새 트리 생성
            new_tree = repo.create_git_tree(tree_elements, base_tree)
            
            # 새 커밋 생성
            new_commit = repo.create_git_commit(
                message=commit_message,
                tree=new_tree,
                parents=[repo.get_git_commit(main_sha)]
            )
            
            # main 브랜치 업데이트
            main_ref = repo.get_git_ref("heads/main")
            main_ref.edit(new_commit.sha)
            
            return f"Successfully created {len(files_to_create)} files in one commit"
            
        except Exception as e:
            print(f"Error creating multiple files: {e}")
            # 실패 시 개별 파일 생성으로 폴백
            results = []
            for file_path, content in files_to_create.items():
                try:
                    self.create_workflow_file(repo_full_name, content, file_path, commit_message)
                    results.append(f"Created: {file_path}")
                except Exception as e:
                    results.append(f"Failed {file_path}: {e}")
            return "\n".join(results)
    
    def create_issue(self, repo: str, title: str, body: str, labels: list = None):
        """GitHub 이슈 생성"""
        try:
            repository = self.get_repo(repo)
            
            # 이슈 생성
            issue = repository.create_issue(
                title=title,
                body=body,
                labels=labels or []
            )
            
            return {
                'number': issue.number,
                'url': issue.html_url,
                'created': True
            }
            
        except Exception as e:
            print(f"Failed to create issue: {e}")
            raise Exception(f"Failed to create issue: {str(e)}")
    
    async def create_or_update_file(self, repo_full_name: str, path: str, content: str, message: str) -> Dict[str, Any]:
        """파일 생성 또는 업데이트 (비동기)"""
        repo = self.get_repo(repo_full_name)
        
        try:
            # 파일이 이미 존재하는지 확인
            try:
                existing_file = repo.get_contents(path)
                # 파일이 존재하면 업데이트
                result = repo.update_file(
                    path=path,
                    message=message,
                    content=content,
                    sha=existing_file.sha
                )
                return {
                    "path": path,
                    "commit": {
                        "sha": result["commit"].sha,
                        "message": message
                    },
                    "action": "updated"
                }
            except GithubException as e:
                if e.status == 404:
                    # 파일이 없으면 생성
                    result = repo.create_file(
                        path=path,
                        message=message,
                        content=content
                    )
                    return {
                        "path": path,
                        "commit": {
                            "sha": result["commit"].sha,
                            "message": message
                        },
                        "action": "created"
                    }
                else:
                    raise
                    
        except Exception as e:
            print(f"Error creating/updating file {path}: {e}")
            raise Exception(f"Failed to create/update file: {str(e)}")
    
    async def create_or_update_secret(self, repo_full_name: str, secret_name: str, secret_value: str):
        """GitHub Repository Secret 생성 또는 업데이트 (비동기 버전)"""
        return self.create_or_update_secret_direct(repo_full_name, secret_name, secret_value)