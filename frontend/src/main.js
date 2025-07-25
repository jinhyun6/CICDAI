import { createApp } from 'vue'
import { createPinia } from 'pinia'
import './style.css'
import './styles/global.css'
import App from './App.vue'
import router from './router'
import './config/axios' // Axios 기본 설정

const pinia = createPinia()

createApp(App)
  .use(pinia)
  .use(router)
  .mount('#app')