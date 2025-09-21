# Vista3D Server Setup Guide

This guide explains how to deploy the Vista3D server on a remote Linux host with NVIDIA GPU support for AI processing.

## 🚀 **Vista3D Server Deployment on Remote Host**

### **Prerequisites for Remote Host**
1. **Linux Server** (Ubuntu 18.04+ or RHEL/CentOS 7+)
2. **NVIDIA GPU** with CUDA support (RTX/Tesla/A100/H100 series)
3. **NVIDIA Drivers** (version 470+)
4. **Docker** and **NVIDIA Container Toolkit**
5. **At least 8GB RAM** and **10GB free disk space**
6. **NVIDIA NGC account** and API key

### **Step 1: Prepare the Remote Host**

```bash
# 1. Clone the repository on the remote host
git clone <your-repo-url>
cd HPE-Nvidia-Vista-3D

# 2. Run the server setup script
python3 setup_vista3d_server.py
```

This will:
- Check system requirements (NVIDIA GPU, Docker, NGC CLI)
- Configure server settings (ports, networking, performance)
- Set up NGC credentials
- Create environment configuration
- Set up Vista3D Docker container

### **Step 2: Configure Server Settings**

The setup script will prompt you for:

- **Vista3D Server Port** (default: 8000)
- **Network Configuration** (host networking recommended for servers)
- **Output Folder** (absolute path for processed results)
- **GPU Configuration** (which GPUs to use)
- **Performance Settings** (memory, CPU limits)
- **Auto-restart** (enable automatic container restart)

### **Step 3: Start the Vista3D Server**

```bash
# Start the Vista3D server container
python3 utils/start_vista3d_server.py
```

This will:
- Start the Vista3D Docker container with GPU support
- Configure for external client access
- Set up networking for remote connections

### **Step 4: Configure Network Access**

**For External Access:**
```bash
# Open firewall port (replace 8000 with your chosen port)
sudo ufw allow 8000

# Or for iptables
sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
```

**Get Server IP Address:**
```bash
# Get public IP
curl ifconfig.me

# Get local IP
ip addr show | grep inet
```

### **Step 5: Test Server Connectivity**

```bash
# Test from the server itself
curl http://localhost:8000/health

# Test from a remote client
curl http://YOUR_SERVER_IP:8000/health
```

### **Step 6: Configure Client Connections**

On your client machines, update the `.env` file:

```bash
# In your client's .env file
VISTA3D_SERVER=http://YOUR_SERVER_IP:8000
IMAGE_SERVER=http://YOUR_CLIENT_IP:8888
```

### **Step 7: Monitor Server Status**

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

### **Step 8: Optional - Set Up as System Service**

For automatic startup on boot:

```bash
# Create systemd service
sudo python3 utils/start_vista3d_server.py --create-service

# Enable and start service
sudo systemctl enable vista3d
sudo systemctl start vista3d

# Check service status
sudo systemctl status vista3d
```

## 🔧 **Server Configuration Details**

### **Environment Variables** (in `.env` file):
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

### **Network Configuration:**
- **Host Networking**: Recommended for maximum compatibility
- **Port 8000**: Default Vista3D API port
- **Firewall**: Ensure port 8000 is open for external access
- **Security**: Consider VPN or secure tunnel for production use

## 🧪 **Testing the Setup**

1. **Server Health Check:**
   ```bash
   curl http://YOUR_SERVER_IP:8000/health
   ```

2. **Test Inference:**
   ```bash
   curl -X POST http://YOUR_SERVER_IP:8000/v1/vista3d/inference \
        -H "Content-Type: application/json" \
        -d '{"image": "http://YOUR_CLIENT_IP:8888/path/to/image.nii.gz"}'
   ```

3. **Monitor Performance:**
   ```bash
   # GPU usage
   watch -n 1 nvidia-smi
   
   # Container stats
   docker stats vista3d
   ```

## 🔍 **Troubleshooting**

**Common Issues:**
- **GPU not detected**: Check NVIDIA drivers and Container Toolkit
- **Port not accessible**: Check firewall and network configuration
- **Container won't start**: Check Docker logs and resource availability
- **NGC authentication failed**: Verify API key and organization ID

**Debug Commands:**
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

## 📋 **Quick Reference Commands**

### **Server Management:**
```bash
# Start server
python3 utils/start_vista3d_server.py

# Stop server
docker stop vista3d

# Restart server
docker restart vista3d

# View logs
docker logs -f vista3d

# Check status
docker ps | grep vista3d
```

### **System Service Management:**
```bash
# Start service
sudo systemctl start vista3d

# Stop service
sudo systemctl stop vista3d

# Restart service
sudo systemctl restart vista3d

# Check service status
sudo systemctl status vista3d

# View service logs
sudo journalctl -u vista3d -f
```

### **Performance Monitoring:**
```bash
# GPU usage
nvidia-smi

# Container resource usage
docker stats vista3d

# System resource usage
htop

# Network connections
netstat -tlnp | grep 8000
```

## 🔐 **Security Considerations**

### **Production Deployment:**
1. **Use HTTPS** for external access
2. **Implement authentication** for API endpoints
3. **Use VPN** or secure tunnel for network access
4. **Regular security updates** for system and Docker images
5. **Monitor access logs** for suspicious activity
6. **Backup configuration** and data regularly

### **Network Security:**
```bash
# Restrict access to specific IPs
sudo ufw allow from 192.168.1.0/24 to any port 8000

# Use fail2ban for additional protection
sudo apt install fail2ban
```

## 📊 **Performance Optimization**

### **GPU Optimization:**
- Use multiple GPUs for parallel processing
- Monitor GPU memory usage
- Adjust `GPU_MEMORY_FRACTION` based on available memory
- Use `CUDA_VISIBLE_DEVICES` to control GPU access

### **Container Optimization:**
- Adjust memory and CPU limits based on server capacity
- Use SSD storage for better I/O performance
- Monitor shared memory usage
- Enable auto-restart for reliability

### **Network Optimization:**
- Use host networking for maximum performance
- Configure appropriate firewall rules
- Monitor network bandwidth usage
- Consider load balancing for multiple clients

This setup will give you a fully functional Vista3D server that can process medical imaging data and serve multiple clients remotely.
