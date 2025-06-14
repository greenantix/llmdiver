#!/usr/bin/env python3

# Aura VS Code Integration Verifier
# Author: Aura-X
# Purpose: To verify that the Aura VS Code extension can activate and
#          communicate with the backend service.

import asyncio
import websockets
import subprocess
import json
import time

# --- CONFIGURATION ---
WEBSOCKET_HOST = "localhost"
WEBSOCKET_PORT = 6789  # Must match the port in the VS Code extension
EXTENSION_ID = "aura.aura-vscode"  # The 'publisher.name' from package.json

async def verification_server(websocket, path):
    """A mock server that behaves like the Aura backend for verification."""
    print("✅ SUCCESS: Aura VS Code extension has connected to the verification server!")
    
    # Send a welcome message to prove the connection is two-way
    welcome_message = {
        "type": "AURA_STATUS",
        "payload": {
            "status": "CONNECTED",
            "message": "Verification Successful. Connection established."
        }
    }
    await websocket.send(json.dumps(welcome_message))
    print("✅ SENT: Welcome message to the extension.")

    try:
        # Keep the connection open for a few seconds to receive any messages
        async for message in websocket:
            print(f"✅ RECEIVED: Message from extension: {message}")
            # In a real scenario, you'd process this. For now, just acknowledge.
    except websockets.exceptions.ConnectionClosed:
        print("INFO: Connection closed by the extension.")
    finally:
        # Stop the server after verification
        print("INFO: Verification complete. Shutting down server.")
        asyncio.get_event_loop().stop()

def check_extension_installed():
    """Uses the 'code' command-line tool to check if the extension is installed."""
    print(f"--- Step 1: Checking if extension '{EXTENSION_ID}' is installed ---")
    try:
        result = subprocess.run(
            ['code', '--list-extensions'],
            capture_output=True,
            text=True,
            check=True
        )
        installed_extensions = result.stdout.lower()
        if EXTENSION_ID.lower() in installed_extensions:
            print(f"✅ SUCCESS: Extension '{EXTENSION_ID}' is present in VS Code.")
            return True
        else:
            print(f"❌ FAILURE: Extension '{EXTENSION_ID}' not found.")
            print("Please run the 'install_vscode_extension.sh' script first.")
            return False
    except FileNotFoundError:
        print("❌ FAILURE: The 'code' command was not found.")
        print("Please ensure Visual Studio Code is installed and 'code' is in your system's PATH.")
        return False
    except Exception as e:
        print(f"❌ An error occurred while checking extensions: {e}")
        return False

async def main():
    if not check_extension_installed():
        return

    print("\n--- Step 2: Starting mock Aura backend server ---")
    print(f"Listening on ws://{WEBSOCKET_HOST}:{WEBSOCKET_PORT}")
    print("Please open a Python project in VS Code now to trigger the extension activation.")
    print("Waiting for connection...")

    start_server = websockets.serve(verification_server, WEBSOCKET_HOST, WEBSOCKET_PORT)

    try:
        await start_server
        # The loop will be stopped by the server once a connection is verified
        await asyncio.get_event_loop().create_future()
    except OSError as e:
        print(f"❌ FAILURE: Could not start WebSocket server: {e}")
        print(f"The port {WEBSOCKET_PORT} might be in use by another application.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError:
        print("\nVerification process concluded.")

