#!/bin/sh
# Docker 入口：支持 run-test / run-smoke / 默认 MCP
set -e
export PYTHONPATH=/app/src

case "${1:-}" in
  run-test)
    exec python3 /app/scripts/run_demo.py
    ;;
  run-smoke)
    exec python3 /app/scripts/run_smoke.py
    ;;
  *)
    exec webtest-mcp "$@"
    ;;
esac
