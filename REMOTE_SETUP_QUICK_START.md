# Remote Setup Quick Start

## The Most Common Setup: Remote Backend + Local Frontend

This guide covers the **recommended and most common** deployment:
- **Backend (Vista3D)**: Remote Ubuntu server with NVIDIA GPUs
- **Frontend**: Local Mac
- **Connection**: SSH tunnels

## Quick Setup (3 Steps)

### Step 1: Setup Remote Backend (on Ubuntu Server)

SSH into your Ubuntu server:

```bash
ssh user@your-ubuntu-server
cd ~
git clone https://github.com/your-org/HPE-Nvidia-Vista-3D.git
cd HPE-Nvidia-Vista-3D/backend
python3 setup_backend_remote.py
```

Follow the prompts to enter your NVIDIA NGC API key and configure directories.

**Start the backend:**
```bash
./start_remote_backend.sh
# Or manually:
docker-compose up -d
```

### Step 2: Setup Local Frontend (on your Mac)

```bash
cd ~/AI/HPE
git clone https://github.com/your-org/HPE-Nvidia-Vista-3D.git
cd HPE-Nvidia-Vista-3D/frontend
python3 setup_frontend_local.py
```

Follow the prompts to:
- Set your local DICOM and output folder paths
- Enter your remote server hostname/IP
- Enter your remote server username

### Step 3: Connect and Run

**Terminal 1 - SSH Tunnel (keep open):**
```bash
cd ~/AI/HPE/HPE-Nvidia-Vista-3D/frontend
./connect_to_backend.sh
```

**Terminal 2 - Image Server:**
```bash
cd ~/AI/HPE/HPE-Nvidia-Vista-3D/frontend
./start_image_server.sh
```

**Terminal 3 - Frontend:**
```bash
cd ~/AI/HPE/HPE-Nvidia-Vista-3D/frontend
./start_frontend.sh
```

**Open Browser:**
```
http://localhost:8501
```

## The SSH Tunnel Command Explained

```bash
ssh -L 8000:localhost:8000 -R 8888:localhost:8888 user@remote-server
```

**What each part does:**

- `-L 8000:localhost:8000`: **Forward tunnel**
  - Your Mac's port 8000 → Remote server's port 8000
  - Allows your Mac to access the Vista3D backend
  - Frontend connects to `http://localhost:8000`

- `-R 8888:localhost:8888`: **Reverse tunnel**
  - Remote server's port 8888 → Your Mac's port 8888  
  - Allows Vista3D backend to access your Mac's image server
  - Backend fetches images from `http://localhost:8888`

**Why this works:**

```
┌─────────────────────┐         ┌─────────────────────┐
│   Your Mac          │         │   Ubuntu Server     │
│                     │         │                     │
│   Frontend          │         │   Vista3D           │
│      ↓              │         │      ↑              │
│   localhost:8000 ───┼────────→│   localhost:8000    │
│      (Forward)      │         │   (Backend API)     │
│                     │         │                     │
│   Image Server      │         │                     │
│      ↑              │         │      ↓              │
│   localhost:8888 ←──┼─────────│   localhost:8888    │
│      (Reverse)      │         │   (Fetch Images)    │
└─────────────────────┘         └─────────────────────┘
```

## Common Issues and Solutions

### Issue: SSH tunnel keeps disconnecting

**Solution:** Use the auto-reconnect script or SSH config

**Option 1 - SSH Config** (Recommended):
```bash
# Edit ~/.ssh/config
cat >> ~/.ssh/config << EOF
Host vista3d
    HostName your-server.com
    User your-username
    LocalForward 8000 localhost:8000
    RemoteForward 8888 localhost:8888
    ServerAliveInterval 60
    ServerAliveCountMax 3
EOF

# Connect using:
ssh vista3d
```

**Option 2 - Auto-reconnect script**:
```bash
# Already created by setup: connect_to_backend.sh
./connect_to_backend.sh
```

### Issue: Backend can't access image server

**Check:**
1. SSH reverse tunnel is active
2. Image server is running on Mac
3. Both are using port 8888

**Test:**
```bash
# On Mac: Is image server running?
curl http://localhost:8888/health

# On remote server: Can it reach the tunnel?
curl http://localhost:8888/health
```

### Issue: Frontend can't access backend

**Check:**
1. SSH forward tunnel is active
2. Backend is running on remote server
3. Both are using port 8000

**Test:**
```bash
# On Mac: Can you reach backend?
curl http://localhost:8000/v1/vista3d/info

# On remote server: Is backend running?
docker ps | grep vista3d
curl http://localhost:8000/v1/vista3d/info
```

## Updating Code

### From Mac (after making changes):

```bash
git add .
git commit -m "Your changes"
git push origin main
```

### On Remote Server (to get updates):

```bash
cd ~/HPE-Nvidia-Vista-3D
git pull
cd backend
docker-compose down
docker-compose up -d
```

## Daily Workflow

### Starting Work:

1. **Ensure backend is running** (on remote server):
   ```bash
   ssh user@remote-server
   cd ~/HPE-Nvidia-Vista-3D/backend
   docker-compose up -d
   exit
   ```

2. **Connect with SSH tunnel** (Terminal 1):
   ```bash
   ./connect_to_backend.sh
   ```

3. **Start image server** (Terminal 2):
   ```bash
   ./start_image_server.sh
   ```

4. **Start frontend** (Terminal 3):
   ```bash
   ./start_frontend.sh
   ```

5. **Open browser**: http://localhost:8501

### Ending Work:

1. Stop frontend: `Ctrl+C` in Terminal 3
2. Stop image server: `Ctrl+C` in Terminal 2 (or `docker-compose down`)
3. Close SSH tunnel: `Ctrl+C` in Terminal 1
4. Optionally stop remote backend:
   ```bash
   ssh user@remote-server "cd ~/HPE-Nvidia-Vista-3D/backend && docker-compose down"
   ```

## Alternative: Use start_all.sh

Instead of 3 terminals, use the master script:

```bash
cd ~/AI/HPE/HPE-Nvidia-Vista-3D/frontend
./start_all.sh
```

This will guide you through:
1. Establishing SSH tunnel
2. Starting image server
3. Starting frontend

## Next Steps

- **Full Documentation**: See `docs/REMOTE_BACKEND_SETUP.md`
- **Troubleshooting**: See above or the full docs
- **Data Management**: Consider how to sync DICOM files
- **Production Deployment**: See `docs/HELM.md` for Kubernetes

## Summary

**Setup once:**
1. `setup_backend_remote.py` on Ubuntu server
2. `setup_frontend_local.py` on Mac

**Use daily:**
1. SSH tunnel: `./connect_to_backend.sh`
2. Image server: `./start_image_server.sh`
3. Frontend: `./start_frontend.sh`
4. Browser: http://localhost:8501

**Or just:**
```bash
./start_all.sh
```

That's it! 🚀

