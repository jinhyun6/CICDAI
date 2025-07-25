import { defineStore } from 'pinia'
import axios from 'axios'
import { API_BASE_URL } from '../config/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: null,
    isAuthenticated: false,
    githubConnected: false,
    googleConnected: false
  }),

  getters: {
    currentUser: (state) => state.user,
    isLoggedIn: (state) => state.isAuthenticated,
    hasGithubAccess: (state) => state.githubConnected,
    hasGoogleAccess: (state) => state.googleConnected
  },

  actions: {
    // 초기화 - localStorage에서 토큰 확인
    async initialize() {
      const token = localStorage.getItem('jwt_token')
      if (token) {
        this.token = token
        this.isAuthenticated = true
        await this.fetchUserInfo()
      }
    },

    // 회원가입
    async register(userData) {
      try {
        const response = await axios.post(`${API_BASE_URL}/api/auth/register`, userData)
        this.token = response.data.access_token
        this.user = response.data.user
        this.isAuthenticated = true
        
        localStorage.setItem('jwt_token', this.token)
        axios.defaults.headers.common['Authorization'] = `Bearer ${this.token}`
        
        return { success: true }
      } catch (error) {
        return { 
          success: false, 
          error: error.response?.data?.detail || '회원가입 실패' 
        }
      }
    },

    // 로그인
    async login(credentials) {
      try {
        const formData = new FormData()
        formData.append('username', credentials.email)
        formData.append('password', credentials.password)
        
        const response = await axios.post('${API_BASE_URL}/api/auth/login', formData)
        this.token = response.data.access_token
        this.user = response.data.user
        this.isAuthenticated = true
        
        localStorage.setItem('jwt_token', this.token)
        axios.defaults.headers.common['Authorization'] = `Bearer ${this.token}`
        
        // OAuth 연결 상태 확인
        await this.fetchUserInfo()
        
        return { success: true }
      } catch (error) {
        return { 
          success: false, 
          error: error.response?.data?.detail || '로그인 실패' 
        }
      }
    },

    // 로그아웃
    logout() {
      this.user = null
      this.token = null
      this.isAuthenticated = false
      this.githubConnected = false
      this.googleConnected = false
      
      localStorage.removeItem('jwt_token')
      localStorage.removeItem('github_username')
      delete axios.defaults.headers.common['Authorization']
    },

    // 사용자 정보 가져오기
    async fetchUserInfo() {
      try {
        const response = await axios.get('${API_BASE_URL}/api/auth/me', {
          headers: { Authorization: `Bearer ${this.token}` }
        })
        
        this.user = response.data
        this.githubConnected = !!response.data.github_username
        this.googleConnected = !!response.data.google_email
      } catch (error) {
        console.error('Failed to fetch user info:', error)
        this.logout()
      }
    },

    // GitHub OAuth 콜백 처리
    async handleGithubCallback(code) {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/auth/github/callback?code=${code}`, {
          headers: { Authorization: `Bearer ${this.token}` }
        })
        
        this.githubConnected = true
        this.user.github_username = response.data.github_username
        
        return { success: true }
      } catch (error) {
        return { 
          success: false, 
          error: error.response?.data?.detail || 'GitHub 연동 실패' 
        }
      }
    },

    // Google OAuth 콜백 처리
    async handleGoogleCallback(code) {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/auth/google/callback?code=${code}`, {
          headers: { Authorization: `Bearer ${this.token}` }
        })
        
        this.googleConnected = true
        this.user.google_email = response.data.google_email
        
        return { success: true }
      } catch (error) {
        return { 
          success: false, 
          error: error.response?.data?.detail || 'Google 연동 실패' 
        }
      }
    }
  }
})