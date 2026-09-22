<script setup>
import EmptyState from '../components/EmptyState.vue'
import RiskBadge from '../components/RiskBadge.vue'
defineProps({ history: { type: Array, default: () => [] } })
</script>
<template><section class="view-section"><div class="view-heading"><div><p class="eyebrow">台账 / 05</p><h2>保留本次会话记录。</h2><p class="lede">本次浏览器会话中的巡检结果会持续显示在这里。</p></div></div><div class="panel history-panel"><div v-if="history.length" class="history-list"><div v-for="(entry, index) in history" :key="`${entry.time}-${index}`" class="history-item"><div><p class="eyebrow">{{ entry.time }} / {{ entry.type }}</p><strong>{{ entry.title }}</strong></div><RiskBadge :level="entry.risk || 'GREEN'" /></div></div><EmptyState v-else title="台账为空" message="完成一次视觉巡检或传感器研判后，结果会显示在这里。" /></div></section></template>
