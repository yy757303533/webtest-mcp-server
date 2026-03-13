#!/bin/sh
# Docker 入口：run-test / run-smoke 支持指定项目
# run-test [project] [excel]  default: demo, login_cases.xlsx
# run-smoke [project]         default: demo, smoke_cases.xlsx
set -e
export PYTHONPATH=/app/src

case "${1:-}" in
  run-test)
    shift
    exec python3 /app/scripts/run_suite.py "$@"
    ;;
  run-smoke)
    shift
    exec python3 /app/scripts/run_smoke.py "$@"
    ;;
  *)
    exec webtest-mcp "$@"
    ;;
esac
