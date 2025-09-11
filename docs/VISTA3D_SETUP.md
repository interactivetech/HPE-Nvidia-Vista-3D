# NVIDIA Vista3D NIM Setup Guide

This guide explains how to use the automated setup script to install and configure NVIDIA Vista3D NIM on Ubuntu Linux.

## Overview

The `setup.py` script now includes a complete Vista3D setup mode (`--setup-vista3d`) that will:

### **VISTA3D Model Capabilities & Limitations**

**Important Note**: The VISTA3D model does not segment the entire brain because it was specifically trained and intended for segmenting body structures and lesions in 3D Computed Tomography (CT) images. While it supports segmenting many anatomical structures, it was not developed or trained on the necessary datasets for a full, detailed brain segmentation, which is a complex and specialized task in medical imaging.

**Model Focus Areas**:
- Abdominal and thoracic organ segmentation
- Vascular structure identification
- Body lesion detection and segmentation
- Soft tissue and bone structure analysis (excluding detailed brain anatomy)

### **Setup Process**

The automated setup will:

1. ✅ Check system requirements (Ubuntu, sudo access)
2. ✅ Verify NVIDIA GPU and drivers
3. ✅ Install Docker (if not present)
4. ✅ Install NVIDIA Container Toolkit
5. ✅ Test NVIDIA Docker integration
6. ✅ Prompt for NVIDIA NGC credentials
7. ✅ Create `.env` configuration file
8. ✅ Login to NVIDIA NGC registry
9. ✅ Download Vista3D Docker image
10. ✅ Start Vista3D container
11. ✅ Verify container health

## Prerequisites

### System Requirements
- **Ubuntu Linux** (18.04+ recommended)
- **NVIDIA GPU** with CUDA support
- **Sudo access** for system package installation
- **Internet connection** for downloading packages and Docker images

### NVIDIA Requirements
- **NVIDIA GPU drivers** (automatically installed if missing)
- **NVIDIA NGC account** (free registration at https://ngc.nvidia.com/)

## Quick Start

### 1. Clone the Repository
```bash
git clone <repository-url>
cd <repository-directory>
```

### 2. Run Vista3D Setup
```bash
python3 setup.py --setup-vista3d
```

### 3. Follow the Interactive Prompts
The script will prompt you for:
- **NVIDIA NGC API Key** (starts with `nvapi-`)
- **NGC Organization ID** (optional, defaults to "nvidia")

### 4. Wait for Completion
The setup process may take 10-30 minutes depending on your internet connection and system.

## What Gets Installed

### System Packages
- Docker CE (Community Edition)
- NVIDIA Container Toolkit
- Required system dependencies

### Docker Images
- NVIDIA Vista3D NIM: `nvcr.io/nim/nvidia/vista3d:1.0.0`
- Test CUDA image (for verification)

### Configuration Files
- `.env` file with your NGC credentials and Vista3D settings
- Docker daemon configuration for NVIDIA runtime
 - `conf/vista3d_label_sets.json` predefined label sets (e.g., Head/Neck)

## 🔑 Critical: External IP Configuration

**Important:** After Vista3D setup, you must configure your external IP address for the image server to work with remote Vista3D.

### Why This is Required
- Vista3D runs on a **remote server** (not on your local machine)
- Your image server runs **locally** and serves files from your `output/` folder
- Vista3D needs a **publicly accessible URL** to download images from your local server

### Find Your Public IP Address
```bash
# Method 1: Using curl (Recommended)
curl ifconfig.me

# Method 2: Using wget
wget -qO- ifconfig.me

# Method 3: Using dig
dig +short myip.opendns.com @resolver1.opendns.com
```

### Update Your .env File
Add this line to your `.env` file with your actual public IP:
```bash
IMAGE_SERVER="http://localhost:8888"
```

**Example:**
```bash
IMAGE_SERVER="http://203.0.113.1:8888"
```

### Firewall Configuration
Ensure port 8888 is open in your firewall/router to allow external access to your image server.

### Alternative: Using ngrok (if firewall configuration is not possible)
```bash
# Install ngrok
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok

# Create tunnel
ngrok http 8888
# Use the provided https URL as your IMAGE_SERVER
```

## Usage Examples

### Complete Vista3D Setup
```bash
# Full automated setup
python3 setup.py --setup-vista3d
```

### Standard Project Setup (after Vista3D is installed)
```bash
# Set up project environment, image server, etc.
python3 setup.py
```

### Other Options
```bash
# Start image server only
python3 setup.py --start-server

# Run DICOM conversion
python3 setup.py --convert-dicom

# Show help
python3 setup.py --help
```

### Manual Vista3D Management
```bash
# Start Vista3D manually (if already set up)
python3 utils/start_vista3d.py

# Query Vista3D API for supported labels
python3 utils/query_vista3d_api.py

# Run segmentation analysis
python3 utils/segment.py
```

## Post-Setup Verification

After successful setup, you should see:
```
🎉 Vista3D setup completed successfully!

Vista3D is running on: http://localhost:8000
API endpoint: http://localhost:8000/v1/vista3d/inference
```

### Test the API
```bash
# Check container status
sudo docker ps | grep vista3d

# View container logs
sudo docker logs vista3d

# Test API endpoint
curl -X POST http://localhost:8000/v1/vista3d/inference \
  -H "Content-Type: application/json" \
  -d '{"image": "/workspace/output/nifti/test.nii.gz"}'

# Query API for supported labels
curl http://localhost:8000/v1/vista3d/info
```

## Container Management

### Useful Commands
```bash
# Check container status
sudo docker ps | grep vista3d

# View logs
sudo docker logs -f vista3d

# Stop Vista3D
sudo docker stop vista3d

# Start Vista3D
sudo docker start vista3d

# Restart Vista3D
sudo docker restart vista3d

# Remove container (will need to re-run setup)
sudo docker rm vista3d
```

## Troubleshooting

### Common Issues

#### 1. NVIDIA Drivers Not Found
```bash
# Install NVIDIA drivers
sudo apt update
sudo apt install nvidia-driver-535
sudo reboot
```

#### 2. Docker Permission Denied
```bash
# Add user to docker group
sudo usermod -aG docker $USER
sudo systemctl restart docker
newgrp docker
```

#### 3. NGC Login Failed
- Verify your API key starts with `nvapi-`
- Check your internet connection
- Ensure NGC account is active

#### 4. Container Won't Start
```bash
# Check Docker logs
sudo docker logs vista3d

# Check system resources
nvidia-smi
free -h
df -h
```

#### 5. GPU Not Detected
```bash
# Test NVIDIA Docker
sudo docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi

# Check NVIDIA runtime
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

#### 6. File Access Issues
```bash
# Check file permissions
ls -la output/
sudo chown -R $USER:$USER output/

# Verify .env file exists and is readable
cat .env
```

#### 7. Vista3D API Not Responding
```bash
# Check if container is running
sudo docker ps | grep vista3d

# Check container logs for errors
sudo docker logs vista3d

# Test API connectivity
curl -v http://localhost:8000/v1/vista3d/info
```

### Log Files
- **Setup logs**: Output displayed in terminal
- **Docker logs**: `sudo docker logs vista3d`
- **System logs**: `journalctl -f`

### Getting Help
If you encounter issues:
1. Check the logs for error messages
2. Verify system requirements
3. Try rerunning the setup script
4. Check NVIDIA NGC documentation

## Configuration Details

### Environment Variables (`.env` file)
```bash
# NVIDIA NGC Credentials
NGC_API_KEY=nvapi-xxxxxxxxxxxxx
NGC_ORG_ID=nvidia

# Vista3D Configuration
VISTA3D_CONTAINER_NAME=vista3d
VISTA3D_PORT=8000
LOCAL_NIM_CACHE=~/.cache/nim

# GPU Configuration
CUDA_VISIBLE_DEVICES=0
NVIDIA_VISIBLE_DEVICES=0
NVIDIA_DRIVER_CAPABILITIES=compute,utility

# Image Server Configuration
EXTERNAL_IMAGE_SERVER=https://host.docker.internal:8888
EXTERNAL_IMAGE_SERVER_HOST=host.docker.internal
EXTERNAL_IMAGE_SERVER_PORT=8888
EXTERNAL_IMAGE_SERVER_PROTOCOL=https

# Project Configuration
PROJECT_ROOT=/path/to/your/project
DICOM_FOLDER=dicom
IMAGE_SERVER=http://localhost:8888
VESSELS_OF_INTEREST=all

# Optional: Use a predefined label set from conf/vista3d_label_sets.json
# Examples: HeadNeckCore, HeadNeckExtended
#LABEL_SET=HeadNeckCore

# File Access Configuration
ALLOW_LOCAL_FILES=True
ENABLE_FILE_ACCESS=True
ALLOW_FILE_PROTOCOL=True
WORKSPACE_IMAGES_PATH=/workspace/output/nifti
WORKSPACE_OUTPUTS_PATH=/workspace/output
IGNORE_SSL_ERRORS=True

# Additional Vista3D Environment Variables (optional)
ENABLE_CONTAINER_PATHS=True
ALLOW_ABSOLUTE_PATHS=True
ALLOW_RELATIVE_PATHS=True
ALLOW_LOCAL_PATHS=True
DISABLE_URL_VALIDATION=False
ALLOW_ABSOLUTE_FILE_PATHS=True
ALLOW_RELATIVE_FILE_PATHS=True
FILE_ACCESS_MODE=local
LOCAL_FILE_ACCESS=True
IMAGE_URI_ALLOW_REDIRECTS=True
IMAGE_URI_HTTPS_ONLY=False
```

### Container Configuration
- **Image**: `nvcr.io/nim/nvidia/vista3d:1.0.0`
- **Port**: 8000 (Vista3D API)
- **GPU**: All available GPUs
- **Memory**: 8GB shared memory
- **Volumes**: Project output directory mounted at `/workspace/output`
- **Runtime**: NVIDIA Container Runtime
- **Environment Variables**: NGC credentials and file access settings

## Next Steps

After Vista3D is running:

1. **Set up the project environment**:
   ```bash
   python3 setup.py
   ```

2. **Configure your environment**:
   ```bash
   # Copy and edit the environment template
   cp dot_env_template .env
   # Edit .env to set your PROJECT_ROOT and other settings
   ```

3. **Add NIFTI files**:
   ```bash
   # Place your .nii.gz files here
   mkdir -p output/nifti
   cp your_scan.nii.gz output/nifti/
   ```

4. **Start the web viewer**:
   ```bash
   streamlit run app.py
   ```

5. **Run segmentation**:
   ```bash
   python3 utils/segment.py
   ```

6. **Convert DICOM files** (if needed):
   ```bash
   python3 setup.py --convert-dicom
   ```

## Security Considerations

- **API Keys**: The `.env` file contains sensitive credentials. Do not commit it to version control.
- **Docker Access**: The script requires sudo access for Docker operations.
- **Network**: Vista3D container runs on localhost:8000 by default.
- **File Access**: Container has access to the project output directory.

## Performance Tips

- **GPU Memory**: Ensure sufficient GPU memory (8GB+ recommended)
- **System Memory**: 16GB+ RAM recommended for large medical images
- **Storage**: SSD storage recommended for faster image processing
- **Network**: Stable internet connection required for initial download
- **File Access**: Ensure proper file permissions for the output directory
- **Container Resources**: Monitor container resource usage with `sudo docker stats vista3d`

---

**Note**: This setup is designed for development and testing environments. For production deployments, consider additional security measures and container orchestration platforms.
