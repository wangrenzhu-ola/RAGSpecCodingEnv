#!/bin/bash
set -euo pipefail

echo "Initializing AI Development Environment..."

PROJECT_ROOT="$(pwd)"
AI_ENV_DIR="${PROJECT_ROOT}/.ai-env"
SKILLS_SRC_DIR="${AI_ENV_DIR}/skills-src"

rm -rf "${AI_ENV_DIR}"

rm -rf "${PROJECT_ROOT}/.claude/skills/openspec" "${PROJECT_ROOT}/.claude/skills/OpenSpec"

if ! command -v node >/dev/null 2>&1; then
  echo "Node.js is required but was not found in PATH."
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required but was not found in PATH."
  exit 1
fi

mkdir -p "${AI_ENV_DIR}"

if [ ! -f "${AI_ENV_DIR}/package.json" ]; then
  cat > "${AI_ENV_DIR}/package.json" <<'EOF'
{
  "name": "ai-env",
  "private": true,
  "version": "0.0.0"
}
EOF
fi

(cd "${AI_ENV_DIR}" && npm install --save-dev openskills @fission-ai/openspec)

OPENSKILLS_BIN="${AI_ENV_DIR}/node_modules/.bin/openskills"
OPENSPEC_BIN="${AI_ENV_DIR}/node_modules/.bin/openspec"

# 1. Clone Anthropic Skills repo and install ALL skills
echo "Cloning Anthropic Skills repository..."
rm -rf "${AI_ENV_DIR}/anthropics-skills-repo"
git clone https://github.com/anthropics/skills.git "${AI_ENV_DIR}/anthropics-skills-repo"

echo "Installing all Anthropic Skills..."
for skill_dir in "${AI_ENV_DIR}/anthropics-skills-repo/skills"/*; do
  if [ -d "$skill_dir" ]; then
    skill_name=$(basename "$skill_dir")
    echo "Installing skill: $skill_name"
    "${OPENSKILLS_BIN}" install "$skill_dir" --yes || echo "Warning: Failed to install skill $skill_name"
  fi
done

# 1.5. Clone and install Community Skills (alirezarezvani/claude-skills)
echo "Cloning Community Skills repository (alirezarezvani/claude-skills)..."
rm -rf "${AI_ENV_DIR}/community-skills-repo"
git clone https://github.com/alirezarezvani/claude-skills.git "${AI_ENV_DIR}/community-skills-repo"

echo "Installing all Community Skills..."
# Find all directories containing SKILL.md and install them
if [ -d "${AI_ENV_DIR}/community-skills-repo" ]; then
    find "${AI_ENV_DIR}/community-skills-repo" -name "SKILL.md" -print0 | while IFS= read -r -d '' skill_file; do
      skill_dir=$(dirname "$skill_file")
      skill_name=$(basename "$skill_dir")
      # Skip if it's the root repo SKILL.md (if any, though usually skills are in subdirs)
      # But openskills install handles paths fine.
      echo "Installing community skill: $skill_name"
      "${OPENSKILLS_BIN}" install "$skill_dir" --yes || echo "Warning: Failed to install community skill $skill_name"
    done
fi

# 2. Clone OpenSpec repo and make it a skill
echo "Cloning OpenSpec repository..."
rm -rf "${AI_ENV_DIR}/openspec-repo"
git clone https://github.com/Fission-AI/OpenSpec.git "${AI_ENV_DIR}/openspec-repo"

# Ensure OpenSpec has a SKILL.md (Create if missing, as it might not be in the repo root yet)
if [ ! -f "${AI_ENV_DIR}/openspec-repo/SKILL.md" ]; then
  echo "Creating SKILL.md for OpenSpec..."
  cat > "${AI_ENV_DIR}/openspec-repo/SKILL.md" <<'EOF'
---
name: openspec
description: Spec-driven development workflow (proposal/apply/archive) to keep requirements explicit and prevent scope drift.
---

# OpenSpec

## When to use

Use this skill whenever the user request:

- Introduces a new feature, behavior change, refactor, or architecture change
- Feels ambiguous or likely to expand in scope
- Needs reviewable, deterministic intent before implementation

## Workflow

1. Create a proposal first, and get agreement on requirements.
2. Implement only what the proposal specifies.
3. Archive once verified, so specs become the source of truth.

## Commands (run from project root)

- Create proposal: `npx openspec proposal "Title"`
- Apply proposal: `npx openspec apply <change-id>`
- Archive proposal: `npx openspec archive <change-id>`
- List changes: `npx openspec changes`
EOF
fi

echo "Installing OpenSpec as a skill..."
"${OPENSKILLS_BIN}" install "${AI_ENV_DIR}/openspec-repo" --yes

if [ -d "${PROJECT_ROOT}/hkt-memory" ]; then
  echo "Installing local skill: hkt-memory..."
  "${OPENSKILLS_BIN}" install "${PROJECT_ROOT}/hkt-memory" --yes
fi

if [ ! -d "${PROJECT_ROOT}/openspec" ]; then
  if "${OPENSPEC_BIN}" init --help 2>/dev/null | grep -q -- "--skip-tools"; then
    "${OPENSPEC_BIN}" init --skip-tools
  else
    mkdir -p "${PROJECT_ROOT}/openspec/specs" "${PROJECT_ROOT}/openspec/changes"
  fi
fi

if [ ! -f "${PROJECT_ROOT}/AGENTS.md" ]; then
  cat > "${PROJECT_ROOT}/AGENTS.md" <<'EOF'
# AI Assistant Context

You are an advanced AI software engineer operating in a Spec-Driven Development environment.

## Workflow
1. **Analyze**: Understand the user's request.
2. **Check Specs**: Read `openspec/specs/` to understand current behavior.
3. **Propose**: For non-trivial changes, create an OpenSpec proposal first.
4. **Implement**: Implement strictly according to the agreed proposal/specs.
5. **Archive**: After verification, archive the change so specs stay authoritative.
6. **Memory**: 每轮对话前通过 hkt-memory 技能检索记忆，对话完毕后通过 hkt-memory 技能储存关键记忆。
EOF
fi

"${OPENSKILLS_BIN}" sync --yes

echo "Done."
echo "Next: read AI_WORKFLOW_GUIDE.md"
echo ""
echo "⚠️ 重要：为了验证并完成环境配置，请复制以下提示词发送给你的 AI 助手："
echo "--------------------------------------------------------------------------------"
echo "请检查当前环境。我刚刚运行了 'init-ai-env.sh' 脚本。"
echo "1. 验证 'AGENTS.md' 是否存在，且包含可用的技能列表（包括 OpenSpec 和 Anthropic 官方技能）。"
echo "2. 如果 'AGENTS.md' 中缺少任何技能，请运行 'npx openskills sync' 进行更新。"
echo "3. 确认你能看到 'openspec' 技能以及至少一个其他技能（例如 'pdf' 或 'frontend-design'）。"
echo "4. 验证通过后，请告诉我 'AI 环境已准备就绪 🚀'。"
echo "--------------------------------------------------------------------------------"
