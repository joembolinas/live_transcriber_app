# Live Transcriber App

A cross-platform Python application that captures audio from microphone or system audio and provides real-time transcription with language detection and translation support.

## Features

- Live audio capture from microphone or system audio (if available)
- Real-time transcription using OpenAI's Whisper model (faster-whisper implementation)
- Automatic language detection
- Translation support (Tagalog to English)
- Save transcripts as text files
- User-friendly GUI interface

## Requirements

- Python 3.8 or higher
- FFmpeg installed and available in PATH

## Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/yourusername/live_transcriber_app.git
   cd live_transcriber_app
   ```
2. Create a virtual environment (recommended):

   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```
4. Install FFmpeg:

   - **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html), extract, and add the bin folder to your system's PATH environment variable.
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt update && sudo apt install ffmpeg`

## Usage

Run the application:

### Main Application

```bash
# Run the enhanced version (recommended)
python main_adaptive.py

# Or run the basic version
python main.py
```

### Using Scripts

#### Windows
```bash
# Double-click any of these scripts in the scripts/ folder
scripts\run_app.bat
```

#### macOS/Linux
```bash
# Make the script executable first
chmod +x scripts/run_app.sh
# Then run it
./scripts/run_app.sh
```

### Using the App

1. **Select Audio Device**: Choose your input device from the dropdown.

   - For your voice: Choose your microphone.
   - For system audio:
     - **Windows**: Look for "Stereo Mix", "Wave Out Mix", or "What U Hear"
     - **macOS**: Use a virtual audio device like BlackHole
     - **Linux**: Configure PulseAudio/PipeWire for loopback
2. **LISTEN NOW**: Start capturing and transcribing audio.
3. **Live Transcript**: Text will appear in real-time:

   - `[EN]` Text from English speech
   - `[TL > EN]` Text translated from Tagalog to English
   - `[XX]` Text from other language XX
4. **STOP LISTENING**: Stop the recording.
5. **Save Transcript**: Save the contents to a .txt file.

## Notes

- The first time you run the app, it will download the Whisper model, which requires an internet connection.
- System audio capture varies by platform and may require additional setup.
- Transcription quality depends on audio clarity and the model size.
- **main_adaptive.py** is the enhanced version with better accuracy and features
- Use the test scripts in the `tests/` folder to diagnose audio issues

## Project Structure

```
live_transcriber_app/
├── main_adaptive.py      # Enhanced transcriber (recommended)
├── main.py              # Basic transcriber
├── requirements.txt     # Python dependencies
├── README.md           # This file
├── docs/               # Documentation
│   ├── PROJECT_SUMMARY.md
│   └── TROUBLESHOOTING.md
├── scripts/            # Utility scripts
│   ├── run_app.bat
│   ├── run_app.sh
│   ├── find_audio_device.bat
│   └── quick_test.bat
└── tests/              # Test and diagnostic scripts
    ├── audio_debug.py
    ├── mic_volume_test.py
    ├── speech_accuracy_test.py
    └── (other test files)
```
