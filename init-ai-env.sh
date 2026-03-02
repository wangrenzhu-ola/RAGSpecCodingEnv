#!/bin/bash
set -euo pipefail

# Ensure proxy settings are applied (User Rule)
export http_proxy=http://10.48.113.10:8080
export https_proxy=http://10.48.113.10:8080
export OPENAI_API_KEY=642f21a1f8c64c11b1a814e892949865.KrgVUmfbdUO1I3mN
export OPENAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4

echo "Initializing AI Development Environment..."

PROJECT_ROOT="$(pwd)"
AI_ENV_DIR="${PROJECT_ROOT}/.ai-env"
SKILLS_SRC_DIR="${AI_ENV_DIR}/skills-src"
OPENSPEC_VERSION="1.2.0"

rm -rf "${AI_ENV_DIR}"

rm -rf "${PROJECT_ROOT}/.claude/skills/openspec" "${PROJECT_ROOT}/.claude/skills/OpenSpec" "${PROJECT_ROOT}/.claude/skills/openspec-repo"
# rm -rf "${PROJECT_ROOT}/.trae/skills/openspec" "${PROJECT_ROOT}/.trae/skills/OpenSpec" "${PROJECT_ROOT}/.trae/skills/openspec-repo"
rm -rf "${PROJECT_ROOT}/.claude/skills/hkt-memory"

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

(cd "${AI_ENV_DIR}" && npm install --save-dev openskills "@fission-ai/openspec@^${OPENSPEC_VERSION}")

OPENSKILLS_BIN="${AI_ENV_DIR}/node_modules/.bin/openskills"
OPENSPEC_BIN="${AI_ENV_DIR}/node_modules/.bin/openspec"

# 1. Clone find-skills repo and install
echo "Cloning find-skills repository..."
rm -rf "${AI_ENV_DIR}/skills"
git clone https://github.com/vercel-labs/skills.git "${AI_ENV_DIR}/skills"

echo "Installing find-skills skill..."
if [ -d "${AI_ENV_DIR}/skills/skills/find-skills" ]; then
    "${OPENSKILLS_BIN}" install "${AI_ENV_DIR}/skills/skills/find-skills" --yes
else
    echo "Warning: find-skills skill not found in expected location"
fi

# 2. Clone OpenSpec repo and make it a skill
echo "Cloning OpenSpec repository..."
rm -rf "${AI_ENV_DIR}/openspec"
git clone --depth 1 --branch "v${OPENSPEC_VERSION}" https://github.com/Fission-AI/OpenSpec.git "${AI_ENV_DIR}/openspec"

# Ensure OpenSpec has a SKILL.md (Create if missing, as it might not be in the repo root yet)
if [ ! -f "${AI_ENV_DIR}/openspec/SKILL.md" ]; then
  echo "Creating SKILL.md for OpenSpec..."
  cat > "${AI_ENV_DIR}/openspec/SKILL.md" <<'EOF'
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
"${OPENSKILLS_BIN}" install "${AI_ENV_DIR}/openspec" --yes

if [ -d "${PROJECT_ROOT}/hkt-memory" ]; then
  echo "Installing local skill: hkt-memory..."
  "${OPENSKILLS_BIN}" install "${PROJECT_ROOT}/hkt-memory" --yes
elif [ -d "${PROJECT_ROOT}/external/hkt-memory" ]; then
  echo "Installing local skill: hkt-memory..."
  "${OPENSKILLS_BIN}" install "${PROJECT_ROOT}/external/hkt-memory" --yes
fi

# Sync ALL installed skills from .claude/skills to .trae/skills
if [ -d "${PROJECT_ROOT}/.claude/skills" ]; then
  echo "Syncing all skills from .claude/skills to .trae/skills..."
  mkdir -p "${PROJECT_ROOT}/.trae/skills"
  
  for skill_path in "${PROJECT_ROOT}/.claude/skills"/*; do
    if [ -d "$skill_path" ]; then
      skill_name=$(basename "$skill_path")
      # Skip if strictly internal or ignored (optional)
      
      echo "Syncing skill: $skill_name"
      rm -rf "${PROJECT_ROOT}/.trae/skills/$skill_name"
      cp -R "$skill_path" "${PROJECT_ROOT}/.trae/skills/"
    fi
  done
  echo "✅ Skills synced to .trae/skills"
else
  echo "⚠️  Source skills directory (.claude/skills) not found."
  echo "Please manually copy skills to .trae/skills if needed."
fi

if [ ! -d "${PROJECT_ROOT}/openspec" ]; then
  if "${OPENSPEC_BIN}" init --help 2>/dev/null | grep -q -- "--skip-tools"; then
    "${OPENSPEC_BIN}" init --skip-tools
  else
    mkdir -p "${PROJECT_ROOT}/openspec/specs" "${PROJECT_ROOT}/openspec/changes"
  fi
fi

"${OPENSKILLS_BIN}" sync --yes

echo "Done."
echo "Next: read AI_WORKFLOW_GUIDE.md"
echo ""
echo "--------------------------------------------------------------------------------"
echo "🔧 配置 Embedding Provider (向量模型)"
echo "默认使用 Zhipu AI (GLM) embedding-3"
echo "--------------------------------------------------------------------------------"
export_env() {
  key="$1"
  val="$2"
  # Export for current session
  export "$key"="$val"
  
  # 1. Write to project local .env
  local env_file="${PROJECT_ROOT}/.env"
  if [ ! -f "$env_file" ]; then touch "$env_file"; fi
  sed -i '' "/^$key=/d" "$env_file"
  echo "$key=\"$val\"" >> "$env_file"
  echo "✅ Updated project .env with $key"

  # 2. Determine which profile to use
  local profiles=("$HOME/.zshrc" "$HOME/.bash_profile" "$HOME/.bashrc")
  for profile in "${profiles[@]}"; do
    if [ -f "$profile" ]; then
      # Remove existing
      sed -i '' "/export $key=/d" "$profile"
      # Add new
      echo "export $key=\"$val\"" >> "$profile"
      echo "✅ Updated $profile with $key"
    fi
  done
}

if [ -z "${OPENAI_API_KEY:-}" ]; then
  echo "❌ 未检测到 OPENAI_API_KEY，请先在环境中设置 GLM API Key。"
  echo "例如：export OPENAI_API_KEY=\"<your-key>\""
  exit 1
fi

export_env "OPENAI_BASE_URL" "https://open.bigmodel.cn/api/paas/v4/"
export_env "HKT_MEMORY_MODEL" "embedding-3"
export_env "HKT_MEMORY_FORCE_LOCAL" "false"
echo "✅ Zhipu AI 配置完成 (使用 embedding-3 模型)。"

echo "--------------------------------------------------------------------------------"
echo "🔄 正在自动执行第一次同步 (hkt-memory sync)..."
# Use the local script to perform sync
if [ -f "hkt-memory/scripts/hkt_memory.py" ]; then
  # Try to use current session variables
  python3 hkt-memory/scripts/hkt_memory.py sync || echo "⚠️ 初始同步失败，请检查 API Key 后手动运行 sync。"
fi

echo "--------------------------------------------------------------------------------"
echo "✅ AI 环境已准备就绪 🚀"
echo "--------------------------------------------------------------------------------"

# Auto-generate AGENTS.md with strict token economy rules (Chinese)
cat > "${PROJECT_ROOT}/AGENTS.md" <<'EOF'
# AI 规则 (严格节省 Token)

## 核心技能
1. **hkt-memory (记忆系统)**: 
   - **查 (缺上下文时必用)**: `bash hkt-memory/entry.sh query --keyword "..." --limit 5`
     * **场景**: 只要你不完全清楚当前项目背景、历史决策或上下文，**必须**先查记忆。
   - **记 (任务结束时)**: `bash hkt-memory/entry.sh add --title "..." --content "..."` 然后 `sync`
     * **场景**: 每一轮对话/任务结束时，总结关键信息写入。

2. **openspec (规范系统)**:
   - **改**: `npx openspec proposal "..."` -> `apply` -> `archive`
   - **读**: `cat openspec/specs/*`

3. **find-skills (能力扩展)**:
   - **缺能力**: `npx openskills run find-skills "..."`
   - **装技能**: `npx openskills install <path>`

## 协议
- **流程**: **查记忆 (未知上下文)** -> **看Spec** -> **找技能 (如需)** -> **行动**
- **少聊**: 能写代码就不解释。
- **省流**: 回答简短，直击要点。
EOF
echo "✅ AGENTS.md generated."
echo ""

