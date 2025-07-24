import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const projectsAPI = {
  // 내 프로젝트 목록 가져오기
  async getMyProjects() {
    const token = localStorage.getItem('jwt_token')
    if (!token) throw new Error('No authentication token')
    
    const response = await axios.get(`${API_BASE_URL}/api/projects/me`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    return response.data
  },
  
  // 프로젝트 삭제
  async deleteProject(projectId) {
    const token = localStorage.getItem('jwt_token')
    if (!token) throw new Error('No authentication token')
    
    const response = await axios.delete(`${API_BASE_URL}/api/projects/${projectId}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    return response.data
  }
}