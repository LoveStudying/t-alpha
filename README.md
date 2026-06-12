# t-alpha

`t-alpha` 是一个基于 FastAPI 的量化研究辅助项目，主要提供 AmazingData 行情数据接口、技术指标计算、T+0 策略信号、回测、定时任务和邮件提醒能力。

当前项目默认本地服务端口是 `8867`，启动后访问地址通常是：

- 健康检查：`http://127.0.0.1:8867/health`
- Swagger 接口文档：`http://127.0.0.1:8867/docs`
- OpenAPI JSON：`http://127.0.0.1:8867/openapi.json`

## 目录结构说明

```text
t-alpha/
├─ src/t_alpha/              项目主代码目录
│  ├─ api/                   FastAPI 路由、接口依赖和请求/响应模型
│  ├─ backtest/              回测引擎和回测指标统计
│  ├─ data/                  AmazingData 客户端封装、行情数据清洗、交易日处理、复权处理
│  ├─ indicators/            技术指标计算，例如 MA、RSI、KDJ、BOLL、ATR
│  ├─ notification/          邮件提醒内容生成和 SMTP 发送逻辑
│  ├─ scheduler/             定时任务相关逻辑，例如盘中提醒检查时间
│  ├─ storage/               数据库连接、SQLAlchemy 模型和仓储操作
│  ├─ strategy/              T+0 策略、风控过滤和交易信号结构
│  ├─ config.py              项目配置读取入口
│  ├─ constants.py           项目常量
│  ├─ cli.py                 安装包后的命令行启动入口
│  └─ main.py                FastAPI 应用入口
├─ tests/                    自动化测试
├─ docs/                     项目设计、接口对接等补充文档
├─ .env.example              环境变量配置模板
├─ pyproject.toml            Python 包信息、依赖、测试配置和命令行入口
└─ README.md                 项目说明文档
```

## 配置文件位置

项目配置由 `src/t_alpha/config.py` 中的 `Settings` 类统一读取，实际运行时会优先读取项目根目录下的 `.env` 文件。

第一次使用时，请复制模板文件：

```powershell
Copy-Item .env.example .env
```

然后打开 `.env`，填写自己的配置。常用配置如下：

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

APP_ENV=dev
APP_HOST=127.0.0.1
APP_PORT=8867
LOG_LEVEL=INFO
```

说明：

- `APP_PORT=8867` 是本项目 FastAPI 服务的本地启动端口。
- `APP_HOST=127.0.0.1` 表示只允许本机访问；如果需要局域网其他机器访问，可改为 `0.0.0.0`。
- `AD_PORT=8600` 是连接 AmazingData 数据源的端口，不是本项目 Web 服务端口。
- `.env` 中通常包含账号、密码等敏感信息，不要提交到 Git。

## 环境准备

项目要求 Python `3.11` 或更高版本。可以先检查版本：

```powershell
python --version
```

如果输出的版本低于 `3.11`，建议先安装新版 Python。

建议在项目根目录创建虚拟环境，避免影响电脑上的其他 Python 项目：

```powershell
python -m venv .venv
```

激活虚拟环境：

```powershell
.\.venv\Scripts\Activate.ps1
```

如果 PowerShell 提示脚本执行策略不允许，可以临时执行：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 安装依赖

开发时推荐使用“可编辑安装”，这样你修改 `src/` 里的代码后，不需要重新安装包：

```powershell
python -m pip install -e ".[dev]"
```

AmazingData SDK 不是公开 PyPI 包，首次配置或重建 `.venv` 后还需要安装 `tgw` 和 `AmazingData` wheel。具体步骤见 `docs/amazingdata_sdk_install.md`。

其中：

- `-e` 表示 editable，可编辑安装。
- `.[dev]` 表示安装项目运行依赖，同时安装测试需要的开发依赖。

如果只想安装运行依赖，不安装测试工具，可以执行：

```powershell
python -m pip install -e .
```

## 启动项目

启动前请确认：

1. 已经在项目根目录创建并填写 `.env`。
2. 已经安装依赖。
3. 当前终端已经激活虚拟环境。

### 方式一：使用 uvicorn 启动

这是最直接的启动方式：

```powershell
uvicorn t_alpha.main:app --host 127.0.0.1 --port 8867 --reload
```

参数说明：

- `t_alpha.main:app` 表示启动 `src/t_alpha/main.py` 里的 FastAPI 应用。
- `--host 127.0.0.1` 表示只在本机访问。
- `--port 8867` 表示服务端口是 `8867`。
- `--reload` 表示开发模式下代码变更后自动重启服务。

启动成功后，浏览器打开：

```text
http://127.0.0.1:8867/docs
```

### 方式二：使用安装后的命令启动

安装项目后，`pyproject.toml` 会注册一个命令：`t-alpha-api`。

先安装项目：

```powershell
python -m pip install -e ".[dev]"
```

然后启动：

```powershell
t-alpha-api
```

这个命令会读取 `.env` 中的 `APP_HOST` 和 `APP_PORT`。如果没有修改配置，默认会在 `127.0.0.1:8867` 启动。

如果想临时换端口，可以在当前终端设置环境变量后再启动：

```powershell
$env:APP_PORT = "9000"
t-alpha-api
```

## 运行测试

安装开发依赖后，可以运行全部测试：

```powershell
pytest -q
```

也可以只运行某一个测试文件，例如只检查配置读取：

```powershell
pytest tests/test_config.py -q
```

## 常见问题

### 端口被占用怎么办？

如果 `8867` 已经被其他程序占用，可以临时换一个端口：

```powershell
uvicorn t_alpha.main:app --host 127.0.0.1 --port 9000 --reload
```

或者修改 `.env`：

```env
APP_PORT=9000
```

然后使用：

```powershell
t-alpha-api
```

### 为什么浏览器打不开接口？

请按顺序检查：

1. 终端里服务是否还在运行。
2. 访问地址是否是 `http://127.0.0.1:8867/docs`。
3. 启动命令里的端口是否和浏览器地址一致。
4. `.env` 是否在项目根目录，而不是放到了 `src/` 或其他目录。

### 配置改了为什么没生效？

如果正在使用 `uvicorn`，请停止服务后重新启动。`.env` 是程序启动时读取的，服务运行中修改 `.env` 通常不会自动生效。

## 安全提醒

`.env` 里会保存 AmazingData、MySQL、SMTP 等账号密码。请只提交 `.env.example`，不要提交真实的 `.env` 文件。
