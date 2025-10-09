# HPE NVIDIA Vista3D Setup Guide

This guide provides a simplified setup process for the HPE NVIDIA Vista3D platform.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Your Mac                                 │
│  ┌────────────────┐          ┌────────────────┐             │
│  │    Frontend    │          │  Image Server  │             │
│  │  (localhost:   │◄─────────┤  (localhost:   │             │
│  │      8501)     │          │      8888)     │             │
│  └────────┬───────┘          └────────────────┘             │
│           │                                                   │
│           │ SSH Tunnel: -L 8000:localhost:8000               │
│           │             -R 8888:0.0.0.0:8888                 │
└───────────┼───────────────────────────────────────────────────┘
            │
            │ Internet
            │
┌───────────┼───────────────────────────────────────────────────┐
│           ▼         Remote Ubuntu Server                      │
│  ┌────────────────┐                                           │
│  │  Vista3D API   │                                           │
│  │  (localhost:   │                                           │
│  │      8000)     │                                           │
│  └────────────────┘                                           │
│     Requires: NVIDIA GPU                                      │
└───────────────────────────────────────────────────────────────┘
```

## Prerequisites

### Mac (Frontend & Image Server)
- Docker Desktop installed
- Python 3.8+ (for running setup script)
- SSH access to remote Ubuntu server

### Ubuntu Server (Backend)
- Ubuntu Linux (18.04+)
- NVIDIA GPU
- Docker with NVIDIA Container Toolkit
- Python 3.8+ (for running setup script)
- NVIDIA NGC API key ([Get free key](https://ngc.nvidia.com/))

## Setup Instructions

### Part 1: Setup Backend (on Ubuntu Server)

1. **SSH into your Ubuntu server:**
   ```bash
   ssh user@your-ubuntu-server
   ```

2. **Navigate to the backend directory:**
   ```bash
   cd /path/to/HPE-Nvidia-Vista-3D/backend
   ```

3. **Run the setup script:**
   ```bash
   python3 setup.py
   ```
   
   This will:
   - Check system requirements (Docker, NVIDIA GPU, NVIDIA Container Toolkit)
   - Ask for your NVIDIA NGC API key
   - Create necessary directories
   - Create `.env` configuration file
   - Pull the Vista3D Docker image (~30GB)

4. **Start the backend:**
   ```bash
   docker compose up
   ```
   
   The Vista3D API will be available at `http://localhost:8000`

   To run in background: `docker compose up -d`

### Part 2: Setup Frontend (on Your Mac)

1. **Navigate to the frontend directory:**
   ```bash
   cd /path/to/HPE-Nvidia-Vista-3D/frontend
   ```

2. **Run the setup script:**
   ```bash
   python3 setup.py
   ```
   
   This will:
   - Check Docker installation
   - Create necessary directories
   - Create `.env` configuration file
   - Pull Docker images for frontend and image server

### Part 3: Connect Everything

1. **Create SSH tunnel from your Mac to the Ubuntu server:**
   
   Open a terminal on your Mac and run:
   ```bash
   ssh -L 8000:localhost:8000 -R 8888:0.0.0.0:8888 user@your-ubuntu-server
   ```
   
   **What this does:**
   - `-L 8000:localhost:8000` - Forward tunnel: Your Mac can access Vista3D backend at `localhost:8000`
   - `-R 8888:0.0.0.0:8888` - Reverse tunnel: Ubuntu server can access your Mac's image server at `localhost:8888`
   
   **Keep this terminal open while using Vista3D!**

2. **Start the frontend and image server (on your Mac):**
   
   Open a new terminal and run:
   ```bash
   cd /path/to/HPE-Nvidia-Vista-3D/frontend
   docker compose up
   ```
   
   This starts both the frontend and image server together.

3. **Access the web interface:**
   
   Open your browser to: **http://localhost:8501**

## Daily Usage

Once setup is complete, follow these steps each time you want to use Vista3D:

### On Ubuntu Server:
```bash
cd /path/to/HPE-Nvidia-Vista-3D/backend
docker compose up -d  # -d runs in background
```

### On Your Mac:

**Terminal 1 - SSH Tunnel:**
```bash
ssh -L 8000:localhost:8000 -R 8888:0.0.0.0:8888 user@your-ubuntu-server
```

**Terminal 2 - Frontend & Image Server:**
```bash
cd /path/to/HPE-Nvidia-Vista-3D/frontend
docker compose up -d  # -d runs in background
```

**Browser:**
Open http://localhost:8501

## Stopping Services

### On Your Mac:
```bash
cd /path/to/HPE-Nvidia-Vista-3D/frontend
docker compose down
```

### On Ubuntu Server:
```bash
cd /path/to/HPE-Nvidia-Vista-3D/backend
docker compose down
```

### Close SSH Tunnel:
Press `Ctrl+C` in the SSH tunnel terminal

## Checking Status

### View running containers:
```bash
docker ps
```

### View logs:
```bash
# Frontend logs
cd frontend && docker compose logs -f

# Backend logs
cd backend && docker compose logs -f
```

## Configuration Files

After running the setup scripts, you'll have:

### Frontend: `frontend/.env`
```bash
DICOM_FOLDER=/path/to/dicom
OUTPUT_FOLDER=/path/to/output
VISTA3D_SERVER=http://localhost:8000
IMAGE_SERVER=http://localhost:8888
FRONTEND_PORT=8501
IMAGE_SERVER_PORT=8888
```

### Backend: `backend/.env`
```bash
NGC_API_KEY=nvapi-xxxxx
OUTPUT_FOLDER=/path/to/output
VISTA3D_SERVER=http://localhost:8000
IMAGE_SERVER=http://localhost:8888
```

## Troubleshooting

### Backend won't start
1. Check NVIDIA GPU: `nvidia-smi`
2. Check NVIDIA Docker: `docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi`
3. Check logs: `cd backend && docker compose logs`

### Frontend can't connect to backend
1. Ensure SSH tunnel is active and running
2. Test backend from Mac: `curl http://localhost:8000/docs`
3. Check firewall settings on Ubuntu server

### Image server errors
1. Check that DICOM and output folders exist
2. Check folder permissions
3. Check logs: `cd frontend && docker compose logs image-server`

### SSH tunnel issues
1. Ensure port 8000 and 8888 are not already in use
2. Check SSH connection: `ssh user@your-ubuntu-server`
3. Check SSH server config allows port forwarding

## Advanced Configuration

### Using Different Ports

Edit the `.env` files in frontend and backend directories to change ports:

**Frontend `.env`:**
```bash
FRONTEND_PORT=9000        # Change frontend port
IMAGE_SERVER_PORT=9001    # Change image server port
```

**Backend `.env`:**
```bash
# Backend port is defined in docker-compose.yml
```

After changing ports, update your SSH tunnel command accordingly:
```bash
ssh -L [NEW_BACKEND_PORT]:localhost:8000 -R [NEW_IMAGE_SERVER_PORT]:0.0.0.0:[NEW_IMAGE_SERVER_PORT] user@server
```

### Using Different Data Folders

Edit the `.env` files to point to your preferred directories:

```bash
DICOM_FOLDER=/path/to/your/dicom/folder
OUTPUT_FOLDER=/path/to/your/output/folder
```

## Additional Resources

- [Backend Setup Guide](docs/BACKEND_GUIDE.md)
- [Frontend Setup Guide](docs/SETUP_GUIDE.md)
- [SSH Tunnel Guide](docs/SSH_TUNNEL_GUIDE.md)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [NVIDIA NGC Documentation](https://docs.nvidia.com/ngc/)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review logs using `docker compose logs`
3. Consult the documentation in the `docs/` directory

