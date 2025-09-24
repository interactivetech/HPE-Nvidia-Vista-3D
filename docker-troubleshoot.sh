#!/bin/bash

# Docker troubleshooting script for Vista3D application

echo "🔍 Docker Vista3D Troubleshooting Script"
echo "========================================"
echo ""

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

echo "✅ Docker is running"

# Check if docker-compose is available
if command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
elif docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    echo "❌ Neither docker-compose nor 'docker compose' is available"
    exit 1
fi

echo "✅ Docker Compose is available ($COMPOSE_CMD)"

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Running setup..."
    ./setup-env.sh
fi

echo "✅ Environment configuration ready"

# Show current container status
echo ""
echo "📊 Current Container Status:"
$COMPOSE_CMD ps

echo ""
echo "🔧 Available Commands:"
echo "  • Start services:     $COMPOSE_CMD up"
echo "  • Start in background: $COMPOSE_CMD up -d"
echo "  • View logs:          $COMPOSE_CMD logs"
echo "  • View specific logs: $COMPOSE_CMD logs vista3d-app"
echo "  • Stop services:      $COMPOSE_CMD down"
echo "  • Rebuild:            $COMPOSE_CMD up --build"
echo ""

# Check if ports are in use
echo "🌐 Port Usage Check:"
for port in 8501 8888 8000; do
    if lsof -i :$port >/dev/null 2>&1; then
        echo "  ⚠️  Port $port is in use:"
        lsof -i :$port | grep LISTEN
    else
        echo "  ✅ Port $port is available"
    fi
done

echo ""
echo "🚀 To start the application:"
echo "   $COMPOSE_CMD up --build"
