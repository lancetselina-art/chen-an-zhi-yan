<script setup>
defineProps({ metrics: { type: Array, default: () => [] } })
</script>
<template>
  <div class="metric-strip">
    <div v-for="metric in metrics" :key="metric.label" class="metric-cell">
      <span class="metric-label">{{ metric.label }}</span>
      <strong>{{ metric.value }}</strong>
      <span v-if="metric.note" class="metric-note">{{ metric.note }}</span>
    </div>
  </div>
</template>
