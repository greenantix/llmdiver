#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="$SCRIPT_DIR/node_modules/.bin"
mkdir -p "$TARGET_DIR"

# Source paths
AUDIT_MAIN="$SCRIPT_DIR/run_llm_audit.sh"
AUDIT_QUICK="$SCRIPT_DIR/audit.sh"
CLAUDE_SYNC="$SCRIPT_DIR/claude_sync_template.sh"

# Fallback if script was run from another repo (like GMAILspambot)
if [[ ! -f "$AUDIT_MAIN" ]]; then
    AUDIT_MAIN="$(realpath "$SCRIPT_DIR/../LLMdiver/run_llm_audit.sh")"
    AUDIT_QUICK="$(realpath "$SCRIPT_DIR/../LLMdiver/audit.sh")"
    CLAUDE_SYNC="$(realpath "$SCRIPT_DIR/../LLMdiver/claude_sync_template.sh")"
fi

# Create symlinks
ln -sf "$AUDIT_MAIN" "$TARGET_DIR/llm-audit"
ln -sf "$AUDIT_QUICK" "$TARGET_DIR/llm-audit-quick"
ln -sf "$CLAUDE_SYNC" "$TARGET_DIR/claude-sync"

# Ensure executable
chmod +x "$AUDIT_MAIN" "$AUDIT_QUICK" "$CLAUDE_SYNC"

echo "✅ LLMdiver installed into $TARGET_DIR"
echo "Available commands:"
echo "  - llm-audit         (full deep scan)"
echo "  - llm-audit-quick   (smart fast audit)"
echo "  - claude-sync       (full auto Claude loop)"
