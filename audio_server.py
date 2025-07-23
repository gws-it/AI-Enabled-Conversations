from flask import Flask, request, jsonify
from flask_cors import CORS
import whisper
import tempfile
import os
import io
import soundfile as sf
import numpy as np
import openai
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

print("\nLoading Whisper model...\n")
model = whisper.load_model("base")  # Options: tiny, base, small, medium, large
print("Whisper model loaded successfully!")

openai.api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI()

@app.route('/chat', methods=['POST'])
def chat_with_openai():
    try:
        data = request.get_json()
        messages = data.get('messages', [])

        print("Sending to OpenAI:", messages)

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )

        reply = response.choices[0].message.content
        print("Reply:", reply)

        return jsonify({'reply': reply})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    tmpfile_path = None
    try:
        # Get the audio file from the request
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        
        # Create a temporary file
        tmpfile_fd, tmpfile_path = tempfile.mkstemp(suffix=".wav")
        
        try:
            # Save the uploaded audio to the temporary file
            with os.fdopen(tmpfile_fd, 'wb') as tmp:
                audio_file.save(tmp)
            
            # Transcribe the audio
            result = model.transcribe(tmpfile_path)
            transcript = result['text'].strip()
            
            print(f"Transcribed: {transcript}")
            
            return jsonify({
                'success': True,
                'transcript': transcript
            })
            
        finally:
            # Clean up the temporary file
            try:
                if tmpfile_path and os.path.exists(tmpfile_path):
                    os.unlink(tmpfile_path)
            except PermissionError:
                # If we can't delete immediately, schedule for later cleanup
                print(f"Warning: Could not delete temporary file {tmpfile_path} immediately")
            
    except Exception as e:
        print(f"Error during transcription: {str(e)}")
        # Try to clean up on error too
        if tmpfile_path and os.path.exists(tmpfile_path):
            try:
                os.unlink(tmpfile_path)
            except:
                pass
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'model': 'whisper-base'})

if __name__ == '__main__':
    print("-" * 50)
    app.run(host='0.0.0.0', port=5000)
