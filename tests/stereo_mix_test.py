#!/usr/bin/env python3
"""
Stereo Mix Test Tool - Diagnose system audio capture issues
"""

import sounddevice as sd
import numpy as np
import time

def find_stereo_mix_devices():
    """Find all potential system audio devices"""
    devices = sd.query_devices()
    stereo_devices = []
    
    print("=== SEARCHING FOR SYSTEM AUDIO DEVICES ===")
    
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            name_lower = device['name'].lower()
            if any(keyword in name_lower for keyword in ['stereo mix', 'what u hear', 'loopback', 'wave out mix']):
                stereo_devices.append((i, device))
                print(f"✓ Found: Device {i} - {device['name']}")
    
    if not stereo_devices:
        print("✗ No stereo mix devices found")
        print("\nAll input devices:")
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                print(f"  Device {i}: {device['name']}")
    
    return stereo_devices

def test_stereo_mix_audio(device_id, device_name, duration=10):
    """Test a stereo mix device for audio"""
    print(f"\n=== TESTING DEVICE {device_id}: {device_name} ===")
    
    try:
        device_info = sd.query_devices(device_id)
        sample_rate = int(device_info['default_samplerate'])
        channels = min(2, device_info['max_input_channels'])  # Try stereo first
        
        print(f"Sample rate: {sample_rate}Hz")
        print(f"Channels: {channels}")
        print(f"Testing for {duration} seconds...")
        print("PLEASE PLAY SOME AUDIO NOW (YouTube, music, etc.)")
        print("-" * 50)
        
        # Record in chunks to show real-time levels
        chunk_duration = 1.0  # 1 second chunks
        total_chunks = int(duration / chunk_duration)
        
        max_volume = 0
        volumes = []
        
        for chunk in range(total_chunks):
            recording = sd.rec(
                int(chunk_duration * sample_rate),
                samplerate=sample_rate,
                channels=channels,
                device=device_id,
                dtype='float64'
            )
            sd.wait()
            
            # Calculate volume
            volume = np.sqrt(np.mean(recording**2))
            volumes.append(volume)
            max_volume = max(max_volume, volume)
            
            # Show progress
            bars = int(volume * 1000)  # Scale for display
            bar_display = "█" * min(bars, 50)
            print(f"Chunk {chunk+1:2d}: Volume {volume:.6f} |{bar_display:<50}|")
        
        print("-" * 50)
        print(f"RESULTS:")
        print(f"Maximum volume detected: {max_volume:.6f}")
        print(f"Average volume: {np.mean(volumes):.6f}")
        
        if max_volume > 0.01:
            print("✓ GOOD: Strong audio signal detected!")
            return True
        elif max_volume > 0.001:
            print("⚠ WEAK: Audio signal detected but very quiet")
            print("  Try increasing system volume or checking audio levels")
            return True
        elif max_volume > 0.0001:
            print("⚠ VERY WEAK: Minimal audio detected")
            print("  Signal may be too weak for reliable transcription")
            return False
        else:
            print("✗ NO AUDIO: No significant signal detected")
            print("  Stereo Mix may not be properly configured")
            return False
            
    except Exception as e:
        print(f"✗ ERROR: Failed to test device - {e}")
        return False

def provide_stereo_mix_help():
    """Provide help for setting up Stereo Mix"""
    print("\n" + "="*60)
    print("STEREO MIX SETUP HELP")
    print("="*60)
    print("If no audio was detected, try these steps:")
    print()
    print("1. ENABLE STEREO MIX:")
    print("   - Right-click speaker icon in system tray")
    print("   - Select 'Open Sound settings'")
    print("   - Click 'Sound Control Panel' (right side)")
    print("   - Go to 'Recording' tab")
    print("   - Right-click empty area → 'Show Disabled Devices'")
    print("   - Find 'Stereo Mix' → Right-click → 'Enable'")
    print("   - Right-click 'Stereo Mix' → 'Set as Default Device'")
    print()
    print("2. CHECK AUDIO LEVELS:")
    print("   - Double-click 'Stereo Mix' in Recording devices")
    print("   - Go to 'Levels' tab")
    print("   - Ensure volume is at 50-100%")
    print("   - Go to 'Listen' tab")
    print("   - Check 'Listen to this device' (temporarily)")
    print()
    print("3. TEST WITH SYSTEM AUDIO:")
    print("   - Play YouTube video or music")
    print("   - You should see green bars in 'Stereo Mix' levels")
    print("   - If no bars, try different audio sources")
    print()
    print("4. ALTERNATIVE: Virtual Audio Cable")
    print("   - Download VB-Audio Virtual Cable (free)")
    print("   - Set as default playback device")
    print("   - Use 'CABLE Output' as input device in app")

def main():
    print("Stereo Mix Diagnostic Tool")
    print("="*50)
    
    # Find stereo mix devices
    stereo_devices = find_stereo_mix_devices()
    
    if not stereo_devices:
        provide_stereo_mix_help()
        return
    
    # Test each device
    working_devices = []
    for device_id, device_info in stereo_devices:
        if test_stereo_mix_audio(device_id, device_info['name']):
            working_devices.append((device_id, device_info['name']))
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    if working_devices:
        print(f"✓ Found {len(working_devices)} working system audio device(s):")
        for device_id, name in working_devices:
            print(f"  - Device {device_id}: {name}")
        print(f"\nYou can use any of these devices in the Live Transcriber app!")
    else:
        print("✗ No working system audio devices found")
        provide_stereo_mix_help()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
    
    print("\nPress Enter to exit...")
    input()
