#!/bin/bash
# HPE NVIDIA Vista3D Master Start Script

set -e

echo "🚀 Starting HPE NVIDIA Vista3D Platform..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please run setup.py first."
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check if Docker Hub images are available
echo "🔍 Checking Docker Hub images..."

# Check frontend image
if ! docker image inspect ${FRONTEND_IMAGE:-dwtwp/vista3d-frontend:latest} > /dev/null 2>&1; then
    echo "📥 Pulling frontend image from Docker Hub..."
    if ! docker pull ${FRONTEND_IMAGE:-dwtwp/vista3d-frontend:latest}; then
        echo "❌ Failed to pull frontend image. Please check your internet connection and Docker Hub access."
        exit 1
    fi
fi

# Check image server image
if ! docker image inspect ${IMAGE_SERVER_IMAGE:-dwtwp/vista3d-image-server:latest} > /dev/null 2>&1; then
    echo "📥 Pulling image server image from Docker Hub..."
    if ! docker pull ${IMAGE_SERVER_IMAGE:-dwtwp/vista3d-image-server:latest}; then
        echo "❌ Failed to pull image server image. Please check your internet connection and Docker Hub access."
        exit 1
    fi
fi



# Start frontend services (includes image server)
echo "🌐 Starting frontend services (including image server)..."
cd frontend
if [ -f "start_frontend.sh" ]; then
    ./start_frontend.sh
else
    docker-compose up -d
fi
cd ..

echo "🎉 Platform startup complete!"
echo "🌐 Web Interface: http://localhost:${FRONTEND_PORT:-8501}"

echo "🖼️  Image Server: http://localhost:8888"
