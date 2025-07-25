<template>
  <div class="cicd-setup">
    <h2>CI/CD 자동 설정</h2>
    
    <!-- Step 1: Repository 선택 -->
    <div class="setup-step" :class="{ active: currentStep >= 1 }">
      <h3>1. GitHub Repository 선택</h3>
      <div v-if="currentStep >= 1" class="step-content">
        <select v-model="selectedRepo" @change="onRepoSelect">
          <option value="">Repository 선택...</option>
          <option v-for="repo in repos" :key="repo.id" :value="repo.full_name">
            {{ repo.full_name }} {{ repo.private ? '🔒' : '' }}
          </option>
        </select>
        <p v-if="isLoadingRepos" class="loading">저장소 목록을 불러오는 중...</p>
      </div>
    </div>

    <!-- Step 2: GCP Project 선택 -->
    <div class="setup-step" :class="{ active: currentStep >= 2 }">
      <h3>2. GCP Project 선택</h3>
      <div v-if="currentStep >= 2" class="step-content">
        <select v-model="selectedProject" @change="onProjectSelect">
          <option value="">Project 선택...</option>
          <option v-for="project in projects" :key="project.projectId" :value="project.projectId">
            {{ project.name }} ({{ project.projectId }})
          </option>
        </select>
        <p v-if="isLoadingProjects" class="loading">프로젝트 목록을 불러오는 중...</p>
      </div>
    </div>

    <!-- Step 3: 워크플로우 생성 방법 선택 -->
    <div class="setup-step" :class="{ active: currentStep >= 3 }">
      <h3>3. 워크플로우 생성 방법 선택</h3>
      <div v-if="currentStep >= 3" class="step-content">
        <div class="workflow-method-selection">
          <label class="method-option">
            <input type="radio" v-model="workflowMethod" value="ai" @change="onWorkflowMethodChange">
            <div class="method-content">
              <h4>🤖 AI 자동 생성</h4>
              <p>Claude AI가 프로젝트를 분석하여 최적화된 워크플로우를 자동으로 생성합니다.</p>
            </div>
          </label>
          <label class="method-option">
            <input type="radio" v-model="workflowMethod" value="manual" @change="onWorkflowMethodChange">
            <div class="method-content">
              <h4>📝 수동 입력</h4>
              <p>직접 작성한 GitHub Actions 워크플로우 코드를 입력합니다.</p>
            </div>
          </label>
        </div>
        
        <!-- 수동 입력 영역 -->
        <div v-if="workflowMethod === 'manual'" class="manual-workflow-input">
          <h4>GitHub Actions 워크플로우 코드 입력</h4>
          <textarea 
            v-model="manualWorkflowContent" 
            placeholder="name: Deploy to Cloud Run&#10;&#10;on:&#10;  push:&#10;    branches:&#10;      - main&#10;..."
            rows="20"
            @input="checkStep3Complete"
          ></textarea>
          <p class="help-text">※ .github/workflows/deploy.yml 파일에 저장될 내용을 입력하세요.</p>
        </div>
      </div>
    </div>

    <!-- Step 4: 배포 설정 -->
    <div class="setup-step" :class="{ active: currentStep >= 4 }">
      <h3>4. 배포 설정</h3>
      <div v-if="currentStep >= 4" class="step-content">
        <div class="form-group">
          <label>서비스 이름</label>
          <input v-model="serviceName" type="text" placeholder="my-app" @input="checkStep4Complete">
        </div>
        
        <div class="form-group">
          <label>배포 리전</label>
          <select v-model="selectedRegion">
            <option value="asia-northeast3">서울 (asia-northeast3)</option>
            <option value="asia-northeast1">도쿄 (asia-northeast1)</option>
            <option value="us-central1">아이오와 (us-central1)</option>
          </select>
        </div>

        <div class="form-group">
          <label>배포 타입</label>
          <div class="deploy-types">
            <label class="deploy-type">
              <input type="radio" v-model="deployType" value="cloudrun" @change="checkStep4Complete">
              <span>Cloud Run</span>
            </label>
            <label class="deploy-type">
              <input type="radio" v-model="deployType" value="appengine" @change="checkStep4Complete">
              <span>App Engine</span>
            </label>
          </div>
        </div>
      </div>
    </div>

    <!-- Step 5: 환경변수 및 파일 설정 -->
    <div class="setup-step" :class="{ active: currentStep >= 5 }">
      <h3>5. 환경변수 및 파일 설정</h3>
      <div v-if="currentStep >= 5" class="step-content">
        <div class="env-vars">
          <div v-for="(envVar, index) in environmentVariables" :key="index" class="env-var">
            <input v-model="envVar.key" placeholder="KEY" />
            <input v-model="envVar.value" placeholder="VALUE" />
            <button @click="removeEnvVar(index)" class="btn-remove">삭제</button>
          </div>
          <button @click="addEnvVar" class="btn-add">+ 환경변수 추가</button>
        </div>
        
        <!-- 파일 덮어쓰기 옵션 -->
        <div class="file-overwrite-option">
          <h4>파일 처리 옵션</h4>
          <div class="option-group">
            <label class="option-label">
              <input type="radio" v-model="fileOverwriteOption" value="skip" />
              <span>기존 파일 유지 (AI가 생성한 파일은 .ai-generated 확장자로 저장)</span>
            </label>
            <label class="option-label">
              <input type="radio" v-model="fileOverwriteOption" value="overwrite" />
              <span>기존 파일 덮어쓰기</span>
            </label>
          </div>
          <p class="option-help">
            ※ Dockerfile이나 GitHub Actions workflow 파일이 이미 존재하는 경우 처리 방법을 선택하세요.
          </p>
        </div>
      </div>
    </div>

    <!-- 실행 버튼 -->
    <div v-if="currentStep >= 5" class="action-buttons">
      <button @click="executeSetup" class="btn-execute" :disabled="!canExecute">
        🚀 CI/CD 설정 시작
      </button>
    </div>

    <!-- 진행 상태 -->
    <div v-if="setupStatus" class="setup-status" :class="setupStatus.type">
      <h4>{{ setupStatus.title }}</h4>
      <p>{{ setupStatus.message }}</p>
      <ul v-if="setupStatus.steps">
        <li v-for="step in setupStatus.steps" :key="step.name" :class="step.status">
          {{ step.status === 'completed' ? '✅' : step.status === 'in-progress' ? '⏳' : '⏸️' }}
          {{ step.name }}
        </li>
      </ul>
      
      <!-- AI 생성 파일 표시 (분석 완료 후) -->
      <div v-if="aiAnalysisResult && aiAnalysisResult.generated_files && setupStatus.type !== 'error'" class="ai-generated-results">
        <h5>🤖 AI가 생성한 파일:</h5>
        
        <!-- Dockerfile -->
        <div v-if="aiAnalysisResult.generated_files.dockerfiles?.length > 0" class="generated-files">
          <h6>Dockerfile(s):</h6>
          <div v-for="(dockerfile, index) in aiAnalysisResult.generated_files.dockerfiles" :key="index" class="file-preview">
            <div class="file-header">
              <span>📄 {{ dockerfile.path }}</span>
              <button @click="toggleFilePreview('result-dockerfile-' + index)" class="btn-toggle">
                {{ showFilePreview['result-dockerfile-' + index] ? '접기' : '펼치기' }}
              </button>
            </div>
            <pre v-if="showFilePreview['result-dockerfile-' + index]" class="file-content">{{ dockerfile.content }}</pre>
          </div>
        </div>
        
        <!-- GitHub Workflow -->
        <div v-if="aiAnalysisResult.generated_files.workflow?.content" class="generated-files">
          <h6>GitHub Actions Workflow:</h6>
          <div class="file-preview">
            <div class="file-header">
              <span>📄 {{ aiAnalysisResult.generated_files.workflow.path }}</span>
              <button @click="toggleFilePreview('result-workflow')" class="btn-toggle">
                {{ showFilePreview['result-workflow'] ? '접기' : '펼치기' }}
              </button>
            </div>
            <pre v-if="showFilePreview['result-workflow']" class="file-content">{{ aiAnalysisResult.generated_files.workflow.content }}</pre>
          </div>
        </div>
      </div>
      
      <!-- 배포 URL 표시 -->
      <div v-if="setupStatus.deploymentUrl" class="deployment-info">
        <h5>🚀 배포 정보</h5>
        <p><strong>예상 배포 URL:</strong> 
          <a :href="setupStatus.deploymentUrl" target="_blank" class="deployment-link">
            {{ setupStatus.deploymentUrl }}
          </a>
        </p>
        <p><strong>GitHub Actions:</strong> 
          <a :href="`https://github.com/${setupStatus.githubRepo}/actions`" target="_blank" class="deployment-link">
            배포 진행 상황 확인하기
          </a>
        </p>
        
        <div class="initial-deployment-guide">
          <h6>🎯 첫 배포를 시작하려면:</h6>
          <ol>
            <li>
              <strong>방법 1: 수동 실행</strong><br>
              위 GitHub Actions 링크 → "Deploy to Cloud Run" 워크플로우 선택 → "Run workflow" 버튼 클릭
            </li>
            <li>
              <strong>방법 2: 코드 푸시</strong><br>
              main 브랜치에 코드 변경사항을 push하면 자동으로 배포가 시작됩니다.
            </li>
          </ol>
        </div>
        
        <p class="note">※ 첫 배포는 몇 분 정도 소요될 수 있습니다.</p>
      </div>
      
      <!-- 배포 상태 모니터링 -->
      <div v-if="setupStatus.deploymentUrl" class="deployment-monitoring">
        <DeploymentStatus 
          :owner="getRepoOwner(setupStatus.githubRepo)" 
          :repo="getRepoName(setupStatus.githubRepo)" 
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import DeploymentStatus from './DeploymentStatus.vue'

// 실제 데이터
const repos = ref([])
const projects = ref([])
const isLoadingRepos = ref(false)
const isLoadingProjects = ref(false)

// 상태 관리
const currentStep = ref(1)
const selectedRepo = ref('')
const selectedProject = ref('')
const serviceName = ref('')
const selectedRegion = ref('asia-northeast3')
const deployType = ref('cloudrun')
const environmentVariables = ref([])
const setupStatus = ref(null)
const fileOverwriteOption = ref('skip') // 기본값: 기존 파일 유지
const workflowMethod = ref('ai') // 'ai' or 'manual'
const manualWorkflowContent = ref('')

// 컴포넌트 마운트 시 데이터 로드
onMounted(async () => {
  // URL에서 토큰 가져오기 (임시)
  const urlParams = new URLSearchParams(window.location.search)
  const token = urlParams.get('token')
  
  if (token) {
    // 토큰을 localStorage에 저장 (임시)
    localStorage.setItem('jwt_token', token)
  }
  
  // Repository 목록 가져오기
  await loadRepositories()
})

// Repository 목록 로드
const loadRepositories = async () => {
  isLoadingRepos.value = true
  try {
    const token = localStorage.getItem('jwt_token')
    const response = await axios.get('http://localhost:8000/api/github/repos', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    repos.value = response.data
  } catch (error) {
    console.error('Failed to load repositories:', error)
    // 에러 시 임시 데이터
    repos.value = [
      { id: 1, full_name: 'user/test-repo', private: false },
      { id: 2, full_name: 'user/another-repo', private: true },
    ]
  } finally {
    isLoadingRepos.value = false
  }
}

// 저장소 분석 상태
const isAnalyzing = ref(false)
const repoAnalysis = ref(null)

// 단계별 진행
const onRepoSelect = async () => {
  console.log('onRepoSelect called with:', selectedRepo.value)
  if (selectedRepo.value) {
    // 분석은 나중에 실행 버튼 누를 때 수행
    currentStep.value = 2
    // 서비스 이름 자동 생성
    serviceName.value = selectedRepo.value.split('/')[1]
    // GCP 프로젝트 목록 로드
    await loadProjects()
  }
}

// AI 분석 사용 여부
const useAIAnalysis = ref(true)
const aiAnalysisResult = ref(null)

// 파일 미리보기 토글
const showFilePreview = ref({})

const toggleFilePreview = (fileId) => {
  showFilePreview.value[fileId] = !showFilePreview.value[fileId]
}

// 저장소 분석
const analyzeRepository = async () => {
  isAnalyzing.value = true
  try {
    const token = localStorage.getItem('jwt_token')
    
    if (useAIAnalysis.value) {
      // AI 분석 사용
      try {
        const aiResponse = await axios.post('http://localhost:8000/api/analyze/ai-analyze-and-generate', {
          repo_full_name: selectedRepo.value
        }, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        
        aiAnalysisResult.value = aiResponse.data
        
        // AI 분석 결과가 있으면 사용
        if (aiResponse.data.ai_analysis && !aiResponse.data.error) {
          const analysis = aiResponse.data.ai_analysis.analysis
          repoAnalysis.value = {
            project_type: analysis.project_type,
            has_dockerfile: aiResponse.data.generated_files.dockerfiles.length > 0,
            has_docker_compose: false, // AI 생성에서는 docker-compose 대신 개별 서비스로 처리
            detected_services: analysis.services,
            deployment_suggestions: [{
              type: "ai-generated",
              description: "AI가 생성한 최적화된 CI/CD 파이프라인",
              recommended: true
            }],
            ai_generated_files: aiResponse.data.generated_files
          }
          
          // 배포 타입 설정
          deployType.value = 'cloudrun'
          return
        }
      } catch (aiError) {
        console.warn('AI analysis failed, falling back to basic analysis:', aiError)
      }
    }
    
    // 기본 분석 (AI 실패 시 또는 AI 사용 안 함)
    const response = await axios.post('http://localhost:8000/api/analyze/analyze-repo', {
      repo_full_name: selectedRepo.value
    }, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    repoAnalysis.value = response.data
    
    // 분석 결과에 따라 배포 타입 자동 설정
    if (repoAnalysis.value.has_docker_compose) {
      deployType.value = 'docker-compose'
    } else if (repoAnalysis.value.has_dockerfile) {
      deployType.value = 'cloudrun'
    }
  } catch (error) {
    console.error('Failed to analyze repository:', error)
  } finally {
    isAnalyzing.value = false
  }
}

// GCP 프로젝트 목록 로드
const loadProjects = async () => {
  isLoadingProjects.value = true
  try {
    const token = localStorage.getItem('jwt_token')
    const response = await axios.get('http://localhost:8000/api/gcp/projects', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    projects.value = response.data
  } catch (error) {
    console.error('Failed to load projects:', error)
    // 에러 시 기본값
    projects.value = [
      { projectId: 'demo-project', name: 'Demo Project' }
    ]
  } finally {
    isLoadingProjects.value = false
  }
}

const onProjectSelect = () => {
  if (selectedProject.value) {
    currentStep.value = 3
  }
}

// 워크플로우 방법 변경
const onWorkflowMethodChange = () => {
  checkStep3Complete()
}

// Step 3 완료 체크
const checkStep3Complete = () => {
  if (workflowMethod.value === 'ai') {
    currentStep.value = 4
  } else if (workflowMethod.value === 'manual' && manualWorkflowContent.value.trim()) {
    currentStep.value = 4
  }
}

// Step 4 완료 체크
const checkStep4Complete = () => {
  if (serviceName.value && deployType.value) {
    currentStep.value = 5
  }
}

// 환경변수 관리
const addEnvVar = () => {
  environmentVariables.value.push({ key: '', value: '' })
}

const removeEnvVar = (index) => {
  environmentVariables.value.splice(index, 1)
}

// 실행 가능 여부
const canExecute = computed(() => {
  const baseRequirements = selectedRepo.value && 
                          selectedProject.value && 
                          serviceName.value
  
  if (workflowMethod.value === 'manual') {
    return baseRequirements && manualWorkflowContent.value.trim()
  }
  
  return baseRequirements
})

// CI/CD 설정 실행 (AI 생성 파일 커밋)
const executeSetup = async () => {
  setupStatus.value = {
    type: 'in-progress',
    title: '🔄 CI/CD 설정 진행 중...',
    message: '저장소를 분석하고 있습니다...',
    steps: [
      { name: '저장소 분석 및 파일 생성', status: 'in-progress' },
      { name: 'GitHub에 파일 커밋', status: 'pending' },
      { name: 'GitHub Secrets 설정', status: 'pending' },
      { name: 'GCP 서비스 계정 생성', status: 'pending' },
    ]
  }

  try {
    const token = localStorage.getItem('jwt_token')
    
    // 수동 워크플로우 입력인 경우
    if (workflowMethod.value === 'manual') {
      setupStatus.value.steps = [
        { name: '수동 워크플로우 준비', status: 'in-progress' },
        { name: 'GitHub에 파일 커밋', status: 'pending' },
        { name: 'GitHub Secrets 설정', status: 'pending' },
        { name: 'GCP 서비스 계정 생성', status: 'pending' },
      ]
      
      // 수동 워크플로우를 사용하여 generated_files 형식 생성
      const manualGeneratedFiles = {
        dockerfiles: [], // 수동 모드에서는 Dockerfile 생성 안 함
        workflow: {
          path: '.github/workflows/deploy.yml',
          content: manualWorkflowContent.value
        }
      }
      
      aiAnalysisResult.value = {
        generated_files: manualGeneratedFiles,
        ai_analysis: {
          analysis: {
            project_type: 'manual',
            services: ['custom']
          }
        }
      }
      
      setupStatus.value.steps[0].status = 'completed'
    } else {
      // AI 분석 모드
      // Step 0: 저장소 분석 (아직 분석하지 않은 경우)
      if (!aiAnalysisResult.value || !aiAnalysisResult.value.generated_files) {
        await analyzeRepository()
      }
    }
    
    setupStatus.value.steps[0].status = 'completed'
    
    // AI가 생성한 파일이 있는 경우
    if (aiAnalysisResult.value && aiAnalysisResult.value.generated_files) {
      // Step 1: GitHub에 파일 커밋
      setupStatus.value.steps[1].status = 'in-progress'
      
      const commitResponse = await axios.post('http://localhost:8000/api/github-actions/commit-cicd-files', {
        repo_full_name: selectedRepo.value,
        generated_files: aiAnalysisResult.value.generated_files,
        force_overwrite: fileOverwriteOption.value === 'overwrite'
      }, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (commitResponse.data.success) {
        setupStatus.value.steps[1].status = 'completed'
        
        // Step 2: GitHub Secrets 설정
        setupStatus.value.steps[2].status = 'in-progress'
        
        const secretsResponse = await axios.post('http://localhost:8000/api/github-actions/setup-github-secrets', {
          repo_full_name: selectedRepo.value,
          gcp_project_id: selectedProject.value,
          service_name: serviceName.value,
          region: selectedRegion.value
        }, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        
        if (secretsResponse.data.success) {
          setupStatus.value.steps[2].status = 'completed'
          
          // Step 3: GCP 서비스 계정 생성
          setupStatus.value.steps[3].status = 'in-progress'
          
          const gcpResponse = await axios.post('http://localhost:8000/api/gcp-setup/create-service-account-for-cicd', {
            gcp_project_id: selectedProject.value,
            repo_full_name: selectedRepo.value,
            service_name: serviceName.value
          }, {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          })
          
          if (gcpResponse.data.success) {
            setupStatus.value.steps[3].status = 'completed'
          } else {
            setupStatus.value.steps[3].status = 'pending'
          }
          
          // 최종 검증
          const verifyResponse = await axios.post('http://localhost:8000/api/gcp-setup/verify-gcp-setup', {
            gcp_project_id: selectedProject.value,
            repo_full_name: selectedRepo.value
          }, {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          })
          
          setupStatus.value = {
            type: 'success',
            title: '✅ CI/CD 설정 완료!',
            message: verifyResponse.data.ready ? 
              '모든 설정이 완료되었습니다. 이제 배포할 준비가 되었습니다!' : 
              `일부 설정이 누락되었습니다: ${verifyResponse.data.missing_secrets?.join(', ')}`,
            deploymentUrl: commitResponse.data.next_steps.workflow_url,
            githubRepo: selectedRepo.value,
            steps: setupStatus.value.steps,
            verificationResult: verifyResponse.data
          }
          
          return
        }
      }
    }
    
    // 기존 코드 (AI 없이 진행하는 경우)
    const envVars = {}
    environmentVariables.value.forEach(env => {
      if (env.key) {
        const upperKey = env.key.toUpperCase().replace(/[^A-Z0-9_]/g, '_')
        envVars[upperKey] = env.value
      }
    })

    const response = await axios.post('http://localhost:8000/api/cicd/setup', {
      github_repo: selectedRepo.value,
      gcp_project_id: selectedProject.value,
      service_name: serviceName.value,
      region: selectedRegion.value,
      environment_variables: envVars
    }, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    // 성공 상태 업데이트
    const deploymentInfo = response.data.details.deployment_info
    setupStatus.value = {
      type: 'success',
      title: '✅ CI/CD 설정 완료!',
      message: '이제 main 브랜치에 푸시하면 자동으로 배포됩니다.',
      steps: [
        { name: 'GCP 서비스 계정 생성', status: 'completed' },
        { name: '권한 설정', status: 'completed' },
        { name: 'GitHub Secrets 설정', status: 'completed' },
        { name: 'Workflow 파일 생성', status: 'completed' },
      ],
      deploymentUrl: deploymentInfo.expected_url,
      githubRepo: deploymentInfo.github_repo
    }
    
    // 배포 정보는 이제 백엔드에서 자동으로 저장됨

  } catch (error) {
    setupStatus.value = {
      type: 'error',
      title: '❌ 설정 실패',
      message: error.response?.data?.detail || '오류가 발생했습니다.'
    }
  }
}

// Step 4 완료 시 Step 5로
const onDeployTypeSelect = () => {
  if (serviceName.value) {
    currentStep.value = 5
  }
}

// GitHub repo에서 owner와 repo 이름 추출
const getRepoOwner = (repoFullName) => {
  return repoFullName ? repoFullName.split('/')[0] : ''
}

const getRepoName = (repoFullName) => {
  return repoFullName ? repoFullName.split('/')[1] : ''
}
</script>

<style scoped>
.cicd-setup {
  max-width: 800px;
  margin: 0 auto;
}

.setup-step {
  background: white;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  margin-bottom: 1rem;
  padding: 1.5rem;
  transition: all 0.3s;
}

.setup-step.active {
  border-color: #3498db;
}

.setup-step h3 {
  margin: 0 0 1rem 0;
  color: #666;
}

.setup-step.active h3 {
  color: #2c3e50;
}

.step-content {
  margin-top: 1rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: bold;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.deploy-types {
  display: flex;
  gap: 1rem;
}

.deploy-type {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.env-vars {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.env-var {
  display: flex;
  gap: 0.5rem;
}

.env-var input {
  flex: 1;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.btn-remove {
  background: #e74c3c;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
}

.btn-add {
  background: #3498db;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  align-self: flex-start;
}

.action-buttons {
  margin-top: 2rem;
  text-align: center;
}

.btn-execute {
  background: #27ae60;
  color: white;
  border: none;
  padding: 1rem 2rem;
  font-size: 1.2rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-execute:hover:not(:disabled) {
  background: #229954;
  transform: translateY(-2px);
}

.btn-execute:disabled {
  background: #95a5a6;
  cursor: not-allowed;
}

.setup-status {
  margin-top: 2rem;
  padding: 1.5rem;
  border-radius: 8px;
  background: #f8f9fa;
}

.setup-status.in-progress {
  border-left: 4px solid #3498db;
}

.setup-status.success {
  border-left: 4px solid #27ae60;
}

.setup-status.error {
  border-left: 4px solid #e74c3c;
}

.setup-status h4 {
  margin: 0 0 0.5rem 0;
}

.setup-status ul {
  list-style: none;
  padding: 0;
  margin-top: 1rem;
}

.setup-status li {
  padding: 0.5rem 0;
}

.setup-status li.completed {
  color: #27ae60;
}

.setup-status li.in-progress {
  color: #3498db;
}

.setup-status li.pending {
  color: #95a5a6;
}

.loading {
  color: #3498db;
  font-size: 0.9rem;
  margin-top: 0.5rem;
}

.analysis-result {
  margin-top: 1rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.analysis-result h4 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
}

.analysis-details p {
  margin: 0.5rem 0;
}

.detected-services,
.suggestions {
  margin-top: 1rem;
}

.detected-services h5,
.suggestions h5 {
  margin: 0 0 0.5rem 0;
  color: #495057;
}

.detected-services ul,
.suggestions ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.detected-services li,
.suggestions li {
  padding: 0.5rem;
  background: white;
  border-radius: 4px;
  margin-bottom: 0.5rem;
  border: 1px solid #dee2e6;
}

.suggestions li.recommended {
  border-color: #28a745;
  background: #f8fff9;
}

.has-dockerfile {
  font-size: 0.875rem;
  color: #28a745;
  margin-left: 0.5rem;
}

.badge {
  background: #28a745;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  margin-left: 0.5rem;
}

.ai-generated {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 2px dashed #dee2e6;
}

.ai-generated h5 {
  color: #6366f1;
  margin-bottom: 1rem;
}

.generated-files h6 {
  margin: 1rem 0 0.5rem 0;
  color: #495057;
}

.file-preview {
  margin-bottom: 1rem;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  overflow: hidden;
}

.file-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
}

.btn-toggle {
  background: #6366f1;
  color: white;
  border: none;
  padding: 0.25rem 0.75rem;
  border-radius: 4px;
  font-size: 0.875rem;
  cursor: pointer;
}

.btn-toggle:hover {
  background: #4f46e5;
}

.file-content {
  margin: 0;
  padding: 1rem;
  background: #1e1e1e;
  color: #d4d4d4;
  font-size: 0.875rem;
  line-height: 1.5;
  overflow-x: auto;
  max-height: 400px;
  overflow-y: auto;
}

.env-requirements {
  margin-top: 1rem;
}

.env-requirements ul {
  list-style: none;
  padding: 0;
}

.env-requirements li {
  padding: 0.5rem;
  background: #f8f9fa;
  border-radius: 4px;
  margin-bottom: 0.5rem;
}

.env-requirements .required {
  color: #dc3545;
  font-size: 0.875rem;
  margin-left: 0.5rem;
}

.deployment-info {
  margin-top: 1.5rem;
  padding: 1rem;
  background: #f0f8ff;
  border-radius: 6px;
  border: 1px solid #e0e0e0;
}

.deployment-info h5 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
}

.deployment-info p {
  margin: 0.5rem 0;
}

.deployment-link {
  color: #3498db;
  text-decoration: none;
  font-weight: 500;
}

.deployment-link:hover {
  text-decoration: underline;
}

.note {
  font-size: 0.85rem;
  color: #7f8c8d;
  font-style: italic;
  margin-top: 1rem !important;
}

.initial-deployment-guide {
  margin: 1rem 0;
  padding: 1rem;
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.initial-deployment-guide h6 {
  margin: 0 0 0.75rem 0;
  color: #2c3e50;
  font-size: 1rem;
}

.initial-deployment-guide ol {
  margin: 0;
  padding-left: 1.5rem;
}

.initial-deployment-guide li {
  margin-bottom: 0.75rem;
  line-height: 1.5;
}

.initial-deployment-guide li:last-child {
  margin-bottom: 0;
}

.initial-deployment-guide strong {
  color: #3498db;
}

.deployment-monitoring {
  margin-top: 2rem;
  border-top: 1px solid #e0e0e0;
  padding-top: 2rem;
}

.file-overwrite-option {
  margin-top: 2rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.file-overwrite-option h4 {
  margin: 0 0 1rem 0;
  color: #495057;
  font-size: 1rem;
}

.option-group {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.option-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.option-label:hover {
  background-color: #e9ecef;
}

.option-label input[type="radio"] {
  width: auto;
  margin: 0;
}

.option-label span {
  font-size: 0.95rem;
  color: #212529;
}

.option-help {
  margin: 1rem 0 0 0;
  font-size: 0.85rem;
  color: #6c757d;
  line-height: 1.5;
}

.ai-generated-results {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 2px dashed #dee2e6;
}

.ai-generated-results h5 {
  color: #6366f1;
  margin-bottom: 1rem;
}

.ai-generated-results .generated-files {
  margin-bottom: 1rem;
}

.ai-generated-results .generated-files h6 {
  margin: 0.5rem 0;
  color: #495057;
}

/* 워크플로우 방법 선택 */
.workflow-method-selection {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 2rem;
}

.method-option {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1rem;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.method-option:hover {
  border-color: #3498db;
  background: #f8f9fa;
}

.method-option input[type="radio"] {
  margin-top: 0.25rem;
  flex-shrink: 0;
}

.method-option input[type="radio"]:checked ~ .method-content {
  color: #2c3e50;
}

.method-option input[type="radio"]:checked {
  accent-color: #3498db;
}

.method-content {
  flex: 1;
}

.method-content h4 {
  margin: 0 0 0.5rem 0;
  font-size: 1.125rem;
  color: #495057;
}

.method-content p {
  margin: 0;
  color: #6c757d;
  font-size: 0.95rem;
  line-height: 1.5;
}

.method-option:has(input:checked) {
  border-color: #3498db;
  background: #f0f8ff;
}

/* 수동 워크플로우 입력 */
.manual-workflow-input {
  margin-top: 1.5rem;
  padding: 1.5rem;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.manual-workflow-input h4 {
  margin: 0 0 1rem 0;
  color: #495057;
  font-size: 1rem;
}

.manual-workflow-input textarea {
  width: 100%;
  padding: 1rem;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 0.875rem;
  line-height: 1.5;
  background: #1e1e1e;
  color: #d4d4d4;
  resize: vertical;
  min-height: 400px;
}

.manual-workflow-input textarea:focus {
  outline: none;
  border-color: #3498db;
}

.manual-workflow-input .help-text {
  margin: 0.5rem 0 0 0;
  font-size: 0.85rem;
  color: #6c757d;
}
</style>