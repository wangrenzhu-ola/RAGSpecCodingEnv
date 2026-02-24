#!/bin/bash
set -euo pipefail

PROJECT_ROOT="$(pwd)"
TRAE_SCRIPT="${PROJECT_ROOT}/.trae/skills/hkt-memory/scripts/hkt_memory.py"
CLAUDE_SCRIPT="${PROJECT_ROOT}/.claude/skills/hkt-memory/scripts/hkt_memory.py"

if [ -f "${TRAE_SCRIPT}" ]; then
  python "${TRAE_SCRIPT}" "$@"
  exit 0
fi

if [ -f "${CLAUDE_SCRIPT}" ]; then
  python "${CLAUDE_SCRIPT}" "$@"
  exit 0
fi

echo "未找到 hkt-memory 脚本: ${TRAE_SCRIPT} 或 ${CLAUDE_SCRIPT}"
exit 1
