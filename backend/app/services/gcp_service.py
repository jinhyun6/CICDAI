from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
#from google.cloud import iam_admin_v1
from google.oauth2 import service_account
import json
import time
from typing import Dict, List

class GCPService:
    def __init__(self, access_token: str):
        self.credentials = Credentials(token=access_token)
        
    def create_service_account(self, project_id: str, account_id: str = None) -> Dict:
        """서비스 계정 생성"""
        if not account_id:
            # 고유한 서비스 계정 ID 생성
            account_id = f"github-actions-{int(time.time())}"
        
        iam_service = build('iam', 'v1', credentials=self.credentials)
        
        service_account_email = f"{account_id}@{project_id}.iam.gserviceaccount.com"
        
        try:
            # 서비스 계정 생성
            request_body = {
                'accountId': account_id,
                'serviceAccount': {
                    'displayName': 'GitHub Actions CI/CD',
                    'description': 'Service account for GitHub Actions deployment'
                }
            }
            
            request = iam_service.projects().serviceAccounts().create(
                name=f'projects/{project_id}',
                body=request_body
            )
            
            service_account = request.execute()
            print(f"Created service account: {service_account_email}")
            
            return {
                'email': service_account['email'],
                'name': service_account['name'],
                'projectId': project_id
            }
            
        except Exception as e:
            # 이미 존재하는 경우
            if 'already exists' in str(e):
                print(f"Service account already exists: {service_account_email}")
                return {
                    'email': service_account_email,
                    'name': f"projects/{project_id}/serviceAccounts/{service_account_email}",
                    'projectId': project_id
                }
            else:
                raise Exception(f"Failed to create service account: {e}")
    
    def grant_permissions(self, project_id: str, service_account_email: str) -> bool:
        """서비스 계정에 필요한 권한 부여"""
        resource_manager = build('cloudresourcemanager', 'v1', credentials=self.credentials)
        
        # 필요한 역할들
        roles = [
            'roles/run.admin',           # Cloud Run 관리
            'roles/storage.admin',       # Cloud Storage (이미지 저장)
            'roles/cloudbuild.builds.builder',  # Cloud Build
            'roles/artifactregistry.admin',     # Artifact Registry
            'roles/iam.serviceAccountUser'      # 서비스 계정 사용
        ]
        
        try:
            # 현재 IAM 정책 가져오기
            policy = resource_manager.projects().getIamPolicy(
                resource=project_id
            ).execute()
            
            # 각 역할에 서비스 계정 추가
            for role in roles:
                binding = None
                for b in policy.get('bindings', []):
                    if b['role'] == role:
                        binding = b
                        break
                
                if binding is None:
                    binding = {
                        'role': role,
                        'members': []
                    }
                    policy['bindings'].append(binding)
                
                member = f"serviceAccount:{service_account_email}"
                if member not in binding['members']:
                    binding['members'].append(member)
            
            # 업데이트된 정책 설정
            request = resource_manager.projects().setIamPolicy(
                resource=project_id,
                body={'policy': policy}
            )
            request.execute()
            
            print(f"Granted permissions to {service_account_email}")
            return True
            
        except Exception as e:
            print(f"Error granting permissions: {str(e)}")
            print(f"Error type: {type(e)}")
            # 권한 에러이지만 계속 진행
            if "403" in str(e) or "does not have" in str(e):
                print("Permission error - continuing anyway (user needs to grant permissions manually)")
                return True
            raise Exception(f"Failed to grant permissions: {e}")
    
    def create_service_account_key(self, project_id: str, service_account_email: str) -> str:
        """서비스 계정 키 생성"""
        iam_service = build('iam', 'v1', credentials=self.credentials)
        
        try:
            # 키 생성
            key = iam_service.projects().serviceAccounts().keys().create(
                name=f'projects/{project_id}/serviceAccounts/{service_account_email}',
                body={}
            ).execute()
            
            # Base64로 인코딩된 키 반환
            private_key_data = key['privateKeyData']
            
            # Base64 디코딩하여 JSON 확인 (디버깅용)
            import base64
            key_json = base64.b64decode(private_key_data).decode('utf-8')
            print(f"Created key for: {service_account_email}")
            
            return private_key_data  # Base64 인코딩된 상태로 반환
            
        except Exception as e:
            print(f"Error creating service account key: {str(e)}")
            print(f"Error type: {type(e)}")
            raise Exception(f"Failed to create service account key: {e}")
    
    def enable_apis(self, project_id: str) -> Dict[str, bool]:
        """필요한 GCP API 활성화"""
        service_usage = build('serviceusage', 'v1', credentials=self.credentials)
        
        required_apis = [
            'cloudbuild.googleapis.com',
            'run.googleapis.com',
            'artifactregistry.googleapis.com',
            'secretmanager.googleapis.com',
            'containerregistry.googleapis.com',
            'cloudresourcemanager.googleapis.com',  # 프로젝트 목록 조회용
            'iam.googleapis.com',  # 서비스 계정 관리용
            'compute.googleapis.com'  # Cloud Run에 필요
        ]
        
        results = {}
        
        for api in required_apis:
            try:
                # API 활성화
                request = service_usage.services().enable(
                    name=f'projects/{project_id}/services/{api}'
                )
                request.execute()
                results[api] = True
                print(f"Enabled API: {api}")
                
                # API 활성화는 시간이 걸리므로 잠시 대기
                time.sleep(2)
                
            except Exception as e:
                if 'already enabled' in str(e).lower():
                    results[api] = True
                    print(f"API already enabled: {api}")
                else:
                    results[api] = False
                    print(f"Failed to enable API {api}: {e}")
        
        return results
    
    def get_service_revisions(self, project_id: str, region: str, service_name: str):
        """Cloud Run 서비스의 리비전 목록 가져오기"""
        try:
            run_service = build('run', 'v1', credentials=self.credentials)
            
            parent = f"projects/{project_id}/locations/{region}"
            service_path = f"{parent}/services/{service_name}"
            
            # 서비스 정보 가져오기
            service = run_service.projects().locations().services().get(
                name=service_path
            ).execute()
            
            # 리비전 목록 가져오기
            revisions_response = run_service.projects().locations().revisions().list(
                parent=parent,
                labelSelector=f"serving.knative.dev/service={service_name}"
            ).execute()
            
            revisions = revisions_response.get('items', [])
            
            # 현재 트래픽 정보
            traffic = service.get('status', {}).get('traffic', [])
            traffic_map = {t['revisionName']: t.get('percent', 0) for t in traffic}
            
            # 리비전 정보 포맷팅
            formatted_revisions = []
            for rev in revisions:
                rev_name = rev['metadata']['name']
                formatted_revisions.append({
                    'name': rev_name,
                    'metadata': rev.get('metadata', {}),
                    'spec': rev.get('spec', {}),
                    'is_active': rev_name in traffic_map,
                    'traffic_percent': traffic_map.get(rev_name, 0)
                })
            
            # 생성 시간 기준으로 정렬 (최신 순)
            formatted_revisions.sort(
                key=lambda x: x['metadata'].get('creationTimestamp', ''),
                reverse=True
            )
            
            return formatted_revisions
            
        except Exception as e:
            print(f"Failed to get revisions: {e}")
            raise Exception(f"Failed to get revisions: {str(e)}")
    
    def update_traffic(self, project_id: str, region: str, service_name: str, traffic_allocation: dict):
        """Cloud Run 서비스의 트래픽 분배 업데이트"""
        try:
            run_service = build('run', 'v1', credentials=self.credentials)
            
            parent = f"projects/{project_id}/locations/{region}"
            service_path = f"{parent}/services/{service_name}"
            
            # 현재 서비스 정보 가져오기
            service = run_service.projects().locations().services().get(
                name=service_path
            ).execute()
            
            # 트래픽 설정 업데이트
            traffic = []
            for revision_name, percent in traffic_allocation.items():
                traffic.append({
                    'revisionName': revision_name,
                    'percent': percent
                })
            
            service['spec']['traffic'] = traffic
            
            # 서비스 업데이트
            response = run_service.projects().locations().services().replaceService(
                name=service_path,
                body=service
            ).execute()
            
            return {
                'success': True,
                'url': response.get('status', {}).get('url'),
                'traffic': traffic
            }
            
        except Exception as e:
            print(f"Failed to update traffic: {e}")
            raise Exception(f"Failed to update traffic: {str(e)}")