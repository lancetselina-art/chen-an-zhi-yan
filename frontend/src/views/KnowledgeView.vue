<script setup>
import { ref } from 'vue'
import EmptyState from '../components/EmptyState.vue'
import { searchKnowledge } from '../api'
const emit = defineEmits(['open-document'])
const query = ref(''); const results = ref([]); const error = ref(''); const loading = ref(false)
async function search() { loading.value = true; error.value = ''; try { results.value = await searchKnowledge(query.value) } catch (e) { error.value = e.message } finally { loading.value = false } }
</script>
<template>
  <section class="view-section">
    <div class="view-heading">
      <div><p class="eyebrow">知识库 / 04</p><h2>规范，随时可查。</h2><p class="lede">搜索现场规则，打开条款全文。</p></div>
    </div>
    <div class="knowledge-search">
      <input v-model="query" placeholder="搜索扬尘、噪声、高温..." aria-label="搜索规范" @keyup.enter="search" />
      <button class="secondary-button" :disabled="loading" @click="search">{{ loading ? '检索中...' : '搜索' }}</button>
    </div>
    <p v-if="error" class="error-text">{{ error }}</p>
    <div class="knowledge-list panel">
      <button v-for="item in results" :key="item.file" class="knowledge-item" @click="emit('open-document', item.file)">
        <span>{{ item.file.replace(/\.md$/i, '') }}</span>
        <small>匹配度 {{ item.score }}</small>
        <p>{{ item.snippet }}</p>
      </button>
      <EmptyState v-if="!results.length && !loading" title="暂无检索结果" message="输入现场规则关键词开始搜索。" />
    </div>
  </section>
</template>
