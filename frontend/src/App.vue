<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import AppHeader from './components/AppHeader.vue'
import DashboardView from './views/DashboardView.vue'
import VisionView from './views/VisionView.vue'
import SensorView from './views/SensorView.vue'
import KnowledgeView from './views/KnowledgeView.vue'
import KnowledgeDocumentView from './views/KnowledgeDocumentView.vue'
import ApiSettingsView from './views/ApiSettingsView.vue'
import HistoryView from './views/HistoryView.vue'
import { getHealth } from './api'

const viewIds = new Set(['dashboard', 'vision', 'sensor', 'knowledge', 'history', 'api'])
function routeFromHash() {
  const [view, ...parts] = window.location.hash.slice(1).split('/')
  if (view === 'knowledge' && parts.length) {
    try { return { view, file: decodeURIComponent(parts.join('/')) } } catch { return { view: 'knowledge', file: '' } }
  }
  return { view: viewIds.has(view) ? view : 'dashboard', file: '' }
}
const initialRoute = routeFromHash()
const activeView = ref(initialRoute.view)
const selectedKnowledgeFile = ref(initialRoute.file)
const connected = ref(false)
const history = ref([])
let healthTimer
const views = [
  { id: 'dashboard', label: '总览', hint: '工作台' },
  { id: 'vision', label: '视觉巡检', hint: '图片分析' },
  { id: 'sensor', label: '传感器', hint: '时序研判' },
  { id: 'knowledge', label: '知识库', hint: '规范检索' },
  { id: 'history', label: '台账', hint: '本次会话' },
  { id: 'api', label: '模型 API', hint: '服务配置' },
]
const currentView = computed(() => ({ dashboard: DashboardView, vision: VisionView, sensor: SensorView, knowledge: KnowledgeView, history: HistoryView, api: ApiSettingsView }[activeView.value]))
function syncRoute() {
  const route = routeFromHash()
  activeView.value = route.view
  selectedKnowledgeFile.value = route.file
}
function navigate(view) { window.location.hash = view }
function openKnowledgeDocument(file) { window.location.hash = `knowledge/${encodeURIComponent(file)}` }
function backToKnowledge() { window.location.hash = 'knowledge' }
async function checkHealth() {
  try { await getHealth(); connected.value = true } catch { connected.value = false }
}
onMounted(() => {
  window.addEventListener('hashchange', syncRoute)
  checkHealth()
  healthTimer = window.setInterval(checkHealth, 3000)
})
onUnmounted(() => {
  window.clearInterval(healthTimer)
  window.removeEventListener('hashchange', syncRoute)
})
function record(entry) { history.value.unshift({ ...entry, time: new Date().toLocaleString() }) }
</script>

<template>
  <div class="app-shell">
    <AppHeader :connected="connected" />
    <div class="layout-grid">
      <aside class="side-nav" aria-label="主导航">
        <p class="nav-caption">现场安全控制台</p>
        <button v-for="view in views" :key="view.id" class="nav-item" :class="{ active: activeView === view.id }" :aria-current="activeView === view.id ? 'page' : undefined" @click="navigate(view.id)">
          <span>{{ view.label }}</span><small>{{ view.hint }}</small>
        </button>
        <div class="nav-footer"><span>Streamlit 可用</span><small>独立前端 + API 服务</small></div>
      </aside>
      <main class="main-content">
        <KnowledgeDocumentView v-if="selectedKnowledgeFile" :file="selectedKnowledgeFile" @back="backToKnowledge" />
        <KeepAlive v-else><component :is="currentView" @record="record" @open-document="openKnowledgeDocument" :history="history" /></KeepAlive>
      </main>
    </div>
  </div>
</template>
