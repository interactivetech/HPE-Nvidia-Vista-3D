# 🚀 Deployment Guide for HPE NVIDIA Vista3D

This comprehensive guide explains how to deploy the HPE NVIDIA Vista3D Medical AI Platform using Docker containers, with support for both local and remote Vista3D server deployments.

## 📋 Overview

The platform consists of three main components:
- **Streamlit App** (Port 8501) - Web interface for medical imaging
- **Image Server** (Port 8888) - HTTP server for medical image files  
- **Vista3D Server** (Port 8000) - AI segmentation service (requires GPU)

## 🏗️ Architecture

The platform uses a flexible three-component architecture:

1. **`setup.py`** - Initial setup and configuration
   - Checks system requirements
   - Sets up Python environment
   - Configures environment variables
   - Creates necessary directories

2. **Backend Services** - Vista3D server startup (GPU-enabled machine)
   - Starts Vista3D Docker container
   - Configures GPU access
   - Sets up networking for remote access

3. **Frontend Services** - Frontend services startup (any machine)
   - Starts Streamlit app container
   - Starts image server container
   - Configures networking and CORS

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
- NVIDIA GPU support (for local Vista3D)

### Initial Setup
```bash
# Run the unified setup script
python3 setup.py

# Follow the prompts to configure your deployment
```

### Start Services

#### Frontend Services (Any Machine)
```bash
cd frontend
# Start image server first
cd ../image_server && docker-compose up -d
# Start frontend
cd ../frontend && docker-compose up -d
```

#### Backend Services (GPU Machine)
```bash
cd backend
# Start Vista3D server
docker-compose up -d
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Vista3D Server Configuration
VISTA3D_SERVER=http://localhost:8000  # or remote server URL
VISTA3D_API_KEY=your_api_key_here

# Frontend Configuration
FRONTEND_PORT=8501
IMAGE_SERVER_PORT=8888

# Data Directories
DICOM_FOLDER=/path/to/dicom/files
OUTPUT_FOLDER=/path/to/output/files

# Docker Images
FRONTEND_IMAGE=dwtwp/vista3d-frontend:latest
IMAGE_SERVER_IMAGE=dwtwp/vista3d-image-server:latest
VISTA3D_IMAGE=nvcr.io/nvidia/vista3d:latest
```

### Remote Vista3D Configuration

For remote Vista3D deployments:

```bash
# .env file for remote Vista3D
VISTA3D_SERVER=http://your-gpu-server:8000
VISTA3D_API_KEY=your_remote_api_key
```

## 🐳 Docker Commands

### Start Services
```bash
# Start all services (if all local)
python3 setup.py --setup all

# Start frontend only
cd frontend
cd ../image_server && docker-compose up -d
cd ../frontend && docker-compose up -d

# Start backend only
cd backend
docker-compose up -d
```

### Stop Services
```bash
# Stop frontend services
cd frontend && docker-compose down
cd ../image_server && docker-compose down

# Stop backend services
cd backend && docker-compose down
```

### View Logs
```bash
# Frontend logs
cd frontend && docker-compose logs -f

# Backend logs
cd backend && docker-compose logs -f
```

### Restart Services
```bash
# Restart frontend
cd frontend && docker-compose restart

# Restart backend
cd backend && docker-compose restart
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
