# 交付清单 — RedScope v1

> 阶段：delivery ｜ 变更：001-redscope-v1 ｜ 工作模式：new

## 1. 已交付能力

| 模块 | 状态 | 说明 |
|------|------|------|
| 采集 | ✅ | 主题驱动任务，异步执行 + 进度落库 + SSE，mock 模式默认可演示；real 模式 Playwright 持久化登录态骨架已隔离 |
| 笔记库 | ✅ | 列表/搜索/排序 + 详情抽屉 + 互动数据 |
| 分析 | ✅ | jieba 选题热词、互动综合分爆款榜单、内容拆解（规则 + LLM 回退） |
| 仿写 | ✅ | 标题矩阵 + 正文（可编辑）+ 标签 + 配图建议 + 导出 Markdown（LLM + 启发式回退） |
| 设置 | ✅ | LLM（base_url/key/model/温度，连通性测试）、采集（数量/限速/并发/评论）落库 |
| 合规 | ✅ | 首屏免责声明、低频限速默认、个人用途定位 |

## 2. 运行方式

### 后端
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --port 8000        # http://localhost:8000
```

### 前端
```bash
cd frontend
npm install
npm run dev                              # http://localhost:5173（已代理 /api -> 8000）
```

## 3. 环境变量（后端，前缀 REDSCOPE_，可选）

| 变量 | 默认 | 说明 |
|------|------|------|
| `REDSCOPE_DATABASE_URL` | `sqlite:///./redscope.db` | 数据库连接 |
| `REDSCOPE_COLLECT_MODE` | `mock` | `mock` 演示 / `real` 真实采集（Playwright） |
| `REDSCOPE_CORS_ORIGINS` | `http://localhost:5173` | 允许的前端来源 |
| `REDSCOPE_LLM_BASE_URL` | `https://api.openai.com/v1` | 默认 LLM 接口（也可在设置页覆盖并落库） |
| `REDSCOPE_LLM_API_KEY` | 空 | LLM Key（未配置时分析/仿写走启发式回退） |
| `REDSCOPE_LLM_MODEL` | `gpt-4o-mini` | 模型名 |
| `REDSCOPE_USER_DATA_DIR` | `./.xhs-user-data` | real 模式 Playwright 登录态目录 |

> 启用 real 模式前需执行：`python -m playwright install chromium`。

## 4. 质量门禁结果

- 前端：`npm run build`（tsc + vite）通过；`npm run lint` 0 warning。
- 后端：`pytest` 7 项通过（分析规则、API 契约、采集流程、设置往返、仿写）。
- 端到端：浏览器实测采集→笔记库→分析（真实 jieba 热词）→仿写全链路通畅，控制台无 error。

## 5. 已知限制 / 后续

1. **真实采集未对接平台解析**：`real` 模式保留 Playwright 持久化上下文骨架，详情解析与签名调用需按平台当前页面结构补全；默认 `mock` 保障可演示与测试稳定。
2. **任务编排为单机内存队列**：v1 单用户本地场景足够；多用户/重负载需引入持久化队列（Celery/Redis）。
3. **前端 bundle 偏大**：可后续按路由 code-split 优化。
4. **登录态为简化实现**：演示用内存态；real 模式应以 Playwright 上下文有效性为准。

## 6. 合规声明

本工具仅用于个人创作辅助与学习研究，须使用本人账号、低频限速，仅采集公开内容，仿写结果应原创化改写；使用者需遵守小红书平台规则与法律法规，自行承担使用后果。

## 7. 关键文件索引

- 文档：`output/xhs-research.md`、`xhs-prd.md`、`xhs-architecture.md`、`xhs-uiux.md`
- Spec：`.super-dev/changes/001-redscope-v1/{proposal,tasks}.md`
- 后端：`backend/app/{main.py, api/*, services/*, models.py, schemas.py, core/*}`
- 前端：`frontend/src/{pages/*, components/*, api/client.ts, lib/*, store/*}`
- 共享：`shared/api-routes.ts`
