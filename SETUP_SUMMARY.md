# Vista3D Setup Summary

## What Was Fixed

The project has been updated to properly support the **most common deployment scenario**:
- **Backend**: Remote Ubuntu server with NVIDIA GPUs  
- **Frontend**: Local Mac workstation
- **Connection**: SSH tunnels

## Key Changes

### 1. New Setup Scripts

#### Backend Setup (`backend/setup_backend_remote.py`)
- Configures Vista3D backend for remote Ubuntu server
- Sets up proper environment for SSH tunnel access
- Creates startup script for backend

#### Frontend Setup (`frontend/setup_frontend_local.py`)
- Configures frontend for local Mac execution
- Creates SSH tunnel connection script
- Generates startup scripts for image server and frontend

### 2. SSH Tunnel Configuration

**The Critical Command:**
```bash
ssh -L 8000:localhost:8000 -R 8888:localhost:8888 user@remote-server
```

**What it does:**
- `-L 8000:localhost:8000`: Forward local port 8000 → remote Vista3D backend
- `-R 8888:localhost:8888`: Reverse tunnel remote port 8888 → local image server

This allows:
- Mac frontend to access remote Vista3D at `http://localhost:8000`
- Remote Vista3D to fetch images from Mac at `http://localhost:8888`

### 3. New Documentation

- **[REMOTE_SETUP_QUICK_START.md](REMOTE_SETUP_QUICK_START.md)**: Quick guide for remote setup
- **[docs/REMOTE_BACKEND_SETUP.md](docs/REMOTE_BACKEND_SETUP.md)**: Comprehensive remote setup guide
- **[docs/SSH_TUNNEL_GUIDE.md](docs/SSH_TUNNEL_GUIDE.md)**: Complete SSH tunnel documentation

### 4. Updated Configuration

- Updated `.env` templates with proper comments for remote setup
- Updated README with remote setup as primary deployment method
- Fixed backend docker-compose to work with SSH tunnels (already had `extra_hosts`)

## How It Works

### Architecture

```
┌─────────────────────┐         ┌─────────────────────┐
│   Mac (Local)       │         │  Ubuntu (Remote)    │
│                     │         │                     │
│   Frontend :8501    │         │   Vista3D :8000     │
│   Image Srv :8888   │         │   (Docker)          │
│                     │         │                     │
│   SSH Tunnels:      │         │                     │
│   -L 8000 ──────────┼────────>│   :8000             │
│   -R 8888 <─────────┼─────────│   requests :8888    │
└─────────────────────┘         └─────────────────────┘
```

### Request Flow

1. **User views scan**: Frontend → `localhost:8000` (tunnel) → Remote Vista3D
2. **Vista3D gets image**: Vista3D → `localhost:8888` (tunnel) → Mac Image Server
3. **Image served**: Mac Image Server → (tunnel) → Vista3D → processes → (tunnel) → Frontend

## Quick Start

### First Time Setup

**On Ubuntu Server:**
```bash
git clone <repo>
cd HPE-Nvidia-Vista-3D/backend
python3 setup_backend_remote.py
./start_remote_backend.sh
```

**On Mac:**
```bash
git clone <repo>
cd HPE-Nvidia-Vista-3D/frontend
python3 setup_frontend_local.py
```

### Daily Usage

**Terminal 1 - SSH Tunnel** (keep open):
```bash
cd ~/AI/HPE/HPE-Nvidia-Vista-3D/frontend
./connect_to_backend.sh
```

**Terminal 2 - Image Server**:
```bash
cd ~/AI/HPE/HPE-Nvidia-Vista-3D/frontend
./start_image_server.sh
```

**Terminal 3 - Frontend**:
```bash
cd ~/AI/HPE/HPE-Nvidia-Vista-3D/frontend
./start_frontend.sh
```

**Browser**:
```
http://localhost:8501
```

## Files Created

### Setup Scripts
- `backend/setup_backend_remote.py` - Remote backend setup
- `frontend/setup_frontend_local.py` - Local frontend setup

### Startup Scripts (Auto-generated)
- `backend/start_remote_backend.sh` - Start Vista3D backend
- `frontend/connect_to_backend.sh` - Create SSH tunnels
- `frontend/start_image_server.sh` - Start local image server
- `frontend/start_frontend.sh` - Start local frontend
- `frontend/start_all.sh` - Master startup script

### Documentation
- `REMOTE_SETUP_QUICK_START.md` - Quick start guide
- `docs/REMOTE_BACKEND_SETUP.md` - Comprehensive setup guide
- `docs/SSH_TUNNEL_GUIDE.md` - SSH tunnel documentation
- `SETUP_SUMMARY.md` - This file

## Deployment Options

### 1. Remote Backend + Local Frontend (Recommended)
- Backend on Ubuntu server with GPUs
- Frontend on Mac
- Connected via SSH tunnels
- **Use**: `setup_backend_remote.py` and `setup_frontend_local.py`

### 2. All-in-One Local
- Everything on one machine
- Good for development
- **Use**: `setup.py`

### 3. Kubernetes
- Production deployment
- Helm charts included
- **Use**: `helm/vista3d/`

## Troubleshooting

### SSH Tunnel Issues

**Tunnel disconnects:**
```bash
# Use auto-reconnect
./connect_to_backend.sh
# (Already includes ServerAliveInterval)
```

**Port already in use:**
```bash
# Find and kill existing tunnel
lsof -i :8000
kill -9 <PID>
```

### Backend Can't Access Image Server

**Test from remote server:**
```bash
curl http://localhost:8888/health
# Should return: {"status":"healthy","service":"image-server"}
```

**If fails:**
1. Check SSH reverse tunnel is active
2. Check image server is running on Mac
3. Restart SSH tunnel

### Frontend Can't Access Backend

**Test from Mac:**
```bash
curl http://localhost:8000/v1/vista3d/info
# Should return Vista3D info
```

**If fails:**
1. Check SSH forward tunnel is active
2. Check backend is running on remote server
3. Restart SSH tunnel

## Git Workflow

### Making Changes on Mac

```bash
git add .
git commit -m "Your changes"
git push origin main
```

### Updating Remote Server

```bash
ssh user@remote-server
cd ~/HPE-Nvidia-Vista-3D
git pull
cd backend
docker-compose down
docker-compose up -d
```

## Next Steps

1. **Try it out**: Follow the Quick Start above
2. **Read the docs**: See `REMOTE_SETUP_QUICK_START.md`
3. **Customize**: Adjust paths and ports as needed
4. **Production**: Consider Kubernetes deployment (`docs/HELM.md`)

## Support

- **Quick Start**: [REMOTE_SETUP_QUICK_START.md](REMOTE_SETUP_QUICK_START.md)
- **Full Guide**: [docs/REMOTE_BACKEND_SETUP.md](docs/REMOTE_BACKEND_SETUP.md)
- **SSH Tunnels**: [docs/SSH_TUNNEL_GUIDE.md](docs/SSH_TUNNEL_GUIDE.md)
- **Main README**: [README.md](README.md)

## Summary

The project now has first-class support for remote backend deployment with:
- ✅ Dedicated setup scripts for remote backend and local frontend
- ✅ Automatic SSH tunnel configuration
- ✅ Startup scripts for easy daily use
- ✅ Comprehensive documentation
- ✅ Troubleshooting guides

**The remote setup is now the primary and recommended deployment method.**

