#!/bin/bash
set -euo pipefail

# Ensure proxy settings are applied (User Rule)
export http_proxy=http://10.48.113.10:8080
export https_proxy=http://10.48.113.10:8080

echo "Initializing AI Development Environment..."

PROJECT_ROOT="$(pwd)"
AI_ENV_DIR="${PROJECT_ROOT}/.ai-env"
SKILLS_SRC_DIR="${AI_ENV_DIR}/skills-src"
OPENSPEC_VERSION="1.2.0"

rm -rf "${AI_ENV_DIR}"

rm -rf "${PROJECT_ROOT}/.claude/skills/openspec" "${PROJECT_ROOT}/.claude/skills/OpenSpec" "${PROJECT_ROOT}/.claude/skills/openspec-repo"
rm -rf "${PROJECT_ROOT}/.trae/skills/openspec" "${PROJECT_ROOT}/.trae/skills/OpenSpec" "${PROJECT_ROOT}/.trae/skills/openspec-repo"
rm -rf "${PROJECT_ROOT}/.claude/skills/hkt-memory" "${PROJECT_ROOT}/.trae/skills/hkt-memory"

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
      cp -R "$skill_path" "${PROJECT_ROOT}/.trae/skills/$skill_name"
    fi
  done
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
echo "--------------------------------------------------------------------------------"
echo "🔧 配置 Embedding Provider (向量模型)"
echo "请选择要使用的 Embedding 服务提供商："
echo "1) OpenAI (官方 API)"
echo "2) Zhipu AI (智谱 GLM - 国内推荐 🇨🇳)"
echo "3) Local (本地 SentenceTransformer - 免费/无网)"
echo "--------------------------------------------------------------------------------"

read -p "请输入选项 [1-3] (默认 3): " provider_choice

# Default to Local (3)
if [ -z "$provider_choice" ]; then
  provider_choice="3"
fi

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

case "$provider_choice" in
  1)
    echo "👉 已选择: OpenAI"
    read -p "请输入 OpenAI API Key: " input_key
    if [ -n "$input_key" ]; then
      export_env "OPENAI_API_KEY" "$input_key"
      export_env "HKT_MEMORY_MODEL" "text-embedding-3-small"
      # Clear Base URL to use default
      if [ -f ~/.bashrc ]; then sed -i '' '/export OPENAI_BASE_URL=/d' ~/.bashrc; fi
      unset OPENAI_BASE_URL
      echo "✅ OpenAI 配置完成。"
    else
      echo "⚠️ 未输入 Key，回退到本地模式。"
      export_env "HKT_MEMORY_MODEL" "all-MiniLM-L6-v2"
    fi
    ;;
  2)
    echo "👉 已选择: Zhipu AI (GLM)"
    read -p "请输入 Zhipu API Key: " input_key
    if [ -n "$input_key" ]; then
      export_env "OPENAI_API_KEY" "$input_key"
      export_env "OPENAI_BASE_URL" "https://open.bigmodel.cn/api/paas/v4/"
      export_env "HKT_MEMORY_MODEL" "embedding-3"
      echo "✅ Zhipu AI 配置完成 (使用 embedding-3 模型)。"
    else
      echo "⚠️ 未输入 Key，回退到本地模式。"
      export_env "HKT_MEMORY_MODEL" "all-MiniLM-L6-v2"
    fi
    ;;
  *)
    echo "👉 已选择: Local (SentenceTransformer)"
    export_env "HKT_MEMORY_MODEL" "all-MiniLM-L6-v2"
    # Ensure force local
    export_env "HKT_MEMORY_FORCE_LOCAL" "true"
    echo "✅ 本地模式已配置 (模型: all-MiniLM-V2)。"
    ;;
esac

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
echo ""
echo "📌 AGENTS.md 调用规范（请手动复制到 AGENTS.md 中）"
echo "--------------------------------------------------------------------------------"
cat <<'EOF'
## Workflow
1. **Analyze**: Understand the user's request.
2. **Check Specs**: Read `openspec/specs/` to understand current behavior.
3. **Propose**: For non-trivial changes, create an OpenSpec proposal first.
4. **Implement**: Implement strictly according to the agreed proposal/specs.
5. **Archive**: After verification, archive the change so specs stay authoritative.
6. **Memory First**: 需要查历史结论或上下文时，优先使用 hkt-memory 查询；只有在记忆不足或需要定位具体代码时才进行工作区搜索。
7. **Memory Read**: 每轮开始前先执行 `bash .trae/skills/hkt-memory/entry.sh query --hybrid --keyword "<query>" --mmr --decay`。
8. **Memory Write**: 每轮结束后将关键结论写入 `memory/` 并执行 `bash .trae/skills/hkt-memory/entry.sh sync`。
EOF
echo "--------------------------------------------------------------------------------"
