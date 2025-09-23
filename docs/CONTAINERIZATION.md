# Docker Deployment Guide for HPE NVIDIA Vista3D

This comprehensive guide explains how to containerize and run the HPE NVIDIA Vista3D medical imaging AI segmentation application using Docker, with support for both local and remote Vista3D server deployments.

## Prerequisites

- Docker Desktop or Docker Engine installed
- Docker Compose (included with Docker Desktop)
- At least 8GB RAM available for the container
- NVIDIA GPU support (optional, for local Vista3D)

## 🎯 Deployment Scenarios

### Scenario 1: Local GUI + Remote Vista3D (Recommended)
- **Streamlit App**: Runs locally in Docker (port 8501)
- **Image Server**: Runs locally in Docker (port 8888)
- **Vista3D Server**: Runs on remote server (most common)
- **Use Case**: Production deployments, shared GPU resources

### Scenario 2: All Services Local (Development)
- **Streamlit App**: Runs locally in Docker (port 8501)
- **Image Server**: Runs locally in Docker (port 8888)
- **Vista3D Server**: Runs locally in Docker (port 8001, requires GPU)
- **Use Case**: Development, testing, single-machine deployments

## 🚀 Quick Start

### Available Scripts

The project includes Python-based startup scripts in the `utils/` folder:

- `utils/start_vista3d.py` - Start Vista3D server container (requires GPU)
- `utils/start_gui.py` - Start GUI containers (Streamlit app + image server)

### Mode 1: Local GUI + Remote Vista3D (Recommended)

**Use Case**: Production deployments, shared GPU resources, cloud-based Vista3D

```bash
# 1. Configure environment for remote Vista3D
cp env.example .env
nano .env  # Edit with your remote Vista3D server details

# 2. Start GUI containers (connects to remote Vista3D)
python3 utils/start_gui.py
```

**Environment Configuration:**
```bash
# .env file for remote Vista3D
VISTA3D_SERVER=https://your-vista3d-server.com:8001
NGC_API_KEY=your_nvidia_api_key_here
IMAGE_SERVER=http://image-server:8888
EXTERNAL_IMAGE_SERVER=http://localhost:8888
```

### Mode 2: All Services Local (Development)

**Use Case**: Development, testing, single-machine deployments

```bash
# 1. Configure environment for local Vista3D
cp env.example .env
nano .env  # Edit for local Vista3D

# 2. Start Vista3D server (requires GPU)
python3 utils/start_vista3d.py

# 3. Start GUI containers (in separate terminal)
python3 utils/start_gui.py
```

**Environment Configuration:**
```bash
# .env file for local Vista3D
VISTA3D_SERVER=http://vista3d-server:8001
NGC_API_KEY=your_nvidia_api_key_here
IMAGE_SERVER=http://image-server:8888
EXTERNAL_IMAGE_SERVER=http://localhost:8888
```

### Mode 3: Production with Auto-Startup

**Use Case**: Production servers with automatic startup on boot

```bash
# Create systemd services for automatic startup
sudo python3 utils/start_vista3d.py --create-service
sudo python3 utils/start_gui.py --create-service

# Enable services
sudo systemctl enable vista3d
sudo systemctl enable vista3d-gui

# Start services
sudo systemctl start vista3d
sudo systemctl start vista3d-gui
```

### Option 3: Manual Docker Commands

```bash
# Build using docker compose
docker compose build

# Or build manually
docker build -t hpe-nvidia-vista3d .

# Run the container
docker run -p 8501:8501 \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/dicom:/app/dicom \
  -v $(pwd)/.env:/app/.env \
  hpe-nvidia-vista3d
```

## 📋 Configuration

### Environment Variables

Copy `env.example` to `.env` and configure the following variables:

#### For Remote Vista3D (Scenario 1):
```bash
# Remote Vista3D Server
VISTA3D_SERVER=https://your-vista3d-server.com:8001
NGC_API_KEY=your_nvidia_api_key_here

# Local services
IMAGE_SERVER=http://image-server:8888
STREAMLIT_SERVER_PORT=8501
```

#### For Local Vista3D (Scenario 2):
```bash
# Local Vista3D Server
VISTA3D_SERVER=http://vista3d-server:8001
NGC_API_KEY=your_nvidia_api_key_here

# Local services
IMAGE_SERVER=http://image-server:8888
STREAMLIT_SERVER_PORT=8501
```

### Volume Mounts

The following directories are mounted as volumes:

- `./output:/app/output` - Output files and results
- `./dicom:/app/dicom` - DICOM input files
- `./.env:/app/.env` - Environment configuration

## 🐳 Docker Services

### Service Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │  Image Server   │    │  Vista3D Server │
│   (Port 8501)   │◄──►│  (Port 8888)    │◄──►│  (Port 8001)    │
│                 │    │                 │    │  (Remote/Local) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Service Details

| Service | Container | Port | Purpose | Network |
|---------|-----------|------|---------|---------|
| Streamlit App | `hpe-nvidia-vista3d-app` | 8501 | Web UI | local-network |
| Image Server | `vista3d-image-server` | 8888 | Image processing | local-network |
| Vista3D Server | `vista3d-server-local` | 8001 | AI segmentation | local-network |

### Main Application (`vista3d-app`)

- **Port**: 8501 (Streamlit web interface)
- **Purpose**: Main Streamlit application for medical imaging segmentation
- **Health Check**: Built-in Streamlit health endpoint

### Image Server (`image-server`)

- **Port**: 8888
- **Purpose**: Separate service for image processing
- **Health Check**: Custom health endpoint

## 🔧 Running Utility Scripts

**Important**: When using Docker containers, utility scripts must be run from the **host system**, not from within the containers.

### Prerequisites
```bash
# Activate virtual environment on host
source .venv/bin/activate

# Ensure you have the required dependencies
uv sync
```

### Utility Scripts
```bash
# DICOM to NIFTI conversion (run from host)
python3 utils/dicom2nifti.py

# Segmentation processing (run from host)
python3 utils/segment.py

# NIFTI to PLY conversion (run from host)
python3 utils/nifti2ply.py --batch
```

## 🔧 Manual Commands

### Start Services

```bash
# Remote Vista3D scenario
docker-compose up -d vista3d-app image-server

# All local services
docker-compose --profile local-vista3d up -d
```

### Monitor Services

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f vista3d-app
docker-compose logs -f image-server
docker-compose logs -f vista3d-server

# Check service status
docker-compose ps
```

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## 🌐 Access Points

### Local Access
- **Streamlit App**: http://localhost:8501
- **Image Server**: http://localhost:8888
- **Vista3D Server**: http://localhost:8001 (local only)

### Health Checks
- **Streamlit**: http://localhost:8501/_stcore/health
- **Image Server**: http://localhost:8888/health
- **Vista3D**: http://localhost:8001/health (local only)

#### Testing Vista3D Server Health
```bash
# Test Vista3D server connectivity
curl -v http://localhost:8001/health
```

## Development

### Building for Development

```bash
# Build without cache
docker-compose build --no-cache

# Run in development mode with live reload
docker-compose up --build
```

### Debugging

```bash
# Access container shell
docker exec -it hpe-nvidia-vista3d-app /bin/bash
docker exec -it vista3d-image-server /bin/bash

# View logs
docker-compose logs -f vista3d-app

# View specific service logs
docker-compose logs -f image-server
```

## Production Deployment

### 1. Multi-Container Setup

For production, you may want to run the image server as a separate service:

```bash
# Start all services including image server
docker-compose --profile image-server up -d
```

### 2. Resource Limits

Add resource limits to `docker-compose.yml`:

```yaml
services:
  vista3d-app:
    # ... existing configuration
    deploy:
      resources:
        limits:
          memory: 8G
          cpus: '4.0'
        reservations:
          memory: 4G
          cpus: '2.0'
```

### 3. Health Checks

The application includes built-in health checks:

- **Interval**: 30 seconds
- **Timeout**: 10 seconds
- **Retries**: 3
- **Start Period**: 40 seconds

### 4. Restart Policy

Containers are configured with `restart: unless-stopped` for automatic recovery.

## GPU Support (Optional)

For NVIDIA GPU acceleration, modify the Dockerfile:

```dockerfile
# Use NVIDIA CUDA base image
FROM nvidia/cuda:11.8-devel-ubuntu22.04

# Install Python 3.11
RUN apt-get update && apt-get install -y python3.11 python3.11-pip
```

And add GPU support to docker-compose.yml:

```yaml
services:
  vista3d-app:
    # ... existing configuration
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Vista3D Connection Failed
```bash
# Check Vista3D server connectivity
curl -v $VISTA3D_SERVER/health

# For local Vista3D server specifically
curl -v http://localhost:8001/health

# Check API key
echo $NGC_API_KEY
```

#### 2. Port Already in Use
```bash
# Check what's using the port
lsof -i :8501
lsof -i :8888
lsof -i :8001

# Change ports in docker-compose.yml
```

#### 3. Permission Issues
```bash
# Fix directory permissions
sudo chown -R $USER:$USER output/ dicom/

# Check Docker permissions
docker ps
```

#### 4. Memory Issues
```bash
# Check Docker memory usage
docker stats

# Increase Docker memory limit in Docker Desktop
```

#### 5. Build Failures
```bash
# Clean build
docker-compose down
docker system prune -a
docker-compose up --build
```

### Debugging Commands

```bash
# Access container shell
docker exec -it hpe-nvidia-vista3d-app /bin/bash
docker exec -it vista3d-image-server /bin/bash

# Check container logs
docker logs hpe-nvidia-vista3d-app
docker logs vista3d-image-server

# Check network connectivity
docker exec -it hpe-nvidia-vista3d-app ping image-server
docker exec -it vista3d-image-server ping vista3d-server

# View all logs
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# View specific service logs
docker-compose logs -f vista3d-app
```

## 🔒 Security Considerations

### Network Security
- Services communicate through Docker internal network
- External access only through exposed ports
- Vista3D API key stored in environment variables

### Data Security
- DICOM files mounted as read-only volumes
- Output files stored in local directories
- No sensitive data in Docker images

### SSL/TLS
- Configure SSL for remote Vista3D connections
- Use HTTPS for production deployments
- Validate certificates for secure connections

### Best Practices
1. **Environment Variables**: Never commit `.env` files with sensitive data
2. **Network Security**: Use Docker networks for service communication
3. **Volume Security**: Be careful with volume mounts containing sensitive data
4. **API Keys**: Store API keys in environment variables, not in code

## 📊 Monitoring

### Health Checks
All services include built-in health checks:
- **Interval**: 30 seconds
- **Timeout**: 10 seconds
- **Retries**: 3
- **Start Period**: 20-40 seconds

### Logging
- Docker logs: `docker-compose logs`
- Health check logs: Available in Docker logs

### Performance
- Monitor CPU and memory usage: `docker stats`
- Check disk usage: `docker system df`
- Monitor network: `docker network ls`

## 🚀 Production Considerations

### Resource Limits
Add to `docker-compose.yml`:
```yaml
services:
  vista3d-app:
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
```

### Scaling
- Run multiple image server instances
- Use load balancer for multiple Streamlit instances
- Consider Kubernetes for production scaling

### Backup
- Backup `output/` directory regularly
- Backup configuration files
- Consider automated backup solutions

## Performance Optimization

1. **Multi-stage Builds**: Consider using multi-stage builds for smaller images
2. **Layer Caching**: Order Dockerfile commands to maximize cache hits
3. **Resource Limits**: Set appropriate CPU and memory limits
4. **Volume Optimization**: Use named volumes for frequently accessed data

## 🔄 Updates

### Updating Application
```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose up --build -d
```

### Updating Dependencies
```bash
# Update pyproject.toml
# Rebuild image
docker-compose build --no-cache
docker-compose up -d
```

## 📞 Support

### Logs to Collect
When reporting issues, collect:
1. `docker-compose logs` output
2. `.env` file (remove sensitive data)
3. `docker-compose ps` output
4. System resource usage

### Common Solutions
- Restart Docker Desktop
- Clear Docker cache: `docker system prune -a`
- Rebuild images: `docker-compose build --no-cache`
- Check network connectivity to remote Vista3D

### For issues related to:

- **Docker**: Check Docker logs and documentation
- **Application**: Check Docker logs for application issues
- **NVIDIA Vista3D**: Refer to NVIDIA documentation
- **HPE Infrastructure**: Contact HPE support
