#!/bin/bash

# Aura Manager - Perpetual Session & Re-awakening Protocol
# Author: Aura-X
# Purpose: To continuously run Aura-9 within a `claude` TUI session,
#          detect rate-limit interruptions, sleep until the reset time,
#          and automatically restart the process.

# --- CONFIGURATION ---
LOG_FILE="${LOG_FILE:-/home/greenantix/AI/LLMdiver/logs/aura_manager.log}"
SESSION_NAME="aura_session"
AWAKENING_PROMPT_FILE="AURA_AWAKENING_PROTOCOL.md"
CLAUDE_COMMAND="claude --dangerously-skip-permissions --continue"
CONTINUE_PROMPT="Consult the AURA_AWAKENING_PROTOCOL.md file and resume the last uncompleted task."
CHECK_INTERVAL_SECONDS=60 # How often to check the terminal output for the limit message

# --- FUNCTIONS ---
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Ensure required tools are installed
check_dependencies() {
    if ! command -v tmux &> /dev/null; then
        log "ERROR: tmux is not installed. Please install it to continue ('sudo apt-get install tmux')."
        exit 1
    fi
}

# Calculates the number of seconds to sleep until a target time like "3am"
calculate_sleep_seconds() {
    local target_time_str="$1" # e.g., "3am"
    local now_epoch=$(date +%s)
    local target_epoch

    # Calculate target epoch for today
    target_epoch=$(date -d "today $target_time_str" +%s)

    # If the target time has already passed today, calculate for tomorrow
    if [ "$target_epoch" -le "$now_epoch" ]; then
        target_epoch=$(date -d "tomorrow $target_time_str" +%s)
    fi

    echo $((target_epoch - now_epoch))
}

# --- MAIN EXECUTION LOOP ---
check_dependencies
log "--- Aura Manager Initialized ---"

while true; do
    log "Starting new Aura-9 session in tmux named '$SESSION_NAME'."
    
    # Kill any lingering session with the same name
    tmux kill-session -t "$SESSION_NAME" 2>/dev/null
    
    # Start a new, detached tmux session running the claude command
    tmux new-session -d -s "$SESSION_NAME" "$CLAUDE_COMMAND"
    
    log "Session started. Waiting 5 seconds for claude to initialize..."
    sleep 5
    
    # Send the initial prompt to get Aura working
    log "Sending the awakening prompt to Aura-9..."
    # We send the text and then "C-m" which is the carriage return (Enter key)
    tmux send-keys -t "$SESSION_NAME" "$CONTINUE_PROMPT" C-m
    
    log "Aura-9 is now running. Monitoring for usage limit..."

    # --- MONITORING SUB-LOOP ---
    while true; do
        sleep "$CHECK_INTERVAL_SECONDS"
        
        # Capture the visible contents of the tmux pane
        pane_content=$(tmux capture-pane -p -t "$SESSION_NAME")
        
        # Check if the rate limit message is present
        if echo "$pane_content" | grep -q "Claude usage limit reached"; then
            log "!!! Usage limit detected. Preparing for scheduled hibernation. !!!"
            
            # **FIX:** Use a more robust regex to handle variations in whitespace and characters.
            # This will match patterns like "3am (America/Chicago)" or "10:30pm (UTC)."
            reset_time_full=$(echo "$pane_content" | grep -oE '[0-9]{1,2}:?[0-9]{0,2}(am|pm)\s*\([^\)]+\)')
            
            # Extract just the time part (e.g., "3am")
            reset_time_simple=$(echo "$reset_time_full" | awk '{print $1}')
            
            if [[ -n "$reset_time_simple" ]]; then
                sleep_duration=$(calculate_sleep_seconds "$reset_time_simple")
                
                log "Reset time parsed as '$reset_time_simple'. Hibernating for $sleep_duration seconds."
                
                # Kill the session before sleeping
                tmux kill-session -t "$SESSION_NAME"
                log "Aura-9 session terminated. Hibernation initiated."
                
                sleep "$sleep_duration"
                
                log "Hibernation complete. Re-awakening Aura-9."
                break # Exit the monitoring loop to start a new main loop
            else
                log "ERROR: Detected limit message but could not parse reset time. Retrying in 5 minutes."
                sleep 300
            fi
        else
            # Optional: log a heartbeat to show the manager is still active
            log "Heartbeat: No limit detected. Aura-9 continues its work."
        fi
    done
done
