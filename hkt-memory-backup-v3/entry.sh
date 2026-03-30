#!/bin/bash
set -euo pipefail

PROJECT_ROOT="$(pwd)"

# Load local .env if exists
if [ -f "${PROJECT_ROOT}/.env" ]; then
  # Use a subshell to export variables without polluting current shell
  # but since this IS a script, we want them exported for the python call
  set -a
  source "${PROJECT_ROOT}/.env"
  set +a
fi

TRAE_SCRIPT="${PROJECT_ROOT}/.trae/skills/hkt-memory/scripts/hkt_memory.py"
CLAUDE_SCRIPT="${PROJECT_ROOT}/.claude/skills/hkt-memory/scripts/hkt_memory.py"

# Try python3 first, then python
PYTHON_BIN=$(command -v python3 || command -v python)

if [ -f "${TRAE_SCRIPT}" ]; then
  "${PYTHON_BIN}" "${TRAE_SCRIPT}" "$@"
  exit 0
fi

if [ -f "${CLAUDE_SCRIPT}" ]; then
  "${PYTHON_BIN}" "${CLAUDE_SCRIPT}" "$@"
  exit 0
fi

echo "未找到 hkt-memory 脚本: ${TRAE_SCRIPT} 或 ${CLAUDE_SCRIPT}"
exit 1
