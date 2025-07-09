#!/bin/bash

# Setup script for offline AI chat on Raspberry Pi 2
# Run this script to install all dependencies

echo "Setting up offline AI chat system..."

# Update system
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python dependencies
echo "Installing Python dependencies..."
sudo apt install -y python3-pip python3-venv

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv ~/ai_chat_env
source ~/ai_chat_env/bin/activate

# Install Python packages
echo "Installing Python packages..."
pip install flask flask-cors openai-whisper torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install Ollama
echo "Installing Ollama..."
curl -fsSL https://ollama.com/install.sh | sh

# Pull lightweight model
echo "Downloading AI model (this may take a while)..."
ollama pull llama3.2:3b

# Create systemd service for Whisper server
echo "Creating Whisper service..."
sudo tee /etc/systemd/system/whisper-server.service > /dev/null <<EOF
[Unit]
Description=Whisper Speech-to-Text Server
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi
Environment=PATH=/home/pi/ai_chat_env/bin
ExecStart=/home/pi/ai_chat_env/bin/python /home/pi/whisper_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start services
echo "Enabling services..."
sudo systemctl daemon-reload
sudo systemctl enable whisper-server
sudo systemctl enable ollama

# Start services
echo "Starting services..."
sudo systemctl start ollama
sudo systemctl start whisper-server

# Check service status
echo "Checking service status..."
sleep 5
sudo systemctl status whisper-server --no-pager
sudo systemctl status ollama --no-pager

echo "Setup complete!"
echo "Services should be running on:"
echo "- Whisper server: http://localhost:5000"
echo "- Ollama API: http://localhost:11434"
echo ""
echo "You can now open the HTML file in a web browser."
echo "To check logs: sudo journalctl -u whisper-server -f"