
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import subprocess
import tempfile

app = Flask(__name__)
CORS(app)

WHISPER_MODEL = "/home/pi/whisper.cpp/models/ggml-tiny.en.bin"
LLAMA_MODEL = "/home/pi/llama.cpp/models/stories.ggml.q4_0.bin"

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    audio_file = request.files['file']
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_wav:
        audio_file.save(temp_wav.name)
        output = subprocess.run(
            ["/home/pi/whisper.cpp/main", "-m", WHISPER_MODEL, "-f", temp_wav.name, "-otxt"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        txt_file = temp_wav.name + ".txt"
        if os.path.exists(txt_file):
            with open(txt_file, 'r') as f:
                text = f.read().strip()
            os.remove(txt_file)
            os.remove(temp_wav.name)
            return jsonify({'text': text})
        else:
            return jsonify({'error': 'Transcription failed'}), 500

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '')
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    prompt = f"### Instruction:\nYou are a black soldier fly in a compost bin. Answer simply about compost, sustainability, or your life.\n\n### User:\n{user_message}\n\n### Response:\n"

    result = subprocess.run(
        ["/home/pi/llama.cpp/main", "-m", LLAMA_MODEL, "-p", prompt, "-n", "100"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    reply = result.stdout.strip()
    return jsonify({'reply': reply})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
