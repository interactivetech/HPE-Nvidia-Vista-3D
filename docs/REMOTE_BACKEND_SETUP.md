# Remote Backend Setup Guide

## Overview

This guide covers the recommended setup where:
- **Backend (Vista3D)** runs on a remote Ubuntu server with NVIDIA GPUs
- **Frontend** runs locally on your Mac
- **Image Server** runs locally on your Mac
- **SSH tunnels** connect the two systems

## Architecture

```
┌─────────────────────────────┐         ┌──────────────────────────────┐
│   Your Mac (Local)          │         │  Ubuntu Server (Remote)      │
│                             │         │                              │
│  ┌─────────────────────┐   │         │  ┌──────────────────────┐   │
│  │  Frontend           │   │         │  │  Vista3D Backend     │   │
│  │  (Streamlit)        │   │         │  │  (Docker Container)  │   │
│  │  Port: 8501         │   │         │  │  Port: 8000          │   │
│  └─────────────────────┘   │         │  └──────────────────────┘   │
│                             │         │                              │
│  ┌─────────────────────┐   │         │                              │
│  │  Image Server       │   │         │                              │
│  │  (FastAPI)          │   │         │                              │
│  │  Port: 8888         │   │         │                              │
│  └─────────────────────┘   │         │                              │
│                             │         │                              │
│  SSH Tunnels:               │         │                              │
│  -L 8000:localhost:8000 ────┼────────>│  (Forward: Access backend)   │
│  -R 8888:0.0.0.0:8888 <─────┼─────────│  (Reverse: Backend→Image)    │
│                             │         │                              │
└─────────────────────────────┘         └──────────────────────────────┘
```

## Prerequisites

### On Remote Ubuntu Server:
- Ubuntu 18.04+ with NVIDIA GPU
- Docker and NVIDIA Container Toolkit installed
- NVIDIA NGC API key
- SSH access enabled
- Git installed

### On Local Mac:
- macOS
- Docker installed (for image server) or Python 3.8+ (for native execution)
- SSH client (built-in)
- Git installed

## Step-by-Step Setup

### 1. Setup Remote Backend (Ubuntu Server)

SSH into your remote server:

```bash
ssh user@remote-server
```

Clone and setup the backend:

```bash
# Clone the repository
git clone https://github.com/your-org/HPE-Nvidia-Vista-3D.git
cd HPE-Nvidia-Vista-3D/backend

# Run the backend setup script
python3 setup.py
```

The setup script will:
- Verify Docker and NVIDIA GPU availability
- Ask for your NVIDIA NGC API key
- Configure the backend for remote access
- Pull the Vista3D Docker image (~30GB)
- Create a `.env` file with proper configuration

**Important**: The backend `.env` should have:
```bash
# Backend .env configuration
NGC_API_KEY="nvapi-your-key-here"
NGC_ORG_ID=""
OUTPUT_FOLDER="/path/to/output"
VISTA3D_SERVER="http://localhost:8000"
IMAGE_SERVER="http://localhost:8888"  # Will be accessed via SSH reverse tunnel
```

### 2. Setup Local Frontend (Mac)

On your Mac:

```bash
# Clone the repository
git clone https://github.com/your-org/HPE-Nvidia-Vista-3D.git
cd HPE-Nvidia-Vista-3D/frontend

# Run the frontend setup script
python3 setup.py
```

The setup script will:
- Verify Docker availability
- Configure frontend to connect to remote backend
- Set up the image server
- Install sample data (if available)
- Create a `.env` file

**Important**: The frontend `.env` should have:
```bash
# Frontend .env configuration
DICOM_FOLDER="/absolute/path/to/dicom"
OUTPUT_FOLDER="/absolute/path/to/output"
VISTA3D_SERVER="http://host.docker.internal:8000"  # Via SSH forward tunnel
IMAGE_SERVER="http://localhost:8888"     # Local image server
VISTA3D_IMAGE_SERVER_URL="http://host.docker.internal:8888"  # For backend to fetch images
IMAGE_SERVER_PORT="8888"
```

### 3. Start the Remote Backend

On the remote Ubuntu server:

```bash
cd HPE-Nvidia-Vista-3D/backend

# Start Vista3D server
docker-compose up -d

# Verify it's running
docker ps
docker logs -f vista3d-server-standalone

# Test the API
curl http://localhost:8000/v1/vista3d/info
```

The backend should be running and accessible on port 8000 (localhost only).

### 4. Establish SSH Tunnels

On your Mac, create the SSH tunnels:

```bash
# Connect with both forward and reverse tunnels
ssh -L 8000:localhost:8000 -R 8888:0.0.0.0:8888 user@remote-server

# Alternative: Run in background
ssh -f -N -L 8000:localhost:8000 -R 8888:0.0.0.0:8888 user@remote-server
```

**Tunnel Explanation:**
- `-L 8000:localhost:8000`: Forward local port 8000 to remote server's localhost:8000 (Vista3D)
- `-R 8888:0.0.0.0:8888`: Reverse tunnel remote port 8888 to your Mac's localhost:8888 (Image Server)
  - **CRITICAL**: Must use `0.0.0.0` (not `localhost`) so Docker containers on Ubuntu can access it
- `-f`: Run in background (optional)
- `-N`: Don't execute remote commands (optional)

**Verify tunnels are working:**

```bash
# On your Mac, test backend access
curl http://localhost:8000/v1/vista3d/info

# On remote server, test image server access
curl http://localhost:8888/health
```

### 5. Start Frontend & Image Server (on Your Mac)

The frontend docker-compose.yml includes both services, so one command starts everything:

```bash
cd HPE-Nvidia-Vista-3D/frontend

# Start both frontend and image server together
docker compose up -d

# View logs
docker compose logs -f

# View specific service logs
docker compose logs -f vista3d-frontend-standalone
docker compose logs -f vista3d-image-server-for-frontend
```

#### Alternative: Native Python Execution (Development Only)

```bash
cd HPE-Nvidia-Vista-3D/frontend

# Install dependencies (first time only)
uv pip install -r requirements.txt

# Start frontend
streamlit run app.py --server.port 8501
```

**Note**: For native execution, you need to start the image server separately in another terminal.

### 6. Access the Web Interface

Open your browser:
- **Frontend**: http://localhost:8501
- **Image Server**: http://localhost:8888 (serves files)
- **Vista3D API**: http://localhost:8000/docs (via tunnel)

## SSH Tunnel Management

### Keep SSH Tunnel Alive

Create a persistent SSH connection:

```bash
# Create an SSH config file: ~/.ssh/config
Host vista3d-remote
    HostName your-remote-server.com
    User your-username
    LocalForward 8000 localhost:8000
    RemoteForward 8888 localhost:8888
    ServerAliveInterval 60
    ServerAliveCountMax 3
    ExitOnForwardFailure yes

# Connect using the config
ssh vista3d-remote
```

### Auto-reconnect Script

Create a script to auto-reconnect SSH tunnels:

```bash
#!/bin/bash
# save as: ~/vista3d-tunnel.sh

HOST="user@remote-server"
FORWARD_PORT="8000:localhost:8000"
REVERSE_PORT="8888:localhost:8888"

while true; do
    echo "Starting SSH tunnels..."
    ssh -o ServerAliveInterval=60 \
        -o ServerAliveCountMax=3 \
        -o ExitOnForwardFailure=yes \
        -L $FORWARD_PORT \
        -R $REVERSE_PORT \
        $HOST
    
    echo "Connection lost. Reconnecting in 5 seconds..."
    sleep 5
done
```

Make it executable:
```bash
chmod +x ~/vista3d-tunnel.sh
./vista3d-tunnel.sh
```

### Check Tunnel Status

```bash
# Check if tunnels are active
ps aux | grep ssh
lsof -i :8000
lsof -i :8888

# Test backend access
curl http://localhost:8000/v1/vista3d/info

# Test image server access
curl http://localhost:8888/health
```

## Data Synchronization

Since the frontend and backend are on different machines, you need to ensure data is accessible:

### Option 1: Shared Storage (Recommended for Production)

Use a shared file system like NFS or S3:

```bash
# On remote server, setup NFS export
# On Mac, mount NFS share
# Both systems access same data
```

### Option 2: Manual Synchronization

```bash
# Upload DICOM files to remote server
scp -r dicom/PA00000001 user@remote-server:/path/to/dicom/

# Download processed output from remote server
scp -r user@remote-server:/path/to/output/PA00000001 output/
```

### Option 3: Rsync (Best for Large Files)

```bash
# Sync dicom folder to remote
rsync -avz --progress dicom/ user@remote-server:/path/to/dicom/

# Sync output from remote
rsync -avz --progress user@remote-server:/path/to/output/ output/
```

### Option 4: Current Setup (Image Server on Mac)

The current recommended approach:
- DICOM and output files stay on your Mac
- Image server on Mac serves files to remote backend via SSH reverse tunnel
- Backend accesses files at `http://localhost:8888` (which tunnels to your Mac)
- This works well for small datasets and development

## Code Updates via Git

When you make changes:

### On Mac (Local Development):
```bash
# Make your changes
git add .
git commit -m "Description of changes"
git push origin main
```

### On Remote Server:
```bash
# Pull latest changes
cd HPE-Nvidia-Vista-3D
git pull

# Restart backend if needed
cd backend
docker-compose down
docker-compose up -d
```

## Troubleshooting

### Backend Can't Access Image Server

```bash
# On remote server, test from within Vista3D container
docker exec vista3d-server-standalone curl -I http://localhost:8888

# If this fails, check:
# 1. SSH reverse tunnel is active
curl http://localhost:8888  # On remote server host

# 2. Image server is running on Mac
curl http://localhost:8888  # On Mac

# 3. Check Vista3D container logs
docker logs vista3d-server-standalone
```

### Frontend Can't Access Backend

```bash
# On Mac, test backend access
curl http://localhost:8000/v1/vista3d/info

# If this fails, check:
# 1. SSH forward tunnel is active
lsof -i :8000

# 2. Backend is running on remote server
# (SSH into server and check)
docker ps
curl http://localhost:8000/v1/vista3d/info
```

### SSH Tunnel Keeps Disconnecting

```bash
# Use SSH config with keep-alive
# Edit ~/.ssh/config:
Host vista3d-remote
    ServerAliveInterval 60
    ServerAliveCountMax 3
    TCPKeepAlive yes
    
# Or use autossh
brew install autossh
autossh -M 0 -f -N -L 8000:localhost:8000 -R 8888:localhost:8888 user@remote-server
```

### Port Already in Use

```bash
# Find what's using the port
lsof -i :8000  # or :8888, :8501

# Kill the process if needed
kill -9 <PID>
```

### Firewall Issues

```bash
# On remote server, ensure ports are open for SSH
sudo ufw status
sudo ufw allow 22/tcp

# Note: Ports 8000 and 8888 don't need to be open externally
# They're only accessed via SSH tunnels
```

## Performance Considerations

1. **Network Bandwidth**: SSH tunnels add overhead. For large DICOM files, consider:
   - Compressing files before upload
   - Using rsync for efficient transfers
   - Setting up a VPN for better performance

2. **Latency**: SSH tunnels add latency. For interactive work:
   - Keep connections alive with ServerAliveInterval
   - Use compression: `ssh -C` flag
   - Consider a dedicated VPN

3. **Data Transfer**: For large datasets:
   - Upload data directly to remote server
   - Process on remote server
   - Download only final results

## Security Best Practices

1. **Use SSH Keys**: Instead of passwords
   ```bash
   ssh-keygen -t ed25519
   ssh-copy-id user@remote-server
   ```

2. **Restrict SSH Access**: Configure `~/.ssh/config`
   ```
   Host vista3d-remote
       IdentityFile ~/.ssh/vista3d_key
       IdentitiesOnly yes
   ```

3. **Use Bastion/Jump Host**: If available
   ```bash
   ssh -J bastion-host vista3d-remote
   ```

4. **Firewall Rules**: On remote server
   ```bash
   sudo ufw enable
   sudo ufw allow 22/tcp
   sudo ufw deny 8000/tcp  # Only accessible via SSH tunnel
   sudo ufw deny 8888/tcp  # Only accessible via SSH tunnel
   ```

## Quick Reference

### Start Everything (Typical Workflow)

1. **Start Remote Backend** (once per server reboot):
   ```bash
   ssh user@remote-server
   cd HPE-Nvidia-Vista-3D/backend
   docker-compose up -d
   exit
   ```

2. **Start SSH Tunnels** (keep running):
   ```bash
   ssh -L 8000:localhost:8000 -R 8888:0.0.0.0:8888 user@remote-server
   # Or use background mode:
   ssh -f -N -L 8000:localhost:8000 -R 8888:0.0.0.0:8888 user@remote-server
   ```
   
   **Important**: Must use `-R 8888:0.0.0.0:8888` (not `localhost`) so Docker containers can access it!

3. **Start Frontend & Image Server** (on your Mac):
   ```bash
   cd HPE-Nvidia-Vista-3D/frontend
   docker compose up -d  # Starts both frontend and image server
   ```

5. **Open Browser**: http://localhost:8501

### Stop Everything

```bash
# Stop frontend & image server (on Mac)
cd HPE-Nvidia-Vista-3D/frontend
docker compose down

# Kill SSH tunnel (if background)
pkill -f "ssh.*8000.*8888"

# Stop remote backend (SSH into server)
ssh user@remote-server
cd HPE-Nvidia-Vista-3D/backend
docker compose down
```

## Next Steps

- Set up automated backup for your data
- Configure monitoring for the remote server
- Set up alerts for service failures
- Consider Kubernetes deployment for production (see `docs/HELM.md`)

## Support

For issues:
1. Check the troubleshooting section above
2. Review logs: `docker logs vista3d-server-standalone`
3. Verify SSH tunnels are active
4. Check firewall and network settings

