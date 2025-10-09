# Setup Script Fixes - Summary

## Issues Fixed

### 1. ✅ Docker Networking for Remote Vista3D (SSH Tunnel Setup)
**Problem:** Vista3D running on remote Ubuntu server couldn't access image server via SSH reverse tunnel

**Solution:**
- Added `extra_hosts: - "host.docker.internal:host-gateway"` to `backend/docker-compose.yml`
- This enables Vista3D on Linux to resolve `host.docker.internal` to the host machine
- Works with SSH reverse tunnel: `-R 8888:localhost:8888`

**Files Changed:**
- `backend/docker-compose.yml` - Added extra_hosts configuration
- `frontend/docker-compose.yml` - Set default VISTA3D_IMAGE_SERVER_URL to host.docker.internal
- `frontend/setup_frontend.py` - Generate correct VISTA3D_IMAGE_SERVER_URL
- `setup.py` - Generate correct VISTA3D_IMAGE_SERVER_URL

### 2. ✅ Missing IMAGE_SERVER_PORT Configuration
**Problem:** Backend-only setup crashed with KeyError: 'IMAGE_SERVER_PORT'

**Solution:**
- Added `IMAGE_SERVER_PORT` to all config dictionaries in setup.py
- Added IMAGE_SERVER_PORT to .env file template

**Files Changed:**
- `setup.py` - Added IMAGE_SERVER_PORT = "8888" in all config functions

### 3. ✅ Setup Script Reads Existing .env File
**Problem:** Setup script always prompted for NGC API key even when .env existed with valid credentials

**Solution:**
- Modified `get_user_input()` to check for existing `.env` file
- Automatically loads NGC_API_KEY and NGC_ORG_ID if they exist and are valid
- Loads all other configuration values from existing .env
- Only prompts user if values are missing or invalid

**Files Changed:**
- `setup.py` - Enhanced get_user_input() to read existing .env

**Behavior:**
```bash
# If .env exists with NGC_API_KEY='nvapi-...' and NGC_ORG_ID='...'
✅ Found existing .env file
✅ Loaded existing configuration from .env file
✅ Using existing NGC API Key from .env: nvapi-AX__kVWL...
✅ Using existing NGC Org ID from .env: 0509588398571510

# Setup continues without prompting for these values
```

## New Documentation Files

### 1. `REMOTE_SERVER_SETUP.md`
Instructions for setting up the Ubuntu backend server after git pull:
- How to restart Vista3D with updated docker-compose.yml
- How to verify the configuration
- Troubleshooting steps for SSH tunnel setup

### 2. `NVIDIA_DOCKER_TROUBLESHOOTING.md`
Complete troubleshooting guide for NVIDIA Docker Toolkit issues:
- Docker 28.x configuration for NVIDIA runtime
- Common fixes for exit code 125 errors
- Step-by-step verification commands

## Network Flow (Remote Setup)

```
┌─────────────────────────────────────────────────────────────────┐
│                         Your Mac                                │
│                                                                 │
│  Frontend Container ──────────────────────────────────────────┐ │
│       │                                                        │ │
│       │ HTTP requests                                          │ │
│       ▼                                                        │ │
│  Image Server (localhost:8888) ◄──────────────────────────┐   │ │
│       │                                                    │   │ │
└───────┼────────────────────────────────────────────────────┼───┘ │
        │                                                    │     │
        │ SSH Forward Tunnel                                 │     │
        │ -L 8000:localhost:8000                             │     │
        │                                                    │     │
        ▼                                                    │     │
┌─────────────────────────────────────────────────────────────────┐ │
│                      Ubuntu Server                              │ │
│                                                                 │ │
│  Vista3D Container                                              │ │
│       │                                                         │ │
│       │ Fetches images via                                     │ │
│       │ http://host.docker.internal:8888 ────────────┐         │ │
│       │                                              │         │ │
│       │                                              ▼         │ │
│  Ubuntu Host (localhost:8888) ◄─────────── SSH Reverse Tunnel  │ │
│                                             -R 8888:localhost:8888 │
└─────────────────────────────────────────────────────────────────┘ │
                                                                    │
        SSH Reverse Tunnel (returns to Mac) ───────────────────────┘
```

## How to Apply on Ubuntu Server

```bash
# On Ubuntu server
cd ~/HPE-Nvidia-Vista-3D
git pull

# Fix NVIDIA Docker if needed (for Docker 28.x)
sudo nvidia-ctk runtime configure --runtime=docker --set-as-default
sudo systemctl restart docker

# Run setup (will use existing NGC credentials from .env)
python3 setup.py
# Choose option 2 (Backend Only)

# Start Vista3D
cd backend
docker compose up -d

# Verify
docker compose ps
docker exec vista3d-server-standalone curl http://host.docker.internal:8888
```

## Testing the Fix

From your Mac frontend, run a segmentation. You should now see:
```
Vista3D Server: http://host.docker.internal:8000
Image URL (Vista3D-accessible): http://host.docker.internal:8888/output/.../file.nii.gz
✅ Segmentation successful
```

## Files Ready for Git Push

Modified files:
- `setup.py` - All three fixes applied
- `backend/docker-compose.yml` - extra_hosts for Linux
- `frontend/docker-compose.yml` - Updated default VISTA3D_IMAGE_SERVER_URL
- `frontend/setup_frontend.py` - Generate correct URL
- `docs/IMAGE_SERVER.md` - Docker networking documentation
- `docs/SETUP_GUIDE.md` - Troubleshooting section added

New files:
- `REMOTE_SERVER_SETUP.md` - Remote server instructions
- `NVIDIA_DOCKER_TROUBLESHOOTING.md` - NVIDIA Docker fixes
- `SETUP_FIXES_SUMMARY.md` - This file

