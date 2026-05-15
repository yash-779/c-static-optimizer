#!/bin/bash

# Trap ensures that if you press Ctrl+C, both servers stop.
trap "kill 0" EXIT

echo "========================================="
echo "🚀 Starting OptiC Servers..."
echo "========================================="

echo "Starting Flask Backend (Port 5000)..."
source venv/bin/activate
python app.py &

sleep 2 

echo "Starting Next.js Frontend (Port 3000)..."
cd frontend
npm run dev &

echo "========================================================"
echo "✨ Application is running!"
echo "👉 Open your browser and go to: http://localhost:3000"
echo "🛑 Press Ctrl+C in this terminal to stop both servers."
echo "========================================================"

wait
