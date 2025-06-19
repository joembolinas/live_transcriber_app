import tkinter as tk
from tkinter import scrolledtext, messagebox, OptionMenu, StringVar, filedialog
import sounddevice as sd
import numpy as np
import threading
import queue
import time

# --- Configuration ---
MODEL_SIZE = "base"  # "tiny", "base", "small", "medium", "large"
SAMPLE_RATE = 16000  # Whisper prefers 16kHz
CHUNK_DURATION_SECONDS = 5  # Process audio in chunks of this duration
CHANNELS = 1

# --- Global Variables ---
audio_queue = queue.Queue()
transcript_queue = queue.Queue()
is_listening = False
stop_listening_event = threading.Event()
recording_thread = None
transcription_thread = None
whisper_model = None
selected_device_id = None

# Try to import whisper (either openai-whisper or faster-whisper)
whisper_available = False
use_faster_whisper = False

try:
    from faster_whisper import WhisperModel
    whisper_available = True
    use_faster_whisper = True
    print("Using faster-whisper")
except ImportError:
    try:
        import whisper
        whisper_available = True
        use_faster_whisper = False
        print("Using openai-whisper")
    except ImportError:
        whisper_available = False
        print("No whisper implementation available")

# --- Audio Handling ---
def list_audio_devices():
    devices = sd.query_devices()
    input_devices = {f"{i}: {dev['name']}": i for i, dev in enumerate(devices) if dev['max_input_channels'] > 0}
    # Try to find a loopback device for convenience
    default_device_name = None
    for name, idx in input_devices.items():
        if "loopback" in name.lower() or "stereo mix" in name.lower() or "what u hear" in name.lower():
            default_device_name = name
            break
    if not default_device_name and input_devices:
        default_device_name = list(input_devices.keys())[0] # Fallback to first mic
    return input_devices, default_device_name

def audio_callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, flush=True)
    if is_listening:
        audio_queue.put(indata.copy())

def find_working_device():
    """Automatically find a working audio device"""
    try:
        devices = sd.query_devices()
        input_devices = [(i, dev) for i, dev in enumerate(devices) if dev['max_input_channels'] > 0]
        
        # Try system default first (None)
        test_devices = [None] + [device_id for device_id, _ in input_devices]
        
        for device_id in test_devices:
            try:
                print(f"Testing device {device_id}...")
                
                # Try a very short recording
                test_recording = sd.rec(
                    frames=1000,  # Very short test
                    samplerate=SAMPLE_RATE,
                    channels=CHANNELS,
                    device=device_id,
                    dtype='float64'
                )
                sd.wait()
                
                if test_recording is not None:
                    print(f"✓ Device {device_id} works!")
                    return device_id
                    
            except Exception as e:
                print(f"✗ Device {device_id} failed: {e}")
                continue
                
        return None
    except Exception as e:
        print(f"Error finding working device: {e}")
        return None

def record_audio():
    global is_listening, selected_device_id
    
    # If no device selected, try to find one automatically
    if selected_device_id is None:
        print("No device selected. Searching for working device...")
        transcript_queue.put("[INFO] Searching for working audio device...\n")
        selected_device_id = find_working_device()
        
        if selected_device_id is None:
            print("Error: No working audio device found.")
            transcript_queue.put("ERROR: No working audio device found. Please check your microphone settings.\n")
            stop_listening_event.set()
            return

    stop_listening_event.clear()
    
    try:
        # Try multiple device configurations
        device_configs = [
            (selected_device_id, SAMPLE_RATE, CHANNELS),
            (selected_device_id, 44100, CHANNELS),
            (selected_device_id, 22050, CHANNELS),
            (None, SAMPLE_RATE, CHANNELS),  # System default
        ]
        
        for device_id, sample_rate, channels in device_configs:
            try:
                print(f"Trying device {device_id} at {sample_rate}Hz, {channels} channels...")
                
                with sd.InputStream(samplerate=sample_rate,
                                     device=device_id,
                                     channels=channels,
                                     callback=audio_callback,
                                     blocksize=int(sample_rate * CHUNK_DURATION_SECONDS)):
                    
                    device_name = "Default" if device_id is None else sd.query_devices(device_id)['name']
                    print(f"✓ Listening started on device: {device_name}")
                    transcript_queue.put(f"[INFO] Listening started on device: {device_name}\n")
                    
                    while not stop_listening_event.is_set():
                        time.sleep(0.1)
                    break  # If we get here, it worked
                    
            except Exception as device_error:
                print(f"✗ Device config failed: {device_error}")
                continue
        else:
            # If we get here, all configurations failed
            raise Exception("All audio device configurations failed")
            
    except Exception as e:
        print(f"Error during audio recording: {e}")
        transcript_queue.put(f"[ERROR] Audio recording error: {e}\n")
        transcript_queue.put("[INFO] Try selecting a different device or check your audio settings.\n")
    finally:
        print("Recording loop finished.")
        is_listening = False

def process_transcription():
    global whisper_model
    
    if not whisper_available:
        transcript_queue.put("[ERROR] No whisper implementation available. Audio will be processed for volume only.\n")
        process_audio_simple()
        return
    
    if whisper_model is None:
        try:
            print(f"Loading Whisper model: {MODEL_SIZE}...")
            transcript_queue.put(f"[INFO] Loading Whisper model ({MODEL_SIZE})... This may take a moment.\n")
            
            if use_faster_whisper:
                whisper_model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
            else:
                whisper_model = whisper.load_model(MODEL_SIZE)
                
            transcript_queue.put(f"[INFO] Whisper model loaded.\n")
            print("Whisper model loaded.")
        except Exception as e:
            print(f"Error loading Whisper model: {e}")
            transcript_queue.put(f"[ERROR] Could not load Whisper model: {e}\n")
            stop_listening_event.set()
            return

    while not stop_listening_event.is_set() or not audio_queue.empty():
        try:
            audio_data_chunk = audio_queue.get(timeout=1)
            
            # Convert to float32, Whisper expects this
            audio_float32 = audio_data_chunk.astype(np.float32).flatten()

            # Transcribe using the appropriate method
            if use_faster_whisper:
                segments, info = whisper_model.transcribe(audio_float32, language=None)
                detected_language = info.language
                text = " ".join([segment.text for segment in segments]).strip()
            else:
                result = whisper_model.transcribe(audio_float32, fp16=False)
                detected_language = result['language']
                text = result['text'].strip()

            if not text: # Skip empty transcriptions
                continue

            final_text = f"[{detected_language.upper()}] {text}"

            if detected_language == 'tl': # Tagalog
                transcript_queue.put(f"[INFO] Tagalog detected. Translating to English...\n")
                if use_faster_whisper:
                    segments, info = whisper_model.transcribe(audio_float32, language='tl', task='translate')
                    translated_text = " ".join([segment.text for segment in segments]).strip()
                else:
                    translation_result = whisper_model.transcribe(audio_float32, language='tl', task='translate', fp16=False)
                    translated_text = translation_result['text'].strip()
                final_text = f"[TL > EN] {translated_text}"
            
            transcript_queue.put(final_text + "\n")

        except queue.Empty:
            continue
        except Exception as e:
            print(f"Error during transcription: {e}")
            transcript_queue.put(f"[ERROR] Transcription error: {e}\n")
    print("Transcription loop finished.")

def process_audio_simple():
    """Fallback audio processing when whisper is not available"""
    while not stop_listening_event.is_set() or not audio_queue.empty():
        try:
            audio_data_chunk = audio_queue.get(timeout=1)
            
            # Calculate audio level (volume) for demonstration
            audio_float32 = audio_data_chunk.astype(np.float32).flatten()
            volume_level = np.sqrt(np.mean(audio_float32**2))
            
            if volume_level > 0.01:  # Only show if there's significant audio
                transcript_queue.put(f"[AUDIO] Volume level: {volume_level:.4f} (Whisper not available)\n")
            
        except queue.Empty:
            continue
        except Exception as e:
            print(f"Error during audio processing: {e}")
            transcript_queue.put(f"[ERROR] Audio processing error: {e}\n")
    print("Audio processing loop finished.")

# --- GUI Handling ---
class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        
        title = "Live Transcriber"
        if not whisper_available:
            title += " (Audio Test Mode - Whisper Not Available)"
        elif use_faster_whisper:
            title += " (Faster-Whisper)"
        else:
            title += " (OpenAI-Whisper)"
            
        self.master.title(title)
        self.master.geometry("700x500")
        self.pack(fill=tk.BOTH, expand=True)
        self.create_widgets()
        self.update_transcript_display()

        self.input_devices, default_device = list_audio_devices()
        if not self.input_devices:
            messagebox.showerror("Audio Error", "No input audio devices found! Please check your microphone/system audio settings.")
            self.listen_button.config(state=tk.DISABLED)
        else:
            self.device_var.set(default_device if default_device else list(self.input_devices.keys())[0])
            self.device_menu['menu'].delete(0, 'end')
            for device_name in self.input_devices.keys():
                self.device_menu['menu'].add_command(label=device_name, command=tk._setit(self.device_var, device_name))
            self.on_device_select()

    def create_widgets(self):
        # Controls Frame
        controls_frame = tk.Frame(self)
        controls_frame.pack(pady=10, padx=10, fill=tk.X)

        self.listen_button = tk.Button(controls_frame, text="LISTEN NOW", command=self.toggle_listening, width=15, height=2)
        self.listen_button.pack(side=tk.LEFT, padx=(0,10))

        save_text = "Save Transcript" if whisper_available else "Save Log"
        self.save_button = tk.Button(controls_frame, text=save_text, command=self.save_transcript, state=tk.DISABLED)
        self.save_button.pack(side=tk.LEFT, padx=(0,10))
        
        # Device Selection
        tk.Label(controls_frame, text="Audio Device:").pack(side=tk.LEFT, padx=(10,5))
        self.device_var = StringVar(self.master)
        self.device_menu = OptionMenu(controls_frame, self.device_var, "No devices found", command=self.on_device_select_event)
        self.device_menu.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Status info
        if not whisper_available:
            info_frame = tk.Frame(self)
            info_frame.pack(pady=5, padx=10, fill=tk.X)
            info_label = tk.Label(info_frame, 
                                 text="NOTE: Whisper not installed. Install 'openai-whisper' or 'faster-whisper' for transcription.", 
                                 fg="orange", font=("Arial", 9, "italic"))
            info_label.pack()

        # Transcript Display Panel
        self.transcript_panel = scrolledtext.ScrolledText(self, wrap=tk.WORD, state='disabled', font=("Arial", 10))
        self.transcript_panel.pack(padx=10, pady=(0,10), fill=tk.BOTH, expand=True)
        self.transcript_panel.bind("<1>", lambda event: self.transcript_panel.focus_set())

    def on_device_select_event(self, selected_device_name):
        self.on_device_select()

    def on_device_select(self):
        global selected_device_id
        selected_name = self.device_var.get()
        if self.input_devices and selected_name in self.input_devices:
            selected_device_id = self.input_devices[selected_name]
            print(f"Selected audio device: {selected_name} (ID: {selected_device_id})")
            if is_listening:
                self.stop_listening_actions()
                self.start_listening_actions()
        elif not self.input_devices:
            selected_device_id = None
            print("No input devices available for selection.")
        else:
            selected_device_id = None
            print(f"Warning: Selected device '{selected_name}' not found in cached list.")

    def toggle_listening(self):
        global is_listening, recording_thread, transcription_thread

        if not selected_device_id and not is_listening:
             messagebox.showerror("Device Error", "Please select a valid audio input device first.")
             return

        if is_listening:
            self.stop_listening_actions()
        else:
            self.start_listening_actions()

    def start_listening_actions(self):
        global is_listening, recording_thread, transcription_thread, audio_queue, transcript_queue
        
        # Allow starting even without device selected - will auto-find
        # if not selected_device_id:
        #     messagebox.showwarning("No Device", "Cannot start listening. No audio device is properly selected.")
        #     return

        is_listening = True
        stop_listening_event.clear()

        # Clear queues
        audio_queue = queue.Queue()
        # Don't clear transcript queue completely, just add a separator
        transcript_queue.put("\n--- New Session ---\n")

        recording_thread = threading.Thread(target=record_audio, daemon=True)
        transcription_thread = threading.Thread(target=process_transcription, daemon=True)

        recording_thread.start()
        transcription_thread.start()

        self.listen_button.config(text="STOP LISTENING")
        self.save_button.config(state=tk.DISABLED)
        self.device_menu.config(state=tk.DISABLED)

    def stop_listening_actions(self):
        global is_listening
        if not is_listening and not stop_listening_event.is_set():
            return

        is_listening = False
        stop_listening_event.set()

        self.listen_button.config(text="Processing...", state=tk.DISABLED)

    def update_gui_after_stop(self):
        """Called when threads are confirmed stopped."""
        self.listen_button.config(text="LISTEN NOW", state=tk.NORMAL)
        self.save_button.config(state=tk.NORMAL)
        self.device_menu.config(state=tk.NORMAL)
        transcript_queue.put("[INFO] Listening stopped.\n")

    def update_transcript_display(self):
        try:
            while not transcript_queue.empty():
                message = transcript_queue.get_nowait()
                self.transcript_panel.config(state='normal')
                self.transcript_panel.insert(tk.END, message)
                self.transcript_panel.see(tk.END)
                self.transcript_panel.config(state='disabled')
        except queue.Empty:
            pass
        
        if stop_listening_event.is_set() and self.listen_button['text'] == "Processing...":
            if (not recording_thread or not recording_thread.is_alive()) and \
               (not transcription_thread or not transcription_thread.is_alive()) and \
               audio_queue.empty():
                self.update_gui_after_stop()

        self.master.after(100, self.update_transcript_display)

    def save_transcript(self):
        transcript_content = self.transcript_panel.get(1.0, tk.END).strip()
        if not transcript_content:
            messagebox.showinfo("Empty Content", "Nothing to save.")
            return

        default_ext = ".txt"
        file_types = [("Text files", "*.txt"), ("All files", "*.*")]
        title = "Save Transcript As" if whisper_available else "Save Audio Log As"
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=default_ext,
            filetypes=file_types,
            title=title
        )
        if filepath:
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(transcript_content)
                messagebox.showinfo("Success", f"Content saved to {filepath}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save: {e}")
    
    def on_closing(self):
        global is_listening
        if is_listening:
            if messagebox.askyesno("Quit", "Still listening. Are you sure you want to quit? This will stop the recording."):
                self.stop_listening_actions()
                time.sleep(0.5)
                self.master.destroy()
            else:
                return
        else:
            self.master.destroy()

# --- Main Execution ---
if __name__ == "__main__":
    root = tk.Tk()
    app = Application(master=root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
