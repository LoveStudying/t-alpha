# t-alpha 管理后台使用说明

本文说明如何在本地使用 Vue3 管理后台。后台用于简化行情查询、T0 报告生成、监控维护、记录查看和系统规划阅读。

## 1. 后端配置

在项目根目录 `.env` 中配置后台单用户账号：

```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-local-password
ADMIN_TOKEN_SECRET=change-this-local-secret
ADMIN_SESSION_TTL_SECONDS=28800
```

说明：

- 第一版只有一个后台用户，默认拥有全部权限。
- 后台按本地/内网使用设计，不包含公网访问所需的完整安全套件。
- 不要把 `.env` 提交到 Git。

## 2. 启动 FastAPI

```powershell
$env:PYTHONPATH="src"
python -m uvicorn t_alpha.main:app --host 127.0.0.1 --port 8867
```

常用地址：

- 健康检查：`http://127.0.0.1:8867/health`
- Swagger：`http://127.0.0.1:8867/docs`
- 登录接口：`POST http://127.0.0.1:8867/api/v1/auth/login`
- 管理接口：`/api/v1/admin/**`

## 3. 前端开发模式

首次安装依赖：

```powershell
cd web-admin
npm install
```

启动开发服务器：

```powershell
npm run dev
```

默认前端地址通常为：

```text
http://127.0.0.1:5173
```

如果后端地址不是 `http://127.0.0.1:8867`，可以在 `web-admin/.env.local` 中配置：

```env
VITE_API_BASE_URL=http://127.0.0.1:9000
```

## 4. 构建与本地托管

构建前端：

```powershell
cd web-admin
npm run build
```

构建成功后会生成 `web-admin/dist`。FastAPI 启动时如果检测到该目录，会自动托管后台页面：

```text
http://127.0.0.1:8867/
```

API、Swagger 和健康检查不会被前端路由覆盖。

## 5. 页面范围

当前后台包含：

- 登录页：单用户登录。
- 工作台：服务状态、监控规模、快捷入口。
- 行情查询：封装股票、ETF、基金价格和净值接口。
- T0 策略：生成报告、查看准入和近期交易。
- 监控维护：维护 watchlist 并控制监控启停。
- 数据记录：查看报告、虚拟 T 仓和提醒记录。
- 系统：查看脱敏配置摘要和 T0 参数。
- 远期规划：查看未来系统方向。

## 6. 风险提示

后台展示的行情、回测和提醒结果仅用于研究参考，不构成投资建议。系统不会自动下单，也不会校验真实账户持仓和资金，所有交易动作都需要用户自行判断和执行。
