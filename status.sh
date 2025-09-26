#!/bin/bash
# HPE NVIDIA Vista3D Master Status Script

echo "📊 HPE NVIDIA Vista3D Platform Status"
echo "======================================"



# Check frontend
echo "Frontend (Web Interface):"
if docker ps | grep -q vista3d-frontend-standalone; then
    echo "  ✅ Running on http://localhost:8501"
else
    echo "  ❌ Not running"
fi

# Check image server
echo "Image Server:"
if docker ps | grep -q vista3d-image-server-standalone; then
    echo "  ✅ Running on http://localhost:8888"
else
    echo "  ❌ Not running"
fi

echo ""
echo "📊 All containers:"
docker ps --format "table {.Names}\t{.Status}\t{.Ports}"
