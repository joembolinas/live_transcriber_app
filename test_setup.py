#!/usr/bin/env python3
"""
Simple test script to verify the Live Transcriber dependencies are working.
"""

def test_imports():
    """Test if all required modules can be imported."""
    print("Testing imports...")
    
    try:
        import tkinter as tk
        print("✓ tkinter is available")
    except ImportError as e:
        print(f"✗ tkinter import failed: {e}")
        return False
    
    try:
        import numpy as np
        print("✓ numpy is available")
    except ImportError as e:
        print(f"✗ numpy import failed: {e}")
        return False
    
    try:
        import sounddevice as sd
        print("✓ sounddevice is available")
    except ImportError as e:
        print(f"✗ sounddevice import failed: {e}")
        return False
    
    try:
        import whisper
        print("✓ whisper is available")
    except ImportError as e:
        print(f"✗ whisper import failed: {e}")
        return False
    
    try:
        import threading
        import queue
        print("✓ threading and queue are available")
    except ImportError as e:
        print(f"✗ threading/queue import failed: {e}")
        return False
    
    return True

def test_audio_devices():
    """Test if audio devices can be queried."""
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        print(f"\n✓ Found {len(devices)} audio devices:")
        
        input_devices = [dev for dev in devices if dev['max_input_channels'] > 0]
        print(f"✓ Found {len(input_devices)} input devices")
        
        for i, dev in enumerate(input_devices[:3]):  # Show first 3
            print(f"  - {dev['name']}")
        
        if len(input_devices) > 3:
            print(f"  ... and {len(input_devices) - 3} more")
            
        return True
    except Exception as e:
        print(f"✗ Audio device query failed: {e}")
        return False

def test_whisper_availability():
    """Test if Whisper can be loaded (without actually loading the model)."""
    try:
        import whisper
        print("✓ Whisper module is available")
        
        # Check available models
        available_models = whisper.available_models()
        print(f"✓ Available Whisper models: {', '.join(available_models)}")
        return True
    except Exception as e:
        print(f"✗ Whisper test failed: {e}")
        return False

if __name__ == "__main__":
    print("Live Transcriber App - Dependency Test")
    print("=" * 40)
    
    all_tests_passed = True
    
    # Test imports
    if not test_imports():
        all_tests_passed = False
    
    print()
    
    # Test audio devices
    if not test_audio_devices():
        all_tests_passed = False
    
    print()
    
    # Test Whisper
    if not test_whisper_availability():
        all_tests_passed = False
    
    print("\n" + "=" * 40)
    if all_tests_passed:
        print("🎉 ALL TESTS PASSED! Your environment is ready.")
        print("You can now run the Live Transcriber app with: python main.py")
    else:
        print("❌ Some tests failed. Please check the error messages above.")
        print("You may need to install missing dependencies.")
    
    print("\nPress Enter to exit...")
    input()
