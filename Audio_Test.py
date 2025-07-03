import threading
import queue
import sounddevice as sd
import numpy as np
import whisper
import time
import tempfile
import scipy.io.wavfile as wav
import sys
import msvcrt
from openai import OpenAI

listening = False
running = True
audio_queue = queue.Queue()

print("\nLoading Whisper model...\n")
model = whisper.load_model("base")  # Options: tiny, base, small, medium, large

def get_key():
    return msvcrt.getch().decode('utf-8')

def input_handler():
    global listening, running
    
    print('------------------------------------------------')
    print("Controls:")
    print("- Press ENTER to start/stop recording")
    print("- Press SPACE to quit the program")
    print('------------------------------------------------')

    print("\nPress ENTER to start recording")
    
    while running:
        try:
            key = get_key()
            
            if key == '\r' or key == '\n':  # Enter key
                if not listening:
                    # Start recording
                    listening = True
                    print('\n------------------------------------------------\n')
                    print("Recording... Press ENTER to stop")
                else:
                    # Stop recording
                    listening = False
                    print("Recording stopped, processing audio...")
                    
            elif key == ' ':  # Space key
                print("\nExiting...")
                listening = False
                running = False
                break
                
        except KeyboardInterrupt:
            print("\nExiting...")
            listening = False
            running = False
            break

# Callback function for audio input
def callback(indata, frames, time_info, status):
    if listening:
        audio_queue.put(indata.copy())

# Start input handler thread
input_thread = threading.Thread(target=input_handler, daemon=True)
input_thread.start()

# Stream audio from microphone
samplerate = 16000  # Whisper model expects 16kHz

with sd.InputStream(callback=callback, channels=1, samplerate=samplerate):
    while running:
        if listening:
            recorded_audio = []
            while listening and running:
                try:
                    chunk = audio_queue.get(timeout=0.1)
                    recorded_audio.append(chunk)
                except queue.Empty:
                    continue
            
            # Process the recorded audio if we have any
            if recorded_audio and running:
                
                # Concatenate all recorded chunks into a single NumPy array
                audio_np = np.concatenate(recorded_audio, axis=0)
                
                # Save to temporary WAV file and transcribe
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
                    wav.write(tmpfile.name, samplerate, (audio_np * 32767).astype(np.int16))
                    result = model.transcribe(tmpfile.name)

                user_transcription = result['text'].strip()
                print('------------------------------------------------')
                print(f"\nUser: {user_transcription}\n")
                
                # Feed into AI and get response
                client = OpenAI(api_key='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')

                response = client.responses.create(
                    model = 'gpt-4.1-mini',
                    instructions = 'You are a black soldier fly in a compost bin in Singapore. Answer the question as if you were the fly,' \
                    ' and make the answer informative and engaging, yet concise (Try to keep it under 50 words)',
                    input = user_transcription
                )

                print("Black Soldier Fly:", response.output_text + '\n')
                print('------------------------------------------------')

                if running:
                    print("\nPress ENTER to record again, or SPACE to quit.")
        else:
            # Small delay when not listening
            time.sleep(0.1)