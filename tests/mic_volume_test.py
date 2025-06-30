#!/usr/bin/env python3
"""
Microphone Volume Test - Quick test for microphone levels
"""

import sounddevice as sd
import numpy as np
import time

def test_microphone_volume():
    """Test microphone volume levels in real-time"""
    
    # Find microphone devices
    devices = sd.query_devices()
    mic_devices = []
    
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0 and 'mic' in device['name'].lower():
            mic_devices.append((i, device))
    
    if not mic_devices:
        print("❌ No microphone devices found!")
        return
    
    print("🎤 MICROPHONE VOLUME TEST")
    print("="*50)
    
    for i, (device_id, device_info) in enumerate(mic_devices):
        print(f"{i+1}. {device_info['name']} (ID: {device_id})")
    
    try:
        choice = int(input(f"\nSelect microphone (1-{len(mic_devices)}): ")) - 1
        if choice < 0 or choice >= len(mic_devices):
            print("Invalid choice!")
            return
            
        device_id, device_info = mic_devices[choice]
        
    except (ValueError, KeyboardInterrupt):
        print("Test cancelled.")
        return
    
    print(f"\n🎙️ Testing: {device_info['name']}")
    print("Speak into your microphone for 10 seconds...")
    print("Target volume for good transcription: > 0.01")
    print("-" * 50)
    
    try:
        # Record in 0.5 second chunks for real-time feedback
        sample_rate = int(device_info['default_samplerate'])
        chunk_duration = 0.5
        total_duration = 10
        chunks = int(total_duration / chunk_duration)
        
        max_volume = 0
        good_chunks = 0
        
        for i in range(chunks):
            # Record chunk
            recording = sd.rec(
                int(chunk_duration * sample_rate),
                samplerate=sample_rate,
                channels=1,
                device=device_id,
                dtype='float64'
            )
            sd.wait()
            
            # Calculate volume
            volume = np.sqrt(np.mean(recording**2))
            max_volume = max(max_volume, volume)
            
            # Show real-time feedback
            status = "✓ GOOD" if volume > 0.01 else "⚠ WEAK" if volume > 0.001 else "✗ TOO QUIET"
            if volume > 0.01:
                good_chunks += 1
                
            # Visual bar
            bar_length = min(int(volume * 500), 40)
            bar = "█" * bar_length + "░" * (40 - bar_length)
            
            print(f"Chunk {i+1:2d}: {volume:.4f} |{bar}| {status}")
            
            time.sleep(0.1)  # Small delay between chunks
        
        print("-" * 50)
        print("📊 RESULTS:")
        print(f"Maximum volume: {max_volume:.4f}")
        print(f"Good chunks (>0.01): {good_chunks}/{chunks} ({good_chunks/chunks*100:.0f}%)")
        
        if max_volume > 0.01:
            print("✅ EXCELLENT: Your microphone levels are good for transcription!")
        elif max_volume > 0.005:
            print("⚠️  MARGINAL: Microphone works but try speaking louder")
            print("   Recommendation: Increase microphone volume in Windows settings")
        else:
            print("❌ POOR: Microphone levels too low for reliable transcription")
            print("   Solutions:")
            print("   1. Check if microphone is muted")
            print("   2. Increase microphone volume/boost in Windows")
            print("   3. Move closer to microphone")
            print("   4. Try a different microphone")
        
    except Exception as e:
        print(f"❌ Error testing microphone: {e}")

if __name__ == "__main__":
    try:
        test_microphone_volume()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    
    input("\nPress Enter to exit...")
