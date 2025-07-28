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
import ssl
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import datetime

# visit https://192.168.0.129:5000/health to access this server

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

def generate_self_signed_cert():
    """Generate a self-signed certificate for HTTPS"""
    print("Generating self-signed SSL certificate...")
    
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    
    # Get your local IP address
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    # Create certificate
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "State"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "City"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Local Development"),
        x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
    ])
    
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        datetime.datetime.utcnow() + datetime.timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName("localhost"),
            x509.DNSName("127.0.0.1"),
            x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
            x509.IPAddress(ipaddress.IPv4Address(local_ip)),
        ]),
        critical=False,
    ).sign(private_key, hashes.SHA256())
    
    # Write certificate and key to files
    with open("cert.pem", "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    
    with open("key.pem", "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
    
    print(f"SSL certificate generated for localhost and {local_ip}")
    return True

if __name__ == '__main__':
    print("-" * 50)
    
    # Check if SSL certificates exist, if not generate them
    if not (os.path.exists('cert.pem') and os.path.exists('key.pem')):
        try:
            import ipaddress
            generate_self_signed_cert()
        except ImportError:
            print('Module not found, install required packages')
            app.run(host='0.0.0.0', port=5000)
            exit()
    
    # Create SSL context for HTTPS
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain('cert.pem', 'key.pem')
    
    
    # Get and display local IP
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"Local IP: https://{local_ip}:5000")
    print(f"Accept self-signed certificate at https://{local_ip}:5000/health")

    app.run(host='0.0.0.0', port=5000, ssl_context=context)