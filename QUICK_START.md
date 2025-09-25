# 🚀 HPE NVIDIA Vista3D - Quick Start Guide

**Get up and running in 15 minutes!**

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

# Choose your setup approach:

# Option A: Full setup (both frontend and backend on same machine)
python3 setup_backend.py    # Sets up Vista3D AI server (requires GPU)
python3 setup_frontend.py   # Sets up web interface and image server

# Option B: Backend only (for GPU server)
python3 setup_backend.py

# Option C: Frontend only (for client machine)
python3 setup_frontend.py
```

**What the setup scripts do:**
- ✅ **Backend Setup**: Checks GPU requirements, configures Vista3D AI server, sets up NGC integration
- ✅ **Frontend Setup**: Sets up web interface and image server, configures connection to Vista3D server
- ✅ Sets up Python environment with all dependencies
- ✅ Configures Docker containers for services
- ✅ Prompts for your NVIDIA NGC API key (backend only)
- ✅ Creates all necessary directories and files

## Step 2: Start Services

```bash
# Choose your deployment approach:

# Option A: Start all services (if both frontend and backend are on same machine)
python3 start.py

# Option B: Start only backend (Vista3D AI server)
python3 start.py --vista3d-only

# Option C: Start only frontend (web interface and image server)
python3 start.py --frontend-only
```

**This starts:**
- 🌐 **Streamlit Web Interface** (http://localhost:8501)
- 🖼️ **Image Server** (http://localhost:8888)
- 🧠 **Vista3D AI Server** (http://localhost:8000) - backend only

## Step 3: Process Your Images

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

You now have a fully functional medical AI platform running on your GPU-enabled host.

## 🛠️ Using the Tools Page

The web interface includes a powerful **Tools page** where you can:

- **Convert DICOM to NIFTI**: Upload DICOM files and convert them to NIFTI format
- **Run AI Segmentation**: Process NIFTI files with the Vista3D AI model
- **View 3D Visualizations**: Interactive 3D medical viewer with multi-planar views
- **Batch Processing**: Process multiple patients and studies at once
- **Download Results**: Export segmentation results and 3D models

**Access the Tools page**: Navigate to http://localhost:8501 and click on the "Tools" tab in the sidebar.

## 🔧 Management Commands

```bash
# Start all services
python3 start.py

# Stop all services
python3 start.py --stop

# Restart all services
python3 start.py --restart

# View logs
docker compose logs -f
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
