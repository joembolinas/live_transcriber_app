#!/usr/bin/env python3
"""
Quick Transcription Test - Test a specific phrase for accuracy
"""

import sounddevice as sd
import numpy as np

try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

def test_specific_phrase():
    """Test transcription of a specific phrase"""
    
    if not WHISPER_AVAILABLE:
        print("❌ faster-whisper not available.")
        return
    
    test_phrase = "The final phase focuses on testing, packaging the application into a distributable format, and writing documentation."
    
    print("🎤 SPECIFIC PHRASE TRANSCRIPTION TEST")
    print("="*70)
    print(f"📝 Target phrase:")
    print(f'   "{test_phrase}"')
    print()
    
    # Find microphone
    devices = sd.query_devices()
    mic_device = None
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0 and 'mic' in device['name'].lower():
            mic_device = (i, device)
            break
    
    if not mic_device:
        print("❌ No microphone found!")
        return
    
    device_id, device_info = mic_device
    print(f"🎙️ Using: {device_info['name']}")
    
    # Test different model sizes
    model_sizes = ["base", "small"]
    
    for model_size in model_sizes:
        print(f"\n🔄 Testing with {model_size} model...")
        
        try:
            model = WhisperModel(model_size, device="cpu", compute_type="int8")
            
            print(f"📝 Please say the target phrase clearly.")
            input("Press Enter when ready to record...")
            
            print("🔴 Recording for 10 seconds... SPEAK NOW!")
            
            sample_rate = int(device_info['default_samplerate'])
            recording = sd.rec(
                int(10 * sample_rate),
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
                print("   ⚠️  Volume too low!")
                continue
            
            # Transcribe with different settings
            print("   🔄 Transcribing...")
            
            # Method 1: Basic
            segments1, _ = model.transcribe(
                recording.flatten(),
                language='en',
                temperature=0.0
            )
            result1 = " ".join([segment.text for segment in segments1]).strip()
            
            # Method 2: Enhanced
            segments2, _ = model.transcribe(
                recording.flatten(),
                language='en',
                beam_size=5,
                best_of=5,
                temperature=0.0,
                condition_on_previous_text=False,
                vad_filter=True,
                word_timestamps=True
            )
            result2 = " ".join([segment.text for segment in segments2]).strip()
            
            print(f"\n   📊 {model_size.upper()} MODEL RESULTS:")
            print(f"   🎯 Target:   \"{test_phrase}\"")
            print(f"   🔧 Basic:    \"{result1}\"")
            print(f"   ⚡ Enhanced: \"{result2}\"")
            
            # Simple accuracy check
            target_words = set(test_phrase.lower().split())
            basic_words = set(result1.lower().split())
            enhanced_words = set(result2.lower().split())
            
            basic_accuracy = len(target_words & basic_words) / len(target_words) * 100
            enhanced_accuracy = len(target_words & enhanced_words) / len(target_words) * 100
            
            print(f"   📈 Basic Accuracy:    {basic_accuracy:.0f}%")
            print(f"   📈 Enhanced Accuracy: {enhanced_accuracy:.0f}%")
            
            if enhanced_accuracy > basic_accuracy:
                print(f"   ✅ Enhanced settings are better!")
            else:
                print(f"   ℹ️  Basic settings work fine")
                
        except Exception as e:
            print(f"   ❌ Error with {model_size}: {e}")
    
    print("\n" + "="*70)
    print("💡 RECOMMENDATIONS:")
    print("1. Use 'small' model if enhanced accuracy is significantly better")
    print("2. Speak clearly and at moderate pace")
    print("3. Ensure good microphone volume (>0.01)")
    print("4. Use enhanced settings (beam_size=5, vad_filter=True)")

if __name__ == "__main__":
    try:
        test_specific_phrase()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    
    input("\nPress Enter to exit...")
