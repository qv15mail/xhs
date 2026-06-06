# 交付清单 — RedScope v1

> 阶段：delivery ｜ 变更：001-redscope-v1 ｜ 工作模式：new

## 1. 已交付能力

| 模块 | 状态 | 说明 |
|------|------|------|
| 采集 | ✅ | 主题驱动（搜索页优先+推荐页补充），携带 xsec_token 访问详情页，从 `__INITIAL_STATE__` 解析真实数据；mock 模式可演示 |
| 登录 | ✅ | 正式小红书扫码登录：前端弹窗展示官方二维码，后端轮询 `web_session` cookie 判定并落库；支持退出登录 |
| 笔记库 | ✅ | 默认按采集时间倒序，支持按采集任务分组显示；搜索/排序/详情抽屉；「原文」链接带 xsec_token 可直接打开 |
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
- 端到端：浏览器实测——正式扫码登录落库 → real 模式采集（多主题 5/5 真实笔记，真实标题/作者/互动数 10w 级）→ 笔记库按采集时间倒序+按任务分组 → 分析（jieba 热词干净，无「话题」污染）→ 单篇拆解 → 仿写，全链路通畅，控制台无 error。

## 5. 已知限制 / 后续

1. **已采集的旧笔记 url 不含 xsec_token**：需重新采集才会带上直链；token 有时效，过期后需重新采集刷新。
2. **任务编排为单机内存队列**：v1 单用户本地场景足够；多用户/重负载需引入持久化队列（Celery/Redis）。
3. **前端 bundle 偏大**：可后续按路由 code-split 优化。
4. **登录与采集共用 user_data_dir**：同一时刻只能执行一项（由 `browser_lock` 保障），并发登录/采集需排队。

## 6. 合规声明

本工具仅用于个人创作辅助与学习研究，须使用本人账号、低频限速，仅采集公开内容，仿写结果应原创化改写；使用者需遵守小红书平台规则与法律法规，自行承担使用后果。

## 7. 关键文件索引

- 文档：`output/xhs-research.md`、`xhs-prd.md`、`xhs-architecture.md`、`xhs-uiux.md`
- Spec：`.super-dev/changes/001-redscope-v1/{proposal,tasks}.md`
- 后端：`backend/app/{main.py, api/*, services/*, models.py, schemas.py, core/*}`
- 前端：`frontend/src/{pages/*, components/*, api/client.ts, lib/*, store/*}`
- 共享：`shared/api-routes.ts`
