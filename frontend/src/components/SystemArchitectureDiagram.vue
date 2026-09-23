<script setup>
import { ref } from 'vue'
import { exportSvgAsPng } from '../utils/exportImage'

const svgElement = ref(null)
const error = ref('')
const downloading = ref(false)

async function downloadPng() {
  downloading.value = true
  error.value = ''
  try {
    await exportSvgAsPng(svgElement.value, 'chen-an-zhi-yan-system-architecture.png')
  } catch (downloadError) {
    error.value = downloadError.message || '图片导出失败'
  } finally {
    downloading.value = false
  }
}
</script>

<template>
  <section class="architecture-panel panel">
    <div class="architecture-heading">
      <div>
        <p class="eyebrow">系统模块架构</p>
        <h3>尘安智眼 · 安全巡检工作台</h3>
        <p class="architecture-note">从采集入口到规则、模型与知识库的模块关系</p>
      </div>
      <button class="secondary-button" type="button" :disabled="downloading" @click="downloadPng">
        <span aria-hidden="true">↓</span>{{ downloading ? '生成中...' : '下载 PNG' }}
      </button>
    </div>
    <div class="architecture-scroll">
      <svg ref="svgElement" class="architecture-svg" width="1280" height="700" viewBox="0 0 1280 700" role="img" aria-label="尘安智眼系统模块架构图" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <marker id="architecture-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
            <path d="M0 0L8 4L0 8Z" fill="#667085" />
          </marker>
          <filter id="architecture-shadow" x="-10%" y="-10%" width="120%" height="120%">
            <feDropShadow dx="0" dy="3" stdDeviation="5" flood-color="#182230" flood-opacity=".08" />
          </filter>
        </defs>
        <rect width="1280" height="700" rx="18" fill="#f7f8fa" />
        <text x="48" y="48" fill="#475467" font-family="system-ui, sans-serif" font-size="15" font-weight="700" letter-spacing="1">SYSTEM MODULE ARCHITECTURE</text>
        <text x="48" y="75" fill="#98a2b3" font-family="system-ui, sans-serif" font-size="13">可配置模型服务 · 本地优先知识库 · 规则与 AI 协同</text>

        <g font-family="system-ui, sans-serif" font-size="13" fill="#667085">
          <text x="48" y="124">用户端</text><text x="300" y="124">前端应用</text><text x="552" y="124">FastAPI 接口层</text><text x="808" y="124">核心分析服务</text><text x="1080" y="124">能力与数据</text>
        </g>
        <g fill="#fff" stroke="#d0d5dd" stroke-width="1.5" filter="url(#architecture-shadow)" font-family="system-ui, sans-serif">
          <rect x="48" y="154" width="184" height="92" rx="12" /><rect x="48" y="282" width="184" height="92" rx="12" />
          <rect x="300" y="154" width="184" height="92" rx="12" /><rect x="300" y="282" width="184" height="92" rx="12" /><rect x="300" y="410" width="184" height="92" rx="12" />
          <rect x="552" y="154" width="184" height="92" rx="12" /><rect x="552" y="282" width="184" height="92" rx="12" /><rect x="552" y="410" width="184" height="92" rx="12" />
          <rect x="808" y="154" width="184" height="92" rx="12" /><rect x="808" y="282" width="184" height="92" rx="12" /><rect x="808" y="410" width="184" height="92" rx="12" />
          <rect x="1080" y="154" width="152" height="92" rx="12" /><rect x="1080" y="282" width="152" height="92" rx="12" /><rect x="1080" y="410" width="152" height="92" rx="12" />
        </g>
        <g font-family="system-ui, sans-serif" text-anchor="middle">
          <g fill="#101828" font-size="16" font-weight="700"><text x="140" y="192">浏览器用户</text><text x="140" y="320">现场人员</text><text x="392" y="192">Vue 工作台</text><text x="392" y="320">视觉巡检</text><text x="392" y="448">传感器研判</text><text x="644" y="192">视觉 API</text><text x="644" y="320">传感器 API</text><text x="644" y="448">报告 / 配置 API</text><text x="900" y="192">规则与特征</text><text x="900" y="320">LLM 编排</text><text x="900" y="448">结果与台账</text><text x="1156" y="192">模型服务</text><text x="1156" y="320">知识库</text><text x="1156" y="448">本地数据</text></g>
          <g fill="#667085" font-size="12"><text x="140" y="216">上传图片 / CSV · 查看结果</text><text x="140" y="344">浏览器端操作入口</text><text x="392" y="216">页面状态与导出</text><text x="392" y="344">图片 + 整改建议</text><text x="392" y="472">时序 + 风险分级</text><text x="644" y="216">/api/vision</text><text x="644" y="344">/api/sensors</text><text x="644" y="472">/api/reports · /api/settings</text><text x="900" y="216">阈值计算 / 趋势分析</text><text x="900" y="344">文本与视觉模型调用</text><text x="900" y="472">报告、历史与整改</text><text x="1156" y="216">OpenAI 兼容接口</text><text x="1156" y="344">Markdown 规范原文</text><text x="1156" y="472">示例图片 / 传感器文件</text></g>
        </g>
        <g fill="none" stroke="#667085" stroke-width="2" marker-end="url(#architecture-arrow)">
          <path d="M232 200H300" /><path d="M232 328H270V200H300" /><path d="M484 200H552" /><path d="M484 328H552" /><path d="M484 456H552" /><path d="M736 200H808" /><path d="M736 328H808" /><path d="M736 456H808" /><path d="M992 200H1080" /><path d="M992 328H1040V200H1080" /><path d="M992 456H1040V456H1080" />
        </g>
        <g fill="#98a2b3" font-family="system-ui, sans-serif" font-size="11"><text x="48" y="620">数据流：采集 → 接口 → 确定性分析 → 模型补充解释 → 结果与整改闭环</text><text x="48" y="648">部署边界：前端与 API 服务可独立运行，模型服务通过 Base URL 配置接入</text></g>
      </svg>
    </div>
    <p v-if="error" class="error-text architecture-error" role="alert">{{ error }}</p>
  </section>
</template>
