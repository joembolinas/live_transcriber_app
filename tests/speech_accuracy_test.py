#!/usr/bin/env python3
"""
Advanced Microphone Test - Test speech recognition accuracy
"""

import sounddevice as sd
import numpy as np
import time

try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

def test_speech_accuracy():
    """Test actual speech recognition accuracy"""
    
    if not WHISPER_AVAILABLE:
        print("❌ faster-whisper not available. Install it first: pip install faster-whisper")
        return
    
    # Find microphone devices
    devices = sd.query_devices()
    mic_devices = []
    
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0 and ('mic' in device['name'].lower() or 'microphone' in device['name'].lower()):
            mic_devices.append((i, device))
    
    if not mic_devices:
        print("❌ No microphone devices found!")
        return
    
    print("🎤 SPEECH RECOGNITION ACCURACY TEST")
    print("="*60)
    
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
    
    # Load Whisper model
    print("\n🔄 Loading Whisper model...")
    try:
        model = WhisperModel("base", device="cpu", compute_type="int8")
        print("✅ Model loaded successfully!")
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return
    
    # Test phrases
    test_phrases = [
        "Hello, this is a microphone test",
        "The quick brown fox jumps over the lazy dog",
        "Testing speech recognition accuracy with different words",
        "Can you hear me clearly and accurately",
        "This is the final test phrase for verification"
    ]
    
    print(f"\n🎙️ Testing: {device_info['name']}")
    print("\nYou will be asked to say 5 test phrases.")
    print("The app will show what it heard vs what you should say.")
    print("-" * 60)
    
    sample_rate = int(device_info['default_samplerate'])
    total_score = 0
    
    for i, phrase in enumerate(test_phrases, 1):
        print(f"\nTest {i}/5:")
        print(f"📝 Please say: \"{phrase}\"")
        input("Press Enter when ready to record...")
        
        print("🔴 Recording for 5 seconds... SPEAK NOW!")
        
        try:
            # Record for 5 seconds
            recording = sd.rec(
                int(5 * sample_rate),
                samplerate=sample_rate,
                channels=1,
                device=device_id,
                dtype='float32'
            )
            sd.wait()
            
            # Check volume
            volume = np.sqrt(np.mean(recording**2))
            print(f"   📊 Volume: {volume:.4f}")
            
            if volume < 0.01:
                print("   ⚠️  Volume too low - speak louder!")
                continue
            
            # Transcribe
            print("   🔄 Transcribing...")
            audio_flat = recording.flatten()
            
            segments, info = model.transcribe(
                audio_flat,
                language='en',
                beam_size=5,
                best_of=5,
                temperature=0.0,
                condition_on_previous_text=False,
                vad_filter=True
            )
            
            transcribed = " ".join([segment.text for segment in segments]).strip()
            
            print(f"   🎯 Expected: \"{phrase}\"")
            print(f"   🎤 Heard:    \"{transcribed}\"")
            
            # Simple accuracy check (word matching)
            expected_words = phrase.lower().split()
            heard_words = transcribed.lower().split()
            
            common_words = set(expected_words) & set(heard_words)
            accuracy = len(common_words) / len(expected_words) * 100 if expected_words else 0
            
            total_score += accuracy
            
            if accuracy > 80:
                print(f"   ✅ Accuracy: {accuracy:.0f}% - EXCELLENT!")
            elif accuracy > 60:
                print(f"   ⚠️  Accuracy: {accuracy:.0f}% - Good but could be better")
            else:
                print(f"   ❌ Accuracy: {accuracy:.0f}% - Poor recognition")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Final results
    average_score = total_score / len(test_phrases)
    print("\n" + "="*60)
    print("📊 FINAL RESULTS")
    print("="*60)
    print(f"Average Accuracy: {average_score:.0f}%")
    
    if average_score > 80:
        print("🏆 EXCELLENT: Your microphone setup is working very well!")
        print("   The Live Transcriber should work accurately.")
    elif average_score > 60:
        print("⚠️  GOOD: Your setup works but could be improved.")
        print("   Recommendations:")
        print("   1. Speak more clearly and at consistent volume")
        print("   2. Reduce background noise")
        print("   3. Move closer to microphone")
        print("   4. Increase microphone volume in Windows")
    else:
        print("❌ POOR: Your microphone setup needs improvement.")
        print("   Problems to fix:")
        print("   1. Volume too low - increase microphone boost")
        print("   2. Too much background noise")
        print("   3. Microphone quality issues")
        print("   4. Speaking too fast or unclearly")
    
    print(f"\nFor the Live Transcriber app:")
    if average_score > 70:
        print("✅ Should work well with current settings")
    else:
        print("⚠️  May need microphone adjustments for best results")

if __name__ == "__main__":
    try:
        test_speech_accuracy()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    
    input("\nPress Enter to exit...")
