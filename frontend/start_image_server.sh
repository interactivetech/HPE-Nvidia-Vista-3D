#!/bin/bash
# Start the local image server

set -e

cd "$(dirname "$0")/../image_server"

echo "🖼️  Starting local image server..."

if [ -f ".env" ]; then
    # Check if Docker is available
    if command -v docker &> /dev/null; then
        echo "Using Docker..."
        docker-compose up -d
        echo "✅ Image server started (Docker)"
        echo "📊 Check logs: docker-compose logs -f"
    else
        echo "Docker not found. Starting with Python..."
        if [ -f "server.py" ]; then
            python3 server.py &
            echo $! > .image_server.pid
            echo "✅ Image server started (Python)"
            echo "📊 Check logs: tail -f nohup.out"
        else
            echo "❌ server.py not found"
            exit 1
        fi
    fi
else
    echo "❌ .env file not found"
    exit 1
fi

echo "🌐 Image server: http://localhost:8888"
