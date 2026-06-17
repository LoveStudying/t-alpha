# t-alpha Vue3 管理后台设计

日期：2026-06-18

## 目标

为 `t-alpha` 增加一个本地使用版 Vue3 管理后台，把当前需要手写 HTTP 请求、查看 JSON、直接理解数据库记录的日常操作，整理成可视化页面。

后台第一版服务于单人本地/内网使用：

- 独立 `web-admin/` Vue3/Vite/TypeScript 前端。
- FastAPI 增加最小管理 API。
- 简易单用户登录，不做注册、角色、权限矩阵和公网安全增强。
- 页面覆盖行情查询、T0 报告生成、监控维护、报告记录、虚拟 T 仓、提醒记录、系统设置概览和远期系统规划。
- 风险提示在策略、行情、提醒相关页面持续可见，明确系统不自动下单、不构成投资建议。

## 非目标

- 不接入真实交易账户，不自动下单。
- 不实现多用户、角色权限、组织管理。
- 不做公网部署安全套件，例如 HTTPS 证书、限流、审计报表、登录失败锁定。
- 不把第一版做成完整运维平台；邮件测试、手动跑调度、日志查询可作为后续增强。
- 不替换已有 FastAPI 公开接口和策略核心逻辑。

## 产品定位与视觉方向

后台采用“清爽维护工作台”方向：浅色、清新、高级、低噪音，重点是让日常维护操作稳定、直观、可重复。

视觉原则：

- 主界面使用浅色基底、低饱和蓝绿金融色、少量琥珀色表达观察或警告状态。
- 信息密度高但不拥挤，表格、筛选栏、详情抽屉承担主要工作流。
- 使用清晰的状态标签、开关、确认弹窗和 toast 反馈，避免让用户从原始 JSON 中判断结果。
- 使用 Element Plus 线性图标，导航项同时展示图标和文字。
- 使用 4/8px 间距系统、稳定表格列宽、数字等宽显示。
- 卡片只用于指标摘要、单条记录和需要框定的操作区，不做大面积装饰性卡片堆叠。

交互原则：

- 所有异步动作有 loading、成功和失败反馈。
- 修改监控状态、关闭/打开关键记录前需要确认。
- API 错误显示原因和下一步，例如检查股票代码、日期、报告准入状态或服务配置。
- 页面切换保留常用筛选状态，提升日常重复使用效率。

## 信息架构

一级导航：

1. 工作台
2. 行情查询
3. T0 策略
4. 监控维护
5. 数据记录
6. 系统
7. 远期规划

页面设计：

### 登录页

功能：

- 用户名、密码登录。
- 登录成功后保存 token/session 到前端状态。
- 已登录时直接进入工作台。
- 登录失败显示明确错误。

配置：

- 后端从 `.env` 读取 `ADMIN_USERNAME`、`ADMIN_PASSWORD`、`ADMIN_TOKEN_SECRET`。
- 若未配置，开发环境使用保守默认值并在系统设置概览显示“请配置后台账号”提示；生产或非 dev 环境应要求显式配置。

### 工作台

功能：

- 展示服务健康状态、API 地址、当前环境、数据库配置摘要、监控标的数量、启用监控数量、未关闭虚拟 T 仓数量、最近提醒数量。
- 快捷入口：查询行情、生成 T0 报告、添加监控标的、查看提醒记录。
- 最近记录：最新 T0 报告、最新提醒、当前打开的虚拟 T 仓。

依赖：

- `GET /api/v1/admin/overview`
- `GET /health`

### 行情查询

功能：

- 用表单封装现有行情接口。
- 支持资产类型：A 股、ETF、场内基金、场外基金净值。
- 支持代码、开始日期、结束日期、周期、复权方式。
- 查询结果展示为折线图和数据表。
- 显示 `requested_dates` 与 `normalized_dates`，避免误解交易日归一化。
- 支持复制请求 URL 和导出当前表格 CSV。

复用公开接口：

- `GET /api/v1/market/stock/prices`
- `GET /api/v1/market/etf/prices`
- `GET /api/v1/market/fund/prices`
- `GET /api/v1/market/fund/nav`

### T0 策略

功能：

- 输入股票代码，调用现有报告生成接口。
- 显示准入状态、未通过原因、3 年整体指标、训练集指标、验证集指标、最近 3 个月指标。
- 展示最近交易明细表。
- 只有报告 eligible 时才显示“开启监控”的主操作；否则提供“仅观察”状态说明。
- 成功生成报告后可跳转到报告详情或监控维护。

复用公开接口：

- `POST /api/v1/strategy/t0/build`
- `POST /api/v1/strategy/t0/monitor`

### 监控维护

功能：

- 展示 watchlist 列表：代码、名称、策略名、启用状态、最近报告准入、备注、更新时间。
- 支持新增、编辑、启用/停用、删除 watchlist 项。
- 启用监控时要求存在 eligible 报告；若没有报告或未通过准入，提示先生成报告。
- 支持从列表直接生成报告。

新增管理接口：

- `GET /api/v1/admin/watchlist`
- `POST /api/v1/admin/watchlist`
- `PATCH /api/v1/admin/watchlist/{id}`
- `DELETE /api/v1/admin/watchlist/{id}`

### 数据记录

数据记录分为三个标签页：

1. 报告记录
   - 读取 `t0_strategy_reports`。
   - 展示代码、策略名、eligible、level、生成时间、更新时间。
   - 支持查看完整报告 JSON 的结构化详情。

2. 虚拟 T 仓
   - 读取 `t0_positions`。
   - 展示代码、策略名、状态、打开时间、关闭时间、收益相关 payload 摘要。
   - 支持查看原始 payload。

3. 提醒记录
   - 读取 `alert_records`。
   - 展示代码、信号时间、信号类型、发送状态、错误信息、创建时间。
   - 支持查看 payload。

新增管理接口：

- `GET /api/v1/admin/t0/reports`
- `GET /api/v1/admin/t0/reports/{id}`
- `GET /api/v1/admin/t0/positions`
- `GET /api/v1/admin/t0/positions/{id}`
- `GET /api/v1/admin/alerts`
- `GET /api/v1/admin/alerts/{id}`

### 系统设置概览

功能：

- 展示安全脱敏后的配置摘要：AmazingData 主机、数据库主机和库名、SMTP 是否配置、APP 环境、T0 参数。
- 不显示任何密码、token、授权码。
- 展示管理后台账号配置状态。
- 展示当前 API 文档地址。

新增管理接口：

- `GET /api/v1/admin/settings/summary`

### 远期规划

功能：

- 静态页面，介绍系统未来方向。
- 内容聚焦：多策略、更多数据源、实时快照、风险过滤、任务编排、报告中心、真实账户只读校验、权限系统、部署安全。
- 明确“自动交易”不是近期默认方向，未来如接入也需要单独风控和确认机制。

实现：

- 前端静态页面，不依赖后端。

## 后端设计

### 鉴权

新增 `src/t_alpha/api/routes_auth.py`：

- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/logout`

第一版 token 方案：

- 使用标准库 `secrets`、`hmac`、`hashlib`、`base64`、`time` 实现签名 token，避免新增 Python 依赖。
- token payload 包含用户名、签发时间、过期时间。
- 默认过期时间 8 小时，可通过 `ADMIN_SESSION_TTL_SECONDS` 配置。
- 前端以 `Authorization: Bearer <token>` 调用管理接口。
- 登出由前端清除 token；后端 `logout` 返回成功，不维护服务端黑名单。

新增依赖：

- `get_current_admin_user` 作为管理接口依赖。
- 公开行情和策略接口保持不强制鉴权，避免破坏已有对接。
- 新增 `/api/v1/admin/**` 全部要求鉴权。

### 管理数据访问

新增 `src/t_alpha/api/routes_admin.py` 和必要 schema。

后端只封装已有模型，不改核心策略算法：

- `Watchlist`
- `T0StrategyReportRow`
- `T0Position`
- `AlertRecord`

分页：

- 列表接口支持 `limit`、`offset`。
- 默认 `limit=50`，最大 `limit=200`。

排序：

- 第一版固定按最近更新时间或创建时间倒序。

JSON 字段：

- 后端把 `params_json`、`report_json`、`payload_json` 尽量解析为对象返回。
- 解析失败时返回原始字符串和 `parse_error`，页面显示“JSON 解析失败”但不阻断列表。

数据库会话：

- 当前 `get_strategy_service()` 未注入数据库 session，导致持久化能力不完整。
- 第一版需要在 `deps.py` 增加 `get_db_session`，并让管理接口与策略服务可使用数据库 session。
- 为避免启动时强制连接远程 MySQL，数据库相关管理接口在连接失败时返回明确错误，工作台显示“数据库不可用”状态。

### 前端静态托管

开发阶段：

- 前端运行在 Vite dev server。
- 通过 `VITE_API_BASE_URL=http://127.0.0.1:8867` 调用 API。

本地使用阶段：

- 可选让 FastAPI 托管 `web-admin/dist`。
- 若 `web-admin/dist/index.html` 存在，FastAPI 挂载静态资源并对前端路由返回 index。
- 该托管能力不影响 API-only 使用。

## 前端设计

目录：

```text
web-admin/
  package.json
  index.html
  vite.config.ts
  tsconfig.json
  src/
    main.ts
    App.vue
    router/
    services/
    stores/
    layouts/
    components/
    views/
    styles/
```

建议依赖：

- Vue 3
- Vite
- TypeScript
- Vue Router
- Pinia
- Axios
- Element Plus
- @element-plus/icons-vue
- ECharts

选择 Element Plus 的原因：

- 适合管理后台，表单、表格、抽屉、弹窗、分页成熟。
- 中文生态友好。
- 能快速实现高质量日常维护界面。
- 与 Vue3/Vite 集成简单。

状态管理：

- `authStore`：token、用户信息、登录/登出。
- `appStore`：全局 loading、API base URL、系统状态缓存。

API 客户端：

- `src/services/http.ts` 创建 Axios 实例。
- 自动附加 Bearer token。
- 401 自动跳转登录。
- 标准化错误 toast。

布局：

- 桌面端：左侧 sidebar + 顶部工具条 + 主内容区。
- 小屏：sidebar 收起为抽屉菜单。
- 主内容区宽度自适应，不使用营销式 hero。

组件：

- `MetricTile`：指标摘要。
- `StatusBadge`：eligible、observe、invalid、sent、failed、open、closed 等状态。
- `DataTableToolbar`：搜索、刷新、导出。
- `JsonDrawer`：结构化 JSON 详情。
- `RiskDisclaimer`：风险提示。
- `ConfirmAction`：关键操作确认。

## 数据流

登录：

```text
LoginView -> POST /api/v1/auth/login -> token -> authStore -> router guard -> AdminLayout
```

行情查询：

```text
MarketQueryView -> form -> public market API -> chart/table -> normalized date notice
```

T0 报告：

```text
T0StrategyView -> POST /strategy/t0/build -> metrics/recent trades -> optional monitor enable
```

监控维护：

```text
WatchlistView -> admin watchlist API -> edit/toggle -> optional POST /strategy/t0/monitor
```

数据记录：

```text
RecordsView -> admin list API -> table -> detail drawer -> parsed JSON
```

## 错误处理

前端：

- 401：清除 token 并跳转登录。
- 400/422：显示接口返回 detail，定位到表单字段或操作按钮附近。
- 404：行情和报告页面提示检查代码、日期、数据权限。
- 500：提示服务异常并保留“复制错误信息”入口。
- 数据库不可用：工作台与记录页显示空状态和恢复建议。

后端：

- 管理接口不吞掉数据库异常，转换为清晰 HTTPException。
- 敏感配置永不返回。
- JSON 解析失败不影响列表返回。
- 删除 watchlist 使用确认弹窗，后端执行真实删除；第一版不做软删除。

## 测试计划

后端测试：

- 登录成功、登录失败、token 过期、无 token 访问管理接口返回 401。
- settings summary 不泄露密码字段。
- watchlist CRUD 使用 SQLite 内存库验证。
- T0 reports、positions、alerts 列表和详情接口可解析 JSON。
- 公开市场和策略接口行为不被鉴权改动破坏。

前端验证：

- TypeScript 编译通过。
- Vite build 通过。
- 登录页、路由守卫、主要页面空状态和错误状态可运行。
- 行情查询、T0 报告、监控切换至少使用 mock 或当前 API 形状验证。

人工验证：

- 启动 FastAPI 后访问 `/docs` 仍可用。
- 启动前端 dev server 后可登录并进入工作台。
- 使用默认 `601318.SH` 可触发 T0 报告生成流程；若本地 AmazingData 不可用，页面显示可恢复错误而不是崩溃。

## 实施顺序

1. 后端鉴权与管理 API schema。
2. 数据库 session 依赖和管理接口。
3. 后端测试。
4. Vue3/Vite 项目初始化和设计系统样式。
5. 登录、布局、路由、API 客户端。
6. 工作台、行情查询、T0 策略。
7. 监控维护、数据记录、系统概览、远期规划。
8. 前端构建验证与本地运行说明。
9. 可选 FastAPI 静态托管前端 build。

## 已确认决策

- 第一版范围选择“日常维护版”。
- 登录采用本地单用户系统，默认用户拥有全部权限。
- 部署边界是本地/内网使用，不按公网暴露标准扩展。
- 视觉方向是“清爽维护工作台”，整体要有清新高级感。
- 推荐架构是独立 Vue3 管理端 + 最小 FastAPI 管理 API。

## 待实现时采用的默认假设

- 前端目录名为 `web-admin/`。
- 默认 API 地址为 `http://127.0.0.1:8867`。
- 前端开发端口使用 Vite 默认或自动分配端口。
- 管理接口路径统一为 `/api/v1/admin/**`。
- 登录接口路径为 `/api/v1/auth/**`。
- 第一版使用 Element Plus 和 ECharts。
- 如果本地 Node 环境不可用，后端仍可独立运行，前端构建验证延后到安装 Node 后执行。
