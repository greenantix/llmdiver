#!/bin/bash

# Config
TARGET_REPO="../GMAILspambot"
AUDIT_SCRIPT="./run_llm_audit.sh"
CLAUDE_CMD="claude --dangerously-skip-permissions --continue"
AUDIT_FILE="./audits/$(basename "$TARGET_REPO")/claude.md"

# 1. Run fresh audit
echo "🔍 Running preflight audit on $TARGET_REPO..."
$AUDIT_SCRIPT "$TARGET_REPO" --fast

# 2. Launch Claude with audit preload
echo "🚀 Starting Claude Code with audit context..."
$CLAUDE_CMD <<EOF
Please load the following audit report into memory and continuously reference it while working on this project.

The audit is in Markdown format and includes TODOs, mocks, dead code, and unwired modules. Periodically recheck the file to stay up-to-date.

--- START OF AUDIT ---

$(cat "$AUDIT_FILE")

--- END OF AUDIT ---
EOF
