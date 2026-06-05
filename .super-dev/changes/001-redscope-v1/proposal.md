# 变更提案 001 — RedScope v1

> 阶段：spec ｜ 依据：output/xhs-prd.md、xhs-architecture.md、xhs-uiux.md ｜ 状态：已通过文档确认门

## 1. 目标

交付 RedScope v1：本地优先的「采集 → 分析 → 仿写」闭环工具。采用**前端优先**策略，先用 mock 数据跑通可演示前端，确认后再接后端真实采集与 LLM。

## 2. 范围

**包含**
- 前端：React+TS+Vite+Tailwind+shadcn/ui，6 页面（Dashboard/Collect/Notes/Insights/Compose/Settings），完整状态矩阵，lucide-react 图标，mock 数据层。
- 后端：FastAPI + SQLite + Playwright 采集 + 规则分析 + OpenAI 兼容 LLM 仿写；REST + SSE。
- 共享：`shared/api-routes` 路径常量。
- 质量：lint/tsc/build + 后端 pytest + 交付清单。

**不包含（v1 非目标）**
- 自动发布 / 养号 / 引流 / 多账号矩阵 / 商用数据售卖 / 绕风控高频采集。

## 3. 技术决策（已确认默认）

- 前端：React 18 + TS + Vite + Tailwind + shadcn/ui + TanStack Query + Zustand + Recharts + lucide-react。
- 后端：Python 3.11 + FastAPI + Uvicorn + SQLModel + SQLite + Playwright(Chromium)。
- LLM：httpx + OpenAI 兼容协议，base_url/model/key 可配置。
- 采集：浏览器内签名 + 限速/重试/去重；mock 优先，真实采集可隔离替换。

## 4. 交付里程碑

- M1 前端可演示（mock）→ PREVIEW_CONFIRM_GATE。
- M2 后端 API + 采集 + 落库。
- M3 分析 + 仿写接 LLM + 前后端联调。
- M4 质量门禁 + 交付清单。

## 5. 风险与缓解

- 平台风控 → 限速 + 自有登录态 + 个人用途；mock 优先降低早期对真实平台依赖。
- 页面结构变动 → 采集层适配隔离。
- LLM 不可用 → 可配置 provider + 失败降级提示。

## 6. 验收（对齐 PRD DoD）

见 tasks.md 的逐项 DoD；最终需 build/lint/tsc/test 通过且前端可演示。
