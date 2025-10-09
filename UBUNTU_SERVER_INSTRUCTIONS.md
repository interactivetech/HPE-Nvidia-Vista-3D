# Ubuntu Server Setup - Quick Reference

## What You Need to Do on Your Ubuntu Server

### Step 1: Pull Latest Code
```bash
cd ~/HPE-Nvidia-Vista-3D
git pull
```

### Step 2: Test GPU with Correct CUDA Image
```bash
# Test NVIDIA Docker (now using correct image tag)
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

**Expected Output:**
```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 535.xx.xx    Driver Version: 535.xx.xx    CUDA Version: 12.x   |
|-------------------------------+----------------------+----------------------+
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
...
```

### Step 3: Run Setup Script
```bash
python3 setup.py
# Choose option 2 (Backend Only)
```

**The script will now:**
- ✅ Read NGC_API_KEY from existing .env file (no prompt needed!)
- ✅ Read NGC_ORG_ID from existing .env file (no prompt needed!)
- ✅ Use the correct CUDA image tag for GPU testing
- ✅ Create backend configuration with Docker networking fix

### Step 4: Start Vista3D
```bash
cd backend
docker compose up -d
```

### Step 5: Verify It's Running
```bash
# Check container status
docker compose ps

# Check logs
docker compose logs -f vista3d-server

# Test GPU inside container
docker exec vista3d-server-standalone nvidia-smi

# Test API
curl http://localhost:8000/v1/vista3d/info
```

### Step 6: Test from Your Mac
From your Mac frontend (http://localhost:8501), run a segmentation on patient PA00000050.

**Expected output:**
```
Vista3D Server: http://host.docker.internal:8000
Image URL (Vista3D-accessible): http://host.docker.internal:8888/output/PA00000050/nifti/...
✅ Segmentation successful
```

## Troubleshooting

### If GPU Test Fails
See `NVIDIA_DOCKER_TROUBLESHOOTING.md` for detailed troubleshooting steps.

### If Setup Script Doesn't Find NGC Credentials
Check your .env file:
```bash
cat .env | grep NGC
```

Should show:
```
NGC_API_KEY='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'
NGC_ORG_ID='0509588398571510'
```

### If Vista3D Can't Access Image Server
The updated `backend/docker-compose.yml` includes:
```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

This allows Vista3D on Linux to resolve `host.docker.internal` to reach your Mac's image server via the SSH reverse tunnel.

## What Got Fixed

1. **Docker Networking** - Vista3D can now access image server via SSH tunnel
2. **CUDA Image Tag** - Fixed invalid tag (11.8 → 11.8.0)
3. **NGC Credentials** - Setup script reads from existing .env
4. **Missing Config** - Added IMAGE_SERVER_PORT to prevent KeyError

## Your Current Network Setup

```
Mac (localhost:8888) ◄──── SSH Reverse Tunnel ───┐
         ▲                                        │
         │                                        │
    [Frontend uses]                               │
         │                                        │
         │                             Ubuntu Host (localhost:8888)
         │                                        │
         │                                        ▼
         └──── SSH Forward Tunnel ──── Vista3D Container
              (8000:8000)               (uses host.docker.internal:8888)
```

All traffic flows through your SSH tunnels:
- `-L 8000:localhost:8000` (Vista3D API from Ubuntu to Mac)
- `-R 8888:localhost:8888` (Image Server from Mac to Ubuntu)

