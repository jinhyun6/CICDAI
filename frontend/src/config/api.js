// API Base URL Configuration
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://cicdai-backend-16084823681.asia-northeast3.run.app'

export const getApiUrl = (endpoint) => {
  return `${API_BASE_URL}${endpoint}`
}