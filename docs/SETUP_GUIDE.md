# 🚀 HPE NVIDIA Vista3D Medical AI Platform - Setup Guide

Get up and running with the HPE GreenLake Medical AI Platform with NVIDIA Vista3D in minutes!

## 📋 Prerequisites

### System Requirements

#### For Backend Setup (Vista3D Server):
- **Ubuntu Linux** (18.04+) or **macOS**
- **NVIDIA GPU** with CUDA support (8GB+ VRAM recommended)
- **16GB+ RAM** for large medical imaging datasets
- **10GB+ free disk space**
- **Docker and NVIDIA Container Toolkit** (for Docker deployment)
- **Internet connection** for downloading packages and Docker images

#### For Frontend Setup (Web Interface):
- **Ubuntu Linux** (18.04+) or **macOS**
- **8GB+ RAM** (minimum)
- **5GB+ free disk space**
- **Docker** (required)
- **Internet connection** for downloading packages and Docker images

### NVIDIA Requirements
- **NVIDIA NGC account** (free at [ngc.nvidia.com](https://ngc.nvidia.com/))
- **NVIDIA API Key** (starts with `nvapi-`) - **Required for backend setup only**

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

**Get up and running with our unified setup script!**

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
- ✅ Sets up separate Python environments for frontend and backend
- ✅ Configures environment variables and Docker settings
- ✅ Prompts for your NVIDIA NGC API key (backend only)
- ✅ Creates all necessary directories and files
- ✅ Installs sample medical imaging data (if available)

### Step 2: Start Services

**The commands depend on what you set up in Step 1:**

#### If you set up both frontend and backend:
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

#### If you set up only the backend:
```bash
# Start Vista3D AI Server
cd backend
docker-compose up -d
```

#### If you set up only the frontend:
```bash
# Start Frontend Services
cd frontend
# Start image server first
cd ../image_server && docker-compose up -d
# Start frontend
cd ../frontend && docker-compose up -d
```

**This starts:**
- 🧠 **Vista3D AI Server** (http://localhost:8000) - if backend was set up
- 🌐 **Streamlit Web Interface** (http://localhost:8501) - if frontend was set up
- 🖼️ **Image Server** (http://localhost:8888) - if frontend was set up

**Note**: The Vista3D server takes a few minutes to initialize and be ready for use.

### Step 3: Process Your Images

**Note**: This step requires the frontend web interface to be running.

```bash
# Sample data is automatically installed during setup (if available)
# The setup script installs sample medical imaging data for patient PA00000002

# For your own data:
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

**🎉 You're ready!** You now have a fully functional medical AI platform.

## ⚙️ Setup Options

The `setup.py` script provides flexible installation options to accommodate different deployment scenarios and system configurations.

### 1. Full Platform Setup (Default)
```bash
python3 setup.py
# or
python3 setup.py --setup both
```

**What it does:**
- Sets up both frontend and backend components
- Requires GPU-enabled system
- Prompts for NVIDIA NGC API key
- Creates complete platform with all services

**Best for:**
- Complete development environments
- Single-machine deployments
- Testing and evaluation

### 2. Frontend-Only Setup
```bash
python3 setup.py --setup frontend
```

**What it does:**
- Sets up only the web interface and image server
- No GPU requirements
- No NVIDIA NGC API key needed
- Connects to remote Vista3D server

**Best for:**
- Non-GPU systems (laptops, workstations)
- Web interfaces connecting to remote Vista3D
- Lightweight deployments

**System Requirements:**
- OS: Ubuntu Linux (18.04+) or macOS
- Memory: 8GB+ RAM (minimum)
- Docker: Required
- Disk Space: 5GB+ free space

### 3. Backend-Only Setup
```bash
python3 setup.py --setup backend
```

**What it does:**
- Sets up only the Vista3D AI server
- Requires GPU-enabled system
- Prompts for NVIDIA NGC API key
- Provides API for frontend connections

**Best for:**
- GPU servers providing Vista3D API
- Backend-only deployments
- API service providers

**System Requirements:**
- OS: Ubuntu Linux (18.04+) or macOS
- GPU: NVIDIA GPU with CUDA support (8GB+ VRAM recommended)
- Memory: 16GB+ RAM
- Docker: Required with NVIDIA Container Toolkit
- Disk Space: 10GB+ free space

## 🔧 Additional Setup Options

### Check System Requirements Only
```bash
python3 setup.py --check-only
```

**What it does:**
- Validates system requirements
- No installation or configuration
- Useful for pre-deployment validation

### Non-Interactive Setup
```bash
python3 setup.py --non-interactive
```

**What it does:**
- Uses default configuration values
- No user prompts
- Suitable for automated deployments

### Skip Docker Hub Check
```bash
python3 setup.py --skip-docker-check
```

**What it does:**
- Skips Docker Hub image availability check
- Useful when images are already available locally
- Speeds up setup process

### Use Configuration File
```bash
python3 setup.py --config-file my_config.env
```

**What it does:**
- Loads configuration from external file
- Bypasses interactive configuration
- Useful for consistent deployments

### Get Help
```bash
python3 setup.py --help
```

**What it does:**
- Displays comprehensive help information
- Shows all available options
- Provides usage examples

## 🌐 Deployment Scenarios

### Scenario 1: Single GPU Machine
```bash
# Complete setup on one machine
python3 setup.py

# Start all services
cd backend && docker-compose up -d
cd ../frontend
cd ../image_server && docker-compose up -d
cd ../frontend && docker-compose up -d
```

### Scenario 2: Frontend on Non-GPU Machine
```bash
# On non-GPU machine
python3 setup.py --setup frontend
cd frontend
# Start image server first
cd ../image_server && docker-compose up -d
# Start frontend
cd ../frontend && docker-compose up -d

# On GPU machine (separate)
python3 setup.py --setup backend
cd backend && docker-compose up -d
```

### Scenario 3: Backend API Server
```bash
# On GPU server
python3 setup.py --setup backend
cd backend && docker-compose up -d

# Frontend machines connect to API
```

### Scenario 4: Development Environment
```bash
# Check requirements first
python3 setup.py --check-only

# Setup with custom config
python3 setup.py --config-file dev_config.env
```

## 🐍 Virtual Environment Management

The project uses **separate virtual environments** for frontend and backend services to avoid dependency conflicts.

### Environment Structure
- **`.venv-frontend/`** - Frontend environment (Streamlit, FastAPI, web frameworks)
- **`.venv-backend/`** - Backend environment (PyTorch, AI/ML libraries)
- **`.venv/`** - Shared environment (legacy, contains common dependencies)

### Activating Environments

#### Frontend Environment
```bash
# Activate frontend environment
source .venv-frontend/bin/activate

# Or use uv to run frontend commands directly
uv run --python .venv-frontend/bin/python your_frontend_script.py
```

#### Backend Environment
```bash
# Activate backend environment
source .venv-backend/bin/activate

# Or use uv to run backend commands directly
uv run --python .venv-backend/bin/python your_backend_script.py
```

### Environment Verification
```bash
# Test frontend environment
source .venv-frontend/bin/activate
python -c "import streamlit, fastapi, nibabel; print('✅ Frontend environment working!')"

# Test backend environment
source .venv-backend/bin/activate
python -c "import torch, nibabel; print('✅ Backend environment working!')"
```

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

### VPN and Secure Network Access

When the Vista3D backend server is behind a VPN or firewall, SSH tunneling provides secure access:

#### VPN Scenario Setup
```bash
# 1. Connect to VPN (if required)
# Your organization's VPN client should be running

# 2. Establish SSH tunnel through VPN
ssh user@vpn_server -L 8000:localhost:8000 -R 8888:localhost:8888

# 3. Configure frontend to use tunneled ports
echo "VISTA3D_SERVER=http://localhost:8000" >> .env
echo "IMAGE_SERVER=http://localhost:8888" >> .env
```

#### Why SSH Tunneling for VPN?
- **Security**: Encrypts all traffic between frontend and backend
- **Firewall Bypass**: Works through corporate firewalls and VPNs
- **Port Access**: Makes backend services accessible on localhost
- **No Direct Network Access**: Frontend doesn't need direct VPN access

#### VPN Troubleshooting
```bash
# Test VPN connectivity
ping vpn_server

# Test SSH access through VPN
ssh user@vpn_server "echo 'VPN SSH access working'"

# Verify port forwarding
netstat -an | grep 8000
netstat -an | grep 8888

# Check if ports are accessible
curl -v http://localhost:8000/v1/vista3d/info
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

## 📁 Project Structure

```
HPE-Nvidia-Vista-3D/
├── setup.py              # Unified setup script
├── start_backend.py      # Vista3D server startup script
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
│   └── start_backend.py # Vista3D Docker container manager
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
# 1. Activate frontend environment
source .venv-frontend/bin/activate

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
# 1. Activate frontend environment
source .venv-frontend/bin/activate

# 2. Configure for local Vista3D
echo "VISTA3D_SERVER=http://localhost:8000" >> .env
echo "NGC_API_KEY=your_nvidia_api_key" >> .env

# 3. Place your medical images
cp your_scan.nii.gz output/nifti/

# 4. Convert DICOM to NIFTI (if needed)
python3 utils/dicom2nifti.py

# 5. Start Vista3D server (requires GPU)
python3 start_backend.py

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

#### Frontend-Only Setup Issues
- Ensure remote Vista3D server is accessible
- Check network connectivity
- Verify port forwarding if using SSH tunnels

#### Backend-Only Setup Issues
- Verify GPU availability with `nvidia-smi`
- Check NVIDIA Container Toolkit installation
- Validate NGC API key format

#### Mixed Setup Issues
- Ensure consistent configuration across machines
- Check network connectivity between services
- Verify port availability

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

## 🎯 Next Steps

1. **Explore the Web Interface**: Navigate through different sections
2. **Upload Your Data**: Add DICOM or NIFTI files
3. **Run Segmentation**: Process your medical images
4. **View Results**: Use the 3D viewer to analyze results
5. **Integrate**: Use the API for custom workflows

## 📚 Additional Resources

- **Sample Data**: See [docs/SAMPLE_DATA.md](SAMPLE_DATA.md) for sample data setup
- **Backend Guide**: See `docs/BACKEND_GUIDE.md` for Vista3D server details
- **Frontend Guide**: See `docs/FRONTEND_GUIDE.md` for web interface details
- **API Reference**: Check `utils/` directory for script documentation
- **HPE GreenLake**: Learn about HPE infrastructure integration

---

**Need Help?** Check the troubleshooting section or refer to the specific guides for backend and frontend services.

**Ready to Go?** Follow the Quick Start steps above and you'll be up and running in 15 minutes! 🚀