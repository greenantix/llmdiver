#!/bin/bash

# LLMdiver: AI-powered Code Audit Tool
# Analyzes project structure and generates actionable insights using LM Studio

set -e

# Check for required tools
if ! command -v jq &> /dev/null; then
    echo "❌ Error: jq is required but not installed"
    echo "Please install jq first:"
    echo "  Ubuntu/Debian: sudo apt-get install jq"
    echo "  MacOS: brew install jq"
    exit 1
fi

# Parse command line flags
# Initialize flags
DRY_RUN=0
FAST_MODE=0
DEEP_MODE=0
SHOW_PAYLOAD=0

# Initialize variables
REPO_PATH=""

print_usage() {
    echo "Usage: $0 [OPTIONS] [path/to/repo]"
    echo
    echo "Options:"
    echo "  --dry           Dry run - only generate repo summary"
    echo "  --fast          Fast mode - minimal summary + quick LLM pass"
    echo "  --deep          Deep mode - full repo + architectural audit"
    echo "  --show-payload  Show LLM payload without running"
    echo "  -h, --help      Show this help message"
    echo
    echo "If no path is specified, the current directory will be used."
    exit 1
}

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --dry) DRY_RUN=1 ;;
        --fast) FAST_MODE=1 ;;
        --deep) DEEP_MODE=1 ;;
        --show-payload) SHOW_PAYLOAD=1 ;;
        -h|--help) print_usage ;;
        --*) echo "❌ Unknown option: $1"; print_usage ;;
        *)
            if [[ -n "$REPO_PATH" ]]; then
                echo "❌ Multiple paths specified: $REPO_PATH and $1"
                print_usage
            fi
            REPO_PATH="$(realpath "$1")" ;;
    esac
    shift
done

# Fallback to current directory if no path specified
[[ -z "$REPO_PATH" ]] && REPO_PATH="$(pwd)"

if [[ ! -d "$REPO_PATH" ]]; then
    echo "❌ Error: Target directory not found: $REPO_PATH"
    echo "Usage: $0 [path/to/repo] [--dry] [--fast] [--deep]"
    exit 1
fi

# Setup directory structure
PROJECT_NAME=$(basename "$REPO_PATH")
BASE_DIR="$(dirname "$REPO_PATH")"
AUDIT_DIR="$BASE_DIR/audits/$PROJECT_NAME"
TASKS_DIR="$AUDIT_DIR/tasks"
PROMPTS_DIR="$AUDIT_DIR/prompts"
LOGS_DIR="$AUDIT_DIR/logs"
TMP_DIR="$AUDIT_DIR/.tmp"

# File paths
PROMPT_FILE="$PROMPTS_DIR/audit_plan.txt"
AUDIT_OUT="$AUDIT_DIR/full_audit.md"
PHASE4_LOG="$LOGS_DIR/${PROJECT_NAME}-phase4.md"
MIXED_FILE="$AUDIT_DIR/_repomix_summary.txt"
DEEP_AUDIT_FILE="$AUDIT_DIR/full_deep_audit.md"
CLAUDE_FILE="$AUDIT_DIR/claude.md"

# Create directory structure
# Create required directories
for dir in "$AUDIT_DIR" "$TASKS_DIR" "$PROMPTS_DIR" "$LOGS_DIR" "$TMP_DIR"; do
    mkdir -p "$dir" || {
        echo "❌ Failed to create directory: $dir"
        exit 1
    }
done
rm -rf "$TMP_DIR"/*  # Clean temp files

# LM Studio settings
export LLM_MODEL=${LLM_MODEL:-"meta-llama-3.1-8b-instruct"}
export LLM_TEMP=${LLM_TEMP:-0.3}
export LLM_URL=${LLM_URL:-"http://127.0.0.1:1234/v1/chat/completions"}


# Summary output path
SUMMARY_FILE="$AUDIT_DIR/_repomix_summary.txt"

# Log mode
if [[ $DRY_RUN -eq 1 ]]; then
    echo "🔍 Dry run - will only generate repo summary"
elif [[ $FAST_MODE -eq 1 ]]; then
    echo "⚡ Fast mode enabled - minimal summary + fast LLM pass"
elif [[ $DEEP_MODE -eq 1 ]]; then
    echo "🧠 Deep mode enabled - full repo + architectural audit"
else
    echo "🔍 Standard audit - full summary + LLM analysis"
fi

# Create gitignore backup and LLMdiver-specific ignore
if [[ -f "$REPO_PATH/.gitignore" ]]; then
    cp "$REPO_PATH/.gitignore" "$REPO_PATH/.gitignore.backup"
fi

cat > "$REPO_PATH/.gitignore.llmdiver" << EOF
# LLMdiver Analysis - Include everything except:
node_modules/
dist/
build/
venv/
__pycache__/
.git/
site-packages/
*.log
*.tmp
EOF

# Generate repo summary using repomix
echo "🔀 Generating repo mix with repomix..." > "$SUMMARY_FILE"
repomix "$REPO_PATH" \
  --output "$SUMMARY_FILE" \
  --style markdown \
  --compress \
  --remove-comments \
  --remove-empty-lines \
  --ignore "*.md" \
  --config-ignore ".gitignore.llmdiver" \
  --include "*.py,*.js,*.ts,*.jsx,*.tsx,*.sh" \
  --token-count-encoding cl100k_base

# Restore original gitignore
if [[ -f "$REPO_PATH/.gitignore.backup" ]]; then
    mv "$REPO_PATH/.gitignore.backup" "$REPO_PATH/.gitignore"
fi

echo "✅ Repomix summary created: $SUMMARY_FILE"

# Exit early on dry run
if [[ $DRY_RUN -eq 1 ]]; then
    exit 0
fi

# Show payload if requested without running LM Studio
if [[ $SHOW_PAYLOAD -eq 1 ]]; then
    echo "📋 Generating LM Studio payload preview..."
    
    generate_repomix
    user_prompt=$(cat "$MIXED_FILE" | jq -Rs .)
    system_prompt="You are a world-class code auditor. Analyze the following condensed repo summary and return issues grouped by TODOs, mocks/stubs, dead code, and unwired components."
    escaped_system_prompt=$(echo "$system_prompt" | jq -Rs .)
    
    echo "🔍 Payload that would be sent to LM Studio:"
    cat <<EOF | jq .
{
  "model": "$LLM_MODEL",
  "messages": [
    { "role": "system", "content": ${escaped_system_prompt} },
    { "role": "user", "content": ${user_prompt} }
  ],
  "temperature": $LLM_TEMP,
  "max_tokens": 4096,
  "stream": false
}
EOF
    exit 0
fi

# Send summary to LM Studio for analysis
function send_to_lm_studio() {
  local input_file="$1"
  local output_file="$2"
  local model="${LLM_MODEL:-meta-llama-3.1-8b-instruct}"
  local temperature="${LLM_TEMP:-0.3}"
  local lm_url="${LLM_URL:-http://127.0.0.1:1234/v1/chat/completions}"
  local system_prompt
  if [[ $DEEP_MODE -eq 1 ]]; then
    system_prompt="You are an advanced software architect AI. Your job is to perform a full architectural, functional, and structural audit of the provided code summary.

Based on the summary, identify:
- Unused or redundant files, dead code, and config bloat
- Mismatched or missing module connections
- Conflicting responsibilities or naming patterns
- Orphaned logic, test coverage gaps, inconsistent structure
- Architectural violations or breakdowns in cohesion

Your goal is to help a code-repair assistant (Claude Code) intelligently fix the project structure.

Format output as:
## High-Level Assessment
<overview>

## Actionable Structural Issues
<bulleted list>

## Suggested Refactor Plans
<sections with headings for each problem>

## Claude Code Subtask Guidance
<list of Claude prompt suggestions to delegate fixes>"
  else
    system_prompt="You are a world-class code auditor. Analyze the following condensed repo summary and return issues grouped by TODOs, mocks/stubs, dead code, and unwired components."
  fi

  # Escape content for JSON
  local user_prompt
  user_prompt=$(cat "$input_file" | jq -Rs .)
  local escaped_system_prompt
  escaped_system_prompt=$(echo "$system_prompt" | jq -Rs .)

  echo "📤 Sending repomix summary to LM Studio..."
  local payload
  payload=$(cat <<EOF
{
  "model": "$model",
  "messages": [
    { "role": "system", "content": ${escaped_system_prompt} },
    { "role": "user", "content": ${user_prompt} }
  ],
  "temperature": $temperature,
  "max_tokens": 4096,
  "stream": false
}
EOF
)

  # Send request with longer timeout for deep mode
  local timeout=30
  [[ $DEEP_MODE -eq 1 ]] && timeout=120
  
  # Check if LM Studio is running
  if ! curl -sf "$lm_url" >/dev/null 2>&1; then
    echo "❌ Error: LM Studio API not accessible at $lm_url"
    echo "Make sure LM Studio is running and API is enabled"
    exit 1
  fi

  # Send request with error handling and timeout
  response=$(curl -sS --max-time $timeout "$lm_url" \
    -H "Content-Type: application/json" \
    -d "$payload")
  
  if [[ $? -ne 0 ]]; then
    echo "❌ Error: Failed to connect to LM Studio"
    echo "Check if the service is running and accessible"
    exit 1
  fi

  # Parse response and check for errors
  if ! echo "$response" | jq -e '.choices[0].message.content' >/dev/null 2>&1; then
    echo "❌ Error: Invalid response from LM Studio"
    echo "Raw response: $response"
    exit 1
  fi

  # Extract content and save to file
  echo "$response" | jq -r '.choices[0].message.content' > "$output_file"

  if [[ -s "$output_file" ]]; then
    if [[ $DEEP_MODE -eq 1 ]]; then
      echo "✅ Deep architectural audit complete: $output_file"
      echo "📄 To view the report, run: less $output_file"
    else
      echo "✅ LM Studio responded. Output saved to: $output_file"
    fi
  else
    echo "❌ LM Studio returned empty response. Check the summary or model settings."
  fi
}

echo "🔎 Extracting codebase signals..."

# Generate repo summary for analysis
# Phase 5 Smart Repo Analysis with repomix
generate_repomix() {
    # Create LLMdiver-specific gitignore if not already created
    if [[ ! -f "$REPO_PATH/.gitignore.llmdiver" ]]; then
        cat > "$REPO_PATH/.gitignore.llmdiver" << EOF
# LLMdiver Analysis - Include everything except:
node_modules/
dist/
build/
venv/
__pycache__/
.git/
site-packages/
*.log
*.tmp
EOF
    fi

    echo "🔀 Generating repo mix with repomix..." > "$MIXED_FILE"
    repomix "$REPO_PATH" \
        --output "$MIXED_FILE" \
        --style markdown \
        --compress \
        --remove-comments \
        --remove-empty-lines \
        --ignore "*.md" \
        --config-ignore ".gitignore.llmdiver" \
        --include "*.py,*.js,*.ts,*.jsx,*.tsx,*.sh" \
        --token-count-encoding cl100k_base

    local line_count=$(wc -l < "$MIXED_FILE")
    echo -e "\n✅ Repomix summary created ($line_count lines)\n" >> "$MIXED_FILE"

    # Preview in fast mode
    if [[ $FAST_MODE -eq 1 ]]; then
        less "$MIXED_FILE"
    fi
}

generate_repomix

# Create or use default audit plan
if [[ ! -f "$PROMPT_FILE" ]]; then
    echo "ℹ️ No audit plan found, using default..."
    mkdir -p "$PROMPTS_DIR" || {
        echo "❌ Failed to create prompts directory: $PROMPTS_DIR"
        exit 1
    }
    cat > "$PROMPT_FILE" << 'EOF'
You are an expert software auditor analyzing a codebase.
Focus on:
1. TODOs and tech debt that need addressing
2. Dead or duplicate code that can be removed
3. Mock/stub implementations that should be replaced
4. Unwired or orphaned components
5. Architectural improvements and refactoring opportunities

Format your response as markdown sections:
## TODO Issues
## Dead Code
## Mocks and Stubs
## Duplicate Code
## Unwired Components
EOF
fi

START_TIME=$(date +%s)

echo "🤖 Running LM Studio analysis..."
if [[ $DEEP_MODE -eq 1 ]]; then
  echo "Using deep architectural analysis mode (timeout: 120s)..."
  send_to_lm_studio "$MIXED_FILE" "$DEEP_AUDIT_FILE"
else
  send_to_lm_studio "$MIXED_FILE" "$AUDIT_OUT"
fi

END_TIME=$(date +%s)
DURATION=$((END_TIME-START_TIME))

echo "📑 Splitting findings..."

# Split findings into task files with YAML headers
split_section() {
    local section="$1"
    local file="$2"
    local header="$3"
    awk "/^## $section/{flag=1;next}/^## /{flag=0}flag" "$AUDIT_OUT" | \
        sed '/^\s*$/d' | \
        awk -v h="$header" 'BEGIN{print h "\n"} {print}' > "$file"
}

declare -A HEADERS
HEADERS["TODO Issues"]="---
status: pending
priority: high
assignee: claude_code
---"

HEADERS["Dead Code"]="---
status: pending
priority: medium
assignee: claude_code
---"

HEADERS["Mocks and Stubs"]="---
status: pending
priority: medium
assignee: claude_code
---"

HEADERS["Duplicate Code"]="---
status: pending
priority: low
assignee: claude_code
---"

HEADERS["Unwired Components"]="---
status: pending
priority: medium
assignee: claude_code
---"

for section in "TODO Issues" "Dead Code" "Mocks and Stubs" "Duplicate Code" "Unwired Components"; do
    outfile="$TASKS_DIR/${section,,}.md" # Convert to lowercase
    outfile="${outfile// /_}" # Replace spaces with underscores
    split_section "$section" "$outfile" "${HEADERS[$section]}"
done

echo "📝 Regenerating prompts..."

# Regenerate Claude prompt files
gen_claude_prompt() {
    local section="$1"
    local src="$2"
    local out="$3"
    local intro="$4"
    {
        echo "$intro"
        echo -e "\n## Audit Section: $section\n"
        awk 'f;/^---/{c++}c==2{f=1}' "$src" | sed '/^\s*$/d'
    } > "$out"
}

declare -A PROMPTS
PROMPTS["TODO Issues"]="You are Claude Code. Based on the findings below, perform the following:

- Fix the listed issues in-place
- Leave comments where changes are made
- Do not delete anything unless clearly marked dead/unreachable"

PROMPTS["Dead Code"]="You are Claude Code. Review the following dead code candidates and recommend safe removals or refactors. Only delete if clearly unreachable."

PROMPTS["Mocks and Stubs"]="You are Claude Code. Review the following mocks and stubs. Replace with real implementations where possible."

PROMPTS["Duplicate Code"]="You are Claude Code. Review the following duplicate code findings. Refactor to remove redundancy."

PROMPTS["Unwired Components"]="You are Claude Code. Review the following unwired components. Integrate or remove as appropriate."

for section in "TODO Issues" "Dead Code" "Mocks and Stubs" "Duplicate Code" "Unwired Components"; do
    infile="$TASKS_DIR/${section,,}.md"
    infile="${infile// /_}"
    outfile="$PROMPTS_DIR/CLAUDE_${section,,}.txt"
    outfile="${outfile// /_}"
    gen_claude_prompt "$section" "$infile" "$outfile" "${PROMPTS[$section]}"
done

# Write final summary
# Ensure log directory exists
mkdir -p "$(dirname "$PHASE4_LOG")" || {
    echo "❌ Failed to create log directory: $(dirname "$PHASE4_LOG")"
    exit 1
}

# Generate log with proper escaping
cat > "$PHASE4_LOG" << 'EOF'
# Phase 4 Setup Complete

## Run Details
- Time: $(date)
- Duration: ${DURATION}s
- Model: $LLM_MODEL
- Temperature: $LLM_TEMP
- Est. Input Tokens: ~$(wc -c < "$MIXED_FILE") chars/4
- Working Directory: $TMP_DIR

## Files Created/Updated
- $AUDIT_OUT (Full LM Studio analysis)
- $TASKS_DIR/todo_issues.md
- $TASKS_DIR/dead_code.md
- $TASKS_DIR/mocks_and_stubs.md
- $TASKS_DIR/duplicate_code.md
- $TASKS_DIR/unwired_components.md
- $PROMPTS_DIR/CLAUDE_todo_issues.txt
- $PROMPTS_DIR/CLAUDE_dead_code.txt
- $PROMPTS_DIR/CLAUDE_mocks_and_stubs.txt
- $PROMPTS_DIR/CLAUDE_duplicate_code.txt
- $PROMPTS_DIR/CLAUDE_unwired_components.txt
- $PHASE4_LOG (This summary)

## How to Run
\`\`\`sh
# Optional: Configure LM Studio
export LLM_MODEL="meta-llama-3.1-8b-instruct"
export LLM_TEMP=0.2

# Run audit:
./run_llm_audit.sh

# Show payload without running:
./run_llm_audit.sh --show-payload

# Or dry run to see payload:
./run_llm_audit.sh --dry

# Check task status:
bash audits/show_task_status.sh
\`\`\`

## What Was Done
1. Generated smart repo summary with repomix
   - Limited scan to high-signal patterns
   - Added file structure overview
   - Used intelligent output limits (50 lines per section)
2. Processed through LM Studio
   - Standard mode: Issues and tasks analysis
   - Deep mode: Full architectural assessment (120s timeout)
3. Split findings into task files
4. Generated task prompts
5. Created detailed summary reports

## Next Steps
1. Review the audit in $AUDIT_OUT
2. Use \`send_to_claude.sh\` with generated prompts
3. Track progress in task files
EOF

# Generate Claude-ready format
if [[ -f "$AUDIT_OUT" ]]; then
    # Create directory if needed
    mkdir -p "$(dirname "$CLAUDE_FILE")" || {
        echo "❌ Failed to create directory for Claude tasks: $(dirname "$CLAUDE_FILE")"
        exit 1
    }
    
    # Generate with proper escaping and error checking
    {
        cat << EOF
---
project: ${PROJECT_NAME//\'/\'\\\'\'}
type: code-audit
status: pending
---

# Code Audit Tasks

EOF
        # Extract and transform sections, checking for errors
        if ! awk '/^## /{p=1}p' "$AUDIT_OUT" | sed 's/^##/###/'; then
            echo "❌ Failed to process audit sections"
            exit 1
        fi
    } > "$CLAUDE_FILE"
    
    if [[ -s "$CLAUDE_FILE" ]]; then
        echo "📋 Claude task list generated: $CLAUDE_FILE"
    else
        echo "⚠️ Warning: Generated Claude task list is empty"
    fi
fi

# Exit in dry run mode
if [[ $DRY_RUN -eq 1 ]]; then
    echo "✨ Summary generated at: $MIXED_FILE"
    exit 0
fi

echo "✅ Audit complete for $PROJECT_NAME"
echo "📊 Summary: $PHASE4_LOG"
echo "📝 Claude tasks: $CLAUDE_FILE"