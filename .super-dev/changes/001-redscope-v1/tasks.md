# 任务清单 — RedScope v1

> 阶段：spec ｜ 执行策略：前端优先（mock）→ PREVIEW_CONFIRM_GATE → 后端联调 → 质量交付
> 勾选规则：仅在实际完成并验证后标记 [x]。

## A. 工程脚手架
- [x] A1 初始化仓库结构：`frontend/`、`backend/`、`shared/`、根 README 占位
- [x] A2 前端脚手架：Vite + React + TS + Tailwind + shadcn/ui + 路由
- [x] A3 安装依赖：tanstack-query、zustand、recharts、lucide-react
- [x] A4 定义 `shared/api-routes.ts` 路径常量并在前端引用
- [x] A5 设计 token 落地（Tailwind theme：颜色/字体/间距/圆角/阴影，对齐 uiux）

## B. 前端框架与通用组件
- [x] B1 AppShell：SideNav(240) + TopBar(登录态徽标/新建按钮) + 内容区，响应式
- [x] B2 通用态组件：EmptyState / ErrorState / Skeleton
- [x] B3 DisclaimerDialog：首次进入免责声明（localStorage 记忆）
- [x] B4 mock 数据层：notes/tasks/analysis/compose 假数据 + 模拟延时

## C. 页面实现（mock 驱动）
- [x] C1 Dashboard：4 Metric 卡 + 采集趋势图 + 最近任务（空/加载/错误态）
- [x] C2 Collect：新建任务表单 + 任务卡片(进度/状态) + LoginQRCard
- [x] C3 Notes：FilterBar + NoteCard 网格 + NoteDrawer 详情
- [x] C4 Insights：Tab(选题热词 WordCloud / 爆款 RankingTable / 内容拆解 BreakdownCard)
- [x] C5 Compose：ComposePanel(参考+参数) + TitleMatrix + 正文编辑 + 标签 + 导出/复制
- [x] C6 Settings：LLM / 采集 / 账号与数据 分组卡片 + 连通性测试按钮

## D. 前端质量门 + 预览门
- [x] D1 状态矩阵自检：每个数据组件含 loading/empty/error/success
- [x] D2 可访问性：focus-visible、aria-label、reduced-motion、对比度
- [x] D3 `pnpm build` + `tsc` + `eslint` 通过
- [x] D4 启动 dev 运行验证，截图/说明 → **PREVIEW_CONFIRM_GATE 暂停等确认**

## E. 后端基础
- [x] E1 FastAPI 骨架 + CORS + 配置加载 + SQLite/SQLModel 初始化
- [x] E2 数据模型：collect_task/note/analysis/compose_result/setting
- [x] E3 Settings API：GET/PUT（LLM/采集配置，本地存储）
- [x] E4 路由对齐 `shared/api-routes`

## F. 采集服务
- [x] F1 BrowserManager(持久化上下文) + LoginService(二维码/状态)
- [x] F2 XhsClient：浏览器内签名发起搜索/详情，结构化解析
- [x] F3 RateLimiter + 重试 + Deduplicator
- [x] F4 任务编排：asyncio 队列 + 进度落库 + SSE `/tasks/{id}/events`
- [x] F5 mock 采集开关（无登录时返回样例数据，便于演示/测试）

## G. 分析与仿写
- [x] G1 分析：jieba 分词热词 + 标签聚类 + 互动综合分榜单
- [x] G2 LLM 客户端(OpenAI 兼容) + 连通性测试
- [x] G3 内容拆解 API：固定 schema 输出
- [x] G4 仿写 API：标题矩阵/正文/标签/配图，schema 校验

## H. 联调与质量
- [x] H1 前端切换 mock→真实 API，端到端走通采集/分析/仿写
- [x] H2 后端 pytest：分析规则、schema、限速、API 契约（mock XhsClient）
- [x] H3 全量 build/lint/tsc/test 通过
- [x] H4 交付清单：运行说明、环境变量、合规声明、已知限制
