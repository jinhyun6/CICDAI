<template>
  <div class="deployment-status">
    <h2>🚀 배포 상태</h2>
    
    <!-- 최근 배포 목록 -->
    <div class="recent-deployments">
      <h3>최근 배포</h3>
      <div v-if="loading" class="loading">배포 상태를 불러오는 중...</div>
      
      <div v-else-if="workflows.length === 0" class="no-deployments">
        아직 배포 기록이 없습니다. main 브랜치에 푸시하거나 수동으로 워크플로우를 실행해보세요.
      </div>
      
      <ul v-else class="workflow-list">
        <li v-for="workflow in workflows" :key="workflow.id" 
            class="workflow-item" 
            :class="workflow.status"
            @click="selectWorkflow(workflow)">
          <div class="workflow-header">
            <span class="workflow-name">{{ workflow.name }}</span>
            <span class="workflow-number">#{{ workflow.run_number }}</span>
          </div>
          <div class="workflow-info">
            <span class="workflow-status" :class="getStatusClass(workflow)">
              {{ getStatusIcon(workflow) }} {{ getStatusText(workflow) }}
            </span>
            <span class="workflow-time">{{ formatTime(workflow.created_at) }}</span>
          </div>
        </li>
      </ul>
    </div>
    
    <!-- 선택된 배포 상세 정보 -->
    <div v-if="selectedWorkflow" class="deployment-details">
      <h3>배포 상세 정보</h3>
      
      <div class="detail-header">
        <h4>{{ selectedWorkflow.name }} #{{ selectedWorkflow.run_number }}</h4>
        <a :href="selectedWorkflow.html_url" target="_blank" class="github-link">
          GitHub에서 보기 →
        </a>
      </div>
      
      <!-- 배포 단계 -->
      <div v-if="steps.length > 0" class="deployment-steps">
        <h5>배포 단계</h5>
        <div class="steps-timeline">
          <div v-for="(step, index) in steps" :key="index" 
               class="step-item" 
               :class="getStepClass(step)">
            <div class="step-indicator">
              <span class="step-number">{{ index + 1 }}</span>
            </div>
            <div class="step-content">
              <div class="step-name">{{ step.name }}</div>
              <div class="step-status">{{ getStepStatus(step) }}</div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 로그 표시 (옵션) -->
      <div v-if="showLogs && logs" class="deployment-logs">
        <h5>배포 로그</h5>
        <pre class="log-content">{{ logs }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import axios from 'axios'
import { API_BASE_URL } from '../config/api'

const props = defineProps({
  owner: String,
  repo: String
})

const loading = ref(true)
const workflows = ref([])
const selectedWorkflow = ref(null)
const steps = ref([])
const logs = ref('')
const showLogs = ref(false)
let pollInterval = null

// 워크플로우 상태 조회
const fetchWorkflows = async () => {
  try {
    const token = localStorage.getItem('jwt_token')
    const response = await axios.get(
      `${API_BASE_URL}/api/deployment/status/${props.owner}/${props.repo}`,
      {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    )
    
    workflows.value = response.data.workflow_runs
    loading.value = false
    
    // 실행 중인 워크플로우가 있으면 자동 선택
    const runningWorkflow = workflows.value.find(w => w.status === 'in_progress')
    if (runningWorkflow && !selectedWorkflow.value) {
      selectWorkflow(runningWorkflow)
    }
  } catch (error) {
    console.error('Failed to fetch workflows:', error)
    loading.value = false
  }
}

// 특정 워크플로우 선택
const selectWorkflow = async (workflow) => {
  selectedWorkflow.value = workflow
  
  try {
    const token = localStorage.getItem('jwt_token')
    const response = await axios.get(
      `${API_BASE_URL}/api/deployment/status/${props.owner}/${props.repo}?run_id=${workflow.id}`,
      {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    )
    
    steps.value = response.data.steps
  } catch (error) {
    console.error('Failed to fetch workflow details:', error)
  }
}

// 상태 관련 헬퍼 함수들
const getStatusClass = (workflow) => {
  if (workflow.status === 'completed') {
    return workflow.conclusion === 'success' ? 'success' : 'failure'
  }
  return workflow.status
}

const getStatusIcon = (workflow) => {
  if (workflow.status === 'in_progress') return '⏳'
  if (workflow.status === 'queued') return '⏸️'
  if (workflow.status === 'completed') {
    return workflow.conclusion === 'success' ? '✅' : '❌'
  }
  return '❓'
}

const getStatusText = (workflow) => {
  if (workflow.status === 'in_progress') return '진행 중'
  if (workflow.status === 'queued') return '대기 중'
  if (workflow.status === 'completed') {
    return workflow.conclusion === 'success' ? '성공' : '실패'
  }
  return workflow.status
}

const getStepClass = (step) => {
  if (step.status === 'completed') {
    return step.conclusion === 'success' ? 'completed' : 'failed'
  }
  return step.status
}

const getStepStatus = (step) => {
  if (step.status === 'in_progress') return '진행 중...'
  if (step.status === 'completed') {
    return step.conclusion === 'success' ? '완료' : '실패'
  }
  return '대기 중'
}

// 시간 포맷팅
const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date
  
  if (diff < 60000) {
    return '방금 전'
  } else if (diff < 3600000) {
    return `${Math.floor(diff / 60000)}분 전`
  } else if (diff < 86400000) {
    return `${Math.floor(diff / 3600000)}시간 전`
  } else {
    return date.toLocaleDateString('ko-KR')
  }
}

// 실시간 업데이트를 위한 폴링
onMounted(() => {
  fetchWorkflows()
  
  // 5초마다 상태 업데이트
  pollInterval = setInterval(() => {
    fetchWorkflows()
    
    // 선택된 워크플로우가 있고 진행 중이면 상세 정보도 업데이트
    if (selectedWorkflow.value && selectedWorkflow.value.status === 'in_progress') {
      selectWorkflow(selectedWorkflow.value)
    }
  }, 5000)
})

onUnmounted(() => {
  if (pollInterval) {
    clearInterval(pollInterval)
  }
})
</script>

<style scoped>
.deployment-status {
  padding: 1.5rem;
  background: #f8f9fa;
  border-radius: 8px;
}

.deployment-status h2 {
  margin: 0 0 1.5rem 0;
  color: #2c3e50;
}

.recent-deployments {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  margin-bottom: 1.5rem;
}

.recent-deployments h3 {
  margin: 0 0 1rem 0;
  color: #34495e;
}

.loading {
  text-align: center;
  color: #7f8c8d;
  padding: 2rem;
}

.no-deployments {
  text-align: center;
  color: #7f8c8d;
  padding: 2rem;
  background: #f0f0f0;
  border-radius: 4px;
}

.workflow-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.workflow-item {
  padding: 1rem;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  margin-bottom: 0.5rem;
  cursor: pointer;
  transition: all 0.2s;
}

.workflow-item:hover {
  background: #f8f9fa;
  border-color: #3498db;
}

.workflow-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.workflow-name {
  font-weight: 500;
  color: #2c3e50;
}

.workflow-number {
  color: #7f8c8d;
}

.workflow-info {
  display: flex;
  justify-content: space-between;
  font-size: 0.9rem;
}

.workflow-status {
  font-weight: 500;
}

.workflow-status.success {
  color: #27ae60;
}

.workflow-status.failure {
  color: #e74c3c;
}

.workflow-status.in_progress {
  color: #3498db;
}

.workflow-time {
  color: #7f8c8d;
}

.deployment-details {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.detail-header h4 {
  margin: 0;
  color: #2c3e50;
}

.github-link {
  color: #3498db;
  text-decoration: none;
}

.github-link:hover {
  text-decoration: underline;
}

.deployment-steps h5 {
  margin: 0 0 1rem 0;
  color: #34495e;
}

.steps-timeline {
  position: relative;
  padding-left: 2rem;
}

.step-item {
  position: relative;
  margin-bottom: 1.5rem;
  padding-left: 1.5rem;
}

.step-item::before {
  content: '';
  position: absolute;
  left: -2rem;
  top: 0.5rem;
  bottom: -1.5rem;
  width: 2px;
  background: #e0e0e0;
}

.step-item:last-child::before {
  display: none;
}

.step-indicator {
  position: absolute;
  left: -2.5rem;
  top: 0;
  width: 2rem;
  height: 2rem;
  background: #e0e0e0;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.step-item.completed .step-indicator {
  background: #27ae60;
  color: white;
}

.step-item.failed .step-indicator {
  background: #e74c3c;
  color: white;
}

.step-item.in_progress .step-indicator {
  background: #3498db;
  color: white;
}

.step-number {
  font-size: 0.8rem;
  font-weight: bold;
}

.step-name {
  font-weight: 500;
  color: #2c3e50;
  margin-bottom: 0.25rem;
}

.step-status {
  font-size: 0.85rem;
  color: #7f8c8d;
}

.deployment-logs {
  margin-top: 2rem;
}

.deployment-logs h5 {
  margin: 0 0 1rem 0;
  color: #34495e;
}

.log-content {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 1rem;
  border-radius: 4px;
  overflow-x: auto;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 0.85rem;
  line-height: 1.5;
  max-height: 400px;
  overflow-y: auto;
}
</style>