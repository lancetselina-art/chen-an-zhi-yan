# FastAPI 后端

`backend/` 是尘安智眼的 HTTP 入口。它复用仓库根目录的 `core/`，不复制阈值、Prompt 或报告算法；Streamlit 仍通过 `app.py` 独立运行。知识库检索固定读取项目根目录的 `/knowledge`，不会读取远程内容或前端副本。

## 启动

在项目根目录执行：

```powershell
pip install -r requirements.txt
python -m uvicorn backend.main:app --reload --port 8000
```

启动后可访问 `http://127.0.0.1:8000/docs` 查看 OpenAPI 文档，健康检查为：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

## 接口

| 方法 | 路径 | 输入 |
| --- | --- | --- |
| GET | `/api/health` | 无 |
| GET | `/api/config` | 无；只返回非敏感配置 |
| POST | `/api/vision/analyze` | multipart：`image`、`stage`、`work_type`、`is_night`、`demo_mode` |
| POST | `/api/sensors/features` | JSON `{"rows": [...]}` 或 multipart CSV 文件（可附带 `stage`、`work_type`、`city`、`is_night`） |
| POST | `/api/sensors/analyze` | JSON `{"features": {...}, "demo_mode": true}` |
| GET | `/api/knowledge/search?q=裸土` | 从项目根目录 `/knowledge` 查询参数 `q` |
| GET | `/api/knowledge/{file}` | 知识库文件名 |
| POST | `/api/reports/vision` | JSON `{"data": {...}, "context": {...}}` |
| POST | `/api/reports/sensor` | JSON `{"data": {...}, "features": {...}, "context": {...}}` |

成功和失败响应都包含以下字段：

```json
{
  "ok": true,
  "data": {},
  "error": null,
  "request_id": "..."
}
```

`demo_mode=true` 时使用现有离线演示能力；真实模型调用需要在运行环境中配置 `ZHIPUAI_API_KEY`（或项目 `core` 支持的兼容 API 配置）。服务不会把密钥放入 `/api/config` 响应。

## 开发约定

- 路由位于 `backend/api/`，Pydantic 模型位于 `backend/schemas/`。
- 服务适配位于 `backend/services/`，业务规则继续维护在 `core/`。
- 不在 API 层重新实现传感器阈值或知识库规则。
- 当前台账仍是 Streamlit 会话内存，不提供数据库持久化或鉴权。
