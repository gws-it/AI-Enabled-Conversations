import threading
import queue
import sounddevice as sd
import numpy as np
import whisper
import time
import tempfile
import scipy.io.wavfile as wav

# "Authorization": 'Bearer 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'

listening = True

# Load Whisper model
model = whisper.load_model("base")  # Options: tiny, base, small, medium, large

# Thread-safe queue for audio chunks
audio_queue = queue.Queue()

def wait_for_enter():
    global listening
    input("Start talking. Press ENTER to stop.")
    listening = False

# Callback function for audio input
def callback(indata, frames, time_info, status):
    if listening:
        audio_queue.put(indata.copy())

# Start listening thread
listener_thread = threading.Thread(target=wait_for_enter)
listener_thread.start()

# Stream audio from microphone
samplerate = 16000  # Whisper model expects 16kHz
print("Recording...")
with sd.InputStream(callback=callback, channels=1, samplerate=samplerate):
    recorded_audio = []
    while listening:
        try:
            chunk = audio_queue.get(timeout=0.1)
            recorded_audio.append(chunk)
        except queue.Empty:
            continue

print("Processing...")

# Concatenate all recorded chunks into a single NumPy array
audio_np = np.concatenate(recorded_audio, axis=0)

# Save to temporary WAV file
with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
    wav.write(tmpfile.name, samplerate, (audio_np * 32767).astype(np.int16))
    result = model.transcribe(tmpfile.name)

print("Transcription:", result["text"])