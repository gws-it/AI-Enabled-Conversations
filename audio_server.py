from flask import Flask, request, jsonify
from flask_cors import CORS
import whisper
import tempfile
import os
import io
import soundfile as sf
import numpy as np

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

print("\nLoading Whisper model...\n")
model = whisper.load_model("base")  # Options: tiny, base, small, medium, large
print("Whisper model loaded successfully!")

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    try:
        # Get the audio file from the request
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        
        # Save the uploaded audio to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
            audio_file.save(tmpfile.name)
            
            # Transcribe the audio
            result = model.transcribe(tmpfile.name)
            transcript = result['text'].strip()
            
            # Clean up the temporary file
            os.unlink(tmpfile.name)
            
            print(f"Transcribed: {transcript}")
            
            return jsonify({
                'success': True,
                'transcript': transcript
            })
            
    except Exception as e:
        print(f"Error during transcription: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'model': 'whisper-base'})

if __name__ == '__main__':
    print("Starting Flask server...")
    print("Server will be available at: http://localhost:5000")
    print("Transcription endpoint: http://localhost:5000/transcribe")
    print("-" * 50)
    app.run(host='localhost', port=5000, debug=True)
