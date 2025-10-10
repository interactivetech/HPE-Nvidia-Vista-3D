#!/bin/bash
# ============================================================================
# Vista3D Docker Image Build and Push Script
# ============================================================================
# This script builds and pushes Docker images for Kubernetes deployment
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VERSION=${1:-"1.2.0"}
REGISTRY=${2:-""}  # Leave empty for Docker Hub, or specify your registry
PUSH=${3:-"yes"}

# Image names
FRONTEND_IMAGE="vista3d-frontend"
IMAGE_SERVER_IMAGE="vista3d-image-server"

if [ -n "$REGISTRY" ]; then
    FRONTEND_FULL="${REGISTRY}/${FRONTEND_IMAGE}:${VERSION}"
    IMAGE_SERVER_FULL="${REGISTRY}/${IMAGE_SERVER_IMAGE}:${VERSION}"
    FRONTEND_LATEST="${REGISTRY}/${FRONTEND_IMAGE}:latest"
    IMAGE_SERVER_LATEST="${REGISTRY}/${IMAGE_SERVER_IMAGE}:latest"
else
    # Using Docker Hub (dwtwp/ prefix)
    FRONTEND_FULL="dwtwp/${FRONTEND_IMAGE}:${VERSION}"
    IMAGE_SERVER_FULL="dwtwp/${IMAGE_SERVER_IMAGE}:${VERSION}"
    FRONTEND_LATEST="dwtwp/${FRONTEND_IMAGE}:latest"
    IMAGE_SERVER_LATEST="dwtwp/${IMAGE_SERVER_IMAGE}:latest"
fi

echo -e "${GREEN}================================================================${NC}"
echo -e "${GREEN}       Vista3D Docker Image Build & Push - v${VERSION}         ${NC}"
echo -e "${GREEN}================================================================${NC}"

echo -e "\n${YELLOW}Configuration:${NC}"
echo -e "  Version: ${GREEN}${VERSION}${NC}"
echo -e "  Registry: ${GREEN}${REGISTRY:-Docker Hub (dwtwp/)}${NC}"
echo -e "  Push Images: ${GREEN}${PUSH}${NC}"
echo -e "  Frontend: ${BLUE}${FRONTEND_FULL}${NC}"
echo -e "  Image Server: ${BLUE}${IMAGE_SERVER_FULL}${NC}"

# Confirm
if [ "$PUSH" = "yes" ]; then
    echo -e "\n${YELLOW}This will build and push images to the registry.${NC}"
    echo -e "${YELLOW}Continue? (y/N)${NC}"
    read -r CONFIRM
    if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
        echo -e "${RED}Aborted by user${NC}"
        exit 0
    fi
fi

# Build Frontend
echo -e "\n${YELLOW}[1/4] Building Frontend Image...${NC}"
cd frontend
docker build \
    --tag "${FRONTEND_FULL}" \
    --tag "${FRONTEND_LATEST}" \
    --build-arg VERSION="${VERSION}" \
    --platform linux/amd64 \
    .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Frontend image built successfully${NC}"
else
    echo -e "${RED}✗ Frontend build failed${NC}"
    exit 1
fi

# Build Image Server
echo -e "\n${YELLOW}[2/4] Building Image Server Image...${NC}"
cd ../image_server
docker build \
    --tag "${IMAGE_SERVER_FULL}" \
    --tag "${IMAGE_SERVER_LATEST}" \
    --build-arg VERSION="${VERSION}" \
    --platform linux/amd64 \
    .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Image Server image built successfully${NC}"
else
    echo -e "${RED}✗ Image Server build failed${NC}"
    exit 1
fi

cd ..

# Display image sizes
echo -e "\n${YELLOW}Built Images:${NC}"
docker images | grep -E "(vista3d-frontend|vista3d-image-server)" | grep -E "($VERSION|latest)"

# Push images
if [ "$PUSH" = "yes" ]; then
    echo -e "\n${YELLOW}[3/4] Pushing Frontend Image...${NC}"
    docker push "${FRONTEND_FULL}"
    docker push "${FRONTEND_LATEST}"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Frontend image pushed successfully${NC}"
    else
        echo -e "${RED}✗ Frontend push failed${NC}"
        exit 1
    fi
    
    echo -e "\n${YELLOW}[4/4] Pushing Image Server Image...${NC}"
    docker push "${IMAGE_SERVER_FULL}"
    docker push "${IMAGE_SERVER_LATEST}"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Image Server image pushed successfully${NC}"
    else
        echo -e "${RED}✗ Image Server push failed${NC}"
        exit 1
    fi
else
    echo -e "\n${YELLOW}Skipping push (PUSH=${PUSH})${NC}"
fi

# Summary
echo -e "\n${GREEN}================================================================${NC}"
echo -e "${GREEN}                    Build Complete!                            ${NC}"
echo -e "${GREEN}================================================================${NC}"

echo -e "\n${YELLOW}Images Built:${NC}"
echo -e "  • ${FRONTEND_FULL}"
echo -e "  • ${FRONTEND_LATEST}"
echo -e "  • ${IMAGE_SERVER_FULL}"
echo -e "  • ${IMAGE_SERVER_LATEST}"

if [ "$PUSH" = "yes" ]; then
    echo -e "\n${GREEN}✓ Images pushed to registry${NC}"
    echo -e "\n${YELLOW}Next Steps:${NC}"
    echo -e "  1. Update Helm values to use version ${VERSION}"
    echo -e "  2. Deploy to Kubernetes:"
    echo -e "     ${BLUE}cd helm/vista3d${NC}"
    echo -e "     ${BLUE}helm upgrade --install vista3d . \\${NC}"
    echo -e "     ${BLUE}  --namespace vista3d \\${NC}"
    echo -e "     ${BLUE}  --set frontend.image.tag=${VERSION} \\${NC}"
    echo -e "     ${BLUE}  --set imageServer.image.tag=${VERSION}${NC}"
else
    echo -e "\n${YELLOW}To push images later, run:${NC}"
    echo -e "  ${BLUE}docker push ${FRONTEND_FULL}${NC}"
    echo -e "  ${BLUE}docker push ${IMAGE_SERVER_FULL}${NC}"
fi

echo -e "\n${GREEN}================================================================${NC}"

