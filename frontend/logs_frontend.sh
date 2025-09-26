#!/bin/bash
# HPE NVIDIA Vista3D Frontend Logs Script

echo "📊 Viewing HPE NVIDIA Vista3D Frontend logs..."

# Show logs for frontend services
echo "🌐 Frontend logs:"
docker-compose logs -f --tail=50

# Show logs for image server
echo "🖼️  Image server logs:"
cd ../image_server
if [ -f "docker-compose.yml" ]; then
    docker-compose logs -f --tail=50
else
    echo "⚠️  Image server not found"
fi
cd ../frontend
