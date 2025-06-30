@echo off
echo Testing Live Transcriber Components...
echo.

echo Testing faster-whisper import...
python -c "from faster_whisper import WhisperModel; print('✓ faster-whisper available')" 2>nul
if %ERRORLEVEL% neq 0 (
    echo ✗ faster-whisper not available
) else (
    echo ✓ faster-whisper working
)

echo.
echo Testing audio devices...
python -c "import sounddevice as sd; devices = sd.query_devices(); input_devices = [d for d in devices if d['max_input_channels'] > 0]; print(f'✓ Found {len(input_devices)} input devices')"

echo.
echo Testing GUI components...
python -c "import tkinter as tk; print('✓ GUI components available')"

echo.
echo All tests complete!
echo.
echo You can now run the Live Transcriber with:
echo   python main_adaptive.py
echo.
pause
