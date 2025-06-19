#!/usr/bin/env python3
"""
Auto Audio Device Finder
Automatically finds a working audio device for the live transcriber
"""

import sounddevice as sd
import numpy as np
import threading
import time

def find_working_audio_device():
    """
    Automatically test audio devices and return the first working one
    """
    print("🔍 Searching for working audio devices...")
    
    try:
        devices = sd.query_devices()
        input_devices = [(i, dev) for i, dev in enumerate(devices) if dev['max_input_channels'] > 0]
        
        print(f"Found {len(input_devices)} input devices to test...")
        
        for device_id, device_info in input_devices:
            device_name = device_info['name']
            print(f"\nTesting Device {device_id}: {device_name}")
            
            try:
                # Try to record a short sample
                sample_rate = int(device_info['default_samplerate'])
                channels = min(1, device_info['max_input_channels'])
                
                print(f"  Attempting 1-second test recording at {sample_rate}Hz...")
                
                recording = sd.rec(
                    frames=sample_rate,  # 1 second
                    samplerate=sample_rate,
                    channels=channels,
                    device=device_id,
                    dtype='float64'
                )
                sd.wait()  # Wait for recording to finish
                
                # Check if we got valid audio data
                if recording is not None and len(recording) > 0:
                    volume = np.sqrt(np.mean(recording**2))
                    print(f"  ✓ Success! Volume level: {volume:.6f}")
                    
                    if device_id == 0:  # System default
                        print(f"  🎯 Using system default device: {device_name}")
                    else:
                        print(f"  🎯 Found working device: {device_name}")
                    
                    return device_id, device_name
                else:
                    print(f"  ✗ No audio data received")
                    
            except Exception as e:
                print(f"  ✗ Failed: {e}")
                continue
        
        print("\n❌ No working audio devices found!")
        return None, None
        
    except Exception as e:
        print(f"❌ Error during device search: {e}")
        return None, None

def test_specific_device(device_id):
    """Test a specific device ID"""
    try:
        device_info = sd.query_devices(device_id)
        print(f"Testing device {device_id}: {device_info['name']}")
        
        sample_rate = int(device_info['default_samplerate'])
        channels = min(1, device_info['max_input_channels'])
        
        recording = sd.rec(
            frames=sample_rate,  # 1 second
            samplerate=sample_rate,
            channels=channels,
            device=device_id,
            dtype='float64'
        )
        sd.wait()
        
        volume = np.sqrt(np.mean(recording**2))
        print(f"Success! Volume: {volume:.6f}")
        return True
        
    except Exception as e:
        print(f"Failed: {e}")
        return False

if __name__ == "__main__":
    device_id, device_name = find_working_audio_device()
    
    if device_id is not None:
        print(f"\n🎉 SUCCESS! Use device ID {device_id} in your application")
        print(f"Device name: {device_name}")
        print(f"\nTo use this in main_adaptive.py, edit the file and set:")
        print(f"selected_device_id = {device_id}  # Force use this device")
    else:
        print(f"\n❌ No working devices found")
        print(f"Try these troubleshooting steps:")
        print(f"1. Check if your microphone is connected")
        print(f"2. Check Windows sound settings")
        print(f"3. Try running as administrator")
        print(f"4. Restart audio services")
    
    print(f"\nPress Enter to exit...")
    input()
