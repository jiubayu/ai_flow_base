#!/usr/bin/env bash
# 统一启停入口：start / stop / status，管理 backend、celery、frontend 三个本地服务。
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVER_ROOT="$REPO_ROOT/server"
UI_ROOT="$REPO_ROOT/ui"
ENV_FILE="${DEVCTL_ENV_FILE:-$SERVER_ROOT/.env}"

SERVICES="backend celery frontend"
PROBE_ATTEMPTS=10
PROBE_INTERVAL=1

fail() {
    echo "错误：$*" >&2
    exit 1
}

fail_with_cleanup() {
    for name in $STARTED; do
        stop_service "$name"
    done
    fail "$*"
}

env_value() {
    grep -E "^$1=" "$ENV_FILE" | tail -1 | cut -d= -f2- | tr -d '\r'
}

load_config() {
    if [ ! -f "$ENV_FILE" ]; then
        fail "配置文件缺失：${ENV_FILE}。请先执行 cp server/.env.example server/.env 并填写必填项。"
    fi
    for key in BACKEND_HOST BACKEND_PORT LOG_DIR RUNTIME_DIR CELERY_BROKER_URL CELERY_BROKER_DIR CELERY_RESULT_DB_PATH; do
        value="$(env_value "$key")"
        [ -n "$value" ] || fail "缺少必填配置项：${key}（参见 server/.env.example）"
    done
    BACKEND_HOST="$(env_value BACKEND_HOST)"
    BACKEND_PORT="$(env_value BACKEND_PORT)"
    case "$BACKEND_PORT" in
        *[!0-9]*) fail "BACKEND_PORT 必须是整数，当前值：${BACKEND_PORT}" ;;
    esac
    FRONTEND_PORT="${FRONTEND_PORT_OVERRIDE:-$(env_value FRONTEND_PORT)}"
    FRONTEND_PORT="${FRONTEND_PORT:-5173}"
    LOG_DIR="$SERVER_ROOT/$(env_value LOG_DIR)"
    RUNTIME_DIR="$SERVER_ROOT/$(env_value RUNTIME_DIR)"
}

service_field() {
    name="$1"
    field="$2"
    case "$field" in
        workdir)
            if [ "$name" = "frontend" ]; then echo "$UI_ROOT"; else echo "$SERVER_ROOT"; fi
            ;;
        start_command)
            case "$name" in
                backend) echo "uv run uvicorn src.main:app --host $BACKEND_HOST --port $BACKEND_PORT" ;;
                celery) echo "uv run celery -A src.celery_app:app worker -l info" ;;
                frontend) echo "pnpm dev --port $FRONTEND_PORT" ;;
            esac
            ;;
        health_probe)
            case "$name" in
                backend) echo "http://$BACKEND_HOST:$BACKEND_PORT/api/health" ;;
                frontend) echo "http://$BACKEND_HOST:$FRONTEND_PORT" ;;
                celery) echo "" ;;
            esac
            ;;
        log_path) echo "$LOG_DIR/$name.log" ;;
        pid_path) echo "$RUNTIME_DIR/$name.pid" ;;
        port)
            case "$name" in
                backend) echo "$BACKEND_PORT" ;;
                frontend) echo "$FRONTEND_PORT" ;;
                celery) echo "" ;;
            esac
            ;;
    esac
}

read_pid() {
    pid_path="$(service_field "$1" pid_path)"
    [ -f "$pid_path" ] || return 1
    raw="$(cat "$pid_path")"
    case "$raw" in
        '' | *[!0-9]*) return 1 ;;
    esac
    echo "$raw"
}

process_alive() {
    kill -0 "$1" 2>/dev/null
}

port_in_use() {
    python3 -c 'import socket, sys
try:
    s = socket.socket()
    s.bind(("127.0.0.1", int(sys.argv[1])))
    s.close()
except OSError:
    sys.exit(0)
sys.exit(1)' "$1"
}

probe() {
    url="$1"
    attempt=0
    while [ "$attempt" -lt "$PROBE_ATTEMPTS" ]; do
        if curl -fsS --max-time "$PROBE_INTERVAL" "$url" >/dev/null 2>&1; then
            return 0
        fi
        attempt=$((attempt + 1))
        sleep "$PROBE_INTERVAL"
    done
    return 1
}

start_service() {
    name="$1"
    if pid="$(read_pid "$name")" && process_alive "$pid"; then
        fail_with_cleanup "服务 ${name} 已在运行（PID ${pid}），重复执行请先 stop"
    fi
    port="$(service_field "$name" port)"
    if [ -n "$port" ] && port_in_use "$port"; then
        fail_with_cleanup "端口冲突：${name} 需要端口 ${port} 已被占用，请释放后重试（日志：$(service_field "$name" log_path)）"
    fi
    log_path="$(service_field "$name" log_path)"
    pid_path="$(service_field "$name" pid_path)"
    start_command="$(service_field "$name" start_command)"
    workdir="$(service_field "$name" workdir)"
    mkdir -p "$LOG_DIR" "$RUNTIME_DIR"
    echo "启动 ${name}：${start_command}"
    (
        cd "$workdir"
        set -m
        nohup bash -c "$start_command" >>"$log_path" 2>&1 &
        echo "$!" >"$pid_path"
    )
}

stop_service() {
    name="$1"
    pid_path="$(service_field "$name" pid_path)"
    if [ ! -f "$pid_path" ]; then
        echo "${name}：未运行（无 PID 记录）"
        return 0
    fi
    if pid="$(read_pid "$name")"; then
        if process_alive "$pid"; then
            kill -TERM -- -"$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null || true
            echo "${name}：已停止（PID ${pid}）"
        else
            echo "${name}：PID ${pid} 已失效，执行清理"
        fi
    else
        echo "${name}：PID 文件无效（$(cat "$pid_path")），执行清理"
    fi
    rm -f "$pid_path"
}

status_service() {
    name="$1"
    log_path="$(service_field "$name" log_path)"
    if pid="$(read_pid "$name")"; then
        if process_alive "$pid"; then
            state="running"
            message="进程存活（PID ${pid}）"
        else
            state="failed"
            message="PID ${pid} 已失效，需要清理（执行 stop 可清理）"
        fi
    else
        state="stopped"
        message="未由 devctl 启动"
    fi
    echo "service=${name} state=${state} pid=${pid:-} log_path=${log_path} message=${message}"
}

cmd_start() {
    load_config
    STARTED=""
    for name in $SERVICES; do
        start_service "$name"
        STARTED="$STARTED $name"
    done
    for name in $SERVICES; do
        probe_url="$(service_field "$name" health_probe)"
        if [ -n "$probe_url" ]; then
            if ! probe "$probe_url"; then
                fail_with_cleanup "${name} 健康探针超时（${probe_url}），责任服务：${name}，日志：$(service_field "$name" log_path)"
            fi
            echo "${name}：探针通过（${probe_url}）"
        elif ! process_alive "$(read_pid "$name")"; then
            fail_with_cleanup "${name} 进程已退出，责任服务：${name}，日志：$(service_field "$name" log_path)"
        else
            echo "${name}：进程存活（PID $(read_pid "$name")）"
        fi
    done
    echo "全部服务已启动，日志目录：${LOG_DIR}"
    echo "最小联通验证入口：curl http://${BACKEND_HOST}:${BACKEND_PORT}/api/health，然后 POST /api/dev/tasks/demo"
}

cmd_stop() {
    load_config
    for name in $SERVICES; do
        stop_service "$name"
    done
}

cmd_status() {
    load_config
    for name in $SERVICES; do
        status_service "$name"
    done
}

case "${1:-}" in
    start) cmd_start ;;
    stop) cmd_stop ;;
    status) cmd_status ;;
    *) fail "用法：./scripts/devctl.sh <start|stop|status>" ;;
esac
