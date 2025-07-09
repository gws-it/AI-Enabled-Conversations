#!/bin/bash

echo "Updating system..."
sudo apt update && sudo apt upgrade -y

echo "Installing dependencies..."
sudo apt install -y git build-essential cmake python3-pip python3-venv sox

# whisper.cpp setup
echo "Cloning whisper.cpp..."
cd ~
git clone https://github.com/ggerganov/whisper.cpp.git
cd whisper.cpp
make

echo "Downloading tiny.en model..."
./models/download-ggml-model.sh tiny.en

# llama.cpp setup
echo "Cloning llama.cpp..."
cd ~
git clone https://github.com/ggerganov/llama.cpp.git
cd llama.cpp
make

echo "Downloading tiny LLaMA model..."
curl -L -o models/stories.ggml.q4_0.bin https://huggingface.co/erfanzar/ggml-llama-7b-tiny/resolve/main/ggml-llama-7b-tiny-q4_0.bin

# Python server setup
echo "Setting up Python environment..."
cd ~
python3 -m venv ai_env
source ~/ai_env/bin/activate
pip install flask flask-cors

echo "Done! You can now run: source ~/ai_env/bin/activate && python ~/ai_server.py"
