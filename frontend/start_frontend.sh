#!/bin/bash
# Start the local frontend

set -e

cd "$(dirname "$0")"

echo "🌐 Starting local frontend..."

if [ -f ".env" ]; then
    # Load environment
    export $(cat .env | grep -v '^#' | xargs)
    
    # Check if we should use Docker or native
    if command -v streamlit &> /dev/null; then
        echo "Using native Streamlit..."
        streamlit run app.py --server.port ${FRONTEND_PORT:-8501}
    elif command -v docker &> /dev/null; then
        echo "Streamlit not found locally. Using Docker..."
        docker-compose up
    else
        echo "❌ Neither Streamlit nor Docker found"
        echo "Install Streamlit: pip install streamlit"
        exit 1
    fi
else
    echo "❌ .env file not found"
    exit 1
fi
