#!/bin/bash

# Enhanced audit script for GMAILspambot
# Uses LM Studio for deep code analysis

SCRIPT_DIR="$(dirname "$0")"
PROJECT_ROOT="$SCRIPT_DIR"
LM_URL="http://localhost:1234"
TIMEOUT=600  # 10 minutes timeout

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --lm-url)
            LM_URL="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--timeout SECONDS] [--lm-url URL]"
            exit 1
            ;;
    esac
done

# Check if LM Studio is running
echo "🔍 Checking LM Studio connection..."
curl -s "$LM_URL/v1/models" > /dev/null
if [ $? -ne 0 ]; then
    echo "❌ Error: LM Studio server is not running at $LM_URL"
    echo "Please start LM Studio and ensure a model is loaded"
    echo "Or specify a different URL with --lm-url"
    exit 1
fi

# Print settings
echo "Settings:"
echo "• LM Studio URL: $LM_URL"
echo "• Analysis timeout: ${TIMEOUT}s"

echo "🔍 Starting comprehensive project audit using LM Studio..."
echo "This will perform a deep analysis of the codebase using AI."
echo "The analysis may take several minutes depending on the model and codebase size."

# Ensure output directories exist
mkdir -p "$PROJECT_ROOT/audits"

# Start the analysis with progress indicator
echo -e "\n📋 Running deep code analysis..."
timeout ${TIMEOUT} python3 "$PROJECT_ROOT/tools/deep_audit.py" \
    "$PROJECT_ROOT" \
    --timeout "$TIMEOUT" \
    --lm-url "$LM_URL" &
PID=$!

# Show active progress while analysis runs
DOTS=0
while kill -0 $PID 2>/dev/null; do
    echo -n "."
    DOTS=$((DOTS + 1))
    if [ $DOTS -eq 50 ]; then
        echo  # Start new line after 50 dots
        DOTS=0
    fi
    sleep 1
done
wait $PID
EXIT_CODE=$?

if [ $EXIT_CODE -eq 124 ]; then
    echo -e "\n❌ Analysis timed out after ${TIMEOUT} seconds!"
    echo "Try increasing timeout with --timeout option"
    exit 1
fi

if [ $? -ne 0 ]; then
    echo -e "\n❌ Analysis failed! Check the error messages above."
    exit 1
fi

# Generate summary combining the deep analysis with actionable insights
cat > "$PROJECT_ROOT/audits/executive_summary.md" << EOL
# GMAILspambot Executive Summary
Generated on: $(date "+%Y-%m-%d %H:%M:%S")

## Overview
This is an automated summary of the comprehensive project analysis. The full detailed report can be found in \`audits/deep_analysis.md\`.

## Key Insights
$(grep -A 5 "^## Layer" "$PROJECT_ROOT/audits/deep_analysis.md" | sed 's/^/- /')

## Action Items
$(grep -A 3 "### Security Concerns\|### Performance Issues" "$PROJECT_ROOT/audits/deep_analysis.md" | sed 's/^/- /')

## Recommendations
1. Review and address all security concerns identified in the full report
2. Optimize performance bottlenecks highlighted in the analysis
3. Consider implementing suggested architectural improvements
4. Update documentation based on the current codebase structure

For detailed findings and recommendations, please review the complete analysis in \`audits/deep_analysis.md\`.
EOL

echo -e "\n📑 Generating final reports..."

# Check if reports were generated
if [ ! -f "$PROJECT_ROOT/audits/deep_analysis.md" ]; then
    echo -e "\n❌ Analysis failed to generate reports!"
    exit 1
fi

echo -e "\n✅ Analysis complete!"
echo -e "\nReport generated: audits/deep_analysis.md"
echo -e "\nThe report includes:"
echo "• Executive Summary of findings"
echo "• Detailed analysis of project structure"
echo "• Core functionality assessment"
echo "• Code quality metrics"
echo "• Security & performance insights"
echo "• Actionable recommendations"
echo -e "\nReview the report for comprehensive findings and improvement suggestions."