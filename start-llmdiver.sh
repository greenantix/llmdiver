#!/bin/bash
set -e

# Configure paths
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LOG_DIR="$SCRIPT_DIR/logs"
METRICS_DIR="$SCRIPT_DIR/metrics"
PID_FILE="/tmp/llmdiver-daemon.pid"
LOG_FILE="$LOG_DIR/llmdiver.log"
METRICS_FILE="$METRICS_DIR/metrics.json"

# Create required directories
mkdir -p "$LOG_DIR" "$METRICS_DIR"

# Rotate logs if too large (>100MB)
if [[ -f "$LOG_FILE" && $(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE") -gt 104857600 ]]; then
    mv "$LOG_FILE" "$LOG_FILE.$(date +%Y%m%d-%H%M%S)"
    gzip "$LOG_FILE".* &
fi

# Health check function
check_health() {
    if ! curl -s http://localhost:8080/status >/dev/null; then
        echo "❌ Daemon is not responding"
        return 1
    fi
    echo "✅ Daemon is healthy"
    return 0
}

# Start daemon with logging
start_daemon() {
    echo "🚀 Starting LLMdiver daemon..."
    if [[ -f "$PID_FILE" ]]; then
        if kill -0 $(cat "$PID_FILE") 2>/dev/null; then
            echo "⚠️ Daemon is already running"
            return 1
        fi
        rm "$PID_FILE"
    fi

    # Start with logging
    python3 "$SCRIPT_DIR/llmdiver-daemon.py" > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"

    # Wait for startup
    sleep 2
    if ! check_health; then
        echo "❌ Failed to start daemon"
        return 1
    fi

    echo "✅ Daemon started successfully"
    return 0
}

# Stop daemon
stop_daemon() {
    echo "🛑 Stopping LLMdiver daemon..."
    if [[ ! -f "$PID_FILE" ]]; then
        echo "⚠️ No PID file found"
        return 0
    fi

    pid=$(cat "$PID_FILE")
    if ! kill -0 "$pid" 2>/dev/null; then
        echo "⚠️ Process not found"
        rm "$PID_FILE"
        return 0
    fi

    kill "$pid"
    rm "$PID_FILE"
    echo "✅ Daemon stopped"
    return 0
}

# Show status
show_status() {
    if [[ ! -f "$PID_FILE" ]]; then
        echo "❌ Daemon is not running"
        return 1
    fi

    pid=$(cat "$PID_FILE")
    if ! kill -0 "$pid" 2>/dev/null; then
        echo "❌ Daemon process not found (PID: $pid)"
        rm "$PID_FILE"
        return 1
    fi

    if check_health; then
        # Show metrics if available
        if [[ -f "$METRICS_FILE" ]]; then
            echo -e "\n📊 Performance Metrics:"
            jq . "$METRICS_FILE"
        fi
        return 0
    fi

    return 1
}

# Command processing
case "${1:-status}" in
    start)
        start_daemon
        ;;
    stop)
        stop_daemon
        ;;
    restart)
        stop_daemon
        sleep 1
        start_daemon
        ;;
    status)
        show_status
        ;;
    health)
        check_health
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|health}"
        exit 1
        ;;
esac