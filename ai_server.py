#!/usr/bin/env python3
"""
Lightweight AI Server for Raspberry Pi 2
Uses Vosk for speech recognition and a rule-based chatbot for responses
"""

import os
import json
import wave
import tempfile
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import vosk
import pyaudio
import random
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Initialize Vosk model
VOSK_MODEL_PATH = "vosk-model-small-en-us-0.15"
model = None

def download_vosk_model():
    """Download Vosk model if not present"""
    if not os.path.exists(VOSK_MODEL_PATH):
        print(f"Downloading Vosk model to {VOSK_MODEL_PATH}")
        print("Please download the model manually from:")
        print("https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip")
        print("Extract it to the current directory")
        return False
    return True

def init_vosk():
    """Initialize Vosk speech recognition"""
    global model
    if download_vosk_model():
        try:
            model = vosk.Model(VOSK_MODEL_PATH)
            logger.info("Vosk model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load Vosk model: {e}")
            return False
    return False

# Black Soldier Fly knowledge base and responses
BSF_KNOWLEDGE = {
    "greetings": [
        "Hello! I'm buzzing with excitement to chat with you!",
        "Hi there! Ready to learn about sustainable living?",
        "Greetings from the compost bin! How can I help you today?",
    ],
    "sustainability": [
        "As a black soldier fly, I'm all about sustainability! I turn organic waste into valuable protein and fertilizer.",
        "Sustainability is my life! I help reduce food waste by eating kitchen scraps and producing nutrient-rich compost.",
        "I'm a living example of circular economy - turning waste into resources! My larvae are great for composting.",
    ],
    "composting": [
        "Composting is what I do best! My larvae can process organic waste 10x faster than traditional composting.",
        "I love munching on food scraps! Fruit peels, vegetable waste, coffee grounds - bring it on!",
        "My larvae produce amazing fertilizer called frass. It's like black gold for plants!",
    ],
    "lifecycle": [
        "I start as a tiny larva, grow big eating organic waste, then pupate and emerge as a fly to mate and lay eggs.",
        "My lifecycle is fascinating! From egg to adult takes about 6 weeks, and I can live up to 2 weeks as an adult fly.",
        "As larvae, we're the real workers - eating up to twice our body weight daily in organic waste!",
    ],
    "singapore": [
        "Singapore is perfect for black soldier flies! The tropical climate means we can breed year-round.",
        "In Singapore, food waste is a big issue. We BSF can help process kitchen waste into valuable resources!",
        "The warm, humid weather in Singapore keeps us active and productive all year long.",
    ],
    "nutrition": [
        "My larvae are packed with protein - up to 45%! We're being explored as sustainable protein for animal feed.",
        "We larvae contain all essential amino acids and are rich in calcium and other minerals.",
        "Some humans even eat us! We're considered a sustainable protein source in many cultures.",
    ],
    "benefits": [
        "I help reduce landfill waste, create fertilizer, and produce sustainable protein - talk about multitasking!",
        "We black soldier flies don't bite, sting, or spread disease. We're the good guys of the insect world!",
        "Our larvae can reduce organic waste volume by up to 80% while creating valuable byproducts.",
    ],
    "default": [
        "That's an interesting question! As a black soldier fly, I'm most knowledgeable about composting and sustainability.",
        "Hmm, I'm not sure about that, but I'd love to tell you more about how I help with sustainable waste management!",
        "I might not know everything, but I'm an expert on turning waste into resources! Want to know more?",
    ]
}

def get_bsf_response(message):
    """Generate a response based on the message content"""
    message_lower = message.lower()
    
    # Check for greeting keywords
    if any(word in message_lower for word in ["hello", "hi", "hey", "greetings"]):
        return random.choice(BSF_KNOWLEDGE["greetings"])
    
    # Check for sustainability keywords
    elif any(word in message_lower for word in ["sustainability", "sustainable", "environment", "eco"]):
        return random.choice(BSF_KNOWLEDGE["sustainability"])
    
    # Check for composting keywords
    elif any(word in message_lower for word in ["compost", "waste", "organic", "decompose", "rot"]):
        return random.choice(BSF_KNOWLEDGE["composting"])
    
    # Check for lifecycle keywords
    elif any(word in message_lower for word in ["lifecycle", "life cycle", "grow", "develop", "larva", "larvae"]):
        return random.choice(BSF_KNOWLEDGE["lifecycle"])
    
    # Check for Singapore keywords
    elif any(word in message_lower for word in ["singapore", "tropical", "climate", "weather"]):
        return random.choice(BSF_KNOWLEDGE["singapore"])
    
    # Check for nutrition keywords
    elif any(word in message_lower for word in ["nutrition", "protein", "food", "eat", "amino"]):
        return random.choice(BSF_KNOWLEDGE["nutrition"])
    
    # Check for benefits keywords
    elif any(word in message_lower for word in ["benefit", "advantage", "help", "useful", "good"]):
        return random.choice(BSF_KNOWLEDGE["benefits"])
    
    # Default response
    else:
        return random.choice(BSF_KNOWLEDGE["default"])

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "vosk_loaded": model is not None,
        "message": "Black Soldier Fly AI Server is running"
    })

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    try:
        data = request.json
        message = data.get('message', '')
        
        if not message:
            return jsonify({"error": "No message provided"}), 400
        
        # Generate response
        reply = get_bsf_response(message)
        
        return jsonify({"reply": reply})
    
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/transcribe', methods=['POST'])
def transcribe():
    """Transcribe audio using Vosk"""
    try:
        if not model:
            return jsonify({"error": "Speech recognition not available"}), 503
        
        # Get uploaded audio file
        if 'file' not in request.files:
            return jsonify({"error": "No audio file provided"}), 400
        
        audio_file = request.files['file']
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            audio_file.save(tmp_file.name)
            
            try:
                # Read audio file
                with wave.open(tmp_file.name, 'rb') as wf:
                    # Check if it's mono 16kHz
                    if wf.getnchannels() != 1 or wf.getsampwidth() != 2:
                        return jsonify({"error": "Audio must be mono 16-bit"}), 400
                    
                    # Create recognizer
                    rec = vosk.KaldiRecognizer(model, wf.getframerate())
                    
                    # Process audio
                    results = []
                    while True:
                        data = wf.readframes(4000)
                        if len(data) == 0:
                            break
                        if rec.AcceptWaveform(data):
                            result = json.loads(rec.Result())
                            if result.get('text'):
                                results.append(result['text'])
                    
                    # Get final result
                    final_result = json.loads(rec.FinalResult())
                    if final_result.get('text'):
                        results.append(final_result['text'])
                    
                    # Combine all results
                    full_text = ' '.join(results).strip()
                    
                    return jsonify({"text": full_text})
                    
            finally:
                # Clean up temporary file
                os.unlink(tmp_file.name)
                
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return jsonify({"error": "Transcription failed"}), 500

@app.route('/images/<path:filename>')
def serve_image(filename):
    """Serve static images"""
    # This is a simple static file server
    # In production, use a proper web server like nginx
    try:
        from flask import send_from_directory
        return send_from_directory('images', filename)
    except:
        return jsonify({"error": "Image not found"}), 404

if __name__ == '__main__':
    print("Starting Black Soldier Fly AI Server...")
    print("=" * 50)
    
    # Initialize Vosk
    vosk_ready = init_vosk()
    if not vosk_ready:
        print("WARNING: Vosk speech recognition not available")
        print("Text chat will work, but voice input will be disabled")
    
    # Create images directory if it doesn't exist
    os.makedirs('images', exist_ok=True)
    
    print("Server starting on http://localhost:5000")
    print("Make sure to place your BSF image in the 'images' folder as 'bsf.png'")
    print("=" * 50)
    
    # Run the server
    app.run(host='0.0.0.0', port=5000, debug=False)