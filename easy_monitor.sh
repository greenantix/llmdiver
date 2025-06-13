#!/bin/bash

# Ensure required packages are installed
echo "Checking and installing required packages..."

# Function to check if a Python package is installed
check_package() {
    python3 -c "import $1" 2>/dev/null
    return $?
}

# Install required system packages if missing
if ! command -v python3-tk &> /dev/null; then
    echo "Installing tkinter..."
    sudo apt-get update
    sudo apt-get install -y python3-tk
fi

# Install required Python packages if missing
REQUIRED_PACKAGES=("psutil" "watchdog" "GitPython" "scikit-learn" "numpy" "requests" "decorators")

for package in "${REQUIRED_PACKAGES[@]}"; do
    if ! check_package $package; then
        echo "Installing $package..."
        pip3 install $package
    fi
done

# Launch the monitor
echo "Starting LLMdiver Monitor..."
# Set Python path to include current directory
export PYTHONPATH="${PYTHONPATH:+${PYTHONPATH}:}$(pwd)"

# Start the monitor
python3 ./llmdiver_monitor.py