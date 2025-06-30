#!/usr/bin/env python3
"""
Quick Audio Source Test - Test different audio sources with current setup
"""

import sounddevice as sd
import numpy as np
import time
import webbrowser

def test_stereo_mix_with_sources():
    """Test Stereo Mix with different audio sources"""
    
    # Find Stereo Mix device
    devices = sd.query_devices()
    stereo_mix_id = None
    
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0 and 'stereo mix' in device['name'].lower():
            stereo_mix_id = i
            break
    
    if stereo_mix_id is None:
        print("❌ Stereo Mix device not found")
        return
    
    device_info = sd.query_devices(stereo_mix_id)
    print(f"📻 Testing device: {device_info['name']}")
    print(f"Sample rate: {device_info['default_samplerate']}Hz")
    
    test_sources = [
        ("Windows System Sounds", "Play a Windows sound (like error beep)"),
        ("YouTube Video", "Open YouTube and play a video"),
        ("Windows Media Player", "Play a music file"),
        ("Browser Audio", "Play audio in any browser"),
        ("System Notification", "Get a notification sound")
    ]
    
    print("\n" + "="*60)
    print("AUDIO SOURCE TESTING")
    print("="*60)
    
    for source_name, instruction in test_sources:
        print(f"\n🎵 Testing: {source_name}")
        print(f"📋 Action: {instruction}")
        
        if source_name == "YouTube Video":
            # Auto-open YouTube for convenience
            try:
                webbrowser.open("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
                print("   (YouTube opened automatically)")
            except:
                pass
        
        input("   Press Enter when audio is playing...")
        
        # Record for 3 seconds
        print("   🎙️ Recording for 3 seconds...")
        
        try:
            recording = sd.rec(
                int(3 * device_info['default_samplerate']),
                samplerate=int(device_info['default_samplerate']),
                channels=1,
                device=stereo_mix_id,
                dtype='float64'
            )
            sd.wait()
            
            # Calculate volume
            volume = np.sqrt(np.mean(recording**2))
            
            print(f"   📊 Volume detected: {volume:.6f}")
            
            if volume > 0.001:
                print(f"   ✅ EXCELLENT: Strong signal - This source works!")
            elif volume > 0.0001:
                print(f"   ⚠️  WEAK: Signal detected but may be too quiet")
            else:
                print(f"   ❌ FAILED: No significant signal detected")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
        
        print("   " + "-"*50)
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
    print("If ANY source showed volume > 0.001, that source will work!")
    print("If ALL sources failed, the Stereo Mix setup needs fixing.")

if __name__ == "__main__":
    test_stereo_mix_with_sources()
    input("\nPress Enter to exit...")
