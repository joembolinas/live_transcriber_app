#!/bin/bash

echo "Starting Live Transcriber App..."
echo

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3 and try again."
    exit 1
fi

# Check for FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "WARNING: FFmpeg not found. The application may not work correctly."
    echo "Please install FFmpeg:"
    echo "  macOS: brew install ffmpeg"
    echo "  Linux (Ubuntu/Debian): sudo apt update && sudo apt install ffmpeg"
    echo
    read -p "Press Enter to continue anyway, or Ctrl+C to cancel..."
fi

# Activate virtual environment or create if it doesn't exist
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Virtual environment not found. Creating a new one..."
    python3 -m venv venv
    source venv/bin/activate
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

echo
echo "Launching Live Transcriber App..."
python main.py

echo
echo "Application closed."
read -p "Press Enter to exit..."
