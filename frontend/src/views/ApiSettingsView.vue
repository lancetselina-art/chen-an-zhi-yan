<script setup>
import { onMounted, reactive, ref } from 'vue'
import EmptyState from '../components/EmptyState.vue'
import { getModelSettings, saveModelSettings, testModelSettings } from '../api'

const settings = reactive({ base_url: '', vision_model: '', text_model: '' })
const apiKey = ref('')
const keyConfigured = ref(false)
const loading = ref(true)
const saving = ref(false)
const testing = ref(false)
const error = ref('')
const message = ref('')

function applySettings(value) {
  settings.base_url = value.base_url
  settings.vision_model = value.vision_model
  settings.text_model = value.text_model
  keyConfigured.value = value.api_key_configured
}

async function loadSettings() {
  loading.value = true
  error.value = ''
  try { applySettings(await getModelSettings()) } catch (e) { error.value = e.message }
  finally { loading.value = false }
}

function requestBody(clearApiKey = false) {
  return { ...settings, api_key: clearApiKey ? undefined : apiKey.value || undefined, clear_api_key: clearApiKey }
}

async function save() {
  saving.value = true
  error.value = ''
  message.value = ''
  try {
    applySettings(await saveModelSettings(requestBody()))
    apiKey.value = ''
    message.value = '配置已保存'
  } catch (e) { error.value = e.message }
  finally { saving.value = false }
}

async function testConnection() {
  testing.value = true
  error.value = ''
  message.value = ''
  try {
    const result = await testModelSettings(requestBody())
    message.value = `连接成功 · ${result.model}`
  } catch (e) { error.value = e.message }
  finally { testing.value = false }
}

async function clearKey() {
  saving.value = true
  error.value = ''
  message.value = ''
  try {
    applySettings(await saveModelSettings(requestBody(true)))
    apiKey.value = ''
    message.value = keyConfigured.value ? '本机密钥已清除，仍检测到环境变量配置' : 'API Key 已清除'
  } catch (e) { error.value = e.message }
  finally { saving.value = false }
}

onMounted(loadSettings)
</script>

<template>
  <section class="view-section">
    <div class="view-heading">
      <div><p class="eyebrow">模型服务 / 06</p><h2>模型 API 配置</h2><p class="lede">设置 OpenAI 兼容服务，用于真实视觉与文本分析。</p></div>
    </div>

    <div v-if="loading" class="panel api-loading"><EmptyState title="正在读取配置" message="" /></div>
    <form v-else class="panel api-settings" @submit.prevent="save">
      <div class="api-key-state" :class="{ configured: keyConfigured }">
        <span class="status-dot"></span>
        <span>{{ keyConfigured ? 'API Key 已配置' : '尚未配置 API Key' }}</span>
      </div>

      <label class="api-field api-field-wide">Base URL
        <input v-model.trim="settings.base_url" type="url" required placeholder="https://api.example.com/v1" autocomplete="url" />
      </label>
      <label class="api-field api-field-wide">API Key
        <input v-model="apiKey" type="password" autocomplete="new-password" :placeholder="keyConfigured ? '留空以保留当前密钥' : '输入服务商提供的 API Key'" />
      </label>
      <div class="api-fields">
        <label>视觉模型
          <input v-model.trim="settings.vision_model" required placeholder="例如 glm-5.3-flash" autocomplete="off" />
        </label>
        <label>文本模型
          <input v-model.trim="settings.text_model" required placeholder="例如 glm-5.3-flash" autocomplete="off" />
        </label>
      </div>

      <p v-if="error" class="error-text" role="alert">{{ error }}</p>
      <p v-else-if="message" class="api-message" role="status">{{ message }}</p>
      <div class="api-actions">
        <button class="primary-button" type="submit" :disabled="saving || testing">{{ saving ? '保存中...' : '保存配置' }}</button>
        <button class="secondary-button" type="button" :disabled="saving || testing" @click="testConnection">{{ testing ? '测试中...' : '测试连接' }}</button>
        <button v-if="keyConfigured" class="text-button" type="button" :disabled="saving || testing" @click="clearKey">清除本机密钥</button>
      </div>
    </form>
  </section>
</template>
