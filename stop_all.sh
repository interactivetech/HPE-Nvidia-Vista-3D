#!/bin/bash
# HPE NVIDIA Vista3D Master Stop Script

echo "🛑 Stopping HPE NVIDIA Vista3D Platform..."

# Stop frontend services (includes image server)
echo "Stopping frontend services (including image server)..."
cd frontend
if [ -f "stop_frontend.sh" ]; then
    ./stop_frontend.sh
else
    docker-compose down
    # Also stop image server
    cd ../image_server
    docker-compose down
    cd ../frontend
fi
cd ..



echo "✅ Platform stopped"
