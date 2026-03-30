#!/bin/bash
# HKT-Memory v4 Installation Script

set -e

echo "======================================"
echo "HKT-Memory v4 Installation"
echo "======================================"
echo

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then 
    echo "Error: Python 3.8+ required, found $PYTHON_VERSION"
    exit 1
fi

echo "✓ Python version: $PYTHON_VERSION"

# Check dependencies
echo
echo "Checking dependencies..."

if python3 -c "import openai" 2>/dev/null; then
    echo "✓ openai package installed"
else
    echo "⚠ openai package not found. Installing..."
    pip3 install openai
fi

if python3 -c "import numpy" 2>/dev/null; then
    echo "✓ numpy package installed"
else
    echo "⚠ numpy package not found. Installing..."
    pip3 install numpy
fi

if python3 -c "import requests" 2>/dev/null; then
    echo "✓ requests package installed"
else
    echo "⚠ requests package not found. Installing..."
    pip3 install requests
fi

# Create memory directory
echo
echo "Creating memory directory structure..."
mkdir -p memory/{L0-Abstract/topics,L1-Overview/{sessions,projects},L2-Full/{daily,evergreen,episodes},governance,session-state}

echo "✓ Directory structure created"

# Create initial files
echo
echo "Creating initial files..."

# MEMORY.md
if [ ! -f memory/L2-Full/evergreen/MEMORY.md ]; then
cat > memory/L2-Full/evergreen/MEMORY.md << 'EOF'
# Evergreen Memory

> 永久记忆存储 - 重要规则和知识

EOF
    echo "✓ Created MEMORY.md"
fi

# LEARNINGS.md
if [ ! -f memory/governance/LEARNINGS.md ]; then
cat > memory/governance/LEARNINGS.md << 'EOF'
# Learning Records

> 记录Agent的学习过程和改进

## Records

EOF
    echo "✓ Created LEARNINGS.md"
fi

# ERRORS.md
if [ ! -f memory/governance/ERRORS.md ]; then
cat > memory/governance/ERRORS.md << 'EOF'
# Error Records

> 记录错误及其解决方案

## Records

EOF
    echo "✓ Created ERRORS.md"
fi

# Check environment variables
echo
echo "Checking environment variables..."

if [ -z "$HKT_MEMORY_API_KEY" ] && [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠ Warning: HKT_MEMORY_API_KEY or OPENAI_API_KEY not set"
    echo "  Default will use built-in Zhipu AI key"
else
    echo "✓ API key configured"
fi

echo
echo "======================================"
echo "Installation Complete!"
echo "======================================"
echo
echo "Quick start:"
echo "  python3 scripts/hkt_memory_v4.py store --content 'Test memory' --title 'Test'"
echo "  python3 scripts/hkt_memory_v4.py retrieve --query 'test'"
echo "  python3 scripts/hkt_memory_v4.py stats"
echo
echo "Optional: Set up reranking for better results"
echo "  export JINA_API_KEY='your-jina-key'"
echo "  # or"
echo "  export SILICONFLOW_API_KEY='your-siliconflow-key'"
