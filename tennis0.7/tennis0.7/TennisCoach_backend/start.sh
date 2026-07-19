#!/usr/bin/env bash
#
# TennisCoach 后端服务统一启动脚本（Linux 服务器部署用）
# ----------------------------------------------------------------------------
# 设计要点：
#   1. 屏蔽代理环境变量（HTTP_PROXY / HTTPS_PROXY / ALL_PROXY 等）
#      后端调用的豆包 (ark.cn-beijing.volces.com) 和百度语音都是国内服务，
#      根本不需要走梯子；若不屏蔽，clash 关闭后所有 AI 接口会因连不上
#      127.0.0.1:7890 而失败（健康检查仍 200，但业务静默失效）。
#   2. 强制使用 conda tennis 环境的 python，避免误用 base 环境。
#   3. 后台运行（nohup + disown），关闭终端不影响。
#
# 用法：
#   ./start.sh                # 等同于 ./start.sh start
#   ./start.sh start          # 启动（如已运行则跳过）
#   ./start.sh stop           # 停止（先 SIGTERM，10s 后 SIGKILL）
#   ./start.sh restart        # 重启
#   ./start.sh status         # 查看运行状态
#   ./start.sh logs           # 跟踪 server.log（Ctrl+C 退出）
# ----------------------------------------------------------------------------

set -euo pipefail

# ---------- 路径与配置 ----------
SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON_BIN="/root/miniconda3/envs/tennis/bin/python"
LOG_FILE="$SCRIPT_DIR/server.log"
HOST="127.0.0.1"
PORT="6006"
STARTUP_WAIT=30   # 启动后等待健康检查的最大秒数

# ---------- 屏蔽代理环境变量（关键）----------
# 防止本机梯子（clash on 127.0.0.1:7890）开关状态影响后端对外部 API 的调用。
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy all_proxy NO_PROXY no_proxy

# ---------- 前置校验 ----------
if [ ! -x "$PYTHON_BIN" ]; then
    echo "[ERROR] 未找到 conda tennis 环境的 python: $PYTHON_BIN" >&2
    exit 1
fi
if [ ! -f "$SCRIPT_DIR/main.py" ]; then
    echo "[ERROR] 当前目录没有 main.py: $SCRIPT_DIR" >&2
    exit 1
fi

# ---------- 辅助函数 ----------
is_running() {
    pgrep -f "$PYTHON_BIN main.py" >/dev/null 2>&1
}

current_pid() {
    pgrep -f "$PYTHON_BIN main.py" | head -n1
}

wait_healthy() {
    local elapsed=0
    while [ "$elapsed" -lt "$STARTUP_WAIT" ]; do
        if curl -fs "http://${HOST}:${PORT}/health" >/dev/null 2>&1; then
            return 0
        fi
        sleep 1
        elapsed=$((elapsed + 1))
    done
    return 1
}

# ---------- 子命令 ----------
cmd_start() {
    if is_running; then
        echo "[SKIP] 服务已在运行 (pid=$(current_pid))"
        exit 0
    fi
    echo "[START] 启动 tennis 后端..."
    nohup "$PYTHON_BIN" main.py > "$LOG_FILE" 2>&1 &
    local new_pid=$!
    disown "$new_pid" 2>/dev/null || true
    echo "[START] 后台进程 pid=$new_pid, 日志: $LOG_FILE"
    echo "[START] 等待 /health 就绪（最多 ${STARTUP_WAIT}s）..."

    if wait_healthy; then
        echo "[OK] 服务已就绪: http://${HOST}:${PORT}/health"
    else
        echo "[WARN] 健康检查超时，请查看日志: tail -f $LOG_FILE"
        exit 1
    fi
}

cmd_stop() {
    if ! is_running; then
        echo "[SKIP] 服务未在运行"
        return 0
    fi
    local pids
    pids="$(pgrep -f "$PYTHON_BIN main.py" || true)"
    echo "[STOP] 发送 SIGTERM: $pids"
    # shellcheck disable=SC2086
    kill $pids 2>/dev/null || true

    local elapsed=0
    while [ "$elapsed" -lt 10 ]; do
        if ! is_running; then
            echo "[OK] 已停止"
            return 0
        fi
        sleep 1
        elapsed=$((elapsed + 1))
    done
    echo "[WARN] 优雅停止超时，强制 SIGKILL"
    # shellcheck disable=SC2086
    pkill -9 -f "$PYTHON_BIN main.py" 2>/dev/null || true
}

cmd_status() {
    if is_running; then
        echo "[RUNNING] pid=$(current_pid)"
        ss -tlnp 2>/dev/null | grep ":${PORT}" || true
    else
        echo "[STOPPED] 服务未运行"
        exit 1
    fi
}

cmd_logs() {
    tail -n 200 -f "$LOG_FILE"
}

case "${1:-start}" in
    start)   cmd_start ;;
    stop)    cmd_stop ;;
    restart) cmd_stop; cmd_start ;;
    status)  cmd_status ;;
    logs)    cmd_logs ;;
    *)
        echo "用法: $0 {start|stop|restart|status|logs}" >&2
        exit 1
        ;;
esac
