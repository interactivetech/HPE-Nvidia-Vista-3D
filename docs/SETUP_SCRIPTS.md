# HPE NVIDIA Vista3D Setup Scripts

This document describes the setup scripts available for the HPE NVIDIA Vista3D platform.

## Overview

The platform now includes three setup scripts to make installation and configuration easier:

1. **`setup.py`** - Master setup script (recommended)
2. **`backend/setup_backend.py`** - Backend-only setup
3. **`frontend/setup_frontend.py`** - Frontend-only setup

## Master Setup Script (`setup.py`)

The master setup script provides a unified experience for setting up the entire platform.

### Features
- ✅ System requirements validation
- ✅ NVIDIA NGC API key configuration
- ✅ Directory structure creation
- ✅ Environment configuration
- ✅ Backend setup (Vista3D server)
- ✅ Frontend setup (Web interface)
- ✅ Master management scripts creation

### Usage
```bash
# Clone the repository
git clone <repository-url>
cd HPE-Nvidia-Vista-3D

# Run the master setup
python3 setup.py
```

### What it does
1. Checks system requirements (OS, Python, Docker, GPU, memory, disk space)
2. Prompts for configuration (NVIDIA API key, directories, ports)
3. Creates necessary directories
4. Generates `.env` files for all services
5. Runs backend setup script
6. Runs frontend setup script
7. Creates master management scripts

### Generated Scripts
- `start_all.sh` - Start all services
- `stop_all.sh` - Stop all services
- `status.sh` - Check service status

## Backend Setup Script (`backend/setup_backend.py`)

Sets up the Vista3D backend service (AI server).

### Features
- ✅ System requirements validation
- ✅ NVIDIA NGC API key configuration
- ✅ Docker and NVIDIA Container Toolkit verification
- ✅ Environment configuration
- ✅ Directory structure creation
- ✅ Docker image pulling
- ✅ Startup script creation

### Usage
```bash
cd backend
python3 setup_backend.py
```

### What it does
1. Validates system requirements
2. Prompts for NVIDIA NGC API key and configuration
3. Creates data directories
4. Generates `.env` file
5. Pulls Vista3D Docker image
6. Creates `start_backend.sh` script

## Frontend Setup Script (`frontend/setup_frontend.py`)

Sets up the frontend services (Web interface and image server).

### Features
- ✅ System requirements validation
- ✅ Docker verification
- ✅ Environment configuration
- ✅ Directory structure creation
- ✅ Image server setup and configuration
- ✅ Docker image building
- ✅ Management scripts creation

### Usage
```bash
cd frontend
python3 setup_frontend.py
```

### What it does
1. Validates system requirements
2. Prompts for configuration (directories, ports)
3. Creates data directories
4. Generates `.env` file
5. Sets up image server configuration
6. Builds Docker images
7. Provides Docker commands for service management

## System Requirements

### Critical Requirements
- **OS**: Ubuntu Linux (18.04+) or macOS
- **Python**: 3.8+
- **Docker**: Latest version with Docker Compose

### Optional Requirements (for full functionality)
- **NVIDIA GPU**: 8GB+ VRAM recommended
- **Memory**: 16GB+ RAM recommended
- **Disk Space**: 10GB+ free space
- **NVIDIA Container Toolkit**: For GPU acceleration

## Configuration

### Environment Variables
The setup scripts create `.env` files with the following configuration:

```bash
# NVIDIA NGC Configuration
NGC_API_KEY="nvapi-your-api-key"
NGC_ORG_ID="your-org-id"

# Data Directories
DICOM_FOLDER="/path/to/dicom"
OUTPUT_FOLDER="/path/to/output"

# Server URLs
VISTA3D_SERVER="http://localhost:8000"
IMAGE_SERVER="http://localhost:8888"

# Ports
FRONTEND_PORT="8501"

# Segmentation Settings
VESSELS_OF_INTEREST="all"
```

## Quick Start

### Option 1: Master Setup (Recommended)
```bash
# Clone and setup everything
git clone <repository-url>
cd HPE-Nvidia-Vista-3D
python3 setup.py

# Start all services
./start_all.sh

# Open web interface
open http://localhost:8501
```

### Option 2: Individual Setup
```bash
# Setup backend
cd backend
python3 setup_backend.py
./start_backend.sh

# Setup frontend (in another terminal)
cd frontend
python3 setup_frontend.py
# Start image server first
cd ../image_server && docker-compose up -d
# Start frontend
cd ../frontend && docker-compose up -d
```

## Management Commands

### Master Scripts
```bash
./start_all.sh    # Start all services
./stop_all.sh     # Stop all services
./status.sh       # Check service status
```

### Backend Scripts
```bash
cd backend
./start_backend.sh    # Start Vista3D server
docker-compose up -d  # Alternative start method
docker-compose down   # Stop Vista3D server
```

### Frontend Commands
```bash
cd frontend
# Start image server first
cd ../image_server && docker-compose up -d
# Start frontend
cd ../frontend && docker-compose up -d

# Stop services
docker-compose down && cd ../image_server && docker-compose down

# View logs
docker-compose logs -f
```

## Troubleshooting

### Common Issues

#### Setup Scripts Not Found
```bash
# Make sure you're in the right directory
ls -la setup.py
ls -la backend/setup_backend.py
ls -la frontend/setup_frontend.py
```

#### Permission Denied
```bash
# Make scripts executable
chmod +x *.sh
chmod +x backend/*.sh
chmod +x frontend/*.sh
```

#### Docker Not Running
```bash
# Start Docker daemon
sudo systemctl start docker  # Linux
# or start Docker Desktop on macOS
```

#### NVIDIA Container Toolkit Issues
```bash
# Test NVIDIA Docker support
docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu22.04 nvidia-smi
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

### Getting Help

1. **Check logs**: Use the generated log scripts or `docker logs`
2. **Verify requirements**: Run the setup scripts again to check system requirements
3. **Check configuration**: Verify `.env` files are correctly configured
4. **Test individual services**: Start services one by one to isolate issues

## Advanced Usage

### Custom Configuration
Edit the `.env` files after setup to customize:
- Server URLs
- Port numbers
- Directory paths
- Segmentation settings

### Remote Deployment
For remote Vista3D server deployments:
1. Set up SSH port forwarding
2. Update `VISTA3D_SERVER` in `.env` files
3. Run only frontend setup

### Development Mode
For development work:
1. Use individual setup scripts
2. Modify Docker Compose files as needed
3. Use `docker-compose up` for live development

## Next Steps

After successful setup:
1. **Upload Data**: Place DICOM or NIFTI files in the configured directories
2. **Use Web Interface**: Navigate to http://localhost:8501
3. **Process Images**: Use the Tools page for image processing
4. **View Results**: Use the 3D viewer for visualization

---

**Need Help?** Check the troubleshooting section or refer to the main README.md for detailed documentation.
