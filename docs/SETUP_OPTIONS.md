# 🚀 HPE NVIDIA Vista3D - Setup Options Guide

This guide explains the different setup options available for the HPE NVIDIA Vista3D platform.

## Overview

The `setup.py` script provides flexible installation options to accommodate different deployment scenarios and system configurations.

## Available Setup Options

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

## Additional Options

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

## Deployment Scenarios

### Scenario 1: Single GPU Machine
```bash
# Complete setup on one machine
python3 setup.py
./start_all.sh
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
cd backend && ./start_backend.sh
```

### Scenario 3: Backend API Server
```bash
# On GPU server
python3 setup.py --setup backend
cd backend && ./start_backend.sh

# Frontend machines connect to API
```

### Scenario 4: Development Environment
```bash
# Check requirements first
python3 setup.py --check-only

# Setup with custom config
python3 setup.py --config-file dev_config.env
```

## Configuration Requirements

### Backend Setup Requirements
- **NVIDIA NGC API Key**: Required (starts with 'nvapi-')
- **NVIDIA Org ID**: Optional
- **GPU**: Required for Vista3D processing
- **Memory**: 16GB+ RAM recommended

### Frontend Setup Requirements
- **NVIDIA NGC API Key**: Not required
- **Remote Vista3D**: Must be accessible via network
- **Memory**: 8GB+ RAM minimum
- **GPU**: Not required

## Management After Setup

### Full Platform Management
```bash
# Start all services
./start_all.sh

# Stop all services
./stop_all.sh

# Check status
./status.sh
```

### Individual Service Management
```bash
# Backend only
cd backend && ./start_backend.sh

# Frontend only
cd frontend
# Start image server first
cd ../image_server && docker-compose up -d
# Start frontend
cd ../frontend && docker-compose up -d
```

## Troubleshooting

### Frontend-Only Setup Issues
- Ensure remote Vista3D server is accessible
- Check network connectivity
- Verify port forwarding if using SSH tunnels

### Backend-Only Setup Issues
- Verify GPU availability with `nvidia-smi`
- Check NVIDIA Container Toolkit installation
- Validate NGC API key format

### Mixed Setup Issues
- Ensure consistent configuration across machines
- Check network connectivity between services
- Verify port availability

## Best Practices

1. **Use `--check-only` first** to validate system requirements
2. **Frontend-only** for non-GPU systems connecting to remote Vista3D
3. **Backend-only** for GPU servers providing API services
4. **Full setup** for complete single-machine deployments
5. **Use configuration files** for consistent deployments across environments

## Examples

### Quick Frontend Setup
```bash
# Check if system is suitable
python3 setup.py --setup frontend --check-only

# Setup frontend only
python3 setup.py --setup frontend

# Start frontend services
cd frontend
# Start image server first
cd ../image_server && docker-compose up -d
# Start frontend
cd ../frontend && docker-compose up -d
```

### Automated Backend Setup
```bash
# Create config file
cat > backend_config.env << EOF
NGC_API_KEY=nvapi-your-key-here
NGC_ORG_ID=your-org-id
VISTA3D_SERVER=http://localhost:8000
DICOM_FOLDER=/data/dicom
OUTPUT_FOLDER=/data/output
EOF

# Setup with config file
python3 setup.py --setup backend --config-file backend_config.env
```

### Development Setup
```bash
# Check requirements
python3 setup.py --check-only

# Setup with non-interactive mode
python3 setup.py --non-interactive --setup both
```

---

**Need Help?** Run `python3 setup.py --help` for detailed information about all available options.
