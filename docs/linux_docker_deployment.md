# t-alpha Linux Docker 部署说明

本文档用于在 Linux 服务器上部署已经构建好的 `t-alpha` Docker 镜像。

## 镜像地址

```bash
docker pull crpi-36rftbsqfy7g8oj0.cn-beijing.personal.cr.aliyuncs.com/zhuliye/t-alpha:latest
```

项目容器内默认监听端口为 `8867`，健康检查地址为 `/health`。

## 前置条件

1. 服务器已安装 Docker。
2. 当前用户可以执行 `docker` 命令，或使用 `sudo` 运行脚本。
3. 服务器可以访问阿里云镜像仓库。
4. 已准备好生产环境 `.env` 文件。

## 推荐目录结构

建议在服务器上创建一个独立部署目录：

```bash
mkdir -p /usr/local/t-alpha
cd /usr/local/t-alpha
```

将仓库中的以下文件上传或复制到该目录：

```text
/usr/local/t-alpha/
├── .env
├── deploy/
│   ├── pull_start.sh
│   └── restart.sh
├── data/
└── logs/
```

`data/` 和 `logs/` 会由脚本自动创建。

## 配置 .env

可以从 `.env.example` 复制一份：

```bash
cp .env.example .env
vim .env
```

至少检查以下配置：

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
```

脚本会在启动容器时强制覆盖以下容器运行配置：

```env
APP_ENV=prod
APP_HOST=0.0.0.0
APP_PORT=8867
AMAZINGDATA_LOCAL_PATH=/app/data/amazingdata
```

这样可以避免 `.env` 中仍保留本地开发配置 `APP_HOST=127.0.0.1` 时，Docker 端口映射后服务无法从容器外访问。

## 首次部署或更新镜像后启动

给脚本增加执行权限：

```bash
chmod +x deploy/pull_start.sh deploy/restart.sh
```

拉取最新镜像并启动：

```bash
./deploy/pull_start.sh
```

脚本会执行以下动作：

1. 检查 Docker 是否可用。
2. 检查 `.env` 是否存在。
3. 拉取最新镜像。
4. 删除同名旧容器 `t-alpha`。
5. 使用最新镜像重新启动容器。
6. 等待容器健康检查通过。

启动成功后访问：

```text
http://服务器IP:8867/health
http://服务器IP:8867/docs
```

## 不拉取镜像，仅重启项目

如果只是修改 `.env`、重启服务，或服务器重启后手动恢复项目，不需要重新拉取镜像：

```bash
./deploy/restart.sh
```

如果 `t-alpha` 容器已经存在，该脚本只执行：

```bash
docker restart t-alpha
```

如果容器不存在，但本地已有镜像，该脚本会使用本地镜像重新创建容器，不会执行 `docker pull`。

## 常用自定义参数

脚本支持通过环境变量覆盖默认值。

### 修改宿主机端口

容器内部仍使用 `8867`，只修改宿主机暴露端口：

```bash
HOST_PORT=9000 ./deploy/pull_start.sh
```

访问地址变为：

```text
http://服务器IP:9000/docs
```

### 修改容器名称

```bash
CONTAINER_NAME=t-alpha-prod ./deploy/pull_start.sh
```

### 指定其他 .env 文件

```bash
ENV_FILE=/usr/local/t-alpha/.env.prod ./deploy/pull_start.sh
```

### 指定数据和日志目录

```bash
DATA_DIR=/data/t-alpha LOG_DIR=/var/log/t-alpha ./deploy/pull_start.sh
```

## 查看运行状态

```bash
docker ps --filter name=t-alpha
docker inspect --format '{{json .State.Health}}' t-alpha
```

## 查看日志

```bash
docker logs -f --tail 200 t-alpha
```

## 停止服务

```bash
docker stop t-alpha
```

## 删除容器

删除容器不会删除镜像，也不会删除宿主机上的 `data/` 和 `logs/` 目录。

```bash
docker rm -f t-alpha
```

## 手工 Docker 命令参考

不使用脚本时，可以手工执行：

```bash
docker pull crpi-36rftbsqfy7g8oj0.cn-beijing.personal.cr.aliyuncs.com/zhuliye/t-alpha:latest

docker rm -f t-alpha 2>/dev/null || true

docker run -d \
  --name t-alpha \
  --restart unless-stopped \
  -p 8867:8867 \
  --env-file ./.env \
  -e APP_ENV=prod \
  -e APP_HOST=0.0.0.0 \
  -e APP_PORT=8867 \
  -e AMAZINGDATA_LOCAL_PATH=/app/data/amazingdata \
  -v "$(realpath ./data):/app/data" \
  -v "$(realpath ./logs):/app/logs" \
  crpi-36rftbsqfy7g8oj0.cn-beijing.personal.cr.aliyuncs.com/zhuliye/t-alpha:latest
```

## 排查建议

### 端口无法访问

先检查容器是否运行：

```bash
docker ps --filter name=t-alpha
docker logs --tail 100 t-alpha
```

再检查服务器防火墙或云厂商安全组是否放行 `8867` 端口。

### 健康检查失败

查看容器日志：

```bash
docker logs --tail 200 t-alpha
```

常见原因包括 `.env` 配置错误、数据库无法连接、AmazingData 服务地址不可达或账号密码错误。

### 修改 .env 后未生效

`.env` 在容器启动时读取，修改后需要重启：

```bash
./deploy/restart.sh
```
