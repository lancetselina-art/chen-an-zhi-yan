<script setup>
defineProps({ connected: { type: Boolean, default: false } })
</script>
<template>
  <header class="app-header"><div class="brand-lockup"><div class="brand-mark" aria-hidden="true">尘</div><div><p class="eyebrow">现场安全系统</p><h1>尘安智眼</h1></div></div><div class="connection-state" :class="{ online: connected }"><span class="status-dot"></span>{{ connected ? 'API 已连接' : '等待 API' }}</div></header>
</template>
