@echo off
echo Audio Device Finder and Tester
echo ==============================
echo.
echo This tool will test all your audio devices to find which one works
echo for the live transcription application.
echo.
pause

cd /d "%~dp0"
python audio_device_finder.py

echo.
echo Testing complete! Check the output above for the recommended device.
echo.
pause
