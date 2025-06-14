#!/bin/bash

# Aura VS Code Extension Installer
# Author: Aura-X
# Purpose: To compile, package, and install the Aura VS Code extension.

set -e # Exit immediately if a command exits with a non-zero status.

# --- CONFIGURATION ---
VSCODE_EXT_DIR="/home/greenantix/AI/LLMdiver/aura/vscode"
LOG_FILE="/home/greenantix/AI/LLMdiver/logs/vscode_install.log"
EXTENSION_NAME="aura-vscode"

# --- FUNCTIONS ---
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# --- MAIN EXECUTION ---
log "--- Starting Aura VS Code Extension Installation ---"

# Navigate to the extension directory
if [ ! -d "$VSCODE_EXT_DIR" ]; then
    log "ERROR: VS Code extension directory not found at '$VSCODE_EXT_DIR'"
    exit 1
fi
cd "$VSCODE_EXT_DIR"
log "Navigated to extension directory: $(pwd)"

# Step 1: Install Node.js dependencies
log "Step 1: Installing npm dependencies..."
if ! npm install; then
    log "ERROR: 'npm install' failed. Please check for errors."
    exit 1
fi
log "SUCCESS: npm dependencies installed."

# Step 2: Ensure vsce (Visual Studio Code Extensions) is installed
log "Step 2: Checking for 'vsce' packaging tool..."
if ! npm list -g vsce &>/dev/null; then
    log "INFO: 'vsce' not found globally, installing..."
    if ! npm install -g vsce; then
        log "ERROR: Failed to install 'vsce'. Please install it manually with 'npm install -g vsce'."
        exit 1
    fi
fi
log "SUCCESS: 'vsce' tool is available."

# Step 3: Package the extension into a .vsix file
VSIX_FILE="${EXTENSION_NAME}.vsix"
log "Step 3: Packaging extension into '$VSIX_FILE'..."
if ! npx vsce package --out "$VSIX_FILE"; then
    log "ERROR: 'vsce package' failed. Please check for compilation errors or configuration issues in package.json."
    exit 1
fi
log "SUCCESS: Extension packaged successfully."

# Step 4: Uninstall any old version of the extension
log "Step 4: Uninstalling any previous versions of the extension..."
code --uninstall-extension "${EXTENSION_NAME}" || log "INFO: No previous version to uninstall."
sleep 2 # Give VS Code a moment to process the uninstall

# Step 5: Install the new .vsix file
log "Step 5: Installing the new extension version..."
if ! code --install-extension "$VSIX_FILE" --force; then
    log "ERROR: 'code --install-extension' failed. Ensure VS Code is installed and the 'code' command is in your PATH."
    exit 1
fi
log "SUCCESS: Extension installed in VS Code."

# Step 6: Cleanup
log "Step 6: Cleaning up temporary files..."
rm "$VSIX_FILE"
log "Cleanup complete."

log "--- Aura VS Code Extension Installation Complete ---"
echo "✅ Aura is now installed in VS Code. Please restart VS Code to activate the extension."

