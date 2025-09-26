# 🚀 HPE NVIDIA Vista3D - Quick Start Guide

**Get up and running in 3 simple steps!**

## Prerequisites

### For Backend Setup (Vista3D Server):
- **OS**: Ubuntu Linux (18.04+) or macOS
- **GPU**: NVIDIA GPU with CUDA support (8GB+ VRAM recommended)
- **Memory**: 16GB+ RAM
- **Docker**: Docker and NVIDIA Container Toolkit installed
- **NVIDIA NGC**: Account and API key (free at [ngc.nvidia.com](https://ngc.nvidia.com/))

### For Frontend Setup (Web Interface):
- **OS**: Ubuntu Linux (18.04+) or macOS
- **Memory**: 8GB+ RAM (minimum)
- **Docker**: Docker installed
- **NVIDIA NGC**: Not required (connects to remote Vista3D server)

## Step 1: Clone and Setup

```bash
# Clone the repository
gh repo clone dw-flyingw/HPE-Nvidia-Vista-3D
cd HPE-Nvidia-Vista-3D

# Run the master setup script
python3 setup.py
```

**Setup Options:**
```bash
# Setup everything (default)
python3 setup.py

# Setup only frontend (for non-GPU systems)
python3 setup.py --setup frontend

# Setup only backend (for GPU-enabled systems)
python3 setup.py --setup backend

# Check system requirements only
python3 setup.py --check-only

# Non-interactive setup with defaults
python3 setup.py --non-interactive

# Get help
python3 setup.py --help
```

**What the setup script does:**
- ✅ Checks system requirements (OS, Python, GPU, Docker)
- ✅ Prompts for your NVIDIA NGC API key (backend only)
- ✅ Configures directories and ports
- ✅ Sets up backend (Vista3D AI server) - if selected
- ✅ Sets up frontend (Web interface + Image server) - if selected
- ✅ Creates Docker configurations

## Step 2: Start All Services

```bash
# Start Vista3D AI Server (GPU-enabled machine)
cd backend
docker-compose up -d

# Start Frontend Services (any machine)
cd ../frontend
# Start image server first
cd ../image_server && docker-compose up -d
# Start frontend
cd ../frontend && docker-compose up -d
```

**This starts:**
- 🧠 **Vista3D AI Server** (http://localhost:8000)
- 🌐 **Streamlit Web Interface** (http://localhost:8501)
- 🖼️ **Image Server** (http://localhost:8888)

**Note**: The Vista3D server takes a few minutes to initialize and be ready for use.

## Step 3: Process Your Images

```bash
# Add your medical images
# Option A: Place DICOM files in dicom/ folder
# The dicom/ folder contains patient folders (e.g., PA00000001, PA00000002)
mkdir -p dicom
# Copy your DICOM files to dicom/PA00000001/

# Option B: Place NIFTI files directly
mkdir -p output/nifti
# Copy your .nii.gz files to output/nifti/

# Open your browser to http://localhost:8501
# Use the Tools page in the web interface to:
# - Convert DICOM to NIFTI
# - Run AI segmentation
# - View 3D visualizations
```

## 🎉 You're Done!

You now have a fully functional medical AI platform running!

## 🌐 Remote Server Setup

For remote Vista3D server deployments, you'll need to set up port forwarding:

### SSH Port Forwarding
```bash
# Forward local ports to remote Vista3D server
ssh user@remote_server -L 8000:localhost:8000 -R 8888:localhost:8888

# This forwards:
# - Local port 8000 → Remote Vista3D server port 8000
# - Remote port 8888 → Local image server port 8888
```

### Configuration for Remote Vista3D
```bash
# Edit .env file to point to remote server
VISTA3D_SERVER="http://localhost:8000"  # Uses SSH tunnel
IMAGE_SERVER="http://localhost:8888"    # Local image server
```

### Deployment Options
- **Same Machine**: Run both Vista3D and frontend on the same GPU-enabled machine
- **Remote Vista3D**: Run Vista3D on remote GPU server, frontend locally
- **Distributed**: Run Vista3D and frontend on different machines with proper networking

## 🛠️ Using the Tools Page

The web interface includes a powerful **Tools page** where you can:

- **Convert DICOM to NIFTI**: Upload DICOM files and convert them to NIFTI format
- **Run AI Segmentation**: Process NIFTI files with the Vista3D AI model
- **View 3D Visualizations**: Interactive 3D medical viewer with multi-planar views
- **Batch Processing**: Process multiple patients and studies at once
- **Download Results**: Export segmentation results and 3D models

**Access the Tools page**: Navigate to http://localhost:8501 and click on the "Tools" tab in the sidebar.

## 🔧 Management Commands

### Individual Service Management

#### Backend (Vista3D AI Server)
```bash
cd backend
docker-compose up -d    # Start Vista3D server
docker-compose down     # Stop Vista3D server
docker-compose logs -f  # View logs
```

#### Frontend (Web Interface + Image Server)
```bash
# Start services
cd frontend
# Start image server first
cd ../image_server && docker-compose up -d
# Start frontend
cd ../frontend && docker-compose up -d

# Stop services
cd frontend && docker-compose down && cd ../image_server && docker-compose down

# View logs
cd frontend && docker-compose logs -f
cd image_server && docker-compose logs -f
```

## 🔍 Troubleshooting

### Services Not Starting
```bash
# Check Docker is running
docker info

# Check GPU availability
nvidia-smi

# Check specific service logs
cd backend && docker logs -f vista3d-server-standalone
cd frontend && docker logs -f vista3d-frontend-standalone
cd image_server && docker logs -f vista3d-image-server-standalone
```

### Permission Issues
```bash
# Fix file permissions
sudo chown -R $USER:$USER output/
sudo chmod -R 755 output/
```

### Port Already in Use
```bash
# Check what's using the ports
lsof -i :8501
lsof -i :8888
lsof -i :8000

# Stop conflicting services
sudo systemctl stop conflicting-service
```

## 📚 Next Steps

1. **Explore the Web Interface**: Navigate to http://localhost:8501
2. **Upload Your Data**: Add DICOM or NIFTI files through the web interface
3. **Use the Tools Page**: Convert DICOM to NIFTI and run AI segmentation
4. **View Results**: Use the 3D viewer to analyze results
5. **Process Multiple Studies**: Use batch processing features in the GUI

## 🆘 Need Help?

- Check the full [README.md](README.md) for detailed documentation
- See the [docs/SETUP_OPTIONS.md](docs/SETUP_OPTIONS.md) for setup scenarios and options
- See the [docs/SETUP_SCRIPTS.md](docs/SETUP_SCRIPTS.md) for comprehensive setup guide
- Check the troubleshooting section above for common issues

---

**Ready to Go?** Follow the 3 steps above and you'll be up and running in 10 minutes! 🚀
