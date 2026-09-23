import { get, getApiBaseUrl, postForm, postJson, request } from './client'

export const getHealth = () => get('/api/health')
export const getConfig = () => get('/api/config')
export const getModelSettings = () => get('/api/settings/model')
export const saveModelSettings = (settings) => request('/api/settings/model', {
  method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(settings),
})
export const testModelSettings = (settings) => request('/api/settings/model/test', {
  method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(settings),
})
export const analyzeVision = ({ file, stage, workType, isNight, demoMode }) => {
  const form = new FormData()
  if (file) form.append('image', file)
  form.append('stage', stage || '')
  form.append('work_type', workType || '')
  form.append('is_night', String(Boolean(isNight)))
  form.append('demo_mode', String(Boolean(demoMode)))
  return postForm('/api/vision/analyze', form)
}
export const resolveAssetUrl = (path) => {
  if (!path) return ''
  return /^https?:\/\//.test(path) ? path : `${getApiBaseUrl()}${path}`
}
export const computeSensorFeatures = (rows, context = {}) => postJson('/api/sensors/features', { rows, ...context })
export const computeSensorFeaturesFile = (file, context = {}) => {
  const form = new FormData()
  form.append('file', file)
  form.append('stage', context.stage || '')
  form.append('work_type', context.work_type || '')
  form.append('city', context.city || '')
  form.append('is_night', String(Boolean(context.is_night)))
  return postForm('/api/sensors/features', form)
}
export const analyzeSensors = (features, context = {}, demoMode = true) => postJson('/api/sensors/analyze', { features, context, demo_mode: demoMode })
export const searchKnowledge = async (query) => {
  const payload = await get(`/api/knowledge/search?q=${encodeURIComponent(query || '')}`)
  return Array.isArray(payload) ? payload : (payload?.results || [])
}
export const getKnowledgeFile = (file) => get(`/api/knowledge/${encodeURIComponent(file)}`)
export const reportVision = (data, context = {}) => postJson('/api/reports/vision', { data, context })
export const reportSensor = (data, features, context = {}) => postJson('/api/reports/sensor', { data, features, context })
