#!/usr/bin/env bash
# 开启严格模式：命令失败、未定义变量、管道失败时立即退出。
set -Eeuo pipefail

# 基础部署参数，可在执行脚本时通过同名环境变量覆盖。
IMAGE="${IMAGE:-crpi-36rftbsqfy7g8oj0.cn-beijing.personal.cr.aliyuncs.com/zhuliye/t-alpha:latest}"
CONTAINER_NAME="${CONTAINER_NAME:-t-alpha}"
HOST_PORT="${HOST_PORT:-8867}"
CONTAINER_PORT="${CONTAINER_PORT:-8867}"
ENV_FILE="${ENV_FILE:-./.env}"
DATA_DIR="${DATA_DIR:-./data}"
LOG_DIR="${LOG_DIR:-./logs}"
RESTART_POLICY="${RESTART_POLICY:-unless-stopped}"
HEALTH_TIMEOUT_SECONDS="${HEALTH_TIMEOUT_SECONDS:-60}"

# 输出普通日志，统一加上项目名前缀。
log() {
  printf '[t-alpha] %s\n' "$*"
}

# 输出错误日志并退出脚本。
fail() {
  printf '[t-alpha] ERROR: %s\n' "$*" >&2
  exit 1
}

# 检查 Docker 命令和 Docker 服务是否可用。
command -v docker >/dev/null 2>&1 || fail "docker is not installed or not in PATH"
docker info >/dev/null 2>&1 || fail "docker daemon is not running or current user cannot access it"

# 启动容器前必须先准备好环境变量文件。
[ -f "$ENV_FILE" ] || fail "env file not found: $ENV_FILE"

# 创建宿主机数据目录和日志目录，用于挂载到容器内。
mkdir -p "$DATA_DIR" "$LOG_DIR"

# 拉取远程最新镜像。
log "pulling image: $IMAGE"
docker pull "$IMAGE"

# 如果已存在同名容器，先删除旧容器，避免 docker run 名称冲突。
if docker ps -a --format '{{.Names}}' | grep -Fxq "$CONTAINER_NAME"; then
  log "removing existing container: $CONTAINER_NAME"
  docker rm -f "$CONTAINER_NAME" >/dev/null
fi

# 使用最新镜像启动容器，并挂载数据、日志目录。
log "starting container: $CONTAINER_NAME"
docker run -d \
  --name "$CONTAINER_NAME" \
  --restart "$RESTART_POLICY" \
  -p "${HOST_PORT}:${CONTAINER_PORT}" \
  --env-file "$ENV_FILE" \
  -e APP_ENV=prod \
  -e APP_HOST=0.0.0.0 \
  -e APP_PORT="$CONTAINER_PORT" \
  -e AMAZINGDATA_LOCAL_PATH=/app/data/amazingdata \
  -v "$(realpath "$DATA_DIR"):/app/data" \
  -v "$(realpath "$LOG_DIR"):/app/logs" \
  "$IMAGE" >/dev/null

# 循环等待容器健康检查通过，超时后输出最近日志便于排查。
deadline=$((SECONDS + HEALTH_TIMEOUT_SECONDS))
while [ "$SECONDS" -lt "$deadline" ]; do
  # 优先读取 Dockerfile 中 HEALTHCHECK 的状态；没有健康检查时读取容器运行状态。
  status="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$CONTAINER_NAME" 2>/dev/null || true)"
  case "$status" in
    healthy|running)
      # 容器可用后输出常用访问地址。
      log "container is $status"
      log "health: http://127.0.0.1:${HOST_PORT}/health"
      log "api docs: http://127.0.0.1:${HOST_PORT}/docs"
      exit 0
      ;;
    unhealthy|exited|dead)
      docker logs --tail 80 "$CONTAINER_NAME" >&2 || true
      fail "container started but became $status"
      ;;
  esac
  sleep 2
done

# 等待超时，输出容器最后日志并失败退出。
docker logs --tail 80 "$CONTAINER_NAME" >&2 || true
fail "container did not become healthy within ${HEALTH_TIMEOUT_SECONDS}s"
