#!/bin/bash

# Setup script for Docker environment variables
# This creates a .env file with the necessary environment variables

echo "Setting up Docker environment variables..."

# Get the current directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create .env file
cat > .env << EOF
# DICOM folder location - ABSOLUTE PATH
DICOM_FOLDER=${PROJECT_DIR}/dicom

# Output folder - ABSOLUTE PATH  
OUTPUT_FOLDER=${PROJECT_DIR}/output

# Local HTTP Image Server (for your local machine)
IMAGE_SERVER=http://localhost:8888

# Remote Vista3D server URL
VISTA3D_SERVER=http://your-remote-vista3d-server:8000

# Vessels of interest for segmentation analysis or "all"
VESSELS_OF_INTEREST="all"
EOF

echo "✅ Created .env file with the following configuration:"
echo ""
cat .env
echo ""
echo "📁 Created directories:"
mkdir -p output dicom
echo "   - output/"
echo "   - dicom/"
echo ""
echo "🚀 You can now run: docker compose up"
