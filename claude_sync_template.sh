#!/bin/bash

# Exit on error
set -e

# Get dynamic paths
REPO_DIR="$(pwd)"
PROJECT_NAME="$(basename "$REPO_DIR")"
AUDIT_DIR="./audits/$PROJECT_NAME"

# Create audit directory if it doesn't exist
mkdir -p "$AUDIT_DIR"

echo "🔍 Starting LLMdiver audit for $PROJECT_NAME"

# Run quick audit first
llm-audit-quick

echo "✅ Audit complete for $PROJECT_NAME"
echo "📁 Results saved in $AUDIT_DIR"