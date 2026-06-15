# 做T策略使用操作指引

本文说明如何使用当前 `t-alpha` 中的低吸型做T策略 v1。该功能仅用于量化研究、回测和交易提醒，不会自动下单，也不构成投资建议。

## 1. 功能边界

当前 v1 支持：

- 单只 A 股低吸型做T：先发买点提醒，再基于虚拟 T 仓监控卖点。
- 生成指定股票的 3 年回测报告和最近 3 个月交易明细。
- 根据报告准入结果开启或关闭监控。
- 买点触发后创建虚拟 T 仓；虚拟仓未关闭前不再为同一股票开新 T 仓。
- 卖点触发条件为达到 3% 目标价，或最长持有 10 个交易日超时退出。

当前 v1 不支持：

- 自动下单。
- 账户持仓、资金、底仓校验。
- 先卖后买回的高抛型做T。
- 多笔重叠 T 仓。
- 中途止损。

## 2. 环境准备

先配置 `.env`。可参考 `.env.example`：

```env
AD_USERNAME=your_amazingdata_username
AD_PASSWORD=your_amazingdata_password
AD_HOST=your_amazingdata_host
AD_PORT=8600

DB_HOST=your_mysql_host
DB_PORT=3306
DB_USERNAME=your_mysql_user
DB_PASSWORD=your_mysql_password
DB_NAME=t_alpha

SMTP_HOST=smtp.163.com
SMTP_PORT=465
SMTP_USERNAME=your_smtp_username
SMTP_PASSWORD=your_smtp_password
SMTP_FROM=alerts@example.com
ALERT_TO=you@example.com

T0_TARGET_RETURN=0.03
T0_MAX_HOLDING_TRADE_DAYS=10
T0_TRADE_COST_RATE=0.0001
T0_MIN_3Y_TRADES=60
T0_OBSERVE_MIN_3Y_TRADES=30
T0_MIN_SUCCESS_RATE=0.65
```

默认参数含义：

| 参数 | 默认值 | 含义 |
| --- | --- | --- |
| `T0_TARGET_RETURN` | `0.03` | 达到 3% 毛收益目标后触发卖点 |
| `T0_MAX_HOLDING_TRADE_DAYS` | `10` | 最长持仓 10 个交易日 |
| `T0_TRADE_COST_RATE` | `0.0001` | 回测和收益估算使用的简化成本率 |
| `T0_MIN_3Y_TRADES` | `60` | 进入监控候选的最低 3 年交易笔数 |
| `T0_OBSERVE_MIN_3Y_TRADES` | `30` | 观察策略最低 3 年交易笔数 |
| `T0_MIN_SUCCESS_RATE` | `0.65` | 3 年和验证集成功率准入门槛 |

## 3. 启动服务

在项目根目录执行：

```powershell
$env:PYTHONPATH="src"
py -3 -m uvicorn t_alpha.main:app --host 127.0.0.1 --port 8867
```

健康检查：

```powershell
Invoke-RestMethod http://127.0.0.1:8867/health
```

查看接口文档：

- Swagger UI: `http://127.0.0.1:8867/docs`
- OpenAPI JSON: `http://127.0.0.1:8867/openapi.json`

## 4. 生成做T策略报告

以中国平安 `601318.SH` 为例：

```powershell
$body = @{ code = "601318.SH" } | ConvertTo-Json
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8867/api/v1/strategy/t0/build" `
  -ContentType "application/json" `
  -Body $body
```

响应核心字段：

| 字段 | 说明 |
| --- | --- |
| `code` | 股票代码 |
| `strategy_name` | 策略名，当前为 `mean_reversion_t0_v1` |
| `params` | 本次报告使用的策略参数 |
| `full_metrics` | 3 年整体回测指标 |
| `train_metrics` | 训练区间指标 |
| `validation_metrics` | 验证区间指标 |
| `recent_metrics` | 最近 3 个月展示区间指标 |
| `recent_trades` | 最近 3 个月交易明细 |
| `eligibility` | 是否达到监控准入 |
| `disclaimer` | 风险提示 |

重点看 `eligibility`：

```json
{
  "eligible": true,
  "level": "eligible",
  "reasons": []
}
```

准入解释：

- `eligible=true`：可进入监控候选。
- `level=observe`：样本或指标不够，仅观察，不建议自动监控。
- `level=invalid`：样本明显不足或指标不合格。
- `reasons`：未通过原因，例如交易笔数不足、成功率低、平均收益不为正。

## 5. 开启监控

只有通过准入的策略才应开启监控：

```powershell
$body = @{ code = "601318.SH"; enabled = $true } | ConvertTo-Json
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8867/api/v1/strategy/t0/monitor" `
  -ContentType "application/json" `
  -Body $body
```

成功响应示例：

```json
{
  "code": "601318.SH",
  "enabled": true,
  "strategy_name": "mean_reversion_t0_v1",
  "reason": null
}
```

如果报告缺失或未通过准入，生产接入时应拒绝开启监控。当前 API 默认依赖未绑定数据库会话时，只能完成接口层调用；要让“报告持久化、准入读取、虚拟仓持久化、重启后继续监控”完整生效，需要在应用启动时为 `T0StrategyService` 注入数据库 session。

## 6. 监控运行逻辑

监控检查点：

- `10:00`
- `11:00`
- `13:00`
- `14:00`
- `15:00`

每次检查的处理顺序：

1. 判断当天是否交易日。
2. 判断当前时间是否监控检查点。
3. 对每个已启用的 T0 股票检查是否存在未关闭虚拟 T 仓。
4. 如果存在虚拟 T 仓，优先扫描卖点。
5. 如果不存在虚拟 T 仓，扫描新的买点。
6. 买点触发后发送买点邮件，并创建虚拟 T 仓。
7. 卖点触发后发送卖点邮件，并关闭虚拟 T 仓。

卖点优先级高于买点。也就是说，同一股票有未关闭虚拟 T 仓时，即使再次出现低吸信号，也不会开新仓。

## 7. 买点邮件如何理解

买点邮件会包含：

- 股票代码。
- 信号时间。
- 当前参考价。
- 建议买入区间。
- 建议买入金额。
- 建议买入股数，按 A 股 100 股整手向下取整。
- 目标卖出价。
- 最长持仓交易日数。
- 3 年样本数和成功率。
- 最近 3 个月样本数和成功率。
- 触发原因。

重要提示：

- 邮件只是提醒，不代表系统已经下单。
- v1 默认用户已有足够可卖底仓。
- 如果用户未按买点提醒实际买入，后续卖点邮件只代表策略跟踪信号。

## 8. 卖点邮件如何理解

卖点邮件触发原因有两类：

| 类型 | 含义 |
| --- | --- |
| `target` | 当前价格达到或超过目标卖出价 |
| `timeout` | 已达到最长持仓交易日数但未达目标价 |

卖点邮件会包含：

- 原买点信号时间。
- 买点提醒发送时间。
- 参考买入价。
- 建议买入股数。
- 目标卖出价。
- 当前价格和触发价格。
- 持仓交易日数。
- 毛收益率。
- 扣成本后收益率估算。
- 收益金额估算。
- 虚拟 T 仓状态，正常为 `closed`。

卖点邮件不代表真实账户已卖出。真实卖出动作需要用户自行确认。

## 9. 关闭监控

```powershell
$body = @{ code = "601318.SH"; enabled = $false } | ConvertTo-Json
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8867/api/v1/strategy/t0/monitor" `
  -ContentType "application/json" `
  -Body $body
```

关闭监控只影响后续扫描，不会代表真实账户平仓。

## 10. 推荐操作流程

日常使用建议按这个顺序：

1. 配置 AmazingData、数据库和邮件环境变量。
2. 启动 API 服务。
3. 调用 `/api/v1/strategy/t0/build` 生成股票策略报告。
4. 检查 `eligibility.eligible` 是否为 `true`。
5. 查看 `full_metrics`、`validation_metrics` 和 `recent_metrics`，确认样本量和近期表现。
6. 只有通过准入后，调用 `/api/v1/strategy/t0/monitor` 开启监控。
7. 监控任务在固定检查点运行，收到买点邮件后自行决定是否实际买入。
8. 收到卖点邮件后自行确认是否卖出等量底仓。
9. 若不再跟踪该股票，调用 monitor 接口关闭。

## 11. 常见问题

### 生成报告返回 404

通常表示行情源没有返回该股票在指定窗口的日线或 60 分钟线数据。检查：

- 股票代码是否正确，例如 `601318.SH`。
- AmazingData 账号是否有权限。
- 行情数据是否覆盖最近 3 年。

### 开启监控失败

常见原因：

- 还没有先生成报告。
- 报告未通过准入。
- 3 年有效交易笔数不足。
- 3 年成功率或验证集成功率不超过 65%。
- 扣成本后平均单笔收益不为正。

### 买点出现后为什么不再发新买点

同一股票有未关闭虚拟 T 仓时，系统只监控卖点，不再创建新的买点提醒。这是 v1 的非重叠仓位规则。

### 收到卖点提醒但我没有买入怎么办

忽略该卖点提醒即可。v1 不接入真实账户成交，卖点提醒只基于系统记录的虚拟 T 仓。

## 12. 风险提示

- 回测不代表未来表现。
- 当前成本模型是简化成本率，不包含完整印花税、滑点、最低佣金等真实交易成本。
- v1 不检查真实底仓和可用资金。
- v1 不自动下单，所有买卖动作都需要用户自行判断和执行。
- 单只股票样本量可能偏少，尤其要关注 `recent_metrics` 是否明显弱化。
