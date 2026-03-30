#!/bin/bash
# HKT-Memory v4 Deployment Script
# Deploys v4 to replace existing hkt-memory

set -e

echo "======================================"
echo "HKT-Memory v4 Deployment"
echo "======================================"
echo

# Configuration
SOURCE_DIR=".trae/skift-memory-v4"
TARGET_DIR=".trae/skills/hkt-memory"
BACKUP_DIR="backups/hkt-memory-$(date +%Y%m%d-%H%M%S)"

echo "Source: $SOURCE_DIR"
echo "Target: $TARGET_DIR"
echo "Backup: $BACKUP_DIR"
echo

# Confirm
read -p "Continue with deployment? [y/N]: " confirm
if [[ $confirm != "y" && $confirm != "Y" ]]; then
    echo "Deployment cancelled."
    exit 1
fi

# Step 1: Backup existing installation
echo
echo "Step 1: Backing up existing installation..."
mkdir -p "$BACKUP_DIR"

if [ -d "$TARGET_DIR" ]; then
    cp -r "$TARGET_DIR"/* "$BACKUP_DIR"/ 2>/dev/null || true
    echo "✓ Backup created at $BACKUP_DIR"
else
    echo "! No existing installation to backup"
fi

# Step 2: Validate v4 installation
echo
echo "Step 2: Validating v4 installation..."

if [ ! -d "$SOURCE_DIR" ]; then
    echo "✗ Source directory not found: $SOURCE_DIR"
    exit 1
fi

if [ ! -f "$SOURCE_DIR/scripts/hkt_memory_v4.py" ]; then
    echo "✗ Main script not found"
    exit 1
fi

if [ ! -f "$SOURCE_DIR/layers/l0_abstract.py" ]; then
    echo "✗ Layer modules not found"
    exit 1
fi

echo "✓ Validation passed"

# Step 3: Run tests
echo
echo "Step 3: Running tests..."

cd "$SOURCE_DIR"

if python3 tests/test_layers.py 2>&1 | grep -q "All tests passed"; then
    echo "✓ Layer tests passed"
else
    echo "✗ Layer tests failed"
    exit 1
fi

if python3 tests/test_extraction.py 2>&1 | grep -q "All tests passed"; then
    echo "✓ Extraction tests passed"
else
    echo "✗ Extraction tests failed"
    exit 1
fi

cd - > /dev/null

# Step 4: Deploy v4
echo
echo "Step 4: Deploying v4..."

# Create target directory
mkdir -p "$TARGET_DIR"

# Copy new files
cp -r "$SOURCE_DIR"/* "$TARGET_DIR"/

# Create compatibility symlink/alias for old commands
mkdir -p "$TARGET_DIR/scripts"
ln -sf "hkt_memory_v4.py" "$TARGET_DIR/scripts/hkt_memory.py" 2>/dev/null || true

echo "✓ Files deployed"

# Step 5: Update SKILL.md
echo
echo "Step 5: Updating SKILL.md..."

if [ -f "$SOURCE_DIR/SKILL.md" ]; then
    cp "$SOURCE_DIR/SKILL.md" "$TARGET_DIR/SKILL.md"
    echo "✓ SKILL.md updated"
fi

# Step 6: Run migration if needed
echo
echo "Step 6: Running migration..."

if [ -f "$TARGET_DIR/scripts/migrate_from_v3.py" ]; then
    cd "$TARGET_DIR"
    python3 scripts/migrate_from_v3.py --auto || echo "! Migration may need manual intervention"
    cd - > /dev/null
fi

# Step 7: Verify deployment
echo
echo "Step 7: Verifying deployment..."

if python3 "$TARGET_DIR/scripts/hkt_memory_v4.py" stats > /dev/null 2>&1; then
    echo "✓ Deployment verified"
else
    echo "✗ Verification failed - checking..."
    python3 "$TARGET_DIR/scripts/hkt_memory_v4.py" stats
fi

# Step 8: Update AGENTS.md reference
echo
echo "Step 8: Updating AGENTS.md references..."

# Check if AGENTS.md exists and update references
if [ -f "AGENTS.md" ]; then
    # Create a backup
    cp AGENTS.md "AGENTS.md.bak.$(date +%Y%m%d)"
    
    # Update references (if using sed)
    sed -i.bak 's|skift-memory-v4|skills/hkt-memory|g' AGENTS.md 2>/dev/null || true
    
    echo "✓ AGENTS.md updated (backup created)"
fi

# Summary
echo
echo "======================================"
echo "Deployment Complete!"
echo "======================================"
echo
echo "Summary:"
echo "  - Backup: $BACKUP_DIR"
echo "  - New version: v4.0.0"
echo "  - Location: $TARGET_DIR"
echo
echo "New features available:"
echo "  - MCP Server tools (9 tools)"
echo "  - Auto-Capture/Auto-Recall"
echo "  - Layered storage (L0/L1/L2)"
echo "  - Weibull Decay lifecycle"
echo "  - Smart Extraction (6 categories)"
echo
echo "Quick test:"
echo "  python3 $TARGET_DIR/scripts/hkt_memory_v4.py stats"
echo
echo "To start MCP server:"
echo "  python3 $TARGET_DIR/mcp/server.py --mode http --port 8000"
