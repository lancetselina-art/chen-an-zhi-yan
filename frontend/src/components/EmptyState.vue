<script setup>
defineProps({ title: { type: String, default: '暂无数据' }, message: { type: String, default: '' } })
</script>
<template><div class="empty-state"><span class="empty-icon">-</span><strong>{{ title }}</strong><p v-if="message">{{ message }}</p></div></template>
