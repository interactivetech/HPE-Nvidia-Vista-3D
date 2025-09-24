# Vista3D Backend Server Guide

This guide explains how to start and manage the Vista3D backend server for AI-powered medical image segmentation.

## 🚀 Quick Start

### Start Vista3D Server
```bash
# Start the Vista3D server (requires GPU)
python3 start_backend.py
```

**This starts:**
- 🧠 **Vista3D AI Server** (http://localhost:8000)
- ⚡ **GPU-accelerated processing** for medical image segmentation
- 🔄 **Auto-restart capability** for production deployments

**Note**: The Vista3D server takes a few minutes to initialize and be ready for use.

## 📋 Prerequisites

### System Requirements
- **Linux Server** (Ubuntu 18.04+ or RHEL/CentOS 7+)
- **NVIDIA GPU** with CUDA support (RTX/Tesla/A100/H100 series)
- **NVIDIA Drivers** (version 470+)
- **Docker** and **NVIDIA Container Toolkit**
- **At least 8GB RAM** and **10GB free disk space**
- **NVIDIA NGC account** and API key

### Pre-Setup
Before starting the backend, ensure you've run the initial setup:
```bash
# Run the unified setup script first
python3 setup.py
```

## 🐍 Virtual Environment Setup

The backend uses a separate virtual environment with AI/ML dependencies. Here's how to activate it:

### Method 1: Direct Activation (Recommended)
```bash
# Navigate to the project directory
cd /path/to/HPE-Nvidia-Vista-3D

# Activate the backend environment directly
source .venv-backend/bin/activate
```

### Method 2: Using `uv run` (No Activation Needed)
```bash
# Run backend commands directly without activating the environment
uv run --python .venv-backend/bin/python your_backend_script.py
```

### Method 3: Using `uv` with Active Environment
```bash
# Activate the environment first
source .venv-backend/bin/activate

# Then use uv commands (but avoid 'uv sync' as it tries to build packages)
uv pip install package_name  # Use this instead of uv sync
```

**⚠️ Important Note**: Do not use `uv sync` with the backend environment as it will try to build the project as a package, which will fail. Use `uv pip install` instead for installing additional packages.

### Environment Verification
```bash
# Test backend environment
source .venv-backend/bin/activate
python -c "import monai, torch, nibabel; print('✅ Backend environment working!'); print(f'MONAI: {monai.__version__}, PyTorch: {torch.__version__}')"
```

## 🔧 Configuration

### Environment Variables
The backend uses these key environment variables from your `.env` file:

```bash
# Server Configuration
VISTA3D_SERVER=http://localhost:8000
VISTA3D_PORT=8000
USE_HOST_NETWORKING=True

# GPU Configuration
CUDA_VISIBLE_DEVICES=0
GPU_MEMORY_FRACTION=0.9

# Performance Settings
VISTA3D_MEMORY_LIMIT=16G
VISTA3D_CPU_LIMIT=8
VISTA3D_SHM_SIZE=12G
VISTA3D_AUTO_RESTART=true

# NGC Credentials
NGC_API_KEY=nvapi-xxxxxxxxxxxxx
NGC_ORG_ID=nvidia
LOCAL_NIM_CACHE=~/.cache/nim
```

### Network Configuration
- **Host Networking**: Recommended for maximum compatibility
- **Port 8000**: Default Vista3D API port
- **Firewall**: Ensure port 8000 is open for external access
- **Security**: Consider VPN or secure tunnel for production use

## 🌐 Remote Server Deployment

### Server Setup (GPU Machine)
```bash
# On the GPU server
python3 start_backend.py
```

### Network Access Configuration
```bash
# Open firewall port (replace 8000 with your chosen port)
sudo ufw allow 8000

# Or for iptables
sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
```

### Get Server IP Address
```bash
# Get public IP
curl ifconfig.me

# Get local IP
ip addr show | grep inet
```

### Client Configuration
On your client machines, update the `.env` file:
```bash
# In your client's .env file
VISTA3D_SERVER=http://YOUR_SERVER_IP:8000
IMAGE_SERVER=http://YOUR_CLIENT_IP:8888
```

## 🧪 Testing the Setup

### Server Health Check
```bash
# Test from the server itself
curl http://localhost:8000/health

# Test from a remote client
curl http://YOUR_SERVER_IP:8000/health
```

### Test Inference
```bash
curl -X POST http://YOUR_SERVER_IP:8000/v1/vista3d/inference \
     -H "Content-Type: application/json" \
     -d '{"image": "http://YOUR_CLIENT_IP:8888/path/to/image.nii.gz"}'
```

### Query API for Supported Labels
```bash
curl http://YOUR_SERVER_IP:8000/v1/vista3d/info
```

## 📊 Monitoring

### Check Container Status
```bash
# Check container status
docker ps | grep vista3d

# View server logs
docker logs -f vista3d

# Monitor GPU usage
nvidia-smi

# Monitor resource usage
docker stats vista3d
```

### Performance Monitoring
```bash
# GPU usage
watch -n 1 nvidia-smi

# Container stats
docker stats vista3d

# System resource usage
htop

# Network connections
netstat -tlnp | grep 8000
```

## 🔧 Management Commands

### Server Management
```bash
# Start server
python3 start_backend.py

# Stop server
docker stop vista3d

# Restart server
docker restart vista3d

# View logs
docker logs -f vista3d

# Check status
docker ps | grep vista3d
```

### System Service Management (Optional)
```bash
# Create systemd service for automatic startup on boot
sudo python3 start_backend.py --create-service

# Enable and start service
sudo systemctl enable vista3d
sudo systemctl start vista3d

# Check service status
sudo systemctl status vista3d

# View service logs
sudo journalctl -u vista3d -f
```

## 🔍 Troubleshooting

### Common Issues

#### GPU Not Detected
```bash
# Check GPU
nvidia-smi

# Test NVIDIA Docker
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi

# Check NVIDIA runtime
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

#### Port Not Accessible
```bash
# Check if port is in use
netstat -tlnp | grep 8000

# Check firewall
sudo ufw status
sudo iptables -L
```

#### Container Won't Start
```bash
# Check Docker logs
docker logs vista3d

# Check system resources
nvidia-smi
free -h
df -h

# Check Docker daemon
sudo systemctl status docker
```

#### NGC Authentication Failed
```bash
# Verify API key format
grep NGC_API_KEY .env
# Should start with 'nvapi-'

# Test NGC login
docker login nvcr.io -u '$oauthtoken' -p 'your-api-key'
```

#### Vista3D API Not Responding
```bash
# Check if container is running
docker ps | grep vista3d

# Check container logs for errors
docker logs vista3d

# Test API connectivity
curl -v http://localhost:8000/v1/vista3d/info
```

### Debug Commands
```bash
# Check GPU
nvidia-smi

# Check Docker
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi

# Check container logs
docker logs -f vista3d

# Check network
netstat -tlnp | grep 8000
```

## 🔐 Security Considerations

### Production Deployment
1. **Use HTTPS** for external access
2. **Implement authentication** for API endpoints
3. **Use VPN** or secure tunnel for network access
4. **Regular security updates** for system and Docker images
5. **Monitor access logs** for suspicious activity
6. **Backup configuration** and data regularly

### Network Security
```bash
# Restrict access to specific IPs
sudo ufw allow from 192.168.1.0/24 to any port 8000

# Use fail2ban for additional protection
sudo apt install fail2ban
```

## 📊 Performance Optimization

### GPU Optimization
- Use multiple GPUs for parallel processing
- Monitor GPU memory usage
- Adjust `GPU_MEMORY_FRACTION` based on available memory
- Use `CUDA_VISIBLE_DEVICES` to control GPU access

### Container Optimization
- Adjust memory and CPU limits based on server capacity
- Use SSD storage for better I/O performance
- Monitor shared memory usage
- Enable auto-restart for reliability

### Network Optimization
- Use host networking for maximum performance
- Configure appropriate firewall rules
- Monitor network bandwidth usage
- Consider load balancing for multiple clients

## 🌐 Remote Client Setup

For clients connecting to a remote Vista3D server:

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

## 🏗️ Architecture

The backend uses Docker containers for all services:
- **Image**: `nvcr.io/nim/nvidia/vista3d:1.0.0`
- **Port**: 8000 (Vista3D API)
- **GPU**: All available GPUs
- **Memory**: 8GB shared memory
- **Volumes**: Project output directory mounted at `/workspace/output`
- **Runtime**: NVIDIA Container Runtime
- **Environment Variables**: NGC credentials and file access settings

## 📚 Additional Resources

- **Setup Guide**: See `docs/SETUP_GUIDE.md` for initial setup
- **Frontend Guide**: See `docs/FRONTEND_GUIDE.md` for web interface
- **API Reference**: Check `utils/` directory for script documentation

---

**Need Help?** Check the troubleshooting section or refer to the main setup guide for initial configuration.
