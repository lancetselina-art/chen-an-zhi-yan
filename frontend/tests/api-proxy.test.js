import assert from 'node:assert/strict'
import { test } from 'node:test'
import config from '../vite.config.js'

test('forwards same-origin API requests to the local backend', () => {
  assert.equal(config.server.proxy?.['/api']?.target, 'http://127.0.0.1:8000')
})
