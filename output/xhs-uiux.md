# UI/UX 文档 — RedScope

> 阶段：docs ｜ 依据：PRD + 架构 ｜ 状态：待用户确认
> 本文件是前端实现的强约束；实现阶段不得临时切换图标库 / token / 组件体系。

## 1. 设计定位与反 AI 感声明

- 产品是**数据驱动的创作工作台**，不是对话式 AI。
- **明确避免**：Claude/ChatGPT 式侧栏聊天壳层、窄中栏对话布局、紫/粉渐变主视觉、emoji 充当功能图标、默认系统字体直出。
- 视觉气质：**清爽、专业、信息密度高的工作台**，借鉴数据分析平台（千瓜/灰豚）的看板感，但更克制现代。
- 布局范式：**左侧固定导航 + 顶部操作栏 + 主内容区**（看板/列表/详情抽屉），非聊天流。

## 2. 设计 Token

### 颜色（语义化，浅色为主，预留暗色）
```
--bg:        #F7F8FA   背景
--surface:   #FFFFFF   卡片
--border:    #E8EAED   描边
--text:      #1A1D21   主文本
--text-mut:  #6B7280   次文本
--primary:   #E23744   品牌主色(克制的小红书红，用于强调/主按钮)
--primary-fg:#FFFFFF
--accent:    #2563EB   数据/链接强调(蓝)
--success:   #16A34A   --warning:#D97706   --danger:#DC2626
```
> 红色仅用于品牌强调与主行动，**不做大面积红底**；数据图表以蓝/中性为主，避免红绿色盲冲突。

### 字体
- 中文：`"PingFang SC", "Microsoft YaHei", "Source Han Sans"`；英文/数字：`Inter`。
- 字号阶梯：12 / 14 / 16 / 20 / 24 / 32；数字看板用 tabular-nums。

### 间距 / 圆角 / 阴影
- 间距 token：4 / 8 / 12 / 16 / 24 / 32。
- 圆角：sm 6 / md 10 / lg 14。
- 阴影：卡片用轻阴影 `0 1px 2px rgba(0,0,0,.06)`，悬浮态加重一档。

### 图标
- **唯一图标库：lucide-react**。常用：LayoutDashboard、Radar、FileText、BarChart3、PenLine、Settings、QrCode、ScanLine、LogOut、Loader2、Play、RefreshCw、Download、Copy、Filter、TrendingUp、ExternalLink。

## 3. 栅格与响应式

- 桌面优先，主内容 12 栅格，max-width 1440，内容区 padding 24。
- 断点：`<768` 移动（导航收起为底部/抽屉）、`768–1280` 平板、`>1280` 桌面。
- 看板卡片：桌面 4 列 → 平板 2 列 → 移动 1 列。

## 4. 全局框架

- **左侧导航 (240px)**：Logo + 6 个入口（Dashboard/Collect/Notes/Insights/Compose/Settings），当前项高亮（左侧 3px primary 条 + 浅底）。
- **顶部栏**：当前主题/任务上下文、登录态徽标（在线绿点/未登录灰点，未登录时可点击触发扫码登录）、「扫码登录 / 退出登录」按钮、全局新建采集按钮。
- 移动端：左侧导航转为顶部汉堡抽屉。

## 5. 关键页面与状态

### 5.1 Dashboard
- 顶部 4 个 Metric 卡：累计笔记数、采集任务数、平均互动、最近任务状态。
- 采集趋势折线图 + 最近任务列表（状态徽标）。
- 空态：引导「新建第一个采集任务」。

### 5.2 Collect（采集）
- 新建任务表单：主题输入、数量滑块、排序下拉、含评论开关、限速档位（保守/标准）。
- 提交后任务卡片：进度条（已采/目标）、实时状态（SSE）、错误提示、重跑。
- 登录态卡：未登录点「扫码登录」唤起**扫码登录弹窗（LoginDialog）**；已登录显示账号在线 + 退出登录。
- **LoginDialog（扫码登录弹窗）**：展示平台官方二维码，状态机 `loading / waiting / success / expired / error`，过期或失败提供「刷新二维码」；后台轮询登录态，成功后自动关闭。

### 5.3 Notes（笔记库）
- 工具栏：搜索；排序下拉（**默认「按采集时间」倒序**，可选互动量/发布时间）；分组下拉（**「不分组 / 按采集任务分组」**）。
- 笔记卡片网格：封面、标题、作者、互动数据（点赞/收藏/评论 带图标）。
- 分组视图：按采集任务分区，分组头展示任务主题、笔记数徽标与采集日期，分组按任务采集时间倒序。
- 点击 → 右侧**详情抽屉**：完整正文、图片、数据、「原文」（带 token，登录态浏览器直接打开）、「拿去拆解/仿写」按钮。

### 5.4 Insights（分析）
- Tab：选题热词 / 爆款榜单 / 内容拆解。
- 选题热词：词云 + 词频表。
- 爆款榜单：排序表，行内「为什么爆」标签徽标（如「数字标题」「痛点开头」）。
- 内容拆解：选中笔记 → 卡片化展示标题公式/钩子/骨架/标签策略（LLM，带 loading 骨架屏）。

### 5.5 Compose（仿写）
- 左：参考来源（选笔记/选模板）+ 新主题/卖点输入 + 风格/长度参数。
- 右：生成结果——标题矩阵（候选可一键复制）、正文（可编辑）、推荐标签、配图建议。
- 操作：生成、重写、局部再生成、复制、导出 Markdown。
- 生成中：流式/骨架屏 + 取消按钮。

### 5.6 Settings
- 分组卡片：LLM（base_url/key/model/温度，含连通性测试）、采集（默认数量/限速/并发/含评论）、账号与数据（清除登录、清空数据）。

## 6. 组件状态矩阵（强制覆盖）

每个数据组件必须实现：`loading（骨架屏）/ empty（插画+引导）/ error（重试）/ success`。
表单：`default / focus（可见焦点环 2px accent）/ disabled / error（红字+描述）`。
按钮：`default / hover / active / loading / disabled`。

## 7. 可访问性与动效

- 所有可交互元素有可见 `focus-visible` 焦点环；对比度 ≥ WCAG AA。
- 图标按钮配 `aria-label`；表格/图表提供文本替代。
- 动效克制（150–250ms ease-out）；尊重 `prefers-reduced-motion`，关闭非必要动画。

## 8. 文案与免责

- 首次进入弹出**风险与免责声明**，需勾选确认；底部常驻「仅供个人创作研究，请遵守平台规则」。

## 9. 组件清单（实现参照）

`AppShell / SideNav / TopBar / LoginDialog / MetricCard / TrendChart / TaskCard / ProgressBar / LoginQRCard / NoteCard / NoteDrawer / FilterBar / WordCloud / RankingTable / BreakdownCard / ComposePanel / TitleMatrix / SettingsGroup / EmptyState / ErrorState / Skeleton / DisclaimerDialog`。
