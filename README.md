# RedScope · 小红书采集分析与仿写工作台

主题驱动的本地优先内容工具：输入一个主题，自动**采集**相关小红书笔记 →**分析**爆款规律（选题热词 / 榜单 / 内容拆解）→ 基于拆解结论**仿写**出同主题原创笔记。

> ⚠️ 本工具仅用于个人创作辅助与学习研究，须使用本人账号、低频限速、仅采集公开内容，仿写结果应原创化改写。请遵守小红书平台规则与相关法律法规，使用者自行承担使用后果。

---

## 功能特性

- **采集**：主题驱动异步任务，进度实时推送（SSE）、限速 / 重试 / 去重；默认 `mock` 模式可直接演示，`real` 模式基于 Playwright 持久化登录态。
- **笔记库**：列表 / 搜索 / 排序 + 详情抽屉，展示点赞 / 收藏 / 评论 / 分享。
- **分析**：jieba 选题热词、互动综合分爆款榜单、单篇内容拆解（规则 + LLM）。
- **仿写**：标题矩阵 + 正文（可编辑）+ 推荐话题标签 + 配图建议，支持导出 Markdown。
- **设置**：LLM（OpenAI 兼容，可切换厂商 / 本地模型）与采集参数本地落库。

> 未配置 LLM 时，分析拆解与仿写自动回退到内置启发式逻辑，保证可用。

## 技术栈

| 层 | 选型 |
|----|------|
| 前端 | React 18 + TypeScript + Vite + Tailwind CSS + TanStack Query + Zustand + Recharts + lucide-react |
| 后端 | Python 3.11+ + FastAPI + SQLModel + SQLite + Playwright + httpx + jieba |
| 通信 | REST + SSE（采集进度）|

## 目录结构

```
xiaohongshu/
├── frontend/                 # React + Vite 前端
│   └── src/
│       ├── pages/            # 6 个页面：Dashboard/Collect/Notes/Insights/Compose/Settings
│       ├── components/       # ui 基础组件 / layout 布局 / common 通用
│       ├── api/client.ts     # API 客户端（对接后端 REST）
│       ├── store/            # zustand 全局状态
│       └── lib/              # 类型与工具
├── backend/                  # FastAPI 后端
│   └── app/
│       ├── main.py           # 应用入口 + 路由注册
│       ├── api/              # 路由：collect/notes/analysis/compose/settings/auth/stats
│       ├── services/         # collector(采集) / tasks(编排) / analysis / compose / llm
│       ├── models.py         # SQLModel 数据模型
│       ├── schemas.py        # Pydantic 出入参
│       └── core/             # 配置与数据库
├── shared/api-routes.ts      # 前后端共享的 API 路径常量
├── output/                   # 研究 / PRD / 架构 / UIUX / 交付文档
├── docs/                     # 操作文档
└── .super-dev/changes/       # 变更提案与任务清单
```

## 快速开始

### 1. 后端

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --port 8000   # http://localhost:8000
```

### 2. 前端

```bash
cd frontend
npm install
npm run dev                         # http://localhost:5173（已代理 /api -> 8000）
```

打开 http://localhost:5173 ，阅读并同意免责声明后即可使用。

详细使用步骤见 [docs/USAGE.md](docs/USAGE.md)。

## 配置（后端环境变量，前缀 `REDSCOPE_`，均可选）

| 变量 | 默认 | 说明 |
|------|------|------|
| `REDSCOPE_DATABASE_URL` | `sqlite:///./redscope.db` | 数据库连接 |
| `REDSCOPE_COLLECT_MODE` | `mock` | `mock` 演示 / `real` 真实采集 |
| `REDSCOPE_CORS_ORIGINS` | `http://localhost:5173` | 允许的前端来源 |
| `REDSCOPE_LLM_BASE_URL` | `https://api.openai.com/v1` | LLM 接口（也可在「设置」页覆盖）|
| `REDSCOPE_LLM_API_KEY` | 空 | LLM Key（未配置走启发式回退）|
| `REDSCOPE_LLM_MODEL` | `gpt-4o-mini` | 模型名 |
| `REDSCOPE_USER_DATA_DIR` | `./.xhs-user-data` | real 模式 Playwright 登录态目录 |

> 启用 `real` 模式前需执行：`python -m playwright install chromium`。

## 测试与质量

```bash
# 后端
cd backend && source .venv/bin/activate && pytest

# 前端
cd frontend && npm run build && npm run lint
```

## 文档索引

- 需求与设计：`output/xhs-research.md`、`xhs-prd.md`、`xhs-architecture.md`、`xhs-uiux.md`
- 操作指南：`docs/USAGE.md`
- 交付清单：`output/xhs-delivery.md`

## 免责声明

见顶部声明。本项目不提供任何绕过平台风控的能力，默认低频限速，仅供个人合规使用。
