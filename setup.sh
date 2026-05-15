#!/bin/bash

echo "========================================="
echo "⚙️ Setting up OptiC Environment..."
echo "========================================="

echo "[1/4] Installing system dependencies (Graphviz)..."
sudo apt-get update
sudo apt-get install -y graphviz python3-venv python3-pip

echo "[2/4] Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "[3/4] Installing Python Backend requirements..."
pip install flask flask-cors networkx pycparser graphviz
pip freeze > requirements.txt

echo "[4/4] Setting up Next.js Frontend..."
cd frontend
rm -rf node_modules package-lock.json
npm cache clean --force
npm install --legacy-peer-deps

echo "========================================="
echo "✅ Setup Complete! You can now run ./start.sh"
echo "========================================="
