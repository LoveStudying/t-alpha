# t-alpha 接口对接文档

生成日期：2026-06-12

## 1. 基本信息

- 服务类型：HTTP JSON API
- 默认本地地址：`http://127.0.0.1:8867`
- API 前缀：`/api/v1`
- 鉴权：当前版本未启用接口鉴权，建议部署到内网或网关后再开放给其他项目。
- 风险声明：行情、回测和提醒结果仅供研究参考，不构成投资建议。

启动命令：

```powershell
uvicorn t_alpha.main:app --host 127.0.0.1 --port 8867
```

OpenAPI 文档：

- Swagger UI：`GET /docs`
- OpenAPI JSON：`GET /openapi.json`

## 2. 通用约定

### 2.1 日期

所有日期参数使用 `YYYYMMDD` 字符串，例如 `20240131`。可选参数如果传空字符串，按未传处理。

日期归一化规则：

- `start_date` 和 `end_date` 都不传：默认最近 10 个交易日。
- 只传 `end_date`：从 `end_date` 向前取最近 10 个交易日。
- 只传 `start_date`：`end_date` 使用最近一个交易日。
- 日期不是交易日时，按交易日历向前取最近交易日，并在响应 `normalized_dates` 中返回归一化结果。

### 2.2 周期与复权

`period` 支持：

| 值 | 说明 |
| --- | --- |
| `day` | 日线，默认值 |
| `60m` | 60 分钟线 |

`adjust` 支持：

| 值 | 说明 |
| --- | --- |
| `none` | 原始价格，默认值 |
| `forward` | 前复权价格；当前仅 A 股价格接口执行前复权 |

### 2.3 通用错误

| HTTP 状态码 | 场景 | 处理建议 |
| --- | --- | --- |
| 400 | 日期区间无效、交易日历无法归一化 | 检查 `start_date`、`end_date` |
| 404 | 数据源未返回该代码该区间数据 | 检查代码和日期范围 |
| 422 | 参数枚举或格式校验失败 | 检查 `period`、`adjust`、必填参数 |
| 500 | 数据源、服务或运行环境异常 | 查看服务日志 |

## 3. 健康检查

### `GET /health`

用于服务存活检查。

响应示例：

```json
{
  "status": "ok"
}
```

## 4. A 股价格查询

### `GET /api/v1/market/stock/prices`

查询 A 股 K 线价格。

请求参数：

| 参数 | 类型 | 必填 | 默认 | 说明 |
| --- | --- | --- | --- | --- |
| `code` | string | 是 | 无 | A 股代码，例如 `601318.SH` |
| `start_date` | string | 否 | 最近 10 个交易日开始日 | `YYYYMMDD` |
| `end_date` | string | 否 | 最近交易日 | `YYYYMMDD` |
| `period` | string | 否 | `day` | `day` 或 `60m` |
| `adjust` | string | 否 | `none` | `none` 或 `forward` |

可选参数如果传空字符串，按默认值处理；`code` 为必填参数，不能省略或传空字符串。

请求示例：

```http
GET /api/v1/market/stock/prices?code=601318.SH&start_date=20240101&end_date=20240131&adjust=forward
```

响应示例：

```json
{
  "code": "601318.SH",
  "asset_type": "stock",
  "period": "day",
  "adjust": "forward",
  "requested_dates": {
    "start_date": "20240101",
    "end_date": "20240131"
  },
  "normalized_dates": {
    "start_date": "20240102",
    "end_date": "20240131"
  },
  "rows": [
    {
      "date": "20240102",
      "open": 10.12,
      "high": 10.3,
      "low": 10.01,
      "close": 10.2,
      "volume": 1234567.0,
      "amount": 12345678.9
    }
  ],
  "disclaimer": "仅供研究参考，不构成投资建议。"
}
```

## 5. ETF 价格查询

### `GET /api/v1/market/etf/prices`

查询 ETF K 线价格。

请求参数同 A 股价格查询。

请求示例：

```http
GET /api/v1/market/etf/prices?code=510300.SH&start_date=20240101&end_date=20240131
```

响应字段与 A 股价格查询一致，其中 `asset_type` 为 `etf`。

## 6. 场内基金价格查询

### `GET /api/v1/market/fund/prices`

查询场内基金/ETF K 线行情。

请求参数同 A 股价格查询。

请求示例：

```http
GET /api/v1/market/fund/prices?code=510300.SH&period=day
```

响应字段与 A 股价格查询一致，其中 `asset_type` 为 `fund`。

## 7. 场外开放式基金净值查询

### `GET /api/v1/market/fund/nav`

查询场外开放式基金净值。

请求参数：

| 参数 | 类型 | 必填 | 默认 | 说明 |
| --- | --- | --- | --- | --- |
| `code` | string | 是 | 无 | 基金代码，例如 `000001.OF` |
| `start_date` | string | 否 | 最近 10 个交易日开始日 | `YYYYMMDD` |
| `end_date` | string | 否 | 最近交易日 | `YYYYMMDD` |

可选参数如果传空字符串，按未传处理；`code` 为必填参数，不能省略或传空字符串。

请求示例：

```http
GET /api/v1/market/fund/nav?code=000001.OF&start_date=20240101&end_date=20240131
```

响应示例：

```json
{
  "code": "000001.OF",
  "requested_dates": {
    "start_date": "20240101",
    "end_date": "20240131"
  },
  "normalized_dates": {
    "start_date": "20240102",
    "end_date": "20240131"
  },
  "rows": [
    {
      "price_date": "20240102",
      "unit_nav": 1.2345,
      "accum_nav": 2.3456,
      "adj_unit_nav": 1.4567,
      "inner_code": "",
      "outer_code": "000001"
    }
  ],
  "disclaimer": "仅供研究参考，不构成投资建议。"
}
```

## 8. 默认监控标的

### `GET /api/v1/strategy/default-watchlist`

返回系统默认监控标的，供其他项目初始化或检查策略配置。

响应示例：

```json
{
  "code": "601318.SH",
  "name": "中国平安",
  "strategy_name": "mean_reversion_t0_v1",
  "enabled": true
}
```

## 9. 对接建议

1. 调用方应读取 `normalized_dates`，不要假设请求日期就是实际查询日期。
2. 调用方应展示或传递 `disclaimer` 字段。
3. 行情接口返回空数据时会使用 404，调用方可提示用户检查代码、日期和数据权限。
4. 生产部署前建议在 API 网关层增加鉴权、限流和访问日志。
5. 若需要稳定契约，建议以 `/openapi.json` 生成客户端 SDK，并锁定服务版本。
