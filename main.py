import tkinter as tk
from tkinter import scrolledtext, messagebox, OptionMenu, StringVar, filedialog
import sounddevice as sd
import numpy as np
import whisper
import threading
import queue
import wave
import os
import tempfile
import time

# --- Configuration ---
MODEL_SIZE = "base"  # "tiny", "base", "small", "medium", "large". "base" is a good start.
# "base.en" or "tiny.en" if you ONLY want English and faster performance.
# For Tagalog detection and translation, a multilingual model (not ".en") is needed.

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

def record_audio():
    global is_listening, selected_device_id
    
    if selected_device_id is None:
        print("Error: No audio device selected.")
        # Potentially update GUI from here if it's safe or use transcript_queue to send error
        transcript_queue.put("ERROR: No audio device selected. Please select one and restart.\n")
        # Ensure GUI is updated to reflect stop
        stop_listening_event.set() # Signal other parts to stop
        update_gui_after_stop()
        return

    stop_listening_event.clear()
    
    try:
        with sd.InputStream(samplerate=SAMPLE_RATE,
                             device=selected_device_id,
                             channels=CHANNELS,
                             callback=audio_callback,
                             blocksize=int(SAMPLE_RATE * CHUNK_DURATION_SECONDS)): # Blocksize defines how often callback is called
            print(f"Listening started on device ID {selected_device_id}...")
            transcript_queue.put(f"[INFO] Listening started on device: {sd.query_devices(selected_device_id)['name']}\n")
            while not stop_listening_event.is_set():
                time.sleep(0.1) # Keep thread alive while InputStream callback works
    except Exception as e:
        print(f"Error during audio recording: {e}")
        transcript_queue.put(f"[ERROR] Audio recording error: {e}\n")
    finally:
        print("Recording loop finished.")
        is_listening = False # Ensure this is reset
        # No need to call update_gui_after_stop here, toggle_listening handles it

def process_transcription():
    global whisper_model
    if whisper_model is None:
        try:
            print(f"Loading Whisper model: {MODEL_SIZE}...")
            transcript_queue.put(f"[INFO] Loading Whisper model ({MODEL_SIZE})... This may take a moment.\n")
            whisper_model = whisper.load_model(MODEL_SIZE)
            transcript_queue.put(f"[INFO] Whisper model loaded.\n")
            print("Whisper model loaded.")
        except Exception as e:
            print(f"Error loading Whisper model: {e}")
            transcript_queue.put(f"[ERROR] Could not load Whisper model: {e}\nPlease ensure ffmpeg is installed and in PATH.\n")
            # Signal stop if model fails to load
            stop_listening_event.set()
            update_gui_after_stop()
            return

    while not stop_listening_event.is_set() or not audio_queue.empty():
        try:
            audio_data_chunk = audio_queue.get(timeout=1) # Wait 1 sec
            
            # Convert to float32, Whisper expects this
            audio_float32 = audio_data_chunk.astype(np.float32).flatten()

            # Transcribe
            # No need to save to temp file if passing numpy array directly
            result = whisper_model.transcribe(audio_float32, fp16=False) # fp16=False for CPU, can be True for CUDA
            
            detected_language = result['language']
            text = result['text'].strip()

            if not text: # Skip empty transcriptions
                continue

            final_text = f"[{detected_language.upper()}] {text}"

            if detected_language == 'tl': # Tagalog
                # Translate Tagalog to English
                # For translation, Whisper needs the language specified
                # We use the same audio_float32 data
                transcript_queue.put(f"[INFO] Tagalog detected. Translating to English...\n")
                translation_result = whisper_model.transcribe(audio_float32, language='tl', task='translate', fp16=False)
                translated_text = translation_result['text'].strip()
                final_text = f"[TL > EN] {translated_text}"
            
            transcript_queue.put(final_text + "\n")

        except queue.Empty:
            continue # No audio data, just loop and check stop_listening_event
        except Exception as e:
            print(f"Error during transcription: {e}")
            transcript_queue.put(f"[ERROR] Transcription error: {e}\n")
            # Consider whether to stop all on transcription error, or just log and continue
            # For now, let's log and continue
    print("Transcription loop finished.")


# --- GUI Handling ---
class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title("Live Transcriber")
        self.master.geometry("700x500")
        self.pack(fill=tk.BOTH, expand=True)
        self.create_widgets()
        self.update_transcript_display() # Start polling the transcript queue

        self.input_devices, default_device = list_audio_devices()
        if not self.input_devices:
            messagebox.showerror("Audio Error", "No input audio devices found! Please check your microphone/system audio settings.")
            self.listen_button.config(state=tk.DISABLED)
            self.device_dropdown.config(state=tk.DISABLED)
        else:
            self.device_var.set(default_device if default_device else list(self.input_devices.keys())[0])
            self.device_menu['menu'].delete(0, 'end')
            for device_name in self.input_devices.keys():
                self.device_menu['menu'].add_command(label=device_name, command=tk._setit(self.device_var, device_name))
            self.on_device_select() # Set initial selected_device_id

    def create_widgets(self):
        # Controls Frame
        controls_frame = tk.Frame(self)
        controls_frame.pack(pady=10, padx=10, fill=tk.X)

        self.listen_button = tk.Button(controls_frame, text="LISTEN NOW", command=self.toggle_listening, width=15, height=2)
        self.listen_button.pack(side=tk.LEFT, padx=(0,10))

        self.save_button = tk.Button(controls_frame, text="Save Transcript", command=self.save_transcript, state=tk.DISABLED)
        self.save_button.pack(side=tk.LEFT, padx=(0,10))
        
        # Device Selection
        tk.Label(controls_frame, text="Audio Device:").pack(side=tk.LEFT, padx=(10,5))
        self.device_var = StringVar(self.master)
        self.device_menu = OptionMenu(controls_frame, self.device_var, "No devices found", command=self.on_device_select_event)
        self.device_menu.pack(side=tk.LEFT, fill=tk.X, expand=True)


        # Transcript Display Panel (Notepad-like)
        self.transcript_panel = scrolledtext.ScrolledText(self, wrap=tk.WORD, state='disabled', font=("Arial", 10))
        self.transcript_panel.pack(padx=10, pady=(0,10), fill=tk.BOTH, expand=True)
        # Allow selection and copying even when disabled
        self.transcript_panel.bind("<1>", lambda event: self.transcript_panel.focus_set())


    def on_device_select_event(self, selected_device_name): # Event from OptionMenu
        self.on_device_select()

    def on_device_select(self): # Called internally or by event
        global selected_device_id
        selected_name = self.device_var.get()
        if self.input_devices and selected_name in self.input_devices:
            selected_device_id = self.input_devices[selected_name]
            print(f"Selected audio device: {selected_name} (ID: {selected_device_id})")
            if is_listening: # If listening, restart with new device
                self.stop_listening_actions()
                self.start_listening_actions()
        elif not self.input_devices:
            selected_device_id = None
            print("No input devices available for selection.")
        else:
            selected_device_id = None # Or handle error
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
        
        if not selected_device_id:
             messagebox.showwarning("No Device", "Cannot start listening. No audio device is properly selected.")
             return

        is_listening = True
        stop_listening_event.clear()

        # Clear queues
        audio_queue = queue.Queue()
        transcript_queue = queue.Queue() # Also clear transcript queue for new session

        # Clear previous transcript from display
        self.transcript_panel.config(state='normal')
        # self.transcript_panel.delete(1.0, tk.END) # Option: clear previous transcript
        self.transcript_panel.config(state='disabled')

        recording_thread = threading.Thread(target=record_audio, daemon=True)
        transcription_thread = threading.Thread(target=process_transcription, daemon=True)

        recording_thread.start()
        transcription_thread.start()

        self.listen_button.config(text="STOP LISTENING")
        self.save_button.config(state=tk.DISABLED)
        self.device_menu.config(state=tk.DISABLED) # Disable device change while listening

    def stop_listening_actions(self):
        global is_listening
        if not is_listening and not stop_listening_event.is_set(): # Already stopping or stopped
            return

        is_listening = False
        stop_listening_event.set() # Signal threads to stop

        self.listen_button.config(text="Processing...", state=tk.DISABLED) # Indicate processing remaining audio
        
        # The update_gui_after_stop will be called from update_transcript_display
        # when threads are confirmed to be done or after a timeout.

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
                self.transcript_panel.see(tk.END)  # Scroll to the end
                self.transcript_panel.config(state='disabled')
        except queue.Empty:
            pass # No new messages
        
        # Check if threads are done after a stop signal
        if stop_listening_event.is_set() and self.listen_button['text'] == "Processing...":
            # A bit of a simplification: assume threads will finish soon after event is set
            # More robust: check recording_thread.is_alive() and transcription_thread.is_alive()
            # However, transcription_thread might still be processing the last chunk from audio_queue
            if (not recording_thread or not recording_thread.is_alive()) and \
               (not transcription_thread or not transcription_thread.is_alive()) and \
               audio_queue.empty(): # Ensure audio_queue is also empty
                self.update_gui_after_stop()


        self.master.after(100, self.update_transcript_display) # Poll queue every 100ms

    def save_transcript(self):
        transcript_content = self.transcript_panel.get(1.0, tk.END).strip()
        if not transcript_content:
            messagebox.showinfo("Empty Transcript", "Nothing to save.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Save Transcript As"
        )
        if filepath:
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(transcript_content)
                messagebox.showinfo("Success", f"Transcript saved to {filepath}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save transcript: {e}")
    
    def on_closing(self):
        global is_listening
        if is_listening:
            if messagebox.askyesno("Quit", "Still listening. Are you sure you want to quit? This will stop the recording."):
                self.stop_listening_actions()
                # Give threads a moment to attempt to close
                # For a clean exit, you'd wait for threads here, but for GUI apps, forceful exit is common.
                time.sleep(0.5) # brief pause
                self.master.destroy()
            else:
                return # Do not close
        else:
            self.master.destroy()


# --- Main Execution ---
if __name__ == "__main__":
    root = tk.Tk()
    app = Application(master=root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing) # Handle window close button
    app.mainloop()

