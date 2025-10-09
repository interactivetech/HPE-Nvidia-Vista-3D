# 🚀 Deployment Guide for HPE NVIDIA Vista3D

This comprehensive guide explains how to deploy the HPE NVIDIA Vista3D Medical AI Platform using Docker containers, with support for both local and remote Vista3D server deployments.

## 📋 Overview

The platform consists of three main components:
- **Streamlit App** (Port 8501) - Web interface for medical imaging
- **Image Server** (Port 8888) - HTTP server for medical image files  
- **Vista3D Server** (Port 8000) - AI segmentation service (requires GPU)

## 🏗️ Architecture

The platform uses a simplified two-component architecture:

1. **Backend** (`backend/setup.py`) - Vista3D AI server (GPU-enabled Ubuntu machine)
   - One setup script checks requirements
   - Configures NGC API access
   - Pulls Vista3D Docker image
   - Creates `.env` configuration
   - Start with: `docker compose up -d`

2. **Frontend** (`frontend/setup.py`) - Web interface + Image server (Mac or any Docker machine)
   - One setup script for both services
   - Configures frontend and image server together
   - Pulls Docker images
   - Creates `.env` configuration
   - Start with: `docker compose up -d` (starts both services)

### **Benefits:**
- **Distributed Deployments**: Vista3D on GPU server, frontend on client machines
- **Scalability**: Multiple frontend instances can connect to one Vista3D server
- **Flexibility**: Mix and match local/remote components as needed
- **Easier Maintenance**: Independent updates and restarts of components
- **Better Resource Management**: Separate resource allocation for GPU vs. frontend workloads

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

### Scenario 3: Backend-Only (GPU Server)
- **Vista3D Server**: Runs on GPU server (port 8000)
- **Use Case**: GPU server farms, API-only deployments

## 🚀 Quick Start

### Prerequisites
- Docker Desktop or Docker Engine installed
- Docker Compose (included with Docker Desktop)
- At least 8GB RAM available for containers
- NVIDIA GPU support (for backend Vista3D)

### Initial Setup

#### Backend (Ubuntu Server with GPU)
```bash
cd backend
python3 setup.py
```

#### Frontend (Mac or any Docker machine)
```bash
cd frontend
python3 setup.py
```

### Start Services

#### Backend (GPU Machine)
```bash
cd backend
docker compose up -d
```

#### Frontend & Image Server (Any Machine)
```bash
cd frontend
docker compose up -d  # Starts both frontend and image server
```

#### SSH Tunnel (from Mac to Ubuntu)
```bash
ssh -L 8000:localhost:8000 -R 8888:0.0.0.0:8888 user@ubuntu-server
```

## 🔧 Configuration

### Environment Variables

The setup scripts automatically create `.env` files with the correct configuration:

**Frontend `.env` (for remote backend setup):**
```bash
# Data Directories
DICOM_FOLDER=/path/to/dicom
OUTPUT_FOLDER=/path/to/output

# Server URLs (configured for SSH tunnel)
VISTA3D_SERVER=http://host.docker.internal:8000
IMAGE_SERVER=http://localhost:8888
VISTA3D_IMAGE_SERVER_URL=http://host.docker.internal:8888

# Ports
FRONTEND_PORT=8501
IMAGE_SERVER_PORT=8888
```

**Backend `.env`:**
```bash
# NVIDIA NGC Configuration
NGC_API_KEY=nvapi-YOUR_KEY_HERE
NGC_ORG_ID=

# Data Directories
OUTPUT_FOLDER=/path/to/output

# Server URLs
VISTA3D_SERVER=http://localhost:8000
IMAGE_SERVER=http://localhost:8888
```

### Remote Vista3D Configuration

The setup scripts automatically configure for remote deployment when using SSH tunnels. No manual configuration needed!

## 🐳 Docker Commands

### Start Services
```bash
# Start backend (GPU machine)
cd backend
docker compose up -d

# Start frontend & image server (any machine)
cd frontend
docker compose up -d
```

### Stop Services
```bash
# Stop frontend & image server
cd frontend
docker compose down

# Stop backend
cd backend
docker compose down
```

### View Logs
```bash
# Frontend logs (both services)
cd frontend
docker compose logs -f

# Backend logs
cd backend
docker compose logs -f

# Specific service logs
cd frontend
docker compose logs -f vista3d-frontend-standalone
docker compose logs -f vista3d-image-server-for-frontend
```

### Restart Services
```bash
# Restart frontend & image server
cd frontend
docker compose restart

# Restart backend
cd backend
docker compose restart
```

## 🌐 Network Configuration

### Ports Used
- **8501**: Streamlit web interface
- **8888**: Image server
- **8000**: Vista3D API server

### Firewall Configuration
```bash
# Allow required ports
sudo ufw allow 8501
sudo ufw allow 8888
sudo ufw allow 8000
```

### CORS Configuration
The image server is configured with CORS headers to allow cross-origin requests from the Streamlit app.

## 🔍 Troubleshooting

### Common Issues

#### Services Not Starting
```bash
# Check Docker status
docker ps -a

# Check logs
docker-compose logs -f

# Check system resources
docker system df
```

#### Port Conflicts
```bash
# Check what's using ports
sudo netstat -tulpn | grep :8501
sudo netstat -tulpn | grep :8888
sudo netstat -tulpn | grep :8000

# Kill conflicting processes
sudo kill -9 <PID>
```

#### GPU Issues
```bash
# Test NVIDIA Docker support
docker run --rm --gpus all nvidia/cuda:11.0.3-base-ubuntu20.04 nvidia-smi

# Check GPU availability
nvidia-smi
```

#### Memory Issues
```bash
# Check Docker memory usage
docker stats

# Clean up unused containers
docker system prune -a
```

### Health Checks

#### Frontend Health
```bash
# Check Streamlit app
curl http://localhost:8501

# Check image server
curl http://localhost:8888/health
```

#### Backend Health
```bash
# Check Vista3D server
curl http://localhost:8000/health
```

## 📊 Monitoring

### Resource Usage
```bash
# Monitor container resources
docker stats

# Monitor system resources
htop
```

### Log Monitoring
```bash
# Follow all logs
docker-compose logs -f

# Follow specific service logs
docker logs -f vista3d-frontend-standalone
docker logs -f vista3d-image-server-standalone
docker logs -f vista3d-backend-standalone
```

## 🔒 Security Considerations

### Network Security
- Use HTTPS in production
- Configure proper firewall rules
- Use VPN for remote access
- Implement API authentication

### Data Security
- Encrypt sensitive data
- Use secure file permissions
- Regular security updates
- Backup important data

## 📈 Performance Optimization

### Resource Allocation
- Allocate sufficient RAM (8GB+ recommended)
- Use SSD storage for better I/O performance
- Configure GPU memory appropriately

### Network Optimization
- Use local network for remote Vista3D
- Configure appropriate timeouts
- Monitor network latency

## 🚀 Production Deployment

### Systemd Services
```bash
# Create systemd service files for auto-start
sudo systemctl enable vista3d-backend
sudo systemctl enable vista3d-frontend
```

### Load Balancing
- Use nginx for load balancing
- Configure multiple frontend instances
- Implement health checks

### Monitoring
- Set up monitoring with Prometheus/Grafana
- Configure alerting for service failures
- Monitor resource usage and performance

## 📝 Maintenance

### Regular Updates
```bash
# Update Docker images
docker-compose pull
docker-compose up -d

# Update application code
git pull
docker-compose build
docker-compose up -d
```

### Backup Strategy
- Regular backup of configuration files
- Backup of processed data
- Version control for configuration changes

## 🆘 Support

### Getting Help
- Check logs for error messages
- Verify configuration settings
- Test individual components
- Review system requirements

### Common Solutions
- Restart services if they become unresponsive
- Check disk space and memory usage
- Verify network connectivity
- Update Docker and dependencies
