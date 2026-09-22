<script setup>
import { onMounted, ref } from 'vue'
import MetricStrip from '../components/MetricStrip.vue'
import EmptyState from '../components/EmptyState.vue'
import { getConfig } from '../api'
const config = ref(null); const error = ref(''); const loading = ref(true)
onMounted(async () => { try { config.value = await getConfig() } catch (e) { error.value = e.message } finally { loading.value = false } })
const metrics = [{ label: '风险模型', value: '规则 + AI', note: '确定性计算优先' }, { label: '监测范围', value: '视觉 / 传感器', note: '两条分析链路' }, { label: '知识库', value: '本地优先', note: '支持离线演示' }]
</script>
<template><section class="view-section"><div class="view-heading"><div><p class="eyebrow">总览 / 01</p><h2>让每一次现场决策都清晰。</h2><p class="lede">从一张现场照片或一段传感器时序开始，把证据转化为可执行行动。</p></div></div><div class="section-rule"></div><MetricStrip :metrics="metrics" /><div class="dashboard-columns"><article class="panel"><p class="eyebrow">工作流</p><h3>专注而完整的检查链路</h3><ol class="workflow-list"><li><span>01</span><div><strong>采集</strong><p>上传现场照片或 CSV 时序数据。</p></div></li><li><span>02</span><div><strong>研判</strong><p>先执行确定性阈值计算，再由 AI 补充解释。</p></div></li><li><span>03</span><div><strong>闭环</strong><p>将隐患和报告保留在本次会话台账中。</p></div></li></ol></article><article class="panel"><p class="eyebrow">运行状态</p><h3>当前配置</h3><div v-if="loading" class="skeleton-line"></div><EmptyState v-else-if="error" title="API 尚未就绪" :message="error" /><div v-else class="config-list"><div><span>视觉模型</span><strong>{{ config?.vision_models?.[0] || '演示模式' }}</strong></div><div><span>文本模型</span><strong>{{ config?.text_models?.[0] || '演示模式' }}</strong></div><div><span>支持城市</span><strong>{{ config?.cities?.length || 0 }} 个</strong></div></div></article></div></section></template>
