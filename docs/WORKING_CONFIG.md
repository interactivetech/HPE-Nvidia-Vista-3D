# Working Configuration Reference

This document shows the **verified working configuration** for Vista3D with remote backend setup.

## Overview

- **Backend**: Ubuntu server with NVIDIA GPU
- **Frontend**: Mac with Docker
- **Connection**: SSH tunnels

## Frontend Configuration (Mac)

**File: `frontend/.env`**

```bash
# Data Directories
DICOM_FOLDER=/Users/dave/AI/HPE/HPE-Nvidia-Vista-3D/dicom
OUTPUT_FOLDER=/Users/dave/AI/HPE/HPE-Nvidia-Vista-3D/output

# Server URLs - CRITICAL SETTINGS
VISTA3D_SERVER=http://host.docker.internal:8000
IMAGE_SERVER=http://localhost:8888
VISTA3D_IMAGE_SERVER_URL=http://host.docker.internal:8888

# Ports
FRONTEND_PORT=8501
IMAGE_SERVER_PORT=8888

# Configuration
VESSELS_OF_INTEREST=all
COMPOSE_PROJECT_NAME=vista3d-frontend
```

### Why These URLs?

**`VISTA3D_SERVER=http://host.docker.internal:8000`**
- Frontend container uses `host.docker.internal` to reach Mac's localhost
- Mac's `localhost:8000` is the SSH forward tunnel to Ubuntu backend
- ✅ This works because Docker Desktop on Mac maps `host.docker.internal` to host

**`VISTA3D_IMAGE_SERVER_URL=http://localhost:8888`**
- This URL is sent to the Vista3D backend
- Backend (on Ubuntu) uses `localhost` to reach SSH reverse tunnel on Ubuntu host
- Ubuntu host's `localhost:8888` is the SSH reverse tunnel back to Mac
- ✅ Backend connects directly to localhost (no need for host.docker.internal mapping)

**`IMAGE_SERVER=http://localhost:8888`**
- Used by browser and local scripts
- Points to image server running on Mac

## Backend Configuration (Ubuntu Server)

**File: `backend/.env`**

```bash
# NVIDIA NGC Configuration
NGC_API_KEY=nvapi-YOUR_API_KEY_HERE
NGC_ORG_ID=

# Data Directories
OUTPUT_FOLDER=/path/to/output

# Server Configuration
VISTA3D_SERVER=http://localhost:8000
IMAGE_SERVER=http://localhost:8888

# Docker Configuration
COMPOSE_PROJECT_NAME=vista3d-backend
```

### Why These URLs?

**`IMAGE_SERVER=http://localhost:8888`**
- Backend container accesses via `host.docker.internal` (mapped in docker-compose.yml)
- This reaches Ubuntu host's `localhost:8888`
- Which is the SSH reverse tunnel back to Mac's image server
- ✅ Works because of the extra_hosts configuration

## SSH Tunnel Command

**Run this on your Mac:**

```bash
ssh -L 8000:localhost:8000 -R 8888:0.0.0.0:8888 user@ubuntu-server
```

### Critical Details

**Forward Tunnel: `-L 8000:localhost:8000`**
- Maps Mac's `localhost:8000` to Ubuntu's `localhost:8000`
- Frontend can access remote backend

**Reverse Tunnel: `-R 8888:0.0.0.0:8888`**
- Maps Ubuntu's `localhost:8888` back to Mac's port 8888
- **MUST use `0.0.0.0`** (not `localhost`) so Docker containers can access it
- Without `0.0.0.0`, Docker containers on Ubuntu cannot reach the tunneled port

## Docker Compose Configuration

### Frontend (already correct)

**File: `frontend/docker-compose.yml`**

```yaml
services:
  vista3d-frontend:
    environment:
      - VISTA3D_SERVER=${VISTA3D_SERVER:-http://host.docker.internal:8000}
      - VISTA3D_IMAGE_SERVER_URL=${VISTA3D_IMAGE_SERVER_URL:-http://host.docker.internal:8888}
```

### Backend (already correct)

**File: `backend/docker-compose.yml`**

```yaml
services:
  vista3d-server:
    environment:
      - IMAGE_SERVER=${IMAGE_SERVER:-http://localhost:8888}
    extra_hosts:
      - "host.docker.internal:host-gateway"  # Maps to Ubuntu host
```

## Data Flow (Verified Working)

```
┌────────────────── Mac ──────────────────┐
│                                          │
│  Browser → http://localhost:8501        │
│                ↓                         │
│  Frontend Container                     │
│    → http://host.docker.internal:8000  │ (reaches Mac's localhost)
│                ↓                         │
│  Mac's localhost:8000                   │
│                ↓                         │
│  SSH Forward Tunnel (-L 8000)          │
└────────────────┼────────────────────────┘
                 │ Internet
┌────────────────┼────── Ubuntu ──────────┐
│                ↓                         │
│  Vista3D Backend :8000                  │
│                ↓                         │
│  Fetch image from:                      │
│    URL: http://host.docker.internal:8888│ (via request payload)
│                ↓                         │
│  Container resolves to Ubuntu host      │
│                ↓                         │
│  Ubuntu host's localhost:8888           │
│                ↓                         │
│  SSH Reverse Tunnel (-R 8888)          │
└────────────────┼────────────────────────┘
                 │ Internet
┌────────────────┼────── Mac ─────────────┐
│                ↓                         │
│  Image Server :8888                     │
│    ✅ Returns NIfTI file                │
└──────────────────────────────────────────┘
```

## Startup Sequence

### 1. Start Backend (Ubuntu)
```bash
cd backend
docker compose up -d
```

### 2. Create SSH Tunnel (Mac)
```bash
ssh -L 8000:localhost:8000 -R 8888:0.0.0.0:8888 user@ubuntu-server
```
Keep this terminal open!

### 3. Start Frontend (Mac)
```bash
cd frontend
docker compose up -d
```

### 4. Access
Open browser: **http://localhost:8501**

## Troubleshooting Quick Reference

### Test Connectivity
```bash
cd frontend
bash quick_test.sh
```

### On Ubuntu Server
```bash
# Test reverse tunnel
netstat -tln | grep 8888                                        # Should show 0.0.0.0:8888
curl http://localhost:8888/health                               # Should return HTTP 200
docker exec vista3d-server-standalone curl http://localhost:8888/health  # Should return HTTP 200
```

### Common Issues

**Segmentation fails with "Connection refused":**
- Reverse SSH tunnel not working
- Solution: Ensure `-R 8888:0.0.0.0:8888` (must use `0.0.0.0`)
- Check Ubuntu's `/etc/ssh/sshd_config` has `GatewayPorts clientspecified`

**Frontend can't reach backend:**
- SSH forward tunnel not active
- Solution: Check tunnel is running with `ps aux | grep ssh`

## Verified Settings

These exact settings have been tested and confirmed working:

✅ Frontend container → Backend: `http://host.docker.internal:8000`  
✅ Backend container → Image server: `http://host.docker.internal:8888`  
✅ Browser → Frontend: `http://localhost:8501`  
✅ Browser → Image server: `http://localhost:8888`  

**Last verified:** After debugging session on Oct 9, 2025
**Status:** ✅ WORKING - Segmentation successful

