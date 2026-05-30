#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
VENV_DIR="$ROOT_DIR/.venv"
LOG_DIR="$ROOT_DIR/.logs"

mkdir -p "$LOG_DIR"

print_step() {
  printf '\n\033[1;34m==> %s\033[0m\n' "$1"
}

print_info() {
  printf '\033[0;36m%s\033[0m\n' "$1"
}

print_warn() {
  printf '\033[0;33m%s\033[0m\n' "$1"
}

ensure_python() {
  if ! command -v python3 >/dev/null 2>&1; then
    echo "未找到 python3，请先安装 Python 3.10+。" >&2
    exit 1
  fi
}

ensure_node() {
  if ! command -v npm >/dev/null 2>&1; then
    echo "未找到 npm，请先安装 Node.js。" >&2
    exit 1
  fi
}

ensure_ca_bundle() {
  local brew_ca="/opt/homebrew/Cellar/ca-certificates/2025-05-20/share/ca-certificates/cacert.pem"
  local openssl_ca="/opt/homebrew/etc/openssl@3/cert.pem"

  if [[ -f "$openssl_ca" ]]; then
    return
  fi

  if [[ -f "$brew_ca" ]]; then
    print_step "修复 Python HTTPS 证书路径"
    mkdir -p "$(dirname "$openssl_ca")"
    ln -sf "$brew_ca" "$openssl_ca"
    print_info "已链接证书：$openssl_ca -> $brew_ca"
  fi
}

ensure_env_file() {
  if [[ -f "$ROOT_DIR/.env" ]]; then
    return
  fi

  print_step "创建 .env 配置文件"
  cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
  print_warn "已创建 .env。请稍后填写 GITHUB_TOKEN 和 AI_API_KEY，以获得完整 AI Review 能力。"
}

load_env() {
  set -a
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.env"
  set +a
}

ensure_backend_deps() {
  print_step "准备后端环境"
  if [[ ! -x "$VENV_DIR/bin/python" ]]; then
    python3 -m venv "$VENV_DIR"
  fi

  "$VENV_DIR/bin/python" -m pip install -e ".[web]" >/tmp/diffsense-backend-install.log 2>&1 || {
    cat /tmp/diffsense-backend-install.log >&2
    exit 1
  }
}

ensure_frontend_deps() {
  print_step "准备前端依赖"
  npm --prefix "$ROOT_DIR/frontend" install >/tmp/diffsense-frontend-install.log 2>&1 || {
    cat /tmp/diffsense-frontend-install.log >&2
    exit 1
  }
}

start_backend() {
  print_step "启动后端服务"
  "$VENV_DIR/bin/uvicorn" app.main:app \
    --reload \
    --app-dir "$ROOT_DIR/backend" \
    --host 127.0.0.1 \
    --port "$BACKEND_PORT" \
    >"$LOG_DIR/backend.log" 2>&1 &
  BACKEND_PID=$!
}

start_frontend() {
  print_step "启动前端页面"
  VITE_BACKEND_URL="http://127.0.0.1:$BACKEND_PORT" \
    npm --prefix "$ROOT_DIR/frontend" run dev -- --host 127.0.0.1 --port "$FRONTEND_PORT" \
    >"$LOG_DIR/frontend.log" 2>&1 &
  FRONTEND_PID=$!
}

cleanup() {
  print_step "正在关闭服务"
  if [[ -n "${BACKEND_PID:-}" ]]; then
    kill "$BACKEND_PID" >/dev/null 2>&1 || true
  fi
  if [[ -n "${FRONTEND_PID:-}" ]]; then
    kill "$FRONTEND_PID" >/dev/null 2>&1 || true
  fi
}

trap cleanup EXIT INT TERM

main() {
  cd "$ROOT_DIR"
  ensure_python
  ensure_node
  ensure_ca_bundle
  ensure_env_file
  load_env
  ensure_backend_deps
  ensure_frontend_deps
  start_backend
  start_frontend

  print_step "启动完成"
  print_info "前端页面：http://127.0.0.1:$FRONTEND_PORT"
  print_info "后端接口：http://127.0.0.1:$BACKEND_PORT"
  print_info "后端日志：$LOG_DIR/backend.log"
  print_info "前端日志：$LOG_DIR/frontend.log"

  if [[ -z "${GITHUB_TOKEN:-}" ]]; then
    print_warn "提示：当前未配置 GITHUB_TOKEN，可能遇到 GitHub API 限流。"
  fi
  if [[ -z "${AI_API_KEY:-}" && -z "${OPENAI_API_KEY:-}" ]]; then
    print_warn "提示：当前未配置 AI_API_KEY，系统会使用规则预分析 fallback。"
  fi

  print_info "按 Ctrl+C 可同时关闭前端和后端。"
  wait
}

main "$@"
