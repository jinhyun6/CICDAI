<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <div class="header-content">
        <div>
          <h1 class="dashboard-title">CI/CD 대시보드</h1>
          <p class="dashboard-subtitle">
            {{ authStore.user?.email }}님, 환영합니다 👋
          </p>
        </div>
        <div class="header-actions">
          <router-link to="/deployments" class="btn btn-secondary">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M13 2L3 14H12L11 22L21 10H12L13 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            배포 관리
          </router-link>
        </div>
      </div>
    </div>
    
    <div class="dashboard-content">
      <!-- Connection Status -->
      <section class="connection-section">
        <h2 class="section-title">연결 상태</h2>
        <div class="connection-grid">
          <div class="connection-card" :class="{ connected: githubConnected }">
            <div class="card-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M9 19C4.7 19 1 15.3 1 11C1 6.7 4.7 3 9 3C11.9 3 14.4 4.4 15.8 6.5C16.2 6.2 16.7 6 17.3 6C18.6 6 19.6 6.7 20.1 7.7C21.7 8.2 23 9.6 23 11.2C23 13.2 21.3 14.9 19.2 14.9L9 19Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <div class="card-content">
              <h3>GitHub</h3>
              <p class="status-text">
                {{ githubConnected ? `@${githubUsername}` : '연결 필요' }}
              </p>
            </div>
            <div class="card-status">
              <span v-if="githubConnected" class="status-badge connected">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M20 6L9 17L4 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                연결됨
              </span>
              <button v-else-if="githubConnecting" @click="cancelGitHubConnection" class="btn btn-secondary btn-sm">
                취소
              </button>
              <button v-else @click="connectGitHub" class="btn btn-primary btn-sm">
                연결하기
              </button>
            </div>
          </div>
          
          <div class="connection-card" :class="{ connected: gcpConnected }">
            <div class="card-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2L2 7V12C2 18 12 22 12 22S22 18 22 12V7L12 2Z" stroke="currentColor" stroke-width="2"/>
              </svg>
            </div>
            <div class="card-content">
              <h3>Google Cloud</h3>
              <p class="status-text">
                {{ gcpConnected ? 'GCP 계정 연결됨' : '연결 필요' }}
              </p>
            </div>
            <div class="card-status">
              <span v-if="gcpConnected" class="status-badge connected">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M20 6L9 17L4 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                연결됨
              </span>
              <button v-else-if="googleConnecting" @click="cancelGoogleConnection" class="btn btn-secondary btn-sm">
                취소
              </button>
              <button v-else @click="connectGCP" class="btn btn-primary btn-sm">
                연결하기
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- Quick Stats -->
      <section class="stats-section" v-if="githubConnected && gcpConnected">
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M13 2L3 14H12L11 22L21 10H12L13 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <div class="stat-content">
              <h4>전체 배포</h4>
              <p class="stat-value">{{ totalDeployments }}</p>
            </div>
          </div>
          
          <div class="stat-card">
            <div class="stat-icon success">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                <path d="M9 12L11 14L15 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <div class="stat-content">
              <h4>성공적인 배포</h4>
              <p class="stat-value">{{ successfulDeployments }}</p>
            </div>
          </div>
          
          <div class="stat-card">
            <div class="stat-icon info">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                <path d="M12 7V12L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <div class="stat-content">
              <h4>마지막 배포</h4>
              <p class="stat-value">{{ lastDeployTime }}</p>
            </div>
          </div>
        </div>
      </section>

      <!-- Setup Section -->
      <section v-if="githubConnected && gcpConnected" class="setup-section">
        <CICDSetup />
      </section>
      
      <!-- Empty State -->
      <section v-else class="empty-state">
        <div class="empty-content">
          <div class="empty-icon">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L2 7V12C2 18.5 6.5 21.7 12 22C17.5 21.7 22 18.5 22 12V7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M12 8V12L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <h3>CI/CD 설정을 시작하려면</h3>
          <p>GitHub과 Google Cloud를 모두 연결해주세요</p>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import CICDSetup from '../components/CICDSetup.vue'
import { projectsAPI } from '../api/projects'

const route = useRoute()
const authStore = useAuthStore()

// 연결 상태 확인
const githubConnected = computed(() => authStore.hasGithubAccess)
const gcpConnected = computed(() => authStore.hasGoogleAccess)
const githubUsername = computed(() => authStore.user?.github_username || '')

// Loading states
const githubConnecting = ref(false)
const googleConnecting = ref(false)

// Stats
const totalDeployments = ref(0)
const successfulDeployments = ref(0)
const lastDeployTime = ref('없음')

// OAuth 콜백 처리
onMounted(async () => {
  // localStorage에서 OAuth 진행중 상태 확인
  const connectingService = localStorage.getItem('oauth_connecting')
  if (connectingService === 'github') {
    githubConnecting.value = true
    // 30초 후 자동으로 상태 초기화
    setTimeout(() => {
      if (githubConnecting.value) {
        githubConnecting.value = false
        localStorage.removeItem('oauth_connecting')
        alert('GitHub 연결이 완료되지 않았습니다. 다시 시도해주세요.')
      }
    }, 30000)
  } else if (connectingService === 'google') {
    googleConnecting.value = true
    // 30초 후 자동으로 상태 초기화
    setTimeout(() => {
      if (googleConnecting.value) {
        googleConnecting.value = false
        localStorage.removeItem('oauth_connecting')
        alert('Google Cloud 연결이 완료되지 않았습니다. 다시 시도해주세요.')
      }
    }, 30000)
  }
  
  // GitHub OAuth 콜백
  if (route.query.from === 'github' && route.query.code === 'success') {
    console.log('GitHub OAuth callback received')
    githubConnecting.value = false
    localStorage.removeItem('oauth_connecting')
    // GitHub 연결 성공 - 사용자 정보 다시 불러오기
    await authStore.fetchUserInfo()
    // URL 파라미터 제거
    window.history.replaceState({}, document.title, '/dashboard')
  }
  
  // Google OAuth 콜백
  if (route.query.from === 'google' && route.query.code === 'success') {
    console.log('Google OAuth callback received')
    googleConnecting.value = false
    localStorage.removeItem('oauth_connecting')
    // Google 연결 성공 - 사용자 정보 다시 불러오기
    await authStore.fetchUserInfo()
    // URL 파라미터 제거
    window.history.replaceState({}, document.title, '/dashboard')
  }
  
  // OAuth 에러 처리
  if (route.query.error) {
    console.error('OAuth error:', route.query.error)
    githubConnecting.value = false
    googleConnecting.value = false
    localStorage.removeItem('oauth_connecting')
    
    let errorMessage = '연결 실패'
    if (route.query.error === 'github_oauth_not_configured') {
      errorMessage = 'GitHub OAuth가 설정되지 않았습니다.\n\n관리자에게 문의하거나 README.md의 설정 가이드를 참고하세요.'
    } else if (route.query.error === 'google_oauth_not_configured') {
      errorMessage = 'Google OAuth가 설정되지 않았습니다.\n\n관리자에게 문의하거나 README.md의 설정 가이드를 참고하세요.'
    } else if (route.query.error === 'github_auth_failed') {
      errorMessage = 'GitHub 인증에 실패했습니다.\n\nGitHub OAuth 앱 설정을 확인해주세요.'
    } else {
      errorMessage = `연결 실패: ${route.query.error}`
    }
    
    alert(errorMessage)
    window.history.replaceState({}, document.title, '/dashboard')
  }
  
  // Load stats
  if (authStore.isAuthenticated) {
    try {
      const projects = await projectsAPI.getMyProjects()
      totalDeployments.value = projects.length
      successfulDeployments.value = projects.length // 임시
      if (projects.length > 0) {
        const latest = new Date(projects[0].created_at)
        lastDeployTime.value = latest.toLocaleDateString('ko-KR')
      }
    } catch (error) {
      console.error('Failed to load stats:', error)
    }
  }
})

const connectGitHub = async () => {
  githubConnecting.value = true
  // 백엔드 OAuth URL로 이동 (토큰 포함)
  const token = localStorage.getItem('jwt_token')
  if (!token) {
    console.error('No JWT token found')
    githubConnecting.value = false
    alert('로그인이 필요합니다.')
    return
  }
  
  // 연결 상태를 localStorage에 저장
  localStorage.setItem('oauth_connecting', 'github')
  
  const oauthUrl = `http://localhost:8000/api/auth/github/login?token=${token}`
  console.log('Redirecting to GitHub OAuth:', oauthUrl)
  window.location.href = oauthUrl
}

const connectGCP = async () => {
  googleConnecting.value = true
  // 백엔드 OAuth URL로 이동 (토큰 포함)
  const token = localStorage.getItem('jwt_token')
  if (!token) {
    console.error('No JWT token found')
    googleConnecting.value = false
    alert('로그인이 필요합니다.')
    return
  }
  
  // 연결 상태를 localStorage에 저장
  localStorage.setItem('oauth_connecting', 'google')
  
  const oauthUrl = `http://localhost:8000/api/auth/google/login?token=${token}`
  console.log('Redirecting to Google OAuth:', oauthUrl)
  window.location.href = oauthUrl
}

const cancelGitHubConnection = () => {
  githubConnecting.value = false
  localStorage.removeItem('oauth_connecting')
}

const cancelGoogleConnection = () => {
  googleConnecting.value = false
  localStorage.removeItem('oauth_connecting')
}
</script>

<style scoped>
.dashboard {
  min-height: 100vh;
  background: var(--bg-secondary);
}

/* Header */
.dashboard-header {
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-color);
  padding: var(--space-xl) 0;
}

.header-content {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 var(--space-xl);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dashboard-title {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: var(--space-xs);
  letter-spacing: -0.02em;
}

.dashboard-subtitle {
  color: var(--text-secondary);
  font-size: 1.125rem;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: var(--space-md);
}

.header-actions .btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
}

.header-actions svg {
  width: 20px;
  height: 20px;
}

/* Content */
.dashboard-content {
  max-width: 1280px;
  margin: 0 auto;
  padding: var(--space-xl);
}

/* Section Base */
section {
  margin-bottom: var(--space-2xl);
}

.section-title {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: var(--space-lg);
  color: var(--text-primary);
}

/* Connection Section */
.connection-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: var(--space-lg);
}

.connection-card {
  background: var(--bg-primary);
  border: 2px solid var(--border-color);
  border-radius: var(--border-radius);
  padding: var(--space-xl);
  display: flex;
  align-items: center;
  gap: var(--space-lg);
  transition: all 0.3s ease;
}

.connection-card.connected {
  border-color: var(--success);
  background: linear-gradient(to right, rgba(16, 185, 129, 0.05) 0%, var(--bg-primary) 100%);
}

.card-icon {
  width: 56px;
  height: 56px;
  background: var(--bg-secondary);
  border-radius: var(--border-radius);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.connection-card.connected .card-icon {
  background: rgba(16, 185, 129, 0.1);
}

.card-icon svg {
  width: 28px;
  height: 28px;
  color: var(--text-tertiary);
}

.connection-card.connected .card-icon svg {
  color: var(--success);
}

.card-content {
  flex: 1;
}

.card-content h3 {
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: var(--space-xs);
}

.status-text {
  color: var(--text-secondary);
  font-size: 0.875rem;
  margin: 0;
}

.card-status {
  flex-shrink: 0;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-xs) var(--space-md);
  background: var(--bg-secondary);
  color: var(--text-secondary);
  border-radius: 100px;
  font-size: 0.875rem;
  font-weight: 500;
}

.status-badge.connected {
  background: rgba(16, 185, 129, 0.1);
  color: var(--success);
}

.status-badge svg {
  width: 16px;
  height: 16px;
}

/* Stats Section */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--space-lg);
}

.stat-card {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  padding: var(--space-lg);
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.stat-icon {
  width: 48px;
  height: 48px;
  background: var(--primary-light);
  border-radius: var(--border-radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-icon svg {
  width: 24px;
  height: 24px;
  color: var(--primary);
}

.stat-icon.success {
  background: rgba(16, 185, 129, 0.1);
}

.stat-icon.success svg {
  color: var(--success);
}

.stat-icon.info {
  background: rgba(59, 130, 246, 0.1);
}

.stat-icon.info svg {
  color: var(--info);
}

.stat-content h4 {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: var(--space-xs);
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

/* Setup Section */
.setup-section {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-lg);
  padding: var(--space-xl);
  box-shadow: var(--shadow);
}

/* Empty State */
.empty-state {
  background: var(--bg-primary);
  border: 2px dashed var(--border-color);
  border-radius: var(--border-radius-lg);
  padding: var(--space-2xl);
  text-align: center;
}

.empty-content {
  max-width: 400px;
  margin: 0 auto;
}

.empty-icon {
  width: 80px;
  height: 80px;
  background: var(--bg-secondary);
  border-radius: var(--border-radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto var(--space-lg);
}

.empty-icon svg {
  width: 40px;
  height: 40px;
  color: var(--text-tertiary);
}

.empty-content h3 {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: var(--space-sm);
}

.empty-content p {
  color: var(--text-secondary);
  margin: 0;
}

/* Responsive */
@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: var(--space-lg);
    text-align: center;
  }
  
  .connection-grid,
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .connection-card {
    flex-direction: column;
    text-align: center;
  }
}
</style>