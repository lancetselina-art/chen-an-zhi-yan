import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { test } from 'node:test'
import { exportSvgAsPng } from '../src/utils/exportImage.js'

test('exports an SVG element as a PNG download', async () => {
  const calls = { clicked: false, revoked: '' }
  const anchor = {
    href: '',
    download: '',
    click() { calls.clicked = true },
  }
  const svg = { outerHTML: '<svg width="1200" height="720"></svg>' }
  const originalDocument = globalThis.document
  const originalUrl = globalThis.URL
  globalThis.document = {
    createElement: (tag) => {
      if (tag === 'a') return anchor
      if (tag === 'img') return {
        set src(value) { queueMicrotask(() => this.onload()) },
      }
      return {
        getContext: () => ({ drawImage() {} }),
        toBlob(callback) { callback(new Blob(['png'], { type: 'image/png' })) },
      }
    },
    body: { append() {}, removeChild() {} },
  }
  globalThis.URL = {
    createObjectURL: () => 'blob:test',
    revokeObjectURL: (value) => { calls.revoked = value },
  }

  try {
    await exportSvgAsPng(svg, 'architecture.png')
    assert.equal(anchor.download, 'architecture.png')
    assert.equal(calls.clicked, true)
    assert.equal(calls.revoked, 'blob:test')
  } finally {
    globalThis.document = originalDocument
    globalThis.URL = originalUrl
  }
})

test('architecture diagram contains system modules without credentials', async () => {
  const source = await readFile(fileURLToPath(new URL('../src/components/SystemArchitectureDiagram.vue', import.meta.url)), 'utf8')
  for (const label of ['浏览器用户', 'Vue 工作台', 'FastAPI 接口层', '规则与特征', 'LLM 编排', '知识库']) {
    assert.match(source, new RegExp(label))
  }
  assert.doesNotMatch(source, /API Key|api_key|密钥/)
})
