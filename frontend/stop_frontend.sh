#!/bin/bash
# HPE NVIDIA Vista3D Frontend Stop Script

echo "🛑 Stopping HPE NVIDIA Vista3D Frontend..."

# Stop the frontend services
docker-compose down

# Stop the image server
echo "🖼️  Stopping image server..."
cd ../image_server
if [ -f "docker-compose.yml" ]; then
    docker-compose down
    echo "✅ Image server stopped"
else
    echo "⚠️  Image server docker-compose.yml not found"
fi
cd ../frontend

echo "✅ Frontend services stopped"
