# Vue 前端

`frontend/` 是独立运行的 Vue 3 + Vite + JavaScript 客户端。它不嵌入 Streamlit，通过 HTTP 调用 `backend/`；Streamlit 仍是无需 Node 的最终展示入口。

## 开发

```powershell
npm.cmd install
copy .env.example .env.local
npm.cmd run dev
```

默认 API 地址为 `http://localhost:8000`。如后端运行在其他地址，修改 `.env.local`：

```text
VITE_API_BASE_URL=http://localhost:8000
```

生产构建：

```powershell
npm.cmd run build
```

## 页面与 API

当前客户端包含五个视图：总览、视觉巡检、传感器、知识库和台账。请求封装集中在 `src/api/`，页面只处理交互状态和展示，不复制 `core/` 算法。

| 前端能力 | 后端接口 |
| --- | --- |
| 服务状态和运行配置 | `GET /api/health`、`GET /api/config` |
| 图片巡检 | `POST /api/vision/analyze` |
| 特征计算与研判 | `POST /api/sensors/features`、`POST /api/sensors/analyze` |
| 规范搜索 | `GET /api/knowledge/search`、`GET /api/knowledge/{file}` |
| 报告生成 | `POST /api/reports/vision`、`POST /api/reports/sensor` |

## 视觉规范

界面采用 Apple 简约分隔风格：浅色背景、黑色正文、低饱和蓝色操作色、细分隔线、弱阴影和不超过 8px 的圆角；风险红/橙/黄/绿只用于状态语义。需要启动前端时，同时启动项目根目录的 FastAPI 服务即可。
