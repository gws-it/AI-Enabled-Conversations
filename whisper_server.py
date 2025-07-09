#!/usr/bin/env python3
"""
Local Whisper server for offline speech-to-text transcription
Designed for Raspberry Pi 2 with lightweight model
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import whisper
import tempfile
import os
import logging

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load Whisper model (using tiny model for RPi2)
logger.info("Loading Whisper model...")
try:
    model = whisper.load_model("tiny")  # Use "base" if you have more RAM
    logger.info("Whisper model loaded successfully")
except Exception as e:
    logger.error(f"Failed to load Whisper model: {e}")
    model = None

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    if model is None:
        return jsonify({"status": "error", "message": "Model not loaded"}), 500
    return jsonify({"status": "ok", "model": "whisper-tiny"})

@app.route('/transcribe', methods=['POST'])
def transcribe():
    """Transcribe audio file"""
    if model is None:
        return jsonify({"error": "Model not loaded"}), 500
    
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    try:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            file.save(tmp_file.name)
            tmp_filename = tmp_file.name
        
        logger.info(f"Transcribing file: {tmp_filename}")
        
        # Transcribe audio
        result = model.transcribe(tmp_filename)
        
        # Clean up temporary file
        os.unlink(tmp_filename)
        
        logger.info(f"Transcription result: {result['text']}")
        
        return jsonify({
            "text": result["text"],
            "language": result.get("language", "en")
        })
        
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        # Clean up temporary file if it exists
        if 'tmp_filename' in locals() and os.path.exists(tmp_filename):
            os.unlink(tmp_filename)
        return jsonify({"error": str(e)}), 500

@app.route('/models', methods=['GET'])
def get_models():
    """Get available models"""
    available_models = ["tiny", "base", "small", "medium", "large"]
    return jsonify({"models": available_models, "current": "tiny"})

if __name__ == '__main__':
    if model is None:
        logger.error("Cannot start server: Whisper model failed to load")
        exit(1)
    
    logger.info("Starting Whisper server on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=False)