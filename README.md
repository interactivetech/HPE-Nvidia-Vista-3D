# HPE Medical Imaging AI Segmentation with NVIDIA Vista3D

A medical imaging AI platform that combines HPE High Performance Compute infrastructure with NVIDIA's Vista3D technology for automated vessel segmentation on DICOM medical imaging data.

<img src="assets/images/1.png" height=200 > <img src="assets/images/2.png" height=200 > <img src="assets/images/3.png" height=200 >

## Overview

This platform provides automated vessel segmentation using NVIDIA's Vista3D model on HPE infrastructure, transforming DICOM medical imaging data into actionable clinical insights through AI-powered segmentation and 3D visualization.

## Key Features

- **AI-Powered Segmentation**: NVIDIA Vista3D model for automated vessel and anatomical structure segmentation
- **3D Visualization**: Interactive 3D medical viewer using NiiVue technology
- **Multi-Planar Views**: Axial, coronal, and sagittal slice visualization
- **Batch Processing**: Efficient processing of large medical imaging datasets
- **HPE Infrastructure**: Optimized for HPE GreenLake HPC and Private Cloud AI

## Model Capabilities

- **CT Scan Focus**: Designed for abdominal, thoracic, and body vessel segmentation
- **Anatomical Scope**: Supports segmentation of organs, vessels, bones, and soft tissue structures
- **Limitation**: Does not segment the entire brain (optimized for body structures and lesions)

### Technology Stack
- **Infrastructure**: HPE GreenLake HPC, Private Cloud AI, HPE ProLiant servers
- **AI/ML**: NVIDIA Vista3D NIM, CUDA acceleration
- **Backend**: Python, FastAPI, Docker
- **Frontend**: Streamlit, NiiVue 3D viewer
- **Data Formats**: DICOM, NIfTI

## System Requirements

- **OS**: Ubuntu Linux (18.04+) or macOS
- **GPU**: NVIDIA GPU with CUDA support (8GB+ VRAM recommended)
- **Memory**: 16GB+ RAM for large medical imaging datasets
- **Docker**: Docker and NVIDIA Container Toolkit (required)
- **NVIDIA NGC**: Account for Vista3D access

## 🚀 Quick Start

**Get up and running with our new three-script architecture!**

### Step 1: Initial Setup
```bash
# Clone the repository
git clone <repository-url>
cd HPE-Nvidia-Vista-3D

# Run the unified setup script
python3 setup.py
```

The setup script will:
- ✅ Check system requirements (Ubuntu/macOS, Python 3.11+, GPU, Docker)
- ✅ Set up Python environment with all dependencies
- ✅ Configure environment variables and Docker settings
- ✅ Guide you through configuration (NVIDIA NGC API key)
- ✅ Create all necessary directories and files

### Step 2: Start Vista3D Server (GPU-Enabled Machine)
```bash
# On your GPU-enabled machine (local or remote)
python3 start_vista3d.py
```

This starts:
- 🧠 **Vista3D AI Server** (http://localhost:8000)
- ⚡ **GPU-accelerated processing** for medical image segmentation
- 🔄 **Auto-restart capability** for production deployments

**Note**: The Vista3D server takes a few minutes to initialize and be ready for use.

### Step 3: Start Frontend Services
```bash
# On any machine (can be same as Vista3D or different)
python3 start_frontend.py
```

This starts:
- 🌐 **Streamlit Web Interface** (http://localhost:8501)
- 🖼️ **Image Server** (http://localhost:8888)

### Step 4: Process Your Images
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

**🎉 That's it!** You now have a fully functional medical AI platform with distributed architecture.

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

## 📋 What You Get

After running the setup and start scripts, you'll have:

- **Complete Medical AI Platform**: All services running in Docker containers
- **Web Interface**: Easy-to-use Streamlit interface with Tools page for image processing
- **AI Segmentation**: NVIDIA Vista3D model for automated vessel segmentation
- **3D Visualization**: Interactive 3D medical viewer
- **Batch Processing**: Process multiple patients and studies through the GUI
- **API Access**: RESTful API for integration with other systems

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

## ⚠️ Command Line Utilities (Advanced Users Only)

The `utils/` directory contains command-line scripts for advanced users who need programmatic access:

```bash
# These are for advanced users only - use the Tools page instead
python3 utils/dicom2nifti.py    # DICOM to NIFTI conversion
python3 utils/segment.py        # Vista3D segmentation processing
python3 utils/nifti2ply.py      # NIFTI to PLY conversion
```

**Recommended**: Use the **Tools page** in the web interface (http://localhost:8501) for all image processing tasks.

## 📁 Project Structure

```
HPE-Nvidia-Vista-3D/
├── setup.py              # Unified setup script
├── start_vista3d.py      # Vista3D server startup script
├── start_frontend.py     # Frontend services startup script
├── app.py                # Main Streamlit web application
├── .env                  # Environment configuration (created by setup)
├── dicom/                # DICOM files (patient folders: PA*, SER*)
├── output/               # Generated files
│   ├── nifti/           # Converted NIFTI files
│   ├── scans/           # Scan results
│   └── voxels/          # Voxel data
├── utils/               # Utility scripts (for advanced users)
│   ├── dicom2nifti.py   # DICOM to NIFTI conversion (use Tools page instead)
│   ├── segment.py       # Vista3D segmentation processing (use Tools page instead)
│   └── nifti2ply.py     # NIFTI to PLY conversion (use Tools page instead)
└── conf/                # Configuration files
```

## 🛠️ Advanced Configuration

### Custom Configuration
Edit the `.env` file created during setup:

```bash
# Vista3D server (local or remote)
VISTA3D_SERVER="http://localhost:8000"  # Local
# VISTA3D_SERVER="http://remote-server:8000"  # Remote

# Segmentation targets
VESSELS_OF_INTEREST="all"  # or specific structures

# Custom paths
DICOM_FOLDER="/path/to/your/dicom"
OUTPUT_FOLDER="/path/to/your/output"
```

### Remote Vista3D Server
If you want to use a remote Vista3D server instead of running it locally:

```bash
# Edit .env file
VISTA3D_SERVER="http://localhost:8000"  # Uses SSH tunnel
NGC_API_KEY="your_nvidia_api_key"

# Set up SSH port forwarding
ssh user@remote_server -L 8000:localhost:8000 -R 8888:localhost:8888

# Start only frontend services
python3 start_frontend.py
```

## 🔍 Troubleshooting

### Common Issues

**Vista3D Not Starting**
```bash
# Check GPU availability
nvidia-smi

# Check Docker GPU support
docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu22.04 nvidia-smi

# Check Vista3D logs
docker logs -f vista3d
```

**Permission Issues**
```bash
# Fix file permissions
sudo chown -R $USER:$USER output/
sudo chmod -R 755 output/
```

**Port Already in Use**
```bash
# Check what's using the ports
lsof -i :8501
lsof -i :8888
lsof -i :8000

# Stop conflicting services
sudo systemctl stop conflicting-service
```

### Getting Help
1. Check the logs for error messages
2. Verify system requirements
3. Try rerunning the setup script
4. Check NVIDIA NGC documentation

## 📊 Performance Tips

- **GPU Memory**: Ensure 8GB+ VRAM for optimal performance
- **System Memory**: 16GB+ RAM recommended for large datasets
- **Storage**: Use SSD storage for faster processing
- **Network**: Stable connection required for initial setup

## 🔒 Security Notes

- **API Keys**: Never commit `.env` file to version control
- **Data Privacy**: All processing happens locally
- **Network**: Services run on localhost by default
- **File Access**: Containers have access to project directories only

## 🌐 Remote Access

To allow external access to your platform:

```bash
# Find your public IP
curl ifconfig.me

# Update .env file
IMAGE_SERVER="http://your-public-ip:8888"

# Ensure firewall allows ports
sudo ufw allow 8501
sudo ufw allow 8888
sudo ufw allow 8000
```

## 📚 Additional Resources

- **Full Documentation**: See `docs/` directory for detailed guides
- **API Reference**: Check `utils/` directory for script documentation
- **HPE GreenLake**: Learn about HPE infrastructure integration
- **NVIDIA NGC**: Access Vista3D models and documentation

---

**Need Help?** Check the troubleshooting section or refer to the full documentation in the `docs/` directory.

**Ready to Go?** Follow the Quick Start steps above and you'll be up and running in 15 minutes! 🚀

---

**Built with ❤️ for Healthcare AI Innovation**
