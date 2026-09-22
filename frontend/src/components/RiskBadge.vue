<script setup>
defineProps({ level: { type: String, default: 'GREEN' } })
const label = { RED: '红线', ORANGE: '橙线', YELLOW: '提醒', GREEN: '合格' }
</script>
<template><span class="risk-badge" :class="`risk-${level.toLowerCase()}`">{{ label[level] || level }}</span></template>
