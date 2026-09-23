<script setup>
import { ref, watch } from 'vue'
import RiskBadge from '../components/RiskBadge.vue'
import EmptyState from '../components/EmptyState.vue'
import SystemArchitectureDiagram from '../components/SystemArchitectureDiagram.vue'
import { analyzeVision, resolveAssetUrl } from '../api'

const emit = defineEmits(['record'])
const file = ref(null)
const result = ref(null)
const error = ref('')
const loading = ref(false)
const demoMode = ref(true)
const isNight = ref(false)
const stage = ref('')
const workType = ref('')

watch(demoMode, (enabled) => {
  if (enabled) file.value = null
})

function choose(event) {
  file.value = event.target.files?.[0] || null
}

async function submit() {
  if (!file.value && !demoMode.value) {
    error.value = '请先选择现场图片'
    return
  }
  loading.value = true
  error.value = ''
  try {
    result.value = await analyzeVision({
      file: file.value,
      stage: stage.value,
      workType: workType.value,
      isNight: isNight.value,
      demoMode: demoMode.value,
    })
    emit('record', {
      type: '视觉巡检',
      title: result.value?.overall?.headline || '视觉巡检完成',
      risk: result.value?.overall?.risk_level || 'GREEN',
    })
  } catch (requestError) {
    error.value = requestError.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="view-section">
    <div class="view-heading">
      <div>
        <p class="eyebrow">视觉巡检 / 02</p>
        <h2>在现场语境中看见风险。</h2>
        <p class="lede">上传现场图片，获取结构化隐患、证据链和整改建议。</p>
      </div>
      <RiskBadge :level="result?.overall?.risk_level || 'GREEN'" />
    </div>

    <div class="split-layout">
      <form class="panel form-panel" @submit.prevent="submit">
        <label class="upload-zone">
          <input type="file" accept="image/jpeg,image/png,image/webp" @change="choose" />
          <span class="upload-icon">+</span>
          <strong>{{ demoMode ? '默认演示图片：data/demo_site.jpg' : (file ? file.name : '选择现场图片') }}</strong>
          <small>{{ demoMode && !file ? '点击开始视觉巡检后自动分析' : '支持 JPG / PNG / WEBP' }}</small>
        </label>
        <div class="form-grid">
          <label>施工阶段<input v-model="stage" placeholder="例如：土方/地基处理" /></label>
          <label>作业类型<input v-model="workType" placeholder="例如：土方开挖" /></label>
        </div>
        <label class="toggle-row"><input v-model="isNight" type="checkbox" /> 夜间施工</label>
        <label class="toggle-row"><input v-model="demoMode" type="checkbox" /> 离线演示模式</label>
        <button class="primary-button" :disabled="loading">
          {{ loading ? '分析中...' : '开始视觉巡检' }}
        </button>
        <p v-if="error" class="error-text">{{ error }}</p>
      </form>

      <article class="panel result-panel">
        <div v-if="result">
          <p class="eyebrow">分析结果</p>
          <div class="result-header">
            <h3>{{ result.overall?.headline || '分析完成' }}</h3>
            <RiskBadge :level="result.overall?.risk_level || 'GREEN'" />
          </div>
          <p class="result-score">{{ result.overall?.risk_score ?? '-' }}<small>/ 100 风险分</small></p>

          <div v-if="result.input_image_url || result.overlay_image_url" class="vision-assets">
            <figure v-if="result.input_image_url">
              <img :src="resolveAssetUrl(result.input_image_url)" alt="演示输入现场图片" />
              <figcaption>输入图片</figcaption>
            </figure>
            <figure v-if="result.overlay_image_url">
              <img :src="resolveAssetUrl(result.overlay_image_url)" alt="隐患标注叠加结果" />
              <figcaption>隐患标注结果</figcaption>
            </figure>
          </div>

          <div class="finding-details">
            <article v-for="finding in result.findings || []" :key="finding.id" class="finding-detail">
              <div class="finding-detail-heading">
                <RiskBadge :level="finding.severity" />
                <strong>{{ finding.item }}</strong>
              </div>
              <p><b>视觉证据</b>{{ finding.visual_evidence || '暂无' }}</p>
              <p><b>证据链</b>{{ finding.accident_chain || '暂无' }}</p>
              <p v-if="finding.standard_refs?.length"><b>标准依据</b>{{ finding.standard_refs.map((item) => item.code).join('、') }}</p>
              <p><b>整改建议</b>{{ finding.rectification?.action || '暂无' }}</p>
            </article>
          </div>
        </div>
        <EmptyState v-else title="等待上传图片" message="结构化巡检结果会显示在这里。" />
      </article>
    </div>
    <SystemArchitectureDiagram v-if="result" />
  </section>
</template>
