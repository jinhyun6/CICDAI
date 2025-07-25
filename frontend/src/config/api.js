// API Base URL Configuration
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://cicdai-backend-22v76y7s7a-du.a.run.app'

export const getApiUrl = (endpoint) => {
  return `${API_BASE_URL}${endpoint}`
}