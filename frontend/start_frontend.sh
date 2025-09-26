#!/bin/bash
# HPE NVIDIA Vista3D Frontend Startup Script

set -e

echo "🚀 Starting HPE NVIDIA Vista3D Frontend (Development Mode)..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please run setup_frontend.py first."
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if required images exist, pull from Docker Hub if needed
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

# Start the image server first
echo "🖼️  Starting image server (development mode)..."
cd ../image_server
if [ -f "docker-compose.yml" ]; then
    docker-compose up -d
    echo "✅ Image server started (development mode)"
else
    echo "❌ Image server docker-compose.yml not found"
    exit 1
fi
cd ../frontend

# Start the frontend services
echo "🌐 Starting frontend services..."
docker-compose up -d

# Wait for the services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 15

# Check if the services are running
if docker ps | grep -q vista3d-frontend-standalone; then
    echo "✅ Frontend is running on http://localhost:${FRONTEND_PORT:-8501}"
    echo "🔄 Development mode: Code changes will auto-reload"
else
    echo "❌ Frontend failed to start"
    echo "📊 Check logs with: docker logs vista3d-frontend-standalone"
    exit 1
fi

if docker ps | grep -q vista3d-image-server-standalone; then
    echo "✅ Image server is running on http://localhost:${IMAGE_SERVER_PORT:-8888}"
    echo "🔄 Image server development mode: Code changes will auto-reload"
else
    echo "❌ Image server failed to start"
    echo "📊 Check logs with: docker logs vista3d-image-server-standalone"
    exit 1
fi

echo "🎉 Frontend setup complete!"
echo "🌐 Web Interface: http://localhost:${FRONTEND_PORT:-8501}"
echo "🖼️  Image Server: http://localhost:${IMAGE_SERVER_PORT:-8888}"
echo "🔄 Development: Edit code in both frontend and image server and see changes automatically!"
echo "📊 Check logs with: docker-compose logs -f"
