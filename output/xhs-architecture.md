# 架构文档 — RedScope

> 阶段：docs ｜ 依据：output/xhs-research.md、output/xhs-prd.md ｜ 状态：待用户确认

## 1. 架构总览

本地优先的前后端分离应用。前端负责交互与可视化；后端负责采集（浏览器自动化）、存储、分析与 LLM 调用。

```
┌───────────────────────────────────────────────────────────┐
│                       前端 (React/Vite)                      │
│  Dashboard │ Collect │ Notes │ Insights │ Compose │ Settings │
└───────────────▲───────────────────────────┬─────────────────┘
                │ REST + SSE(进度)            │
┌───────────────┴───────────────────────────▼─────────────────┐
│                     后端 API (FastAPI)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────┐ │
│  │ 任务编排  │  │ 采集服务  │  │ 分析引擎  │  │ 仿写引擎       │ │
│  │ (asyncio │→ │ Playwright│→ │ 规则+LLM  │  │ LLM+模板       │ │
│  │  队列)    │  │ 登录态+签名│  │          │  │               │ │
│  └──────────┘  └────┬─────┘  └────┬─────┘  └──────┬────────┘ │
│                     │             │                │          │
│              ┌──────▼─────────────▼────────────────▼───────┐  │
│              │            存储层 (SQLite + 文件)            │  │
│              └──────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────┘
                         │ OpenAI 兼容接口
                  ┌──────▼───────┐
                  │  LLM Provider │ (可配置 base_url/model/key)
                  └───────────────┘
```

## 2. 技术栈

| 层 | 选型 | 理由 |
|----|------|------|
| 前端 | React 18 + TypeScript + Vite | 生态成熟、构建快 |
| 样式 | Tailwind CSS + shadcn/ui | 设计 token 可控、组件质量高 |
| 图标 | **lucide-react**（唯一图标库） | 统一、禁用 emoji 作功能图标 |
| 图表 | Recharts | 轻量、与 React 集成好 |
| 状态/请求 | TanStack Query + Zustand | 服务端状态缓存 + 轻量本地态 |
| 后端 | Python 3.11 + FastAPI + Uvicorn | 异步、贴合采集生态 |
| 采集 | Playwright (Chromium) | 登录态 + 浏览器内签名，参考 MediaCrawler |
| 存储 | SQLite + SQLModel | 零依赖、本地优先；图片仅存 URL |
| 任务 | asyncio Task + 内存队列 + DB 状态 | v1 单机足够，避免引入 Celery/Redis |
| LLM | httpx + OpenAI 兼容协议 | 可切换厂商/本地模型 |

> 技术栈倾向 PRD 中标注「你来推荐」，此处给出默认推荐；如需 Next.js/Vue 可在确认门调整。

## 3. 模块设计

### 3.1 采集服务 (collector)
- `BrowserManager`：管理 Playwright 持久化上下文（保存登录态到本地 user-data-dir）。
- `LoginService`：扫码/Cookie 登录，检测登录态有效性。
- `XhsClient`：在浏览器上下文内调用页面签名逻辑发起搜索/详情请求，返回结构化数据。
- `RateLimiter`：随机延时 + 并发信号量 + 重试退避。
- `Deduplicator`：按 note_id 去重。

### 3.2 任务编排 (tasks)
- 任务模型：`id, topic, params, status(pending/running/success/failed), progress, created_at`。
- 执行器：asyncio 协程消费队列；进度写 DB；通过 **SSE** 推送实时进度给前端。

### 3.3 分析引擎 (analysis)
- 规则统计：词频/标签聚类（jieba 分词）、互动综合分、Top 排序。
- LLM 拆解：将笔记标题/正文送入 LLM，按固定 schema 输出（标题公式、钩子、骨架、标签策略）。

### 3.4 仿写引擎 (compose)
- 输入：参考笔记/拆解模板 + 新主题/卖点 + 风格/长度参数。
- Prompt 管线：系统约束（原创化、平台风格）+ few-shot（拆解结论）+ 用户输入。
- 输出 schema：`titles[], body, hashtags[], image_suggestions[]`。

## 4. 数据模型（SQLite）

```
collect_task(id, topic, params_json, status, progress, total, error, created_at)
note(id, task_id, note_id, title, content, author, likes, collects,
     comments, shares, publish_time, url, images_json, raw_json, created_at)
analysis(id, task_id, type, payload_json, created_at)   -- 热词/榜单/拆解缓存
compose_result(id, ref_note_id, topic, titles_json, body, hashtags_json,
               images_json, created_at)
setting(key, value_json)                                 -- LLM/采集配置(本地)
```

## 5. API 设计（REST）

```
POST   /api/collect/tasks          新建采集任务 -> {task_id}
GET    /api/collect/tasks          任务列表
GET    /api/collect/tasks/{id}     任务详情
GET    /api/collect/tasks/{id}/events   SSE 进度流
POST   /api/auth/login/qrcode      获取登录二维码
GET    /api/auth/status            登录态检测
GET    /api/notes                  笔记列表(筛选/分页)
GET    /api/notes/{id}             笔记详情
GET    /api/analysis/{task_id}     分析结果(热词/榜单)
POST   /api/analysis/breakdown     单篇拆解(LLM) -> schema
POST   /api/compose                仿写生成 -> schema
GET/PUT /api/settings              读写设置
```

- 前后端路径以 `shared/api-routes` 常量集中定义，避免前后端不一致（契约要求）。

## 6. 关键流程时序（采集）

```
前端 POST /collect/tasks
  → 后端建任务(pending) 入队 → 返回 task_id
  → 前端订阅 SSE /tasks/{id}/events
  → 执行器: 登录态校验 → 搜索列表 → 逐条详情(限速/去重) → 落库 → 推进度
  → 完成 status=success → 前端跳转笔记库/分析
```

## 7. 安全与合规

- 登录态与 api_key 仅存本地（user-data-dir / SQLite），不外发。
- 采集默认低频限速；提供保守默认值；不内置绕过风控的高频模式。
- 启动展示免责声明；日志不记录敏感凭证。

## 8. 部署与运行

- 开发：`backend`(uvicorn:8000) + `frontend`(vite:5173)，前端代理 `/api`。
- 一键脚本：`make dev` / `pnpm dev` + `uv run`；Playwright 首次安装 Chromium。
- 目录：
```
backend/   app/(api, collector, analysis, compose, models, core)
frontend/  src/(pages, components, lib, store, api)
shared/    api-routes.ts (路径常量)
output/    文档
```

## 9. 测试策略

- 后端：pytest（分析规则、schema 校验、限速逻辑、API 契约）。
- 采集：可 mock XhsClient 返回，避免 CI 真实请求平台。
- 前端：组件渲染 + 关键交互（vitest + testing-library）；lint + tsc。

## 10. 风险与权衡

- 不引入 Redis/Celery：v1 单用户本地场景，asyncio 足够，降低复杂度。
- 采集稳定性依赖平台页面结构 → 采集层做适配隔离，便于单点维护。
