# 🚀 HPE NVIDIA Vista3D - Quick Start Guide

**Get up and running with our new three-script architecture!**

## Prerequisites

- **OS**: Ubuntu Linux (18.04+) or macOS
- **GPU**: NVIDIA GPU with CUDA support (8GB+ VRAM recommended)
- **Memory**: 16GB+ RAM
- **Docker**: Docker and NVIDIA Container Toolkit installed
- **NVIDIA NGC**: Account and API key (free at [ngc.nvidia.com](https://ngc.nvidia.com/))

## Step 1: Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd HPE-Nvidia-Vista-3D

# Run the unified setup script
python3 setup.py
```

**What the setup script does:**
- ✅ Checks system requirements (OS, Python, GPU, Docker)
- ✅ Sets up Python environment with all dependencies
- ✅ Configures environment variables and Docker settings
- ✅ Prompts for your NVIDIA NGC API key
- ✅ Creates all necessary directories and files

## Step 2: Start Vista3D Server (GPU-Enabled Machine)

```bash
# On your GPU-enabled machine (local or remote)
python3 start_vista3d.py
```

**This starts:**
- 🧠 **Vista3D AI Server** (http://localhost:8000)
- ⚡ **GPU-accelerated processing** for medical image segmentation
- 🔄 **Auto-restart capability** for production deployments

**Note**: The Vista3D server takes a few minutes to initialize and be ready for use.

## Step 3: Start Frontend Services

```bash
# On any machine (can be same as Vista3D or different)
python3 start_frontend.py
```

**This starts:**
- 🌐 **Streamlit Web Interface** (http://localhost:8501)
- 🖼️ **Image Server** (http://localhost:8888)

## Step 4: Process Your Images

```bash
# Add your medical images
# Option A: Place DICOM files in dicom/ folder
mkdir -p dicom/PA00000001
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

You now have a fully functional medical AI platform with distributed architecture.

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

### Vista3D Server Management
```bash
# Start Vista3D server
python3 start_vista3d.py

# Stop Vista3D server
docker stop vista3d

# View Vista3D logs
docker logs -f vista3d

# Restart Vista3D server
docker restart vista3d
```

### Frontend Services Management
```bash
# Start frontend services
python3 start_frontend.py

# Stop frontend services
docker compose down

# View frontend logs
docker compose logs -f

# View specific service logs
docker logs -f hpe-nvidia-vista3d-app
docker logs -f vista3d-image-server
```

### Systemd Service Management (Production)
```bash
# Create systemd services for auto-startup
sudo python3 start_vista3d.py --create-service
sudo python3 start_frontend.py --create-service

# Start services
sudo systemctl start vista3d
sudo systemctl start vista3d-gui

# Check service status
sudo systemctl status vista3d
sudo systemctl status vista3d-gui
```

## 🔍 Troubleshooting

### Vista3D Not Starting
```bash
# Check GPU availability
nvidia-smi

# Check Docker GPU support
docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu22.04 nvidia-smi

# Check Vista3D logs
docker logs -f vista3d
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
```

## 📚 Next Steps

1. **Explore the Web Interface**: Navigate to http://localhost:8501
2. **Upload Your Data**: Add DICOM or NIFTI files through the web interface
3. **Use the Tools Page**: Convert DICOM to NIFTI and run AI segmentation
4. **View Results**: Use the 3D viewer to analyze results
5. **Process Multiple Studies**: Use batch processing features in the GUI

## 🆘 Need Help?

- Check the full [README.md](README.md) for detailed documentation
- See the [docs/](docs/) directory for comprehensive guides
- Check the troubleshooting section above for common issues

---

**Ready to Go?** Follow the steps above and you'll be up and running in 15 minutes! 🚀
