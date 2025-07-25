import axios from 'axios'
import { API_BASE_URL } from './api'

// Axios 기본 설정
axios.defaults.baseURL = API_BASE_URL
// 프로덕션에서는 withCredentials를 사용하지 않음 (CORS 와일드카드 때문)
axios.defaults.withCredentials = false

// Request 인터셉터
axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('jwt_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response 인터셉터
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // 토큰 만료 시 로그인 페이지로
      localStorage.removeItem('jwt_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default axios