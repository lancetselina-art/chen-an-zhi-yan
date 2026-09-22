<script setup>
import { ref } from 'vue'
import EmptyState from '../components/EmptyState.vue'
import { searchKnowledge, getKnowledgeFile } from '../api'
const query = ref(''); const results = ref([]); const selected = ref(null); const error = ref(''); const loading = ref(false)
async function search() { loading.value = true; error.value = ''; try { results.value = await searchKnowledge(query.value) } catch (e) { error.value = e.message } finally { loading.value = false } }
async function openFile(file) { try { selected.value = await getKnowledgeFile(file) } catch (e) { error.value = e.message } }
</script>
<template><section class="view-section"><div class="view-heading"><div><p class="eyebrow">知识库 / 04</p><h2>规范，随时可以查。</h2><p class="lede">从本地规则精要开始检索，需要时打开完整条款。</p></div></div><div class="knowledge-search"><input v-model="query" placeholder="搜索扬尘、噪声、高温..." @keyup.enter="search" /><button class="secondary-button" :disabled="loading" @click="search">{{ loading ? '检索中...' : '搜索' }}</button></div><p v-if="error" class="error-text">{{ error }}</p><div class="knowledge-layout"><div class="panel"><div v-if="results.length" class="knowledge-list"><button v-for="item in results" :key="item.file" class="knowledge-item" @click="openFile(item.file)"><span>{{ item.file }}</span><small>匹配度 {{ item.score }}</small><p>{{ item.snippet }}</p></button></div><EmptyState v-else title="暂无检索结果" message="输入现场规则关键词开始搜索。" /></div><article class="panel document-panel"><div v-if="selected"><p class="eyebrow">规范原文</p><h3>{{ selected.file }}</h3><pre>{{ selected.content }}</pre></div><EmptyState v-else title="选择一条规范" message="完整条款会显示在这里。" /></article></div></section></template>
