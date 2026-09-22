<script setup>
import { computed, onMounted, ref } from 'vue'
import AppHeader from './components/AppHeader.vue'
import DashboardView from './views/DashboardView.vue'
import VisionView from './views/VisionView.vue'
import SensorView from './views/SensorView.vue'
import KnowledgeView from './views/KnowledgeView.vue'
import HistoryView from './views/HistoryView.vue'
import { getHealth } from './api'

const activeView = ref('dashboard')
const connected = ref(false)
const history = ref([])
const views = [
  { id: 'dashboard', label: '总览', hint: '工作台' },
  { id: 'vision', label: '视觉巡检', hint: '图片分析' },
  { id: 'sensor', label: '传感器', hint: '时序研判' },
  { id: 'knowledge', label: '知识库', hint: '规范检索' },
  { id: 'history', label: '台账', hint: '本次会话' },
]
const currentView = computed(() => ({ dashboard: DashboardView, vision: VisionView, sensor: SensorView, knowledge: KnowledgeView, history: HistoryView }[activeView.value]))
onMounted(async () => { try { await getHealth(); connected.value = true } catch { connected.value = false } })
function record(entry) { history.value.unshift({ ...entry, time: new Date().toLocaleString() }) }
</script>

<template>
  <div class="app-shell">
    <AppHeader :connected="connected" />
    <div class="layout-grid">
      <aside class="side-nav" aria-label="主导航">
        <p class="nav-caption">现场安全控制台</p>
        <button v-for="view in views" :key="view.id" class="nav-item" :class="{ active: activeView === view.id }" @click="activeView = view.id">
          <span>{{ view.label }}</span><small>{{ view.hint }}</small>
        </button>
        <div class="nav-footer"><span>Streamlit 可用</span><small>独立前端 + API 服务</small></div>
      </aside>
      <main class="main-content"><component :is="currentView" @record="record" :history="history" /></main>
    </div>
  </div>
</template>
