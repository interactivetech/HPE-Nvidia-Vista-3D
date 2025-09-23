# 🚀 Deployment Modes Guide

This guide explains the different ways to deploy the HPE NVIDIA Vista3D Medical AI Platform.

## 📋 Overview

The platform consists of three main components:
- **Streamlit App** (Port 8501) - Web interface for medical imaging
- **Image Server** (Port 8888) - HTTP server for medical image files
- **Vista3D Server** (Port 8000) - AI segmentation service (requires GPU)

## 🎯 Deployment Modes

### Mode 0: Vista3D Server Only

**Best for**: Running Vista3D server as a standalone service, distributed deployments, GPU server farms

**Architecture**:
```
┌─────────────────┐
│  Vista3D Server │
│  (Port 8000)    │
│  Docker/Remote  │
└─────────────────┘
```

**Setup**:
```bash
# 1. Configure environment
cp dot_env_template .env
nano .env  # Set NGC_API_KEY and other required variables

# 2. Start Vista3D server only
docker compose --profile local-vista3d up vista3d-server
```

**Access Points**:
- Vista3D Server: http://localhost:8000
- Health Check: http://localhost:8000/health

**Use Cases**:
- GPU server running only Vista3D
- Frontend running on separate machines
- Load balancing multiple Vista3D instances
- Testing Vista3D server independently

## 🎯 Full Deployment Modes

### Mode 1: Single GPU Host (Recommended)

**Best for**: Single-user deployments, development, testing, local processing

**Architecture**:
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │  Image Server   │    │  Vista3D Server │
│   (Port 8501)   │◄──►│  (Port 8888)    │◄──►│  (Port 8000)    │
│   Local Docker  │    │  Local Docker   │    │  Local Docker   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

**Setup**:
```bash
# 1. Clone and setup
git clone <repository-url>
cd HPE-Nvidia-Vista-3D
python3 setup.py

# 2. Start all services
python3 start.py
```

**Access Points**:
- Streamlit App: http://localhost:8501
- Image Server: http://localhost:8888
- Vista3D Server: http://localhost:8000

### Mode 2: Local GUI + Remote Vista3D

**Best for**: Production deployments, shared GPU resources, cloud-based Vista3D

**Architecture**:
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │  Image Server   │    │  Vista3D Server │
│   (Port 8501)   │◄──►│  (Port 8888)    │◄──►│  (Remote GPU)   │
│   Local Docker  │    │  Local Docker   │    │  Remote Server  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

**Setup**:
```bash
# 1. Setup frontend only
git clone <repository-url>
cd HPE-Nvidia-Vista-3D
python3 setup.py

# 2. Edit .env file for remote Vista3D
VISTA3D_SERVER=https://your-vista3d-server.com:8000
VISTA3D_API_KEY=your_nvidia_api_key_here

# 3. Start frontend services only (choose one method)
# Method A: Using Docker Compose (recommended)
docker compose up vista3d-app image-server

# Method B: Using start script
python3 start.py --frontend-only
```

**Access Points**:
- Streamlit App: http://localhost:8501
- Image Server: http://localhost:8888
- Vista3D Server: https://your-vista3d-server.com:8000 (remote)

### Mode 3: Production with Auto-Startup

**Best for**: Production servers with automatic startup on boot

**Setup**:
```bash
# 1. Create systemd services for automatic startup
sudo python3 utils/start_vista3d.py --create-service
sudo python3 utils/start_gui.py --create-service

# 2. Enable services
sudo systemctl enable vista3d
sudo systemctl enable vista3d-gui

# 3. Start services
sudo systemctl start vista3d
sudo systemctl start vista3d-gui

# 4. Check status
sudo systemctl status vista3d
sudo systemctl status vista3d-gui
```

**Service Management**:
```bash
# Start services
sudo systemctl start vista3d
sudo systemctl start vista3d-gui

# Stop services
sudo systemctl stop vista3d
sudo systemctl stop vista3d-gui

# Restart services
sudo systemctl restart vista3d
sudo systemctl restart vista3d-gui

# View logs
sudo journalctl -u vista3d -f
sudo journalctl -u vista3d-gui -f
```

## 🔧 Configuration Details

### Environment Variables

| Variable | Mode 1 (Remote) | Mode 2 (Local) | Description |
|----------|----------------|----------------|-------------|
| `VISTA3D_SERVER` | `https://remote-server:8000` | `http://vista3d-server:8000` | Vista3D server URL |
| `VISTA3D_API_KEY` | `your_api_key` | `your_api_key` | NVIDIA API key |
| `IMAGE_SERVER` | `http://image-server:8888` | `http://image-server:8888` | Internal image server URL |
| `EXTERNAL_IMAGE_SERVER` | `http://localhost:8888` | `http://localhost:8888` | External image server URL |

### Port Requirements

| Port | Service | Mode 0 | Mode 1 | Mode 2 | Description |
|------|---------|--------|--------|--------|-------------|
| 8501 | Streamlit App | ❌ | ✅ | ✅ | Web interface |
| 8888 | Image Server | ❌ | ✅ | ✅ | Medical image files |
| 8000 | Vista3D Server | ✅ | ❌ (Remote) | ✅ | AI segmentation |

### Network Requirements

**Mode 0 (Vista3D Only)**:
- Local port 8000
- NVIDIA GPU with CUDA support
- No frontend services

**Mode 1 (Remote Vista3D)**:
- Outbound HTTPS to remote Vista3D server
- Local ports 8501, 8888

**Mode 2 (Local Vista3D)**:
- Local ports 8501, 8888, 8000
- NVIDIA GPU with CUDA support

## 🚀 Quick Start Commands

### Mode 0: Vista3D Server Only
```bash
# Start Vista3D server only
docker compose --profile local-vista3d up vista3d-server
```

### Mode 1: Remote Vista3D
```bash
# Method A: Using Docker Compose (recommended)
docker compose up vista3d-app image-server

# Method B: Using start script
VISTA3D_SERVER=https://your-server:8000 VISTA3D_API_KEY=your_key python3 start.py --frontend-only
```

### Mode 2: Local Vista3D
```bash
# Terminal 1: Start Vista3D (choose one method)
# Method A: Using Docker Compose (recommended)
docker compose --profile local-vista3d up vista3d-server

# Method B: Using Python script
python3 utils/start_vista3d.py

# Terminal 2: Start GUI
python3 utils/start_gui.py
```

### Mode 3: Production
```bash
# Create services
sudo python3 utils/start_vista3d.py --create-service
sudo python3 utils/start_gui.py --create-service

# Start everything
sudo systemctl start vista3d vista3d-gui
```

## 🔧 Running Utility Scripts

**Important**: When using Docker containers, utility scripts must be run from the **host system**, not from within the containers.

### Prerequisites
```bash
# Activate virtual environment on host
source .venv/bin/activate

# Ensure you have the required dependencies
uv sync
```

### DICOM to NIFTI Conversion
```bash
# Run from host system (not inside Docker container)
python3 utils/dicom2nifti.py
```

### NIFTI to PLY Conversion
```bash
# Single file conversion
python3 utils/nifti2ply.py input.nii.gz output.ply

# Batch processing of all voxels folders
python3 utils/nifti2ply.py --batch

# Batch processing for specific patient
python3 utils/nifti2ply.py --batch --patient PA00000002
```

### Segmentation Processing
```bash
# Run segmentation (connects to Vista3D server)
python3 utils/segment.py
```

### Complete Workflow Example
```bash
# 1. Start containers
python3 utils/start_gui.py

# 2. Convert DICOM to NIFTI (from host)
python3 utils/dicom2nifti.py

# 3. Run segmentation (from host)
python3 utils/segment.py

# 4. Convert to PLY files (from host)
python3 utils/nifti2ply.py --batch

# 5. Access web interface
# Open http://localhost:8501 in browser
```

## 🔍 Troubleshooting

### Common Issues

#### Vista3D Connection Failed
```bash
# Check Vista3D server connectivity
curl -v $VISTA3D_SERVER/health

# For local Vista3D
curl -v http://localhost:8000/health

# Check API key
echo $VISTA3D_API_KEY
```

#### Port Already in Use
```bash
# Check what's using the ports
lsof -i :8501
lsof -i :8888
lsof -i :8000

# Stop conflicting services
sudo systemctl stop conflicting-service
```

#### GPU Not Available (Mode 2)
```bash
# Check GPU availability
nvidia-smi

# Check Docker GPU support
docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu22.04 nvidia-smi
```

### Debugging Commands

```bash
# Check container status
docker ps

# View logs
docker logs hpe-nvidia-vista3d-app
docker logs vista3d-image-server
docker logs vista3d

# Check network connectivity
docker exec -it hpe-nvidia-vista3d-app ping image-server
docker exec -it hpe-nvidia-vista3d-app curl http://image-server:8888/health
```

## 📊 Performance Considerations

### Mode 1 (Remote Vista3D)
- **Pros**: No local GPU required, shared resources, scalable
- **Cons**: Network latency, requires stable connection
- **Best for**: Production, multiple users, cloud deployments

### Mode 2 (Local Vista3D)
- **Pros**: Low latency, no network dependency, full control
- **Cons**: Requires GPU, single machine only
- **Best for**: Development, testing, single-user deployments

### Resource Requirements

| Component | CPU | RAM | GPU | Storage |
|-----------|-----|-----|-----|---------|
| Streamlit App | 2 cores | 2GB | - | 1GB |
| Image Server | 1 core | 1GB | - | 1GB |
| Vista3D Server | 4 cores | 8GB | 8GB VRAM | 10GB |

## 🔒 Security Considerations

### Mode 1 (Remote Vista3D)
- Use HTTPS for Vista3D connections
- Secure API key storage
- Network firewall configuration

### Mode 2 (Local Vista3D)
- Local network only
- GPU resource isolation
- Container security

### General Security
- Never commit `.env` files
- Use strong API keys
- Regular security updates
- Monitor access logs

## 📚 Additional Resources

- [CONTAINERIZATION.md](CONTAINERIZATION.md) - Detailed Docker setup
- [SETUP_GUIDE.md](SETUP_GUIDE.md) - Complete installation guide
- [README.md](../README.md) - Project overview
- [Troubleshooting Guide](TROUBLESHOOTING.md) - Common issues and solutions

---

**Need Help?** Check the troubleshooting section or refer to the full documentation.

**Ready to Deploy?** Choose your mode and follow the setup instructions above! 🚀
