#!/bin/bash
# LLMdiver GUI Launcher

echo "🚀 Starting LLMdiver Control Panel..."

# Check if we have Python tkinter
if ! python3 -c "import tkinter" 2>/dev/null; then
    echo "❌ Error: Python tkinter not found!"
    echo "Install with: sudo apt-get install python3-tk"
    exit 1
fi

# Check if we're in the right directory
if [[ ! -f "start_llmdiver.sh" ]]; then
    echo "❌ Error: Please run from LLMdiver directory!"
    exit 1
fi

# Launch GUI
python3 llmdiver_gui.py