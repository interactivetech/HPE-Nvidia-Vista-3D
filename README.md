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

- **HPE Infrastructure**: HPE ProLiant servers with NVIDIA GPU support
- **GPU**: NVIDIA GPU with CUDA support (8GB+ VRAM recommended)
- **Memory**: 16GB+ RAM for large medical imaging datasets
- **OS**: Ubuntu Linux (18.04+)
- **Docker**: Docker and NVIDIA Container Toolkit
- **NVIDIA NGC**: Account for Vista3D access

## Quick Start

### Prerequisites
- HPE GreenLake HPC or Private Cloud AI access
- NVIDIA GPU with CUDA support
- Docker and NVIDIA Container Toolkit
- NVIDIA NGC account

## 🐳 Docker Deployment (Recommended)

The **preferred method** for running the Vista3D platform is using Docker containers, which provides better isolation, easier deployment, and consistent environments.

### 🎯 Deployment Modes

**Mode 1: Local GUI + Remote Vista3D (Recommended)**
```bash
# Configure .env for remote Vista3D server
VISTA3D_SERVER=https://your-vista3d-server.com:8000
VISTA3D_API_KEY=your_nvidia_api_key

# Start GUI containers (Streamlit + Image Server)
python3 utils/start_gui.py

# Run utility scripts from host system
python3 utils/dicom2nifti.py    # Convert DICOM to NIFTI
python3 utils/segment.py        # Run segmentation
python3 utils/nifti2ply.py --batch  # Convert to PLY files
```

**Mode 2: All Services Local (Development)**
```bash
# Configure .env for local Vista3D
VISTA3D_SERVER=http://vista3d-server:8000
VISTA3D_API_KEY=your_nvidia_api_key

# Start Vista3D server (requires GPU)
python3 utils/start_vista3d.py

# Start GUI containers (in separate terminal)
python3 utils/start_gui.py

# Run utility scripts from host system
python3 utils/dicom2nifti.py    # Convert DICOM to NIFTI
python3 utils/segment.py        # Run segmentation
python3 utils/nifti2ply.py --batch  # Convert to PLY files
```

**Mode 3: Production with Auto-Startup**
```bash
# Create systemd service for automatic startup
sudo python3 utils/start_gui.py --create-service
sudo python3 utils/start_vista3d.py --create-service
```

See [docs/DEPLOYMENT_MODES.md](docs/DEPLOYMENT_MODES.md) for detailed deployment instructions and [docs/CONTAINERIZATION.md](docs/CONTAINERIZATION.md) for Docker-specific details.

## 🐍 Non-Docker Installation (Alternative)

For development or environments where Docker is not available, you can install the platform directly on the host system.

### Prerequisites
- Python 3.11+
- NVIDIA GPU with CUDA support
- NVIDIA NGC account
- Ubuntu Linux (18.04+) recommended

### Installation Steps

```bash
# Clone the repository
git clone <repository-url>
cd Nvidia-Vista3d-segmenation

# Run automated installation and setup
python3 utils/install.py

# Activate virtual environment
source .venv/bin/activate
```

### Usage

```bash
# Place DICOM files in the dicom/ directory
# Convert DICOM files to NIFTI format
python3 utils/dicom2nifti.py

# Run segmentation
python3 utils/segment.py

# Start the application
streamlit run app.py
```

**Note**: The Docker method is recommended for production use as it provides better isolation and easier management.

---

**Built with ❤️ for Healthcare AI Innovation**
