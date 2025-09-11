# 🚀 Vista3D Medical AI Platform - Quick Start Guide

Get up and running with the HPE GreenLake Medical AI Platform with NVIDIA Vista3D in minutes!

## 📋 Prerequisites

### System Requirements
- **Ubuntu Linux** (18.04+ recommended)
- **NVIDIA GPU** with CUDA support (8GB+ VRAM recommended)
- **16GB+ RAM** for large medical imaging datasets
- **10GB+ free disk space**
- **Sudo access** for system package installation
- **Internet connection** for downloading packages and Docker images

### NVIDIA Requirements
- **NVIDIA NGC account** (free at [ngc.nvidia.com](https://ngc.nvidia.com/))
- **NVIDIA API Key** (starts with `nvapi-`)

## ⚡ Quick Start (15 minutes)

### 1. Install System Dependencies
```bash
# Install required system packages
sudo apt update
sudo apt install -y git curl wget unzip

# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# Install GitHub CLI
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install -y gh

# Authenticate with GitHub
gh auth login
```

### 2. Clone the Repository
```bash
# Clone the repository using GitHub CLI
gh repo clone dw-flyingw/Nvidia-Vista3d-segmenation
cd Nvidia-Vista3d-segmenation
```

### 3. Set Up Python Environment
```bash
# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
uv sync
```

### 4. Set Up Vista3D Docker Container
```bash
# Install Docker and NVIDIA Container Toolkit
python3 setup.py --install-deps

# Set up Vista3D (requires NVIDIA NGC credentials)
python3 setup.py --setup-vista3d
```

**Follow the interactive prompts:**
- Enter your NVIDIA NGC API Key (starts with `nvapi-`)
- Enter your NGC Organization ID (or press Enter for default)

### 5. Add Your Medical Images
```bash
# Place DICOM files in patient-specific folders
mkdir -p dicom/PA00000001
# Copy your DICOM files to dicom/PA00000001/

# Or place NIFTI files directly
mkdir -p output/nifti
# Copy your .nii.gz files to output/nifti/
```

### 6. Convert DICOM to NIFTI
```bash
# Convert DICOM files to NIFTI format
python3 utils/dicom2nifti.py
```

### 7. Run Segmentation
```bash
# Process NIFTI files with Vista3D
# Option A: use a predefined label set
echo "LABEL_SET=HeadNeckCore" >> .env
python3 utils/segment.py
```

### 8. Start Image Server
```bash
# Start HTTPS image server (in a separate terminal)
python3 utils/image_server.py
```

### 9. Start the Web Application
```bash
# Start Streamlit web interface
streamlit run app.py
```

**🎉 You're ready!** Open your browser to `http://localhost:8501`

## 🔧 Alternative: Step-by-Step Manual Setup

If you prefer to run each step manually or encounter issues:

### 1. Install System Dependencies
```bash
# Install basic packages
sudo apt update
sudo apt install -y git curl wget unzip

# Install Docker
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER
newgrp docker

# Install NVIDIA Container Toolkit
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt update
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# Test NVIDIA Docker
sudo docker run --rm --gpus all nvidia/cuda:11.0.3-base-ubuntu20.04 nvidia-smi
```

### 2. Install Package Managers
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# Install GitHub CLI
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install -y gh
gh auth login
```

### 3. Clone and Set Up Project
```bash
# Clone repository
gh repo clone dw-flyingw/Nvidia-Vista3d-segmenation
cd Nvidia-Vista3d-segmenation

# Set up Python environment
uv venv
source .venv/bin/activate
uv sync
```

### 4. Configure Environment
```bash
# Copy environment template
cp dot_env_template .env

# Edit .env file with your settings
nano .env
```

### 5. Set Up Vista3D
```bash
# Start Vista3D container
python3 utils/start_vista3d.py

# Watch logs as it takes a while to start up
sudo docker logs vista3d -f
```

## 📁 Project Structure

```
Nvidia-Vista3d-segmenation/
├── app.py                 # Main Streamlit application
├── setup.py              # Automated setup script
├── dicom/                # Place DICOM files here (patient folders)
├── output/               # Generated files
│   ├── nifti/           # Converted NIFTI files
│   └── results/         # Segmentation results
├── utils/               # Utility scripts
│   ├── dicom2nifti.py   # DICOM conversion
│   ├── segment.py       # Segmentation processing
│   └── image_server.py  # HTTPS image server
└── assets/              # UI components and static files
```

## 🎯 Key Features

### AI-Powered Segmentation
- **Automated vessel segmentation** using NVIDIA Vista3D
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
```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Place your medical images
cp your_scan.nii.gz output/nifti/

# 3. Convert DICOM to NIFTI (if needed)
python3 utils/dicom2nifti.py

# 4. Run segmentation
python3 utils/segment.py

# 5. Start image server (in separate terminal)
python3 utils/image_server.py

# 6. Start web interface
streamlit run app.py
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

- **Full Documentation**: See `README.md` for comprehensive details
- **Setup Guide**: See `docs/VISTA3D_SETUP.md` for detailed setup
- **API Reference**: Check `utils/` directory for script documentation
- **HPE GreenLake**: Learn about HPE infrastructure integration

---

**Need Help?** Check the troubleshooting section or refer to the full documentation in `README.md`.

**Ready to Go?** Follow the Quick Start steps above and you'll be up and running in 15 minutes! 🚀
