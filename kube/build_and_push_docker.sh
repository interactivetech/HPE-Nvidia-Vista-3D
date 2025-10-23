#!/bin/bash

# Docker Build and Push Script for Vista3D
# This script builds and pushes both the image_server and frontend Docker images

set -e  # Exit on error

# Configuration
DOCKER_USERNAME="dwtwp"
VERSION="${1:-$(date +%Y%m%d%H%M%S)}"  # Default to timestamp if no version specified
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Function to build and push an image
build_and_push() {
    local service_name=$1
    local service_path=$2
    local image_name="${DOCKER_USERNAME}/vista3d-${service_name}"
    
    cd "${PROJECT_ROOT}/${service_path}"
    
    docker build --no-cache -t "${image_name}:${VERSION}" .
    
    docker tag "${image_name}:${VERSION}" "${image_name}:latest"
    
    docker push "${image_name}:${VERSION}" > /dev/null
    
    docker push "${image_name}:latest" > /dev/null
}

# Build and push image_server
build_and_push "image-server" "image_server"

# Build and push frontend
build_and_push "frontend" "frontend"

# Print the version for deploy_frontend.sh to capture
echo "${VERSION}"
