#!/bin/bash
# Watches repo dir and reruns audit if anything changes

TARGET_REPO="../GMAILspambot"
AUDIT_SCRIPT="./run_llm_audit.sh"

find "$TARGET_REPO" -type f | entr -c "$AUDIT_SCRIPT" "$TARGET_REPO" --fast
