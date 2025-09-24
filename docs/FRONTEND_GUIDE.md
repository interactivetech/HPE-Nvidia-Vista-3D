# Vista3D Frontend Services Guide

This guide explains how to start and manage the Vista3D frontend services (Streamlit web interface and image server).

## 🚀 Quick Start

### Start Frontend Services
```bash
# Start the frontend containers
python3 start_frontend.py
```

**This starts:**
- 🌐 **Streamlit Web Interface** (http://localhost:8501)
- 🖼️ **Image Server** (http://localhost:8888)

## 📋 Prerequisites

### System Requirements
- Docker installed and running
- Docker Compose available
- Python 3.7+ with required dependencies
- `.env` file with configuration (created during setup)

### Pre-Setup
Before starting the frontend, ensure you've run the initial setup:
```bash
# Run the unified setup script first
python3 setup.py
```

## 🐍 Virtual Environment Setup

The frontend uses a separate virtual environment. Here's how to activate it:

### Method 1: Direct Activation (Recommended)
```bash
# Navigate to the project directory
cd /path/to/HPE-Nvidia-Vista-3D

# Activate the frontend environment directly
source .venv-frontend/bin/activate
```

### Method 2: Using `uv run` (No Activation Needed)
```bash
# Run frontend commands directly without activating the environment
uv run --python .venv-frontend/bin/python your_frontend_script.py
```

### Method 3: Using `uv` with Active Environment
```bash
# Activate the environment first
source .venv-frontend/bin/activate

# Then use uv commands (but avoid 'uv sync' as it tries to build packages)
uv pip install package_name  # Use this instead of uv sync
```

**⚠️ Important Note**: Do not use `uv sync` with the frontend environment as it will try to build the project as a package, which will fail. Use `uv pip install` instead for installing additional packages.

### Environment Verification
```bash
# Test frontend environment
source .venv-frontend/bin/activate
python -c "import streamlit, fastapi, nibabel; print('✅ Frontend environment working!')"
```

## 🔧 Configuration

### Environment Variables
The frontend uses these key environment variables from your `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `STREAMLIT_SERVER_PORT` | `8501` | Port for the Streamlit app |
| `IMAGE_SERVER_PORT` | `8888` | Port for the image server |
| `USE_HOST_NETWORKING` | `False` | Use host networking (allows all interfaces) |
| `IMAGE_SERVER` | `http://image-server:8888` | Image server URL |
| `VISTA3D_SERVER` | `http://vista3d-server:8000` | Vista3D server URL |
| `NGC_API_KEY` | - | API key for Vista3D server |

### Container Details
The script starts two containers:

#### 1. Streamlit App (`hpe-nvidia-vista3d-app`)
- **Port**: 8501 (default)
- **Purpose**: Main GUI application
- **Health Check**: `http://localhost:8501/_stcore/health`

#### 2. Image Server (`vista3d-image-server`)
- **Port**: 8888 (default)
- **Purpose**: Serves medical imaging files
- **Health Check**: `http://localhost:8888/health`

## 🌐 Remote Vista3D Server Setup

For remote Vista3D server deployments:

### SSH Port Forwarding Setup
```bash
# Forward local ports to remote Vista3D server
ssh user@remote_server -L 8000:localhost:8000 -R 8888:localhost:8888

# This forwards:
# - Local port 8000 → Remote Vista3D server port 8000
# - Remote port 8888 → Local image server port 8888
```

### Client Configuration
```bash
# Edit .env file on client machine
VISTA3D_SERVER="http://localhost:8000"  # Uses SSH tunnel
IMAGE_SERVER="http://localhost:8888"    # Local image server
NGC_API_KEY="your_nvidia_api_key"
```

### Complete Client Workflow
```bash
# 1. Set up SSH tunnel (keep running)
ssh user@remote_server -L 8000:localhost:8000 -R 8888:localhost:8888

# 2. Start frontend services on client
python3 start_frontend.py

# 3. Access GUI at http://localhost:8501
```

## 🔧 Management Commands

### Basic Usage
```bash
# Start the frontend containers
python3 start_frontend.py

# Or make it executable and run directly
chmod +x start_frontend.py
./start_frontend.py
```

### Create Systemd Service (Auto-startup)
```bash
# Create systemd service for automatic startup on boot
sudo python3 start_frontend.py --create-service

# Then start the service
sudo systemctl start vista3d-gui

# Check status
sudo systemctl status vista3d-gui

# View logs
sudo journalctl -u vista3d-gui -f
```

### Stop Containers
```bash
# Stop using docker compose
docker compose down

# Or stop individual containers
docker stop hpe-nvidia-vista3d-app vista3d-image-server
```

## 📊 Monitoring

### Check Container Status
```bash
# View all containers
docker compose ps

# View logs
docker compose logs -f

# View specific container logs
docker logs -f hpe-nvidia-vista3d-app
docker logs -f vista3d-image-server
```

### Health Checks
```bash
# Check Streamlit app health
curl http://localhost:8501/_stcore/health

# Check image server health
curl http://localhost:8888/health
```

## 🔍 Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Change ports using environment variables
STREAMLIT_SERVER_PORT=8502 IMAGE_SERVER_PORT=8889 python3 start_frontend.py
```

#### Docker Not Running
```bash
# Start Docker daemon
sudo systemctl start docker

# Check Docker status
sudo systemctl status docker
```

#### Permission Issues
```bash
# Ensure user is in docker group
sudo usermod -aG docker $USER

# Log out and back in, or run:
newgrp docker
```

#### Container Won't Start
```bash
# Check Docker logs
docker compose logs

# Check system resources
free -h
df -h

# Check Docker daemon
sudo systemctl status docker
```

#### Frontend Can't Connect to Backend
```bash
# Check if Vista3D server is running
curl http://localhost:8000/v1/vista3d/info

# Check .env configuration
cat .env | grep VISTA3D_SERVER

# Test network connectivity
ping vista3d-server
```

#### Image Server Issues
```bash
# Check if image server is running
curl http://localhost:8888/health

# Check file permissions
ls -la output/
sudo chown -R $USER:$USER output/
sudo chmod -R 755 output/
```

### Debug Commands
```bash
# Check container status
docker ps -a

# View container logs
docker logs -f hpe-nvidia-vista3d-app
docker logs -f vista3d-image-server

# Check network connectivity
netstat -tlnp | grep -E "(8501|8888)"

# Check Docker compose status
docker compose ps
```

## 🔧 Advanced Configuration

### Custom Ports
```bash
# Set custom ports via environment variables
export STREAMLIT_SERVER_PORT=8502
export IMAGE_SERVER_PORT=8889
python3 start_frontend.py
```

### Host Networking
```bash
# Enable host networking for external access
export USE_HOST_NETWORKING=True
python3 start_frontend.py
```

### External Access Configuration
```bash
# Find your public IP
curl ifconfig.me

# Update .env file for external access
echo "IMAGE_SERVER=http://your-public-ip:8888" >> .env
```

### Firewall Configuration
```bash
# Open required ports
sudo ufw allow 8501
sudo ufw allow 8888

# Check firewall status
sudo ufw status
```

## 🏗️ Architecture

The frontend uses Docker Compose to manage two containers:

### Streamlit App Container
- **Image**: Built from local Dockerfile
- **Port**: 8501 (configurable)
- **Purpose**: Main web interface
- **Dependencies**: Streamlit, medical imaging libraries

### Image Server Container
- **Image**: Built from local Dockerfile
- **Port**: 8888 (configurable)
- **Purpose**: HTTP server for medical images
- **Dependencies**: Python HTTP server, file serving

### Integration
- Both containers share the same network
- Streamlit app communicates with Vista3D backend
- Image server provides files to Vista3D for processing
- All services can run on different machines

## 📚 Usage Examples

### Complete System Workflow
```bash
# 1. Start Vista3D backend (on GPU machine)
python3 start_backend.py

# 2. Start frontend services (on any machine)
python3 start_frontend.py

# 3. Access web interface
# Open http://localhost:8501 in your browser

# 4. Upload medical images
# Use the web interface to upload DICOM or NIFTI files

# 5. Run segmentation
# Use the Tools page to process images with Vista3D
```

### Development Mode
```bash
# Start only the image server
python3 utils/image_server.py

# Start Streamlit in development mode
streamlit run app.py
```

### Production Mode
```bash
# Start with systemd service
sudo python3 start_frontend.py --create-service
sudo systemctl start vista3d-gui
sudo systemctl enable vista3d-gui
```

## 🔐 Security Considerations

### Production Deployment
1. **Use HTTPS** for external access
2. **Implement authentication** for web interface
3. **Use VPN** or secure tunnel for network access
4. **Regular security updates** for system and Docker images
5. **Monitor access logs** for suspicious activity
6. **Backup configuration** and data regularly

### Network Security
```bash
# Restrict access to specific IPs
sudo ufw allow from 192.168.1.0/24 to any port 8501
sudo ufw allow from 192.168.1.0/24 to any port 8888

# Use fail2ban for additional protection
sudo apt install fail2ban
```

## 📊 Performance Tips

### Container Optimization
- Monitor container resource usage with `docker stats`
- Adjust memory and CPU limits based on system capacity
- Use SSD storage for better I/O performance
- Enable auto-restart for reliability

### Network Optimization
- Use host networking for maximum performance
- Configure appropriate firewall rules
- Monitor network bandwidth usage
- Consider load balancing for multiple clients

## 📚 Additional Resources

- **Setup Guide**: See `docs/SETUP_GUIDE.md` for initial setup
- **Backend Guide**: See `docs/BACKEND_GUIDE.md` for Vista3D server
- **API Reference**: Check `utils/` directory for script documentation

---

**Need Help?** Check the troubleshooting section or refer to the main setup guide for initial configuration.
