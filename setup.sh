#!/bin/bash

# Exit on any error
set -e

echo "🚀 Setting up NV project environment..."

# Function to create output directories
create_output_directories() {
    echo "📁 Creating output directories..."
    
    # Create outputs directory
    if [ ! -d "outputs" ]; then
        mkdir -p outputs
        echo "   ✅ Created outputs/"
    else
        echo "   ℹ️  outputs/ already exists"
    fi
    
    # Create outputs/nifti directory
    if [ ! -d "outputs/nifti" ]; then
        mkdir -p outputs/nifti
        echo "   ✅ Created outputs/nifti/"
    else
        echo "   ℹ️  outputs/nifti/ already exists"
    fi
    
    # Create outputs/certs directory
    if [ ! -d "outputs/certs" ]; then
        mkdir -p outputs/certs
        echo "   ✅ Created outputs/certs/"
    else
        echo "   ℹ️  outputs/certs/ already exists"
    fi
    
    echo "   📂 Output directory structure ready"
}

# Function to start HTTPS image server in background
start_https_server() {
    echo "🌐 Starting HTTPS image server in background..."
    
    # Check if server is already running
    if pgrep -f "image_server.py" > /dev/null; then
        echo "   ℹ️  HTTPS image server is already running"
        return 0
    fi
    
    # Check if the server script exists
    if [ ! -f "utils/image_server.py" ]; then
        echo "   ⚠️  Warning: utils/image_server.py not found, skipping server startup"
        return 0
    fi
    
    # Start the server in background
    nohup python utils/image_server.py > outputs/server.log 2>&1 &
    SERVER_PID=$!
    
    # Wait a moment for server to start
    sleep 2
    
    # Check if server started successfully
    if kill -0 $SERVER_PID 2>/dev/null; then
        echo "   ✅ HTTPS image server started successfully (PID: $SERVER_PID)"
        echo "   📝 Server logs: outputs/server.log"
        echo "   🛑 To stop server: kill $SERVER_PID"
    else
        echo "   ❌ Failed to start HTTPS image server"
        return 1
    fi
}

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed. Please install uv first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "✅ uv is installed"

# Create output directories
create_output_directories

# Create virtual environment using uv
echo "🔧 Creating virtual environment..."
uv venv

# Activate the virtual environment
echo "🔌 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies from pyproject.toml
echo "📦 Installing dependencies from pyproject.toml..."
uv pip install -e .

# Start HTTPS image server
start_https_server

echo "✅ Setup completed successfully!"
echo ""
echo "📁 Output directories created:"
echo "   • outputs/"
echo "   • outputs/nifti/"
echo "   • outputs/certs/"
echo ""
echo "🌐 HTTPS image server status:"
if pgrep -f "image_server.py" > /dev/null; then
    SERVER_PID=$(pgrep -f "image_server.py")
    echo "   • Running (PID: $SERVER_PID)"
    echo "   • Logs: outputs/server.log"
else
    echo "   • Not running"
fi
echo ""
echo "To activate the environment in the future, run:"
echo "   source .venv/bin/activate"
echo ""
echo "To deactivate, run:"
echo "   deactivate"
echo ""
echo "To start the HTTPS server manually:"
echo "   source .venv/bin/activate && start_https_server"

