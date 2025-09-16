
# HPE NVIDIA Vista3D Medical AI Platform - Manual Setup Guide

This guide provides manual setup steps for the Vista3D platform. For automated setup, see the main README.md.

## 🐳 Docker Setup (Recommended)

### Prerequisites
- Ubuntu Linux (18.04+)
- NVIDIA GPU with CUDA support
- Sudo access

### 1. Install Docker and NVIDIA Container Toolkit

```bash
# Install Docker
sudo apt update
sudo apt install apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker ${USER}
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

# Test NVIDIA Docker support
sudo docker run --rm --gpus all nvidia/cuda:11.0.3-base-ubuntu20.04 nvidia-smi
```

### 2. Install NGC CLI

```bash
# Install NGC CLI
wget --content-disposition https://api.ngc.nvidia.com/v2/resources/nvidia/ngc-apps/ngc_cli/versions/3.44.0/files/ngccli_linux.zip -O ngccli_linux.zip
unzip ngccli_linux.zip
cd ngc-cli
./install
ngc config set
ngc registry info

# Add NGC CLI to PATH
export PATH="$PATH:/home/${USER}/ngc-cli"
```

### 3. Clone and Setup Project

```bash
# Clone repository
git clone <repository-url>
cd Nvidia-Vista3d-segmenation

# Set up environment
export NGC_API_KEY=<your personal NGC key>
export LOCAL_NIM_CACHE=~/.cache/nim
mkdir -p $LOCAL_NIM_CACHE

# Create .env file
cp dot_env_template .env
# Edit .env file with your settings
```

### 4. Start Services

```bash
# Start Vista3D Docker container
python utils/start_vista3d.py

# Watch logs (in separate terminal)
docker logs vista3d -f

# Start GUI containers
python utils/start_gui.py
```

### 5. Process Medical Images

```bash
# Place DICOM files in dicom/ folder (patient-specific subfolders)
# Convert DICOM to NIfTI
python utils/dicom2nifti.py

# Run segmentation
python utils/segment.py

# Access the application
# Open browser to http://localhost:8501
```

## 🐍 Non-Docker Setup (Alternative)

### Prerequisites
- Python 3.11+
- NVIDIA GPU with CUDA support
- Ubuntu Linux (18.04+)

### 1. Install System Dependencies

```bash
# Install basic packages
sudo apt update
sudo apt install git curl wget

# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone and Setup Project

```bash
# Clone repository
git clone <repository-url>
cd Nvidia-Vista3d-segmenation

# Run automated installation
python utils/install.py

# Activate virtual environment
source .venv/bin/activate
```

### 3. Process Medical Images

```bash
# Place DICOM files in dicom/ folder
# Convert DICOM to NIfTI
python utils/dicom2nifti.py

# Run segmentation
python utils/segment.py

# Start the application
streamlit run app.py
```

## Port Forwarding (for Remote Access)

If accessing from a remote machine:

```bash
# SSH port forwarding
ssh -L 8501:localhost:8501 -L 8888:localhost:8888 <your_ssh_username>@<your_ssh_host>
```
