# Docker Image Build Guide for Vista3D

## 🚀 Quick Start

### Build and Push Images

```bash
# Build and push to Docker Hub (default: dwtwp/)
./build-and-push.sh 1.2.0

# Build only (no push)
./build-and-push.sh 1.2.0 "" no

# Build and push to private registry
./build-and-push.sh 1.2.0 your-registry.com yes
```

---

## 📦 Image Components

### 1. Frontend Image
- **Base**: `python:3.11-slim`
- **Purpose**: Streamlit web interface
- **Size**: ~800MB
- **Components**:
  - Streamlit app
  - NiiVue 3D viewer
  - Medical imaging tools
  - 23+ built-in colormaps

### 2. Image Server
- **Base**: `python:3.11-slim`
- **Purpose**: HTTP file server for medical images
- **Size**: ~400MB
- **Components**:
  - FastAPI server
  - CORS support
  - Health checks

### 3. Backend (NVIDIA)
- **Image**: `nvcr.io/nim/nvidia/vista3d:1.0.0`
- **Source**: NVIDIA NGC Registry
- **Purpose**: AI segmentation server
- **Size**: ~30GB
- **Note**: No build required, pulled from NVIDIA

---

## 🔨 Manual Build Instructions

### Frontend

```bash
cd frontend

# Build for amd64 (Kubernetes standard)
docker build \
  --tag dwtwp/vista3d-frontend:1.2.0 \
  --tag dwtwp/vista3d-frontend:latest \
  --platform linux/amd64 \
  .

# Test locally
docker run -p 8501:8501 \
  -e VISTA3D_SERVER=http://host.docker.internal:8000 \
  dwtwp/vista3d-frontend:1.2.0

# Push to registry
docker push dwtwp/vista3d-frontend:1.2.0
docker push dwtwp/vista3d-frontend:latest
```

### Image Server

```bash
cd image_server

# Build
docker build \
  --tag dwtwp/vista3d-image-server:1.2.0 \
  --tag dwtwp/vista3d-image-server:latest \
  --platform linux/amd64 \
  .

# Test locally
docker run -p 8888:8888 \
  -v $(pwd)/../output:/data/output:ro \
  -v $(pwd)/../dicom:/data/dicom:ro \
  dwtwp/vista3d-image-server:1.2.0

# Push to registry
docker push dwtwp/vista3d-image-server:1.2.0
docker push dwtwp/vista3d-image-server:latest
```

---

## 🏷️ Version Tagging Strategy

### Semantic Versioning

```bash
# Format: MAJOR.MINOR.PATCH
# Example: 1.2.0

MAJOR: Breaking changes
MINOR: New features (backward compatible)
PATCH: Bug fixes
```

### Tag Patterns

```bash
# Specific version
docker tag <image> dwtwp/vista3d-frontend:1.2.0

# Latest (always current stable)
docker tag <image> dwtwp/vista3d-frontend:latest

# Release candidate
docker tag <image> dwtwp/vista3d-frontend:1.2.0-rc1

# Development
docker tag <image> dwtwp/vista3d-frontend:dev
```

---

## 🔐 Registry Configuration

### Docker Hub

```bash
# Login
docker login

# Push
docker push dwtwp/vista3d-frontend:1.2.0
```

### Private Registry

```bash
# Login to private registry
docker login your-registry.com

# Tag for private registry
docker tag dwtwp/vista3d-frontend:1.2.0 \
  your-registry.com/vista3d-frontend:1.2.0

# Push
docker push your-registry.com/vista3d-frontend:1.2.0
```

### HPE GreenLake Registry (if available)

```bash
# Tag for HPE registry
docker tag dwtwp/vista3d-frontend:1.2.0 \
  greenlake-registry.hpe.com/medical-ai/vista3d-frontend:1.2.0

# Push
docker push greenlake-registry.hpe.com/medical-ai/vista3d-frontend:1.2.0
```

---

## 🧪 Testing Images

### Smoke Test

```bash
# Test frontend
docker run --rm -p 8501:8501 \
  dwtwp/vista3d-frontend:1.2.0 &
sleep 10
curl http://localhost:8501/_stcore/health
# Should return 200 OK

# Test image server
docker run --rm -p 8888:8888 \
  dwtwp/vista3d-image-server:1.2.0 &
sleep 5
curl http://localhost:8888/health
# Should return {"status": "healthy"}
```

### Full Integration Test

```bash
# Start all services
docker-compose up -d

# Test endpoints
curl http://localhost:8501/_stcore/health
curl http://localhost:8888/health

# Cleanup
docker-compose down
```

---

## 📊 Image Optimization

### Current Sizes

```bash
docker images | grep vista3d
# frontend:   ~800MB
# image-server: ~400MB
```

### Optimization Tips

1. **Multi-stage builds** (already implemented)
2. **Minimal base images** (python:3.11-slim)
3. **Layer caching** (dependencies before code)
4. **No unnecessary packages**
5. **Clean apt cache**

---

## 🔄 CI/CD Integration

### GitHub Actions Example

See `.github/workflows/docker-build.yml` for automated builds

### Jenkins Pipeline

```groovy
pipeline {
    agent any
    environment {
        DOCKER_REGISTRY = 'your-registry.com'
        VERSION = "1.2.${BUILD_NUMBER}"
    }
    stages {
        stage('Build') {
            steps {
                sh './build-and-push.sh ${VERSION} ${DOCKER_REGISTRY} no'
            }
        }
        stage('Test') {
            steps {
                sh 'docker run --rm dwtwp/vista3d-frontend:${VERSION} python -c "import streamlit"'
            }
        }
        stage('Push') {
            steps {
                sh 'docker push ${DOCKER_REGISTRY}/vista3d-frontend:${VERSION}'
                sh 'docker push ${DOCKER_REGISTRY}/vista3d-image-server:${VERSION}'
            }
        }
    }
}
```

---

## 🐛 Troubleshooting

### Issue: Build Fails

```bash
# Clean Docker cache
docker system prune -af

# Rebuild from scratch
docker build --no-cache -t dwtwp/vista3d-frontend:1.2.0 .
```

### Issue: Image Too Large

```bash
# Check layer sizes
docker history dwtwp/vista3d-frontend:1.2.0

# Analyze
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  wagoodman/dive dwtwp/vista3d-frontend:1.2.0
```

### Issue: Push Failed

```bash
# Check login
docker login

# Check network
docker info

# Manual push
docker push dwtwp/vista3d-frontend:1.2.0 2>&1 | tee push.log
```

---

## 📋 Pre-Deployment Checklist

- [ ] Images built successfully
- [ ] Images tested locally
- [ ] Version tags correct
- [ ] Images pushed to registry
- [ ] Registry accessible from Kubernetes
- [ ] Image pull secrets configured (if private registry)
- [ ] Helm values updated with correct image tags

---

## 🔗 Related Documentation

- **K8S_DEPLOYMENT_CHECKLIST.md** - Full Kubernetes deployment guide
- **helm/vista3d/GREENLAKE_DEPLOYMENT.md** - HPE GreenLake deployment
- **helm/UPGRADE_GUIDE.md** - Upgrade procedures
- **.github/workflows/** - CI/CD pipelines

---

## 📞 Support

For build issues:
1. Check Dockerfile syntax
2. Verify base image availability
3. Review build logs
4. Check Docker version compatibility

**Docker Version Required**: 20.10+  
**BuildKit**: Recommended for faster builds

```bash
# Enable BuildKit
export DOCKER_BUILDKIT=1
docker build ...
```

---

**Last Updated:** October 10, 2025  
**Version:** 1.2.0

