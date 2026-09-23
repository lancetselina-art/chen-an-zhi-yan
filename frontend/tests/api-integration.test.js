import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { test } from 'node:test'

const baseUrl = process.env.API_TEST_BASE_URL || 'http://127.0.0.1:5173'

async function request(path, options) {
  const response = await fetch(`${baseUrl}${path}`, options)
  const payload = response.headers.get('content-type')?.includes('application/json')
    ? await response.json()
    : null
  assert.equal(response.status, 200, `${options?.method || 'GET'} ${path}: ${JSON.stringify(payload)}`)
  return { response, payload: payload?.data }
}

test('same-origin API proxy supports the application workflows', async () => {
  const { payload: health } = await request('/api/health')
  assert.equal(health.status, 'ok')

  const { payload: matches } = await request('/api/knowledge/search?q=%E6%89%AC%E5%B0%98')
  assert.ok(matches.length > 0)
  const file = encodeURIComponent(matches[0].file)
  const { payload: document } = await request(`/api/knowledge/${file}`)
  assert.ok(document.content.length > 100)

  const demoForm = new FormData()
  demoForm.set('demo_mode', 'true')
  const { payload: vision } = await request('/api/vision/analyze', { method: 'POST', body: demoForm })
  assert.equal(vision.findings.length, 6)
  assert.ok(vision.findings.every((finding) => finding.rectification?.action))
  await request(vision.input_image_url)
  await request(vision.overlay_image_url)

  const csv = await readFile(fileURLToPath(new URL('../../data/sample_sensor.csv', import.meta.url)))
  const sensorForm = new FormData()
  sensorForm.append('file', new Blob([csv], { type: 'text/csv' }), 'sample_sensor.csv')
  const { payload: features } = await request('/api/sensors/features', { method: 'POST', body: sensorForm })
  assert.ok(Object.keys(features).length > 0)
  const { payload: sensor } = await request('/api/sensors/analyze', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ features, context: {}, demo_mode: true }),
  })

  await request('/api/reports/vision', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ data: vision, context: {} }),
  })
  await request('/api/reports/sensor', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ data: sensor, features, context: {} }),
  })
})
