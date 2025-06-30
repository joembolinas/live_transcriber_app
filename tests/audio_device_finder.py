#!/usr/bin/env python3
"""
Audio Device Finder and Tester
Comprehensive tool to identify working audio input devices
"""

import pyaudio
import numpy as np
import time
import sys
from typing import List, Dict, Optional, Tuple

class AudioDeviceFinder:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.sample_rate = 16000
        self.chunk_size = 1024
        self.channels = 1
        self.format = pyaudio.paFloat32
        
    def get_all_devices(self) -> List[Dict]:
        """Get all audio devices with detailed information"""
        devices = []
        device_count = self.audio.get_device_count()
        
        print(f"\n=== Found {device_count} total audio devices ===\n")
        
        for i in range(device_count):
            try:
                device_info = self.audio.get_device_info_by_index(i)
                devices.append({
                    'index': i,
                    'info': device_info
                })
                
                # Print device info
                print(f"Device {i}:")
                print(f"  Name: {device_info['name']}")
                print(f"  Max Input Channels: {device_info['maxInputChannels']}")
                print(f"  Max Output Channels: {device_info['maxOutputChannels']}")
                print(f"  Default Sample Rate: {device_info['defaultSampleRate']}")
                print(f"  Host API: {device_info['hostApi']}")
                print(f"  Type: {'INPUT' if device_info['maxInputChannels'] > 0 else 'OUTPUT'}")
                print()
                
            except Exception as e:
                print(f"Error getting info for device {i}: {e}")
                
        return devices
    
    def get_input_devices(self) -> List[Dict]:
        """Get only input devices (microphones)"""
        all_devices = self.get_all_devices()
        input_devices = [d for d in all_devices if d['info']['maxInputChannels'] > 0]
        
        print(f"\n=== Input devices ({len(input_devices)} found) ===\n")
        for device in input_devices:
            info = device['info']
            print(f"Device {device['index']}: {info['name']} ({info['maxInputChannels']} channels)")
            
        return input_devices
    
    def test_device_compatibility(self, device_index: int) -> Dict:
        """Test if a device can be opened with our audio settings"""
        result = {
            'device_index': device_index,
            'can_open': False,
            'error': None,
            'tested_settings': None
        }
        
        try:
            device_info = self.audio.get_device_info_by_index(device_index)
            if device_info['maxInputChannels'] == 0:
                result['error'] = "Device has no input channels"
                return result
                
            # Test our preferred settings
            settings_to_test = [
                # (sample_rate, channels, format)
                (16000, 1, pyaudio.paFloat32),
                (44100, 1, pyaudio.paFloat32),
                (48000, 1, pyaudio.paFloat32),
                (16000, 1, pyaudio.paInt16),
                (44100, 1, pyaudio.paInt16),
                (16000, 2, pyaudio.paFloat32),
                (44100, 2, pyaudio.paFloat32),
            ]
            
            for sample_rate, channels, audio_format in settings_to_test:
                try:
                    # Check if format is supported
                    is_supported = self.audio.is_format_supported(
                        rate=sample_rate,
                        input_device=device_index,
                        input_channels=channels,
                        input_format=audio_format
                    )
                    
                    if is_supported:
                        # Try to open the stream
                        stream = self.audio.open(
                            format=audio_format,
                            channels=channels,
                            rate=sample_rate,
                            input=True,
                            input_device_index=device_index,
                            frames_per_buffer=self.chunk_size
                        )
                        stream.close()
                        
                        result['can_open'] = True
                        result['tested_settings'] = {
                            'sample_rate': sample_rate,
                            'channels': channels,
                            'format': audio_format
                        }
                        break
                        
                except Exception as e:
                    continue
                    
            if not result['can_open']:
                result['error'] = "No compatible format found"
                
        except Exception as e:
            result['error'] = str(e)
            
        return result
    
    def test_device_recording(self, device_index: int, duration: float = 2.0) -> Dict:
        """Test actual recording from a device"""
        result = {
            'device_index': device_index,
            'recording_successful': False,
            'audio_level': 0.0,
            'error': None,
            'samples_recorded': 0
        }
        
        try:
            # First check compatibility
            compat_test = self.test_device_compatibility(device_index)
            if not compat_test['can_open']:
                result['error'] = f"Compatibility test failed: {compat_test['error']}"
                return result
                
            settings = compat_test['tested_settings']
            
            print(f"Testing recording from device {device_index} for {duration} seconds...")
            print(f"Settings: {settings['sample_rate']}Hz, {settings['channels']} channels")
            
            stream = self.audio.open(
                format=settings['format'],
                channels=settings['channels'],
                rate=settings['sample_rate'],
                input=True,
                input_device_index=device_index,
                frames_per_buffer=self.chunk_size
            )
            
            audio_data = []
            start_time = time.time()
            
            while time.time() - start_time < duration:
                try:
                    data = stream.read(self.chunk_size, exception_on_overflow=False)
                    if settings['format'] == pyaudio.paFloat32:
                        audio_array = np.frombuffer(data, dtype=np.float32)
                    else:
                        audio_array = np.frombuffer(data, dtype=np.int16)
                    
                    audio_data.extend(audio_array)
                    
                except Exception as e:
                    print(f"Error reading audio data: {e}")
                    break
                    
            stream.close()
            
            if audio_data:
                audio_array = np.array(audio_data)
                result['audio_level'] = float(np.max(np.abs(audio_array)))
                result['samples_recorded'] = len(audio_data)
                result['recording_successful'] = True
                
                print(f"✓ Recording successful! Audio level: {result['audio_level']:.4f}")
                if result['audio_level'] > 0.001:
                    print("✓ Audio signal detected!")
                else:
                    print("⚠ Very low audio signal - check microphone")
            else:
                result['error'] = "No audio data recorded"
                
        except Exception as e:
            result['error'] = str(e)
            print(f"✗ Recording failed: {e}")
            
        return result
    
    def find_working_devices(self) -> List[Dict]:
        """Find all working input devices"""
        input_devices = self.get_input_devices()
        working_devices = []
        
        print(f"\n=== Testing {len(input_devices)} input devices ===\n")
        
        for device in input_devices:
            device_index = device['index']
            device_name = device['info']['name']
            
            print(f"Testing Device {device_index}: {device_name}")
            print("-" * 50)
            
            # Test compatibility
            compat_result = self.test_device_compatibility(device_index)
            
            if compat_result['can_open']:
                print(f"✓ Device {device_index} is compatible")
                
                # Test recording
                record_result = self.test_device_recording(device_index)
                
                if record_result['recording_successful']:
                    working_devices.append({
                        'device_index': device_index,
                        'device_name': device_name,
                        'device_info': device['info'],
                        'settings': compat_result['tested_settings'],
                        'audio_level': record_result['audio_level'],
                        'recommended': record_result['audio_level'] > 0.001
                    })
                    status = "✓ WORKING" + (" (RECOMMENDED)" if record_result['audio_level'] > 0.001 else " (low signal)")
                    print(f"{status}")
                else:
                    print(f"✗ Recording failed: {record_result['error']}")
            else:
                print(f"✗ Device {device_index} incompatible: {compat_result['error']}")
                
            print()
            
        return working_devices
    
    def get_recommended_device(self) -> Optional[int]:
        """Get the best recommended device for recording"""
        working_devices = self.find_working_devices()
        
        if not working_devices:
            print("❌ No working audio devices found!")
            return None
            
        print(f"\n=== SUMMARY: {len(working_devices)} working devices found ===\n")
        
        # Sort by audio level (higher is better)
        working_devices.sort(key=lambda x: x['audio_level'], reverse=True)
        
        for i, device in enumerate(working_devices):
            status = "🎯 RECOMMENDED" if i == 0 else "✓ Working"
            print(f"{status}: Device {device['device_index']} - {device['device_name']}")
            print(f"   Audio level: {device['audio_level']:.4f}")
            print(f"   Settings: {device['settings']}")
            print()
            
        recommended = working_devices[0]
        print(f"🎯 RECOMMENDATION: Use device {recommended['device_index']}")
        print(f"   Name: {recommended['device_name']}")
        print(f"   Audio level: {recommended['audio_level']:.4f}")
        
        return recommended['device_index']
    
    def cleanup(self):
        """Clean up PyAudio"""
        self.audio.terminate()

def main():
    print("🎤 Audio Device Finder and Tester")
    print("=" * 50)
    
    finder = AudioDeviceFinder()
    
    try:
        # Get recommended device
        recommended_device = finder.get_recommended_device()
        
        if recommended_device is not None:
            print(f"\n🔧 To fix your application, update the device_index to: {recommended_device}")
            print("\nYou can edit main_adaptive.py and change:")
            print(f"   device_index = None  # Change this to device_index = {recommended_device}")
        else:
            print("\n❌ No working devices found. Check your microphone connections.")
            
    except KeyboardInterrupt:
        print("\n\nTesting interrupted by user")
    except Exception as e:
        print(f"\nError during testing: {e}")
    finally:
        finder.cleanup()

if __name__ == "__main__":
    main()
