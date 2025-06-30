#!/usr/bin/env python3
"""
Audio Device Debug Tool - Helps identify and test audio devices
"""

import sounddevice as sd
import numpy as np

def list_all_devices():
    """List all audio devices with detailed information"""
    print("=== ALL AUDIO DEVICES ===")
    devices = sd.query_devices()
    
    for i, device in enumerate(devices):
        status = "✓" if device['max_input_channels'] > 0 else "✗"
        print(f"{status} Device {i}: {device['name']}")
        print(f"    Input channels: {device['max_input_channels']}")
        print(f"    Output channels: {device['max_output_channels']}")
        print(f"    Default sample rate: {device['default_samplerate']}")
        print(f"    Host API: {device['hostapi']}")
        print()

def get_default_devices():
    """Get default input and output devices"""
    try:
        default_input = sd.query_devices(kind='input')
        default_output = sd.query_devices(kind='output')
        
        print("=== DEFAULT DEVICES ===")
        print(f"Default input: {default_input['name']} (ID: {sd.default.device[0] if sd.default.device[0] is not None else 'Auto'})")
        print(f"Default output: {default_output['name']} (ID: {sd.default.device[1] if sd.default.device[1] is not None else 'Auto'})")
        print()
        
        return default_input, default_output
    except Exception as e:
        print(f"Error getting default devices: {e}")
        return None, None

def test_device(device_id, duration=2):
    """Test if a specific device can be opened and record from it"""
    try:
        print(f"Testing device {device_id}...")
        device_info = sd.query_devices(device_id)
        print(f"  Device: {device_info['name']}")
        print(f"  Max input channels: {device_info['max_input_channels']}")
        print(f"  Default sample rate: {device_info['default_samplerate']}")
        
        if device_info['max_input_channels'] == 0:
            print("  ✗ No input channels available")
            return False
        
        # Try to open the device
        sample_rate = int(device_info['default_samplerate'])
        channels = min(1, device_info['max_input_channels'])
        
        print(f"  Attempting to record {duration} seconds at {sample_rate}Hz, {channels} channel(s)...")
        
        recording = sd.rec(int(duration * sample_rate), 
                          samplerate=sample_rate, 
                          channels=channels, 
                          device=device_id, 
                          dtype='float64')
        sd.wait()  # Wait until recording is finished
        
        # Check if we got any signal
        volume = np.sqrt(np.mean(recording**2))
        print(f"  ✓ Successfully recorded! Average volume: {volume:.6f}")
        
        if volume > 0.001:
            print(f"  ✓ Audio signal detected")
        else:
            print(f"  ⚠ Very low audio signal - check if device is working")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Failed to test device: {e}")
        return False

def find_working_devices():
    """Find all working input devices"""
    print("=== TESTING INPUT DEVICES ===")
    devices = sd.query_devices()
    working_devices = []
    
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            if test_device(i, duration=1):
                working_devices.append(i)
            print()
    
    return working_devices

def main():
    print("Audio Device Debug Tool")
    print("=" * 50)
    
    # List all devices
    list_all_devices()
    
    # Get default devices
    get_default_devices()
    
    # Test working devices
    working_devices = find_working_devices()
    
    print("=== SUMMARY ===")
    if working_devices:
        print(f"✓ Found {len(working_devices)} working input devices:")
        for device_id in working_devices:
            device_info = sd.query_devices(device_id)
            print(f"  - Device {device_id}: {device_info['name']}")
        
        print(f"\nRecommended device IDs to try in the app: {working_devices}")
    else:
        print("✗ No working input devices found!")
        print("Possible solutions:")
        print("  1. Check if your microphone is plugged in")
        print("  2. Check Windows sound settings")
        print("  3. Try running as administrator")
        print("  4. Restart the application")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
    
    print("\nPress Enter to exit...")
    input()
