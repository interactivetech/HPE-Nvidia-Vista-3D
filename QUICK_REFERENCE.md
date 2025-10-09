# Vista3D Quick Reference

## One-Time Setup

### Backend (Ubuntu Server)
```bash
cd backend
python3 setup.py
```

### Frontend (Mac)
```bash
cd frontend
python3 setup.py
```

## Daily Usage

### Step 1: Start Backend (on Ubuntu Server)
```bash
cd backend
docker compose up -d
```

### Step 2: SSH Tunnel (from Mac)
```bash
ssh -L 8000:localhost:8000 -R 8888:0.0.0.0:8888 user@ubuntu-server
```
*Keep this terminal open!*

### Step 3: Start Frontend (on Mac)
```bash
cd frontend
docker compose up -d
```

### Step 4: Open Browser
```
http://localhost:8501
```

## Stop Services

### Mac:
```bash
cd frontend
docker compose down
```
*Then close SSH tunnel (Ctrl+C)*

### Ubuntu Server:
```bash
cd backend
docker compose down
```

## Quick Diagnostics

```bash
# Check running containers
docker ps

# View logs
docker compose logs -f

# Test backend API (from Mac)
curl http://localhost:8000/docs

# Check SSH tunnel
netstat -an | grep 8000
netstat -an | grep 8888
```

## Ports

| Service | Port | Location |
|---------|------|----------|
| Frontend | 8501 | Mac |
| Image Server | 8888 | Mac |
| Vista3D API | 8000 | Ubuntu (via tunnel) |

## Default Locations

| Item | Path |
|------|------|
| DICOM files | `../dicom` |
| Output files | `../output` |
| Frontend config | `frontend/.env` |
| Backend config | `backend/.env` |

