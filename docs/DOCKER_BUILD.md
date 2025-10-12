# Docker Build and Push Guide

## Automated Build (Recommended)

Use the provided script to build and push both images:

```bash
# Build and push with default version (v1.0.0)
./build_and_push_docker.sh

# Build and push with specific version
./build_and_push_docker.sh v1.1.0
```

The script will:
- Check Docker Hub login status
- Build both image_server and frontend images
- Tag with specified version and 'latest'
- Push all tags to Docker Hub

## Manual Build

If you prefer to build manually or need to build individual images:

### Build image_server image and publish
```bash
cd ./image_server
docker build -t dwtwp/vista3d-image-server:v1.0.0 .
docker tag dwtwp/vista3d-image-server:v1.0.0 dwtwp/vista3d-image-server:latest
docker push dwtwp/vista3d-image-server:v1.0.0
docker push dwtwp/vista3d-image-server:latest
```

### Build frontend image and publish
```bash
cd ./frontend
docker build -t dwtwp/vista3d-frontend:v1.0.0 .
docker tag dwtwp/vista3d-frontend:v1.0.0 dwtwp/vista3d-frontend:latest
docker push dwtwp/vista3d-frontend:v1.0.0
docker push dwtwp/vista3d-frontend:latest
```
