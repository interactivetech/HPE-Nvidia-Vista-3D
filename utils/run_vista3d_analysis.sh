#!/bin/bash

# VISTA-3D API Analysis Runner
# This script runs the VISTA-3D API analysis with different configurations

echo "🔍 VISTA-3D Label Analysis Runner"
echo "=================================="

# Check if VISTA-3D is running
echo "Checking if VISTA-3D is running..."

# Try different common ports
PORTS=(8000 8080 5000 3000)
API_URL=""

for port in "${PORTS[@]}"; do
    if curl -s "http://localhost:$port/v1/vista3d/info" > /dev/null 2>&1; then
        API_URL="http://localhost:$port"
        echo "✅ Found VISTA-3D running on port $port"
        break
    fi
done

if [ -z "$API_URL" ]; then
    echo "❌ VISTA-3D not found on common ports (8000, 8080, 5000, 3000)"
    echo "Please make sure VISTA-3D is running and specify the correct URL:"
    echo "   python utils/query_vista3d_api.py --api-url http://your-vista3d-url:port"
    exit 1
fi

# Run the analysis
echo "Running analysis with API URL: $API_URL"
python utils/query_vista3d_api.py --api-url "$API_URL"

echo ""
echo "Analysis complete! Check the generated report file for details."
