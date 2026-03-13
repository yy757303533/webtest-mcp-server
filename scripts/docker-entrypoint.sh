#!/bin/sh
# Docker 入口：支持 run-test 或默认启动 MCP
set -e
export PYTHONPATH=/app/src

case "${1:-}" in
  run-test)
    exec python3 /app/scripts/run_demo.py
    ;;
  *)
    exec webtest-mcp "$@"
    ;;
esac
