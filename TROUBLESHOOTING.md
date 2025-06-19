# Troubleshooting Guide and System Audio Setup

## Common Issues

### VS Code AREPL Live Code Extension Error

If you see an error like `ModuleNotFoundError: No module named 'six.moves'`, this is related to the VS Code Live Code extension, not your Live Transcriber app. To fix this:

```bash
pip install six astunparse
```

This installs the dependencies needed by the Live Code extension.

### No Audio Devices Found

1. Ensure your microphone is properly connected
2. Check if your microphone is enabled in your system settings
3. Try running the app with administrator privileges
4. Make sure you have the appropriate audio drivers installed

### Whisper Installation Issues

If `openai-whisper` fails to install, try these alternatives:

1. **Use faster-whisper (recommended)**:
   ```bash
   pip install faster-whisper
   ```
   Then run `main_adaptive.py` instead of `main.py`

2. **Install PyTorch first**:
   ```bash
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
   pip install openai-whisper
   ```

3. **Audio-only testing**:
   If neither whisper implementation works, use `audio_test.py` to test audio capture functionality.

### Transcription Not Working

1. Verify FFmpeg is properly installed and in your PATH
2. Check your internet connection (needed for first-time model download)
3. Ensure you have selected the correct audio input device
4. Try using a different Whisper model (modify the MODEL_SIZE variable in main.py)

### Cannot Hear System Audio

This is the most common issue and varies by platform. Follow the instructions below:

## Setting Up System Audio Capture

### Windows

1. **Enable Stereo Mix**:
   - Right-click the speaker icon in your taskbar
   - Select "Sounds" or "Sound settings"
   - Go to the "Recording" tab
   - Right-click in an empty area and select "Show Disabled Devices"
   - Look for "Stereo Mix" or similar, right-click it and select "Enable"
   - If you don't see Stereo Mix, your sound card may not support it

2. **Alternative: Virtual Audio Cable**:
   - Download and install a virtual audio cable like [VB-Audio Virtual Cable](https://vb-audio.com/Cable/)
   - Configure your system to output to the virtual cable
   - In the app, select the virtual cable as the input device

### macOS

macOS doesn't natively support audio loopback. You need a virtual audio device:

1. **Install BlackHole**:
   ```bash
   brew install blackhole-2ch
   ```
   Or download from [GitHub](https://github.com/ExistentialAudio/BlackHole)

2. **Configure Audio Settings**:
   - Open System Settings > Sound
   - Set BlackHole as your output device
   - In the app, select BlackHole as the input device

3. **Alternative: Soundflower**:
   - Another option is [Soundflower](https://github.com/mattingalls/Soundflower)

### Linux

1. **PulseAudio**:
   - Create a monitor source:
     ```bash
     pactl load-module module-null-sink sink_name=LoopbackCapture
     pactl set-default-sink LoopbackCapture
     ```
   - In pavucontrol, set applications to output to LoopbackCapture
   - In the app, select the monitor of LoopbackCapture as input

2. **PipeWire**:
   - Similar to PulseAudio but may have different command syntax
   - Use tools like qpwgraph for a visual interface to route audio

## Changing Whisper Model Size

The app uses the "base" model by default. To change this:

1. Open `main.py` in a text editor
2. Find the line `MODEL_SIZE = "base"`
3. Change it to one of these options:
   - `"tiny"`: Fastest but least accurate
   - `"base"`: Good balance of speed/accuracy
   - `"small"`: Better accuracy, slower
   - `"medium"`: Even better accuracy, much slower
   - `"large"`: Most accurate, very slow and resource-intensive

For English-only use, you can append ".en" to any model name (e.g., `"base.en"`) for better performance, but this will disable Tagalog translation.

## Improving Transcription Quality

1. **Reduce Background Noise**:
   - Use a good quality microphone
   - Speak clearly and at a moderate pace
   - Minimize background noise and echo

2. **Adjust Audio Levels**:
   - Ensure your microphone or system audio isn't too loud (causing clipping) or too quiet
   - Use your system's audio mixer to adjust levels

3. **Try a Larger Model**:
   - If your computer has enough resources, use a larger Whisper model for better accuracy
