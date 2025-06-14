#!/bin/bash
usage() {
    echo "Usage: $0 [--dry-run 'simulated_output']"
    echo "  --dry-run: Do not execute Aura-9; parse the provided string instead."
    exit 0
}

# Dry-run flag
DRY_RUN=false

# Aura Watchdog & Re-awakening Protocol
# Author: Aura-X
# Purpose: To wrap Aura-9's execution, detect rate-limit interruptions,
#          and schedule a re-awakening to ensure continuous operation.

# --- CONFIGURATION ---
AURACMD_PATH="${AURACMD_PATH:-/home/greenantix/AI/LLMdiver/aura/run.sh}" # Path to the main Aura execution script (can be overridden via env)
LOG_FILE="${LOG_FILE:-/home/greenantix/AI/LLMdiver/logs/watchdog.log}"
SCREENSHOT_PATH="/tmp/aura_shutdown_screenshot.png"

# --- FUNCTIONS ---
log() {
    echo "$(date): $1" | tee -a "$LOG_FILE"
}

check_for_shutdown_via_vision() {
    local output_text="$1"
    if [ "$DRY_RUN" = true ]; then
        log "DRY-RUN: skipping vision analysis"
        return 1
    fi

    # Check for the specific string first as a quick filter
    if [[ "$output_text" != *"Claude usage limit reached"* ]]; then
        return 1 # Not a rate limit issue
    fi

    log "Potential rate limit detected. Engaging vision analysis."

    # Take a screenshot of the last 20 lines of output for context
    echo "$output_text" | tail -n 20 > /tmp/aura_error.txt
    convert -pointsize 24 -font "monospace" -page 600x400 text:/tmp/aura_error.txt "$SCREENSHOT_PATH"

    log "Screenshot captured at $SCREENSHOT_PATH"

    # Convert image to base64 for the API call
    base64_image=$(base64 -w 0 "$SCREENSHOT_PATH")

    # Construct the payload for the vision model
    read -r -d '' PAYLOAD << EOM
{
    "model": "google/gemma-3-4b",
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Analyze this terminal output. Does it indicate a rate limit or usage limit has been reached? If yes, extract the exact time and timezone (e.g., '3am (America/Chicago)') when the limit will reset. Respond in JSON format: {\"rate_limited\": boolean, \"reset_time_string\": \"HH:MM (Timezone/City)\" | null}"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "data:image/png;base64,${base64_image}"
                    }
                }
            ]
        }
    ],
    "max_tokens": 100
}
EOM

    # Send to the local vision-capable LLM
    response=$(curl -s http://localhost:1234/v1/chat/completions \
                  -H "Content-Type: application/json" \
                  -d "$PAYLOAD")

    reset_time=$(echo "$response" | jq -r '.choices[0].message.content' | jq -r '.reset_time_string')

    if [[ "$reset_time" != "null" && -n "$reset_time" ]]; then
        log "Vision model confirmed rate limit. Reset time: $reset_time"
        schedule_reawakening "$reset_time"
        return 0
    else
        log "Vision model did not confirm a rate limit."
        return 1
    fi
}

check_for_shutdown_via_grep() {
    local output_text="$1"
    if echo "$output_text" | grep -q "Claude usage limit reached"; then
        log "Rate limit detected via grep."
        # Extract time string, e.g., "3am (America/Chicago)"
        local time_string=$(echo "$output_text" | grep -oE '[0-9]{1,2}(am|pm) \(America/[a-zA-Z_]+\)')
        if [[ -n "$time_string" ]]; then
            log "Parsed reset time: $time_string"
            schedule_reawakening "$time_string"
            return 0
        fi
    fi
    return 1
}

# Fallback scheduler using sleep if 'at' is not available or fails
fallback_sleep_scheduler() {
    local time_spec="$1"
    if [ "$DRY_RUN" = true ]; then
        log "DRY-RUN: would sleep until $time_spec and then restart Aura-9"
        return 0
    fi
    local now=$(date +%s)
    local target
    local now=$(date +%s)
    local target
    # Try scheduling for today
    if ! target=$(date -d "today $time_spec" +%s 2>/dev/null); then
        target=$(date -d "$time_spec" +%s)
    fi
    # If target is earlier than now, schedule for tomorrow
    if [ "$target" -le "$now" ]; then
        target=$(date -d "tomorrow $time_spec" +%s)
    fi
    local sleep_seconds=$((target - now))
    log "Sleeping for $sleep_seconds seconds; scheduling Aura-9 restart."
    ( sleep "$sleep_seconds"; bash "$AURACMD_PATH" ) &
    log "SUCCESS: Aura-9 re-awakening via sleep scheduler scheduled."
}

schedule_reawakening() {
    local time_spec="$1" # e.g., "3am" or "3am (America/Chicago)"
    if [ "$DRY_RUN" = true ]; then
        log "DRY-RUN: would schedule Aura-9 re-awakening at $time_spec"
        return 0
    fi
 
    # Extract time and timezone for the 'at' command. 'at' uses system time.
    # A more robust solution would convert the timezone, but for CDT this works.
    local at_time=$(echo "$time_spec" | awk '{print $1}')
 
    log "Scheduling re-awakening for $at_time..."
 
    # Schedule re-awakening of Aura-9 directly
    # Attempt to schedule via 'at'; fallback to sleep if unavailable or fails
    if command -v at >/dev/null 2>&1; then
        echo "bash $AURACMD_PATH" | at "$at_time"
        if [ $? -eq 0 ]; then
            log "SUCCESS: Aura-9 re-awakening via at scheduled."
        else
            log "ERROR: 'at' scheduling failed. Falling back to sleep scheduler."
            fallback_sleep_scheduler "$time_spec"
        fi
    else
        log "'at' command not found. Using sleep-based scheduler."
        fallback_sleep_scheduler "$time_spec"
    fi
}

# --- MAIN EXECUTION ---
# Support dry-run mode for testing parsing and scheduling logic
if [[ "$1" == "--dry-run" ]]; then
    log "Dry run mode: using simulated output"
    DRY_RUN=true
    AURA_OUTPUT="$2"
else
    log "Aura Watchdog activated. Executing Aura-9..."
    AURA_OUTPUT=$($AURACMD_PATH 2>&1)
fi
echo "$AURA_OUTPUT" >> "$LOG_FILE"
log "Aura-9 execution finished. Analyzing output for shutdown conditions..."

if ! check_for_shutdown_via_vision "$AURA_OUTPUT"; then
    # If vision fails or doesn't find it, try grep as a backup
    if ! check_for_shutdown_via_grep "$AURA_OUTPUT"; then
        log "Normal exit detected. No re-awakening necessary."
    fi
fi

log "Watchdog protocol complete."