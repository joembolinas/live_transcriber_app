@echo off
echo Starting Live Transcriber App...
echo.
echo Activating virtual environment...
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo Virtual environment not found. Creating a new one...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo Installing dependencies...
    pip install -r requirements.txt
)

echo.
echo Checking for FFmpeg...
where ffmpeg >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo WARNING: FFmpeg not found in PATH. The application may not work correctly.
    echo Please install FFmpeg from https://ffmpeg.org/download.html and add it to your PATH.
    echo.
    pause
)

echo.
echo Launching Live Transcriber App (Adaptive Version)...
python main_adaptive.py

echo.
echo Application closed.
pause
