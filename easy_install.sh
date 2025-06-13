#!/bin/bash

# Exit on error
set -e

# Determine paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_PROJECT_DIR="$(pwd)"
TARGET_BIN_DIR="$TARGET_PROJECT_DIR/node_modules/.bin"

# Check for required tools
if ! command -v jq &> /dev/null; then
    echo "❌ Error: jq is required but not installed"
    echo "Please install jq first:"
    echo "  Ubuntu/Debian: sudo apt-get install jq"
    echo "  MacOS: brew install jq"
    exit 1
fi

# Create necessary directories
mkdir -p "$TARGET_BIN_DIR"
mkdir -p "$TARGET_PROJECT_DIR/audits"

# Source paths for LLMdiver scripts
LLMDIVER_DIR="$SCRIPT_DIR"
AUDIT_MAIN="$LLMDIVER_DIR/run_llm_audit.sh"
AUDIT_QUICK="$LLMDIVER_DIR/audit.sh"
CLAUDE_SYNC="$LLMDIVER_DIR/claude_sync_template.sh"

# Validate source files exist
for file in "$AUDIT_MAIN" "$AUDIT_QUICK" "$CLAUDE_SYNC"; do
    if [[ ! -f "$file" ]]; then
        echo "❌ Error: Required file not found: $file"
        exit 1
    fi
done

# Create symlinks
ln -sf "$AUDIT_MAIN" "$TARGET_BIN_DIR/llm-audit"
ln -sf "$AUDIT_QUICK" "$TARGET_BIN_DIR/llm-audit-quick"
ln -sf "$CLAUDE_SYNC" "$TARGET_BIN_DIR/claude-sync"

# Ensure executable permissions
chmod +x "$AUDIT_MAIN" "$AUDIT_QUICK" "$CLAUDE_SYNC"

# Create basic config if it doesn't exist
CONFIG_DIR="$TARGET_PROJECT_DIR/config"
mkdir -p "$CONFIG_DIR"

if [[ ! -f "$CONFIG_DIR/llmdiver.json" ]]; then
    cat > "$CONFIG_DIR/llmdiver.json" << EOF
{
    "llm_model": "meta-llama-3.1-8b-instruct",
    "llm_temp": 0.3,
    "llm_url": "http://127.0.0.1:1234/v1/chat/completions"
}
EOF
fi

echo "✅ LLMdiver installed successfully!"
echo "Available commands:"
echo "  - llm-audit         (full deep scan)"
echo "  - llm-audit-quick   (smart fast audit)"
echo "  - claude-sync       (full auto Claude loop)"
echo ""
echo "Configuration:"
echo "  - Config file: $CONFIG_DIR/llmdiver.json"
echo "  - Audit results will be saved in: $TARGET_PROJECT_DIR/audits"
echo ""
echo "Make sure LM Studio is running before using the audit commands!"