#!/usr/bin/env python3
"""
HPE NVIDIA Vista3D Remote Backend Setup Script

This script sets up the Vista3D backend for remote server deployment (Ubuntu with GPUs).
The frontend will run on a local Mac and connect via SSH tunnels.

Usage:
    python3 setup_backend_remote.py
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text: str) -> None:
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(70)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}\n")

def print_success(text: str) -> None:
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text: str) -> None:
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_warning(text: str) -> None:
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_info(text: str) -> None:
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")

def run_command(command: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command"""
    try:
        result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
        return result
    except subprocess.CalledProcessError as e:
        if check:
            print_error(f"Command failed: {command}")
            print_error(f"Error: {e}")
            sys.exit(1)
        return e

def check_system():
    """Check system requirements"""
    print_header("Checking System Requirements for Remote Backend")
    
    # Check OS
    system = platform.system().lower()
    if system == 'linux':
        print_success(f"OS: {platform.system()} {platform.release()}")
    else:
        print_error(f"This script is for Ubuntu/Linux servers. Detected: {platform.system()}")
        print_info("For Mac setup, use setup_frontend.py on your local Mac")
        sys.exit(1)
    
    # Check Docker
    result = run_command("docker --version", check=False)
    if result.returncode == 0:
        print_success(f"Docker: {result.stdout.strip()}")
    else:
        print_error("Docker not found - required for Vista3D")
        sys.exit(1)
    
    # Check NVIDIA GPU
    result = run_command("nvidia-smi", check=False)
    if result.returncode == 0:
        print_success("NVIDIA GPU: Detected")
        # Show GPU info
        lines = result.stdout.split('\n')
        for line in lines[:10]:  # First 10 lines have GPU info
            if 'NVIDIA' in line or 'GPU' in line or 'MiB' in line:
                print(f"  {line.strip()}")
    else:
        print_error("NVIDIA GPU not found - required for Vista3D")
        sys.exit(1)
    
    # Check NVIDIA Container Toolkit
    result = run_command("docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi", check=False)
    if result.returncode == 0:
        print_success("NVIDIA Container Toolkit: Working")
    else:
        print_error("NVIDIA Container Toolkit not working")
        print_info("Install from: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html")
        sys.exit(1)

def get_config():
    """Get configuration from user"""
    print_header("Remote Backend Configuration")
    
    config = {}
    
    # NGC API Key
    print_info("NVIDIA NGC API Key is required for Vista3D")
    print_info("Get your free API key at: https://ngc.nvidia.com/")
    while True:
        api_key = input("\nEnter your NVIDIA NGC API key (starts with 'nvapi-'): ").strip()
        if api_key.startswith('nvapi-'):
            config['NGC_API_KEY'] = api_key
            break
        else:
            print_error("API key must start with 'nvapi-'")
    
    # NGC Org ID (optional)
    org_id = input("\nEnter your NVIDIA Org ID (optional, press Enter to skip): ").strip()
    config['NGC_ORG_ID'] = org_id if org_id else ""
    
    # Output directory
    print_info("\nOutput directory (where Vista3D writes segmentation results)")
    default_output = os.path.abspath(os.path.join(os.getcwd(), "..", "output"))
    output_path = input(f"Output folder path [{default_output}]: ").strip()
    config['OUTPUT_FOLDER'] = output_path if output_path else default_output
    
    # DICOM directory
    print_info("\nDICOM directory (optional - you can serve files from Mac via SSH tunnel)")
    default_dicom = os.path.abspath(os.path.join(os.getcwd(), "..", "dicom"))
    dicom_path = input(f"DICOM folder path [{default_dicom}]: ").strip()
    config['DICOM_FOLDER'] = dicom_path if dicom_path else default_dicom
    
    # Set fixed values for remote setup
    config['VISTA3D_SERVER'] = "http://localhost:8000"
    config['IMAGE_SERVER'] = "http://localhost:8888"  # Will be SSH reverse tunnel from Mac
    config['VESSELS_OF_INTEREST'] = "all"
    
    return config

def create_directories(config):
    """Create necessary directories"""
    print_header("Creating Directories")
    
    for key in ['OUTPUT_FOLDER', 'DICOM_FOLDER']:
        path = config[key]
        try:
            os.makedirs(path, exist_ok=True)
            print_success(f"Created: {path}")
        except Exception as e:
            print_error(f"Failed to create {path}: {e}")

def create_env_file(config):
    """Create .env file"""
    print_header("Creating Environment Configuration")
    
    env_content = f"""# HPE NVIDIA Vista3D Remote Backend Configuration
# Generated by setup_backend_remote.py
# 
# This backend expects:
# - Frontend running on local Mac
# - SSH tunnels: -L 8000:localhost:8000 -R 8888:localhost:8888
# - Image server on Mac accessible via reverse tunnel at localhost:8888

# NVIDIA NGC Configuration
NGC_API_KEY="{config['NGC_API_KEY']}"
NGC_ORG_ID="{config['NGC_ORG_ID']}"

# Data Directories
DICOM_FOLDER="{config['DICOM_FOLDER']}"
OUTPUT_FOLDER="{config['OUTPUT_FOLDER']}"

# Server URLs
VISTA3D_SERVER="{config['VISTA3D_SERVER']}"
IMAGE_SERVER="{config['IMAGE_SERVER']}"

# Segmentation Settings
VESSELS_OF_INTEREST="{config['VESSELS_OF_INTEREST']}"

# Docker Configuration
COMPOSE_PROJECT_NAME=vista3d-backend
"""
    
    env_file = os.path.join(os.getcwd(), '.env')
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print_success(f"Created: {env_file}")
    except Exception as e:
        print_error(f"Failed to create .env file: {e}")

def pull_docker_image():
    """Pull Vista3D Docker image"""
    print_header("Pulling Vista3D Docker Image")
    
    image = "nvcr.io/nim/nvidia/vista3d:1.0.0"
    print_info(f"Pulling {image}...")
    print_info("This is a large image (~30GB) and may take considerable time...")
    print("")
    
    try:
        result = run_command(f"docker pull {image}", check=False)
        print("")
        if result.returncode == 0:
            print_success(f"Successfully pulled: {image}")
        else:
            print_error(f"Failed to pull: {image}")
            print_error(result.stderr)
    except Exception as e:
        print_error(f"Failed to pull {image}: {e}")

def create_startup_script():
    """Create startup script"""
    print_header("Creating Startup Script")
    
    script_content = '''#!/bin/bash
# HPE NVIDIA Vista3D Remote Backend Startup Script
# 
# This starts the Vista3D backend on the remote Ubuntu server
# The backend expects SSH tunnels from the Mac:
# - Forward tunnel: -L 8000:localhost:8000 (Mac can access backend)
# - Reverse tunnel: -R 8888:localhost:8888 (Backend can access Mac's image server)

set -e

echo "🚀 Starting Vista3D Remote Backend..."

# Check .env file
if [ ! -f ".env" ]; then
    echo "❌ .env file not found"
    exit 1
fi

# Check Docker
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running"
    exit 1
fi

# Check NVIDIA
if ! docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi > /dev/null 2>&1; then
    echo "⚠️  NVIDIA Container Toolkit may not be working"
fi

# Detect docker-compose command (V1 vs V2)
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo "❌ Docker Compose not found"
    exit 1
fi

# Start Vista3D
echo "🧠 Starting Vista3D server..."
$COMPOSE_CMD up -d

# Wait for service
echo "⏳ Waiting for Vista3D to be ready..."
sleep 10

# Check status
if docker ps | grep -q vista3d-server-standalone; then
    echo "✅ Vista3D server is running"
    echo "📊 Check logs: docker logs -f vista3d-server-standalone"
    echo ""
    echo "Next steps on your Mac:"
    echo "  1. Create SSH tunnel: ssh -L 8000:localhost:8000 -R 8888:localhost:8888 user@$(hostname)"
    echo "  2. Start image server: cd image_server && docker-compose up -d"
    echo "  3. Start frontend: cd frontend && streamlit run app.py"
    echo "  4. Open browser: http://localhost:8501"
else
    echo "❌ Vista3D server failed to start"
    echo "📊 Check logs: docker logs vista3d-server-standalone"
    exit 1
fi
'''
    
    script_path = os.path.join(os.getcwd(), 'start_remote_backend.sh')
    try:
        with open(script_path, 'w') as f:
            f.write(script_content)
        os.chmod(script_path, 0o755)
        print_success(f"Created: {script_path}")
    except Exception as e:
        print_error(f"Failed to create startup script: {e}")

def main():
    print_header("HPE NVIDIA Vista3D - Remote Backend Setup")
    print_info("This script configures Vista3D backend for remote Ubuntu server")
    print_info("Frontend will run on your local Mac with SSH tunnels")
    print("")
    
    # Check we're in the right directory
    if not os.path.exists('docker-compose.yml'):
        print_error("docker-compose.yml not found")
        print_info("Please run this script from the backend directory")
        sys.exit(1)
    
    # Check system
    check_system()
    
    # Get configuration
    config = get_config()
    
    # Create directories
    create_directories(config)
    
    # Create .env file
    create_env_file(config)
    
    # Pull Docker image
    response = input("\nPull Vista3D Docker image now? (y/N): ").strip().lower()
    if response in ['y', 'yes']:
        pull_docker_image()
    else:
        print_info("Skipping Docker image pull. Run 'docker-compose pull' later.")
    
    # Create startup script
    create_startup_script()
    
    # Final instructions
    print_header("Setup Complete!")
    print_success("Remote backend setup completed successfully!")
    print("")
    print_info("Configuration Summary:")
    print_info(f"  Output folder: {config['OUTPUT_FOLDER']}")
    print_info(f"  DICOM folder: {config['DICOM_FOLDER']}")
    print_info(f"  Vista3D server: {config['VISTA3D_SERVER']}")
    print_info(f"  Image server: {config['IMAGE_SERVER']} (via SSH tunnel)")
    print("")
    print_info("Next Steps:")
    print_info("  1. Start backend: ./start_remote_backend.sh")
    print_info("     Or manually: docker-compose up -d")
    print("")
    print_info("  2. On your Mac, setup SSH tunnel:")
    print_info(f"     ssh -L 8000:localhost:8000 -R 8888:localhost:8888 user@$(hostname)")
    print("")
    print_info("  3. On your Mac, setup and start frontend:")
    print_info("     cd frontend && python3 setup_frontend.py")
    print_info("     cd image_server && docker-compose up -d")
    print_info("     cd frontend && streamlit run app.py")
    print("")
    print_info("  4. Open browser on Mac: http://localhost:8501")
    print("")
    print_info("📚 See docs/REMOTE_BACKEND_SETUP.md for detailed instructions")

if __name__ == "__main__":
    main()

