<template>
  <div class="login-view">
    <div class="login-background">
      <div class="bg-gradient"></div>
      <div class="bg-pattern"></div>
    </div>
    
    <div class="login-container">
      <div class="login-card">
        <div class="login-header">
          <router-link to="/" class="back-link">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M19 12H5M5 12L12 19M5 12L12 5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            뒤로가기
          </router-link>
          
          <div class="logo-section">
            <div class="logo-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2L2 7V12C2 18.5 6.5 21.7 12 22C17.5 21.7 22 18.5 22 12V7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M12 8V12L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <h1 class="login-title">{{ isLogin ? '로그인' : '회원가입' }}</h1>
            <p class="login-subtitle">
              {{ isLogin 
                ? '다시 만나서 반가워요' 
                : 'CI/CD AI에 오신 것을 환영합니다' }}
            </p>
          </div>
        </div>
        
        <!-- 이메일/비밀번호 로그인 -->
        <form @submit.prevent="handleSubmit" class="auth-form">
          <div class="form-group">
            <label for="email" class="form-label">이메일</label>
            <div class="input-wrapper">
              <svg class="input-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M4 4H20C21.1 4 22 4.9 22 6V18C22 19.1 21.1 20 20 20H4C2.9 20 2 19.1 2 18V6C2 4.9 2.9 4 4 4Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M22 6L12 13L2 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <input
                type="email"
                id="email"
                v-model="formData.email"
                class="form-input"
                required
                placeholder="your@email.com"
              />
            </div>
          </div>
          
          <div class="form-group">
            <label for="password" class="form-label">비밀번호</label>
            <div class="input-wrapper">
              <svg class="input-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="5" y="11" width="14" height="10" rx="2" ry="2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M7 11V7C7 5.67392 7.52678 4.40215 8.46447 3.46447C9.40215 2.52678 10.6739 2 12 2C13.3261 2 14.5979 2.52678 15.5355 3.46447C16.4732 4.40215 17 5.67392 17 7V11" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <input
                type="password"
                id="password"
                v-model="formData.password"
                class="form-input"
                required
                :placeholder="isLogin ? '비밀번호 입력' : '최소 8자 이상'"
              />
            </div>
          </div>
          
          <div v-if="!isLogin" class="form-group">
            <label for="passwordConfirm" class="form-label">비밀번호 확인</label>
            <div class="input-wrapper">
              <svg class="input-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M9 11L12 14L22 4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M21 12V19C21 20.1 20.1 21 19 21H5C3.9 21 3 20.1 3 19V5C3 3.9 3.9 3 5 3H16" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <input
                type="password"
                id="passwordConfirm"
                v-model="formData.passwordConfirm"
                class="form-input"
                required
                placeholder="비밀번호 재입력"
              />
            </div>
          </div>
          
          <button type="submit" class="btn btn-primary btn-lg submit-btn" :disabled="loading">
            <span v-if="!loading">{{ isLogin ? '로그인' : '회원가입' }}</span>
            <span v-else class="loading-spinner"></span>
          </button>
        </form>
        
        <div v-if="error" class="alert alert-error">
          {{ error }}
        </div>
        
        <!-- OAuth 로그인 -->
        <div class="oauth-section">
          <div class="divider">
            <span>또는 소셜 계정으로</span>
          </div>
          
          <div class="oauth-buttons">
            <button @click="loginWithGitHub" class="oauth-btn" :disabled="loading">
              <svg class="oauth-icon" viewBox="0 0 24 24">
                <path fill="currentColor" d="M12,2A10,10 0 0,0 2,12C2,16.42 4.87,20.17 8.84,21.5C9.34,21.58 9.5,21.27 9.5,21C9.5,20.77 9.5,20.14 9.5,19.31C6.73,19.91 6.14,17.97 6.14,17.97C5.68,16.81 5.03,16.5 5.03,16.5C4.12,15.88 5.1,15.9 5.1,15.9C6.1,15.97 6.63,16.93 6.63,16.93C7.5,18.45 8.97,18 9.54,17.76C9.63,17.11 9.89,16.67 10.17,16.42C7.95,16.17 5.62,15.31 5.62,11.5C5.62,10.39 6,9.5 6.65,8.79C6.55,8.54 6.2,7.5 6.75,6.15C6.75,6.15 7.59,5.88 9.5,7.17C10.29,6.95 11.15,6.84 12,6.84C12.85,6.84 13.71,6.95 14.5,7.17C16.41,5.88 17.25,6.15 17.25,6.15C17.8,7.5 17.45,8.54 17.35,8.79C18,9.5 18.38,10.39 18.38,11.5C18.38,15.32 16.04,16.16 13.81,16.41C14.17,16.72 14.5,17.33 14.5,18.26C14.5,19.6 14.5,20.68 14.5,21C14.5,21.27 14.66,21.59 15.17,21.5C19.14,20.16 22,16.42 22,12A10,10 0 0,0 12,2Z" />
              </svg>
              <span>GitHub로 계속하기</span>
            </button>
            
            <button @click="loginWithGoogle" class="oauth-btn" :disabled="loading">
              <svg class="oauth-icon" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              <span>Google로 계속하기</span>
            </button>
          </div>
        </div>
        
        <div class="form-footer">
          <p v-if="isLogin">
            계정이 없으신가요?
            <a href="#" @click.prevent="isLogin = false" class="link">회원가입</a>
          </p>
          <p v-else>
            이미 계정이 있으신가요?
            <a href="#" @click.prevent="isLogin = true" class="link">로그인</a>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const isLogin = ref(true)
const loading = ref(false)
const error = ref('')

const formData = ref({
  email: '',
  password: '',
  passwordConfirm: ''
})

const handleSubmit = async () => {
  error.value = ''
  
  // 회원가입 시 비밀번호 확인
  if (!isLogin.value && formData.value.password !== formData.value.passwordConfirm) {
    error.value = '비밀번호가 일치하지 않습니다.'
    return
  }
  
  loading.value = true
  
  try {
    let result
    if (isLogin.value) {
      result = await authStore.login({
        email: formData.value.email,
        password: formData.value.password
      })
    } else {
      result = await authStore.register({
        email: formData.value.email,
        password: formData.value.password
      })
    }
    
    if (result.success) {
      router.push('/dashboard')
    } else {
      error.value = result.error
    }
  } catch (err) {
    error.value = '오류가 발생했습니다.'
  } finally {
    loading.value = false
  }
}

// OAuth 로그인
const loginWithGitHub = () => {
  // GitHub OAuth는 로그인 후 처리됨
  error.value = '로그인 후 GitHub 계정을 연결할 수 있습니다.'
}

const loginWithGoogle = () => {
  // Google OAuth는 로그인 후 처리됨
  error.value = '로그인 후 Google 계정을 연결할 수 있습니다.'
}
</script>

<style scoped>
.login-view {
  min-height: 100vh;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-xl);
}

/* Background */
.login-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
  z-index: 0;
}

.bg-gradient {
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: linear-gradient(135deg, var(--primary-light) 0%, var(--secondary) 30%, var(--primary) 100%);
  opacity: 0.05;
  animation: gradient-rotate 30s ease infinite;
}

@keyframes gradient-rotate {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.bg-pattern {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: 
    radial-gradient(circle at 20% 80%, var(--primary-light) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, var(--secondary) 0%, transparent 50%),
    radial-gradient(circle at 40% 40%, var(--primary) 0%, transparent 50%);
  opacity: 0.03;
}

/* Login Container */
.login-container {
  position: relative;
  z-index: 10;
  width: 100%;
  max-width: 480px;
}

.login-card {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-lg);
  box-shadow: var(--shadow-xl);
  overflow: hidden;
}

/* Header */
.login-header {
  padding: var(--space-xl);
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 0.875rem;
  transition: var(--transition);
  margin-bottom: var(--space-lg);
}

.back-link:hover {
  color: var(--primary);
}

.back-link svg {
  width: 16px;
  height: 16px;
}

.logo-section {
  text-align: center;
}

.logo-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto var(--space-md);
  background: var(--primary-light);
  border-radius: var(--border-radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-icon svg {
  width: 32px;
  height: 32px;
  color: var(--primary);
}

.login-title {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: var(--space-sm);
  letter-spacing: -0.02em;
}

.login-subtitle {
  color: var(--text-secondary);
  font-size: 1rem;
  margin: 0;
}

/* Form */
.auth-form {
  padding: var(--space-xl);
}

.input-wrapper {
  position: relative;
}

.input-icon {
  position: absolute;
  left: var(--space-md);
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 20px;
  color: var(--text-tertiary);
  pointer-events: none;
}

.form-input {
  width: 100%;
  padding: var(--space-sm) var(--space-md);
  padding-left: calc(var(--space-xl) + 20px);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-sm);
  font-size: 1rem;
  font-family: var(--font-family);
  background: var(--bg-primary);
  color: var(--text-primary);
  transition: var(--transition);
}

.form-input:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-light);
}

.form-input:focus ~ .input-icon {
  color: var(--primary);
}

.submit-btn {
  width: 100%;
  margin-top: var(--space-lg);
  position: relative;
}

.submit-btn:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

/* OAuth Section */
.oauth-section {
  padding: 0 var(--space-xl) var(--space-xl);
}

.divider {
  text-align: center;
  margin: var(--space-lg) 0;
  position: relative;
}

.divider::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 1px;
  background: var(--border-color);
}

.divider span {
  background: var(--bg-primary);
  padding: 0 var(--space-md);
  position: relative;
  color: var(--text-tertiary);
  font-size: 0.875rem;
}

.oauth-buttons {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.oauth-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  width: 100%;
  padding: var(--space-sm) var(--space-lg);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-sm);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-weight: 500;
  cursor: pointer;
  transition: var(--transition);
}

.oauth-btn:hover:not(:disabled) {
  background: var(--bg-secondary);
  border-color: var(--gray-300);
  transform: translateY(-1px);
  box-shadow: var(--shadow);
}

.oauth-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.oauth-icon {
  width: 20px;
  height: 20px;
}

/* Form Footer */
.form-footer {
  padding: var(--space-lg) var(--space-xl) var(--space-xl);
  text-align: center;
  color: var(--text-secondary);
  font-size: 0.875rem;
  border-top: 1px solid var(--border-color);
}

.form-footer p {
  margin: 0;
}

.link {
  color: var(--primary);
  text-decoration: none;
  font-weight: 500;
  transition: var(--transition);
}

.link:hover {
  color: var(--primary-hover);
  text-decoration: underline;
}

/* Alert */
.alert {
  margin: 0 var(--space-xl);
  margin-top: calc(var(--space-lg) * -1);
  margin-bottom: var(--space-lg);
}

/* Loading State */
.loading-spinner {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 0.8s linear infinite;
}

/* Responsive */
@media (max-width: 480px) {
  .login-card {
    border-radius: 0;
    border: none;
    box-shadow: none;
  }
  
  .login-view {
    padding: 0;
  }
  
  .login-container {
    max-width: 100%;
  }
}
</style>