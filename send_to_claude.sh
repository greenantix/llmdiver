#!/bin/bash

PROJECT_NAME="GMAILspambot"
AUDIT_ROOT="/home/greenantix/AI/audits/$PROJECT_NAME"
PROMPTS_DIR="$AUDIT_ROOT/prompts"
OUTPUT_DIR="$AUDIT_ROOT/responses"

mkdir -p "$OUTPUT_DIR"

echo "🚀 Dispatching Claude tasks via CLI for $PROJECT_NAME..."

find "$PROMPTS_DIR" -type f -name 'CLAUDE_*.txt' | sort | while read -r PROMPT_FILE; do
    TASK_NAME=$(basename "$PROMPT_FILE" .txt | sed 's/^CLAUDE_//')
    OUTPUT_FILE="$OUTPUT_DIR/$TASK_NAME.response.md"

    echo "🧠 Task: $TASK_NAME"
    
    claude --dangerously-skip-permissions --continue <<EOF > "$OUTPUT_FILE"
You are Claude Code. Analyze the following task file and provide a complete implementation plan or code as needed.

=== TASK BEGIN ===
$(cat "$PROMPT_FILE")
=== TASK END ===
EOF

    echo "✅ Saved: $OUTPUT_FILE"
done

echo "📬 All tasks complete. Responses saved in: $OUTPUT_DIR"
