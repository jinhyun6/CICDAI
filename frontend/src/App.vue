<template>
  <div id="app">
    <nav class="navbar">
      <div class="navbar-container">
        <router-link to="/" class="navbar-logo">
          <svg class="logo-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2L2 7V12C2 18.5 6.5 21.7 12 22C17.5 21.7 22 18.5 22 12V7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M12 8V12L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span class="logo-text">CI/CD AI</span>
        </router-link>
        
        <div class="navbar-menu">
          <router-link to="/" class="nav-link" exact-active-class="active">
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M3 9L12 2L21 9V20C21 21.1 20.1 22 19 22H5C3.9 22 3 21.1 3 20V9Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span>홈</span>
          </router-link>
          
          <router-link to="/dashboard" v-if="authStore.isAuthenticated" class="nav-link" active-class="active">
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect x="3" y="3" width="7" height="7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <rect x="14" y="3" width="7" height="7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <rect x="14" y="14" width="7" height="7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <rect x="3" y="14" width="7" height="7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span>대시보드</span>
          </router-link>
          
          <router-link to="/deployments" v-if="authStore.isAuthenticated" class="nav-link" active-class="active">
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M13 2L3 14H12L11 22L21 10H12L13 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span>배포 관리</span>
          </router-link>
        </div>
        
        <div class="navbar-actions">
          <button v-if="!authStore.isAuthenticated" @click="login" class="btn btn-primary">
            시작하기
          </button>
          
          <div v-else class="user-menu">
            <div class="user-avatar">
              {{ authStore.user?.email?.charAt(0).toUpperCase() }}
            </div>
            <span class="user-email">{{ authStore.user?.email }}</span>
            <button @click="logout" class="btn btn-secondary btn-sm">
              로그아웃
            </button>
          </div>
        </div>
      </div>
    </nav>
    
    <main class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'

const router = useRouter()
const authStore = useAuthStore()

// 인증 상태 초기화
onMounted(async () => {
  await authStore.initialize()
})

const login = () => {
  router.push('/login')
}

const logout = () => {
  authStore.logout()
  router.push('/')
}
</script>

<style scoped>
#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* Navbar Styles */
.navbar {
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-color);
  position: sticky;
  top: 0;
  z-index: 100;
  backdrop-filter: blur(10px);
  background: rgba(255, 255, 255, 0.95);
}

.navbar-container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 var(--space-xl);
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

/* Logo */
.navbar-logo {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  text-decoration: none;
  color: var(--text-primary);
  font-weight: 600;
  font-size: 1.25rem;
  transition: var(--transition);
}

.navbar-logo:hover {
  color: var(--primary);
}

.logo-icon {
  width: 32px;
  height: 32px;
  color: var(--primary);
}

.logo-text {
  background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* Navigation Menu */
.navbar-menu {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.nav-link {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-xs) var(--space-md);
  color: var(--text-secondary);
  text-decoration: none;
  border-radius: var(--border-radius-sm);
  transition: var(--transition);
  font-weight: 500;
}

.nav-link:hover {
  color: var(--text-primary);
  background: var(--gray-100);
}

.nav-link.active {
  color: var(--primary);
  background: var(--primary-light);
}

.nav-icon {
  width: 20px;
  height: 20px;
}

/* User Menu */
.navbar-actions {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.user-menu {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 1rem;
}

.user-email {
  color: var(--text-secondary);
  font-size: 0.875rem;
  font-weight: 500;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Main Content */
.main-content {
  flex: 1;
  width: 100%;
}

/* Responsive */
@media (max-width: 768px) {
  .navbar-container {
    padding: 0 var(--space-md);
  }
  
  .navbar-menu {
    display: none;
  }
  
  .user-email {
    display: none;
  }
  
  .logo-text {
    font-size: 1.125rem;
  }
}

@media (max-width: 1024px) {
  .nav-link span {
    display: none;
  }
  
  .nav-link {
    padding: var(--space-sm);
  }
}
</style>