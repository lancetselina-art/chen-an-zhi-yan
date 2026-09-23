<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import MarkdownIt from 'markdown-it'
import EmptyState from '../components/EmptyState.vue'
import { getKnowledgeFile } from '../api'

const props = defineProps({ file: { type: String, required: true } })
defineEmits(['back'])
const document = ref(null)
const error = ref('')
const loading = ref(false)
const markdown = new MarkdownIt({ html: false, linkify: true, breaks: false })
const renderedContent = computed(() => document.value ? markdown.render(document.value.content) : '')

async function loadDocument() {
  loading.value = true
  error.value = ''
  document.value = null
  try { document.value = await getKnowledgeFile(props.file) } catch (e) { error.value = e.message }
  finally { loading.value = false }
}

onMounted(loadDocument)
watch(() => props.file, loadDocument)
</script>

<template>
  <section class="view-section document-view">
    <div class="document-toolbar">
      <button class="secondary-button" @click="$emit('back')">返回规范检索</button>
      <p class="eyebrow">规范原文</p>
    </div>
    <p v-if="error" class="error-text">{{ error }}</p>
    <article v-else-if="document" class="markdown-document">
      <div class="markdown-body" v-html="renderedContent"></div>
    </article>
    <div v-else-if="loading" class="panel"><EmptyState title="正在载入规范" message="" /></div>
  </section>
</template>
