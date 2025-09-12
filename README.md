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

### Installation using one server

Configure HPE GreenLake HPC and Private Cloud AI access
Set up NVIDIA NGC API credentials for Vista3D


```bash
# Clone the repository
git clone <repository-url>
cd Nvidia-Vista3d-segmenation
```
Configure `.env` file with project settings

```bash
# Run automated setup
python3 setup.py --setup-vista3d 
# Activate virtual environment
source .venv/bin/activate 
```

Place DICOM files in the `dicom/` directory        

```bash
# Convert DICOM files to NIFTI format
python3 utils/dicom2nifty.py

# Run segmentation
python3 utils/segment.py

# Start the application
streamlit run app.py
```

---

**Built with ❤️ for Healthcare AI Innovation**
