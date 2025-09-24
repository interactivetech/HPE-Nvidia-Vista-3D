# 🚀 HPE NVIDIA Vista3D Medical AI Platform - Setup Guide

Get up and running with the HPE GreenLake Medical AI Platform with NVIDIA Vista3D in minutes!

## 📋 Prerequisites

### System Requirements
- **Ubuntu Linux** (18.04+) or **macOS**
- **NVIDIA GPU** with CUDA support (8GB+ VRAM recommended)
- **16GB+ RAM** for large medical imaging datasets
- **10GB+ free disk space**
- **Docker and NVIDIA Container Toolkit** (for Docker deployment)
- **Internet connection** for downloading packages and Docker images

### NVIDIA Requirements
- **NVIDIA NGC account** (free at [ngc.nvidia.com](https://ngc.nvidia.com/))
- **NVIDIA API Key** (starts with `nvapi-`)

## 🎯 What This Platform Does

This platform processes medical imaging data through the following workflow:

```
DICOM Images → NIfTI Conversion → Vista3D AI Segmentation → 3D Visualization
```

**Key Capabilities:**
- **CT Scan Focus**: Designed for abdominal, thoracic, and body vessel segmentation
- **Anatomical Scope**: Supports segmentation of organs, vessels, bones, and soft tissue structures
- **Important Note**: Does not segment the entire brain (optimized for body structures and lesions)

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

**What the setup script does:**
- ✅ Checks system requirements (OS, Python, GPU, Docker)
- ✅ Sets up Python environment with all dependencies
- ✅ Configures environment variables and Docker settings
- ✅ Prompts for your NVIDIA NGC API key
- ✅ Creates all necessary directories and files

### Step 2: Start Vista3D Server (GPU-Enabled Machine)
```bash
# On your GPU-enabled machine (local or remote)
python3 start_vista3d.py
```

**This starts:**
- 🧠 **Vista3D AI Server** (http://localhost:8000)
- ⚡ **GPU-accelerated processing** for medical image segmentation
- 🔄 **Auto-restart capability** for production deployments

**Note**: The Vista3D server takes a few minutes to initialize and be ready for use.

### Step 3: Start Frontend Services
```bash
# On any machine (can be same as Vista3D or different)
python3 start_frontend.py
```

**This starts:**
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

**🎉 You're ready!** You now have a fully functional medical AI platform with distributed architecture.

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

## 🔧 Advanced Configuration

### Custom Configuration
Edit the `.env` file created during setup:

```bash
# Vista3D server (local or remote)
VISTA3D_SERVER="http://localhost:8000"  # Local
# VISTA3D_SERVER="http://remote-server:8000"  # Remote

# Image server
IMAGE_SERVER="http://localhost:8888"

# Segmentation targets
VESSELS_OF_INTEREST="all"  # or specific structures
# LABEL_SET="HeadNeckCore"  # or use predefined label set

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

### Vista3D Server Only
If you want to run only the Vista3D server (for distributed deployments):

```bash
# Edit .env file
NGC_API_KEY="your_nvidia_api_key"
NGC_ORG_ID="nvidia"

# Start only Vista3D server
python3 start_vista3d.py
```

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
├── utils/               # Utility scripts
│   ├── dicom2nifti.py   # DICOM to NIFTI conversion
│   ├── segment.py       # Vista3D segmentation processing
│   ├── image_server.py  # HTTP image server
│   └── start_vista3d.py # Vista3D Docker container manager
├── conf/                # Configuration files
│   ├── vista3d_label_sets.json    # Predefined label sets
│   ├── vista3d_label_dict.json    # Label dictionary
│   └── vista3d_label_colors.json  # Label colors
└── assets/              # UI components and static files
```

## 🎯 Key Features

### AI-Powered Segmentation
- **Automated vessel segmentation** using NVIDIA Vista3D NIM
- **Multi-label segmentation** for complex anatomical structures
- **Batch processing** for multiple patient studies
- **Real-time processing** with GPU acceleration

### Advanced Visualization
- **3D Medical Viewer** using NiiVue technology
- **Multi-planar views** (axial, coronal, sagittal)
- **Interactive controls** for medical professionals
- **Real-time rendering** with NVIDIA GPU acceleration

### Enterprise Infrastructure
- **HPE GreenLake Platform** integration
- **Docker containerization** for scalable deployment
- **RESTful API** for system integration
- **Secure data handling** with HIPAA compliance

## 🚀 Usage Examples

### Basic Workflow

#### For Remote Vista3D (Recommended)
```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Configure for remote Vista3D
echo "VISTA3D_SERVER=http://localhost:8000" >> .env  # Uses SSH tunnel
echo "NGC_API_KEY=your_nvidia_api_key" >> .env

# 3. Set up SSH port forwarding
ssh user@remote_server -L 8000:localhost:8000 -R 8888:localhost:8888

# 4. Place your medical images
cp your_scan.nii.gz output/nifti/

# 5. Convert DICOM to NIFTI (if needed)
python3 utils/dicom2nifti.py

# 6. Start frontend services (Streamlit + Image Server)
python3 start_frontend.py

# 7. Run segmentation
python3 utils/segment.py
```

#### For Local Vista3D (Development)
```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Configure for local Vista3D
echo "VISTA3D_SERVER=http://localhost:8000" >> .env
echo "NGC_API_KEY=your_nvidia_api_key" >> .env

# 3. Place your medical images
cp your_scan.nii.gz output/nifti/

# 4. Convert DICOM to NIFTI (if needed)
python3 utils/dicom2nifti.py

# 5. Start Vista3D server (requires GPU)
python3 start_vista3d.py

# 6. Start frontend services (in separate terminal)
python3 start_frontend.py

# 7. Run segmentation
python3 utils/segment.py
```

### Batch Processing
```bash
# Process multiple patients
for patient in dicom/PA*; do
    echo "Processing $patient..."
    # Convert DICOM to NIFTI
    python3 utils/dicom2nifti.py
    # Run segmentation
    python3 utils/segment.py
done
```

### API Integration
```bash
# Query Vista3D API
curl http://localhost:8000/v1/vista3d/info

# Run segmentation via API
curl -X POST http://localhost:8000/v1/vista3d/inference \
  -H "Content-Type: application/json" \
  -d '{"image": "/workspace/output/nifti/scan.nii.gz"}'
```

### Using Predefined Label Sets
```bash
# Edit .env file to use predefined label set
echo "LABEL_SET=HeadNeckCore" >> .env

# Comment out custom vessels list
sed -i 's/VESSELS_OF_INTEREST=/#VESSELS_OF_INTEREST=/' .env

# Run segmentation with predefined labels
python3 utils/segment.py
```

## 🔍 Verification

### Check System Status
```bash
# Verify Vista3D is running
sudo docker ps | grep vista3d

# Check GPU availability
nvidia-smi

# Test API endpoint
curl http://localhost:8000/v1/vista3d/info
```

### Check Web Interface
- Open `http://localhost:8501` in your browser
- Navigate through the different sections
- Upload a test NIFTI file
- Run segmentation and view results

## 🛠️ Troubleshooting

### Common Issues

#### Vista3D Not Starting
```bash
# Check container logs
sudo docker logs vista3d

# Restart container
sudo docker restart vista3d

# Check GPU availability
nvidia-smi
```

#### Permission Issues
```bash
# Fix file permissions
sudo chown -R $USER:$USER output/
sudo chmod -R 755 output/
```

#### API Connection Issues
```bash
# Check if Vista3D is running
sudo docker ps | grep vista3d

# Test API connectivity
curl -v http://localhost:8000/v1/vista3d/info
```

#### DICOM Conversion Issues
```bash
# Check DICOM folder structure
ls -la dicom/

# Verify NIFTI output
ls -la output/nifti/
```

#### NGC Authentication Issues
```bash
# Verify NGC API key format
grep NGC_API_KEY .env
# Should start with 'nvapi-'

# Test NGC login
docker login nvcr.io -u '$oauthtoken' -p 'your-api-key'
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
- **Network**: Vista3D runs on localhost by default
- **File Access**: Container has access to project output directory

## 🌐 Remote Setup Configuration

For running Vista3D on a separate server:

### Server Setup (GPU Machine)
```bash
# On the GPU server
python3 utils/start_vista3d.py
```

### Client Setup (Your Machine)
```bash
# Edit .env file to point to remote server
VISTA3D_SERVER="http://your-gpu-server:8000"
IMAGE_SERVER="http://your-public-ip:8888"
```

### External Access Configuration
```bash
# Find your public IP
curl ifconfig.me

# Update .env file
IMAGE_SERVER="http://your-public-ip:8888"

# Ensure firewall allows port 8888
sudo ufw allow 8888
```

## 🎯 Next Steps

1. **Explore the Web Interface**: Navigate through different sections
2. **Upload Your Data**: Add DICOM or NIFTI files
3. **Run Segmentation**: Process your medical images
4. **View Results**: Use the 3D viewer to analyze results
5. **Integrate**: Use the API for custom workflows

## 📚 Additional Resources

- **Full Documentation**: See `README.md` for comprehensive details
- **Setup Guide**: See `docs/VISTA3D_SETUP.md` for detailed setup
- **API Reference**: Check `utils/` directory for script documentation
- **HPE GreenLake**: Learn about HPE infrastructure integration

---

**Need Help?** Check the troubleshooting section or refer to the full documentation in `README.md`.

**Ready to Go?** Follow the Quick Start steps above and you'll be up and running in 15 minutes! 🚀
