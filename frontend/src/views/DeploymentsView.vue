<template>
  <div class="deployments-view">
    <h1>🚀 배포 관리</h1>
    
    <div class="deployments-container">
      <!-- 저장된 배포 목록 -->
      <div class="saved-deployments">
        <h2>내 배포 프로젝트</h2>
        
        <div v-if="loading" class="loading">
          프로젝트를 불러오는 중...
        </div>
        
        <div v-else-if="error" class="error-message">
          {{ error }}
        </div>
        
        <div v-else-if="savedDeployments.length === 0" class="no-deployments">
          아직 설정된 CI/CD 배포가 없습니다.
        </div>
        
        <div v-else class="deployment-cards">
          <div v-for="deployment in savedDeployments" 
               :key="deployment.id" 
               class="deployment-card"
               :class="{ active: selectedDeployment?.id === deployment.id }"
               @click="selectDeployment(deployment)">
            <div class="card-header">
              <h3>{{ deployment.serviceName }}</h3>
              <span class="timestamp">{{ formatDate(deployment.timestamp) }}</span>
            </div>
            <div class="card-body">
              <p><strong>Repository:</strong> {{ deployment.githubRepo }}</p>
              <p><strong>Project:</strong> {{ deployment.projectId }}</p>
              <p><strong>Region:</strong> {{ deployment.region }}</p>
            </div>
            <div class="card-footer">
              <a :href="deployment.deploymentUrl" target="_blank" class="deployment-link">
                🌐 {{ deployment.deploymentUrl }}
              </a>
              <div class="card-actions">
                <button 
                  @click="showRollbackModal(deployment)" 
                  class="btn btn-secondary btn-sm"
                  title="이전 버전으로 롤백"
                >
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M1 4V10H1M1 10H7M1 10L5 14C6.5 12.5 8.79 11 12 11C16.5 11 20 14.5 20 19M23 20V14H23M23 14H17M23 14L19 10C17.5 11.5 15.21 13 12 13C7.5 13 4 16.5 4 21" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                  롤백
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 선택된 배포의 상태 모니터링 -->
      <div v-if="selectedDeployment" class="deployment-monitor">
        <DeploymentStatus 
          :owner="getRepoOwner(selectedDeployment.githubRepo)" 
          :repo="getRepoName(selectedDeployment.githubRepo)" 
        />
      </div>
    </div>
    
    <!-- 롤백 모달 -->
    <div v-if="showingRollbackModal" class="modal-overlay" @click.self="showingRollbackModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>🔄 롤백</h3>
          <button @click="showingRollbackModal = false" class="modal-close">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </div>
        
        <div class="modal-body">
          <p class="rollback-info">
            <strong>{{ rollbackTarget?.serviceName }}</strong>를 이전 버전으로 롤백합니다.
          </p>
          
          <div v-if="revisions.length > 0" class="revisions-list">
            <h4>현재 리비전 상태</h4>
            <div v-for="(revision, index) in revisions.slice(0, 5)" :key="revision.name" class="revision-item">
              <div class="revision-info">
                <span class="revision-name">{{ revision.name }}</span>
                <span v-if="revision.is_active" class="revision-badge active">현재 활성</span>
                <span v-if="index === 1" class="revision-badge target">롤백 대상</span>
              </div>
              <div class="revision-meta">
                <span class="revision-date">{{ new Date(revision.created_at).toLocaleString('ko-KR') }}</span>
              </div>
            </div>
          </div>
          
          <div v-if="rollbackError" class="alert alert-error">
            {{ rollbackError }}
          </div>
          
          <div class="rollback-warning">
            ⚠️ <strong>주의:</strong> 롤백 후 현재 버전의 문제를 해결하고 다시 배포해야 합니다.
          </div>
        </div>
        
        <div class="modal-footer">
          <button @click="showingRollbackModal = false" class="btn btn-secondary">
            취소
          </button>
          <button 
            @click="performRollback" 
            class="btn btn-danger"
            :disabled="rollbackLoading || revisions.length < 2"
          >
            {{ rollbackLoading ? '롤백 중...' : '롤백 실행' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import DeploymentStatus from '../components/DeploymentStatus.vue'
import { projectsAPI } from '../api/projects'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()
const savedDeployments = ref([])
const selectedDeployment = ref(null)
const loading = ref(true)
const error = ref(null)

// API에서 배포 정보 불러오기
onMounted(async () => {
  if (!authStore.isAuthenticated) {
    router.push('/login')
    return
  }
  
  try {
    loading.value = true
    const projects = await projectsAPI.getMyProjects()
    savedDeployments.value = projects.map(project => ({
      serviceName: project.service_name,
      githubRepo: project.github_repo,
      projectId: project.gcp_project_id,
      region: project.region,
      deploymentUrl: project.deployment_url,
      timestamp: project.created_at,
      id: project.id
    }))
    
    // 첫 번째 배포 자동 선택
    if (savedDeployments.value.length > 0) {
      selectedDeployment.value = savedDeployments.value[0]
    }
  } catch (err) {
    console.error('Failed to load projects:', err)
    error.value = '프로젝트를 불러올 수 없습니다.'
  } finally {
    loading.value = false
  }
})

// 롤백 관련
const showingRollbackModal = ref(false)
const rollbackTarget = ref(null)
const rollbackLoading = ref(false)
const rollbackError = ref('')
const revisions = ref([])

const showRollbackModal = async (deployment) => {
  rollbackTarget.value = deployment
  showingRollbackModal.value = true
  rollbackError.value = ''
  
  // 리비전 목록 가져오기
  try {
    const response = await fetch(`http://localhost:8000/api/rollback/revisions/${deployment.id}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`
      }
    })
    
    if (response.ok) {
      const data = await response.json()
      revisions.value = data.revisions
    } else {
      rollbackError.value = '리비전 목록을 가져올 수 없습니다.'
    }
  } catch (err) {
    rollbackError.value = '리비전 목록을 가져오는 중 오류가 발생했습니다.'
  }
}

const performRollback = async () => {
  if (!rollbackTarget.value || !confirm('정말로 이전 버전으로 롤백하시겠습니까?')) {
    return
  }
  
  rollbackLoading.value = true
  rollbackError.value = ''
  
  try {
    const response = await fetch(`http://localhost:8000/api/rollback/rollback/${rollbackTarget.value.id}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`,
        'Content-Type': 'application/json'
      }
    })
    
    if (response.ok) {
      const result = await response.json()
      alert(`롤백 성공: ${result.message}`)
      showingRollbackModal.value = false
      // 페이지 새로고침
      window.location.reload()
    } else {
      const error = await response.json()
      rollbackError.value = error.detail || '롤백에 실패했습니다.'
    }
  } catch (err) {
    rollbackError.value = '롤백 중 오류가 발생했습니다.'
  } finally {
    rollbackLoading.value = false
  }
}

// 배포 선택
const selectDeployment = (deployment) => {
  selectedDeployment.value = deployment
}

// GitHub repo에서 owner와 repo 이름 추출
const getRepoOwner = (repoFullName) => {
  return repoFullName ? repoFullName.split('/')[0] : ''
}

const getRepoName = (repoFullName) => {
  return repoFullName ? repoFullName.split('/')[1] : ''
}

// 날짜 포맷팅
const formatDate = (timestamp) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date
  
  if (diff < 3600000) {
    return `${Math.floor(diff / 60000)}분 전`
  } else if (diff < 86400000) {
    return `${Math.floor(diff / 3600000)}시간 전`
  } else {
    return date.toLocaleDateString('ko-KR')
  }
}
</script>

<style scoped>
.deployments-view {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.deployments-view h1 {
  margin-bottom: 2rem;
  color: #2c3e50;
}

.deployments-container {
  display: grid;
  grid-template-columns: 400px 1fr;
  gap: 2rem;
  align-items: start;
}

.saved-deployments {
  background: #f8f9fa;
  padding: 1.5rem;
  border-radius: 8px;
}

.saved-deployments h2 {
  margin: 0 0 1.5rem 0;
  color: #34495e;
  font-size: 1.3rem;
}

.no-deployments {
  text-align: center;
  color: #7f8c8d;
  padding: 2rem;
  background: white;
  border-radius: 4px;
}

.loading {
  text-align: center;
  color: #3498db;
  padding: 2rem;
  background: white;
  border-radius: 4px;
}

.error-message {
  text-align: center;
  color: #e74c3c;
  padding: 2rem;
  background: #fff5f5;
  border-radius: 4px;
  border: 1px solid #ffdddd;
}

.deployment-cards {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.deployment-card {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 1rem;
  cursor: pointer;
  transition: all 0.2s;
}

.deployment-card:hover {
  border-color: #3498db;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.deployment-card.active {
  border-color: #3498db;
  background: #f0f8ff;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.card-header h3 {
  margin: 0;
  color: #2c3e50;
  font-size: 1.1rem;
}

.timestamp {
  font-size: 0.85rem;
  color: #7f8c8d;
}

.card-body p {
  margin: 0.25rem 0;
  font-size: 0.9rem;
  color: #555;
}

.card-body strong {
  color: #34495e;
}

.card-footer {
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid #eee;
}

.deployment-link {
  color: #3498db;
  text-decoration: none;
  font-size: 0.85rem;
  word-break: break-all;
}

.deployment-link:hover {
  text-decoration: underline;
}

.card-actions {
  margin-top: var(--space-sm);
  display: flex;
  gap: var(--space-sm);
}

.card-actions .btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
}

.card-actions .btn svg {
  width: 16px;
  height: 16px;
}

.deployment-monitor {
  flex: 1;
}

/* 반응형 디자인 */
@media (max-width: 1024px) {
  .deployments-container {
    grid-template-columns: 1fr;
  }
  
  .saved-deployments {
    max-width: 600px;
    margin: 0 auto;
  }
}

/* 모달 스타일 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: var(--space-xl);
}

.modal-content {
  background: var(--bg-primary);
  border-radius: var(--border-radius-lg);
  box-shadow: var(--shadow-xl);
  max-width: 600px;
  width: 100%;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  padding: var(--space-lg);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.5rem;
}

.modal-close {
  background: none;
  border: none;
  cursor: pointer;
  padding: var(--space-xs);
  color: var(--text-secondary);
  transition: var(--transition);
}

.modal-close:hover {
  color: var(--text-primary);
}

.modal-close svg {
  width: 24px;
  height: 24px;
}

.modal-body {
  padding: var(--space-lg);
  overflow-y: auto;
  flex: 1;
}

.rollback-info {
  margin-bottom: var(--space-lg);
  color: var(--text-secondary);
}

.revisions-list {
  margin-bottom: var(--space-lg);
}

.revisions-list h4 {
  font-size: 1rem;
  margin-bottom: var(--space-md);
  color: var(--text-primary);
}

.revision-item {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-sm);
  padding: var(--space-md);
  margin-bottom: var(--space-sm);
}

.revision-info {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-xs);
}

.revision-name {
  font-family: var(--font-mono);
  font-size: 0.875rem;
  color: var(--text-primary);
}

.revision-badge {
  padding: 2px 8px;
  border-radius: 100px;
  font-size: 0.75rem;
  font-weight: 500;
}

.revision-badge.active {
  background: var(--success);
  color: white;
}

.revision-badge.target {
  background: var(--info);
  color: white;
}

.revision-meta {
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.rollback-warning {
  background: #fef3c7;
  color: #92400e;
  padding: var(--space-md);
  border-radius: var(--border-radius-sm);
  margin-top: var(--space-lg);
}

.modal-footer {
  padding: var(--space-lg);
  border-top: 1px solid var(--border-color);
  display: flex;
  justify-content: flex-end;
  gap: var(--space-sm);
}

.btn-danger {
  background: var(--danger);
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background: #dc2626;
}
</style>