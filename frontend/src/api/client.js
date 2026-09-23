const baseUrl = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')

function unwrap(payload) {
  if (payload && typeof payload === 'object' && 'ok' in payload) {
    if (!payload.ok) throw new Error(payload.error?.message || '请求失败')
    return payload.data
  }
  return payload
}

export async function request(path, options = {}) {
  const response = await fetch(`${baseUrl}${path}`, options)
  let payload = null
  try { payload = await response.json() } catch { /* empty response */ }
  if (!response.ok) throw new Error(payload?.error?.message || payload?.detail || `请求失败（${response.status}）`)
  return unwrap(payload)
}
export const getApiBaseUrl = () => baseUrl
export const get = (path) => request(path)
export const postJson = (path, body) => request(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
export const postForm = (path, form) => request(path, { method: 'POST', body: form })
