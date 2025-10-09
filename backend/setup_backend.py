#!/usr/bin/env python3
"""
HPE NVIDIA Vista3D Backend Setup Script

This script sets up the Vista3D backend service including:
- System requirements validation
- Docker and NVIDIA Container Toolkit verification
- Environment configuration
- Directory structure creation
- Docker image preparation
"""

import os
import sys
import subprocess
import shutil
import platform
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_header(text: str) -> None:
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}\n")

def print_success(text: str) -> None:
    """Print success message"""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text: str) -> None:
    """Print error message"""
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_warning(text: str) -> None:
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_info(text: str) -> None:
    """Print info message"""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")

def run_command(command: str, check: bool = True, capture_output: bool = False) -> subprocess.CompletedProcess:
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=check, 
            capture_output=capture_output,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        if check:
            print_error(f"Command failed: {command}")
            print_error(f"Error: {e}")
            sys.exit(1)
        return e

def check_system_requirements() -> Dict[str, bool]:
    """Check if system meets requirements"""
    print_header("Checking System Requirements")
    
    requirements = {
        'os': False,
        'python': False,
        'docker': False,
        'nvidia_docker': False,
        'gpu': False,
        'memory': False
    }
    
    # Check OS
    system = platform.system().lower()
    if system in ['linux', 'darwin']:
        requirements['os'] = True
        print_success(f"OS: {platform.system()} {platform.release()}")
    else:
        print_error(f"Unsupported OS: {platform.system()}")
        print_info("Supported: Ubuntu Linux (18.04+) or macOS")
    
    # Check Python version
    python_version = sys.version_info
    if python_version >= (3, 8):
        requirements['python'] = True
        print_success(f"Python: {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        print_error(f"Python {python_version.major}.{python_version.minor} is too old")
        print_info("Required: Python 3.8+")
    
    # Check Docker
    try:
        result = run_command("docker --version", capture_output=True)
        if result.returncode == 0:
            requirements['docker'] = True
            print_success(f"Docker: {result.stdout.strip()}")
        else:
            print_error("Docker not found")
    except:
        print_error("Docker not found")
        print_info("Install Docker from: https://docs.docker.com/get-docker/")
    
    # Check NVIDIA Container Toolkit
    try:
        result = run_command("docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu22.04 nvidia-smi", capture_output=True)
        if result.returncode == 0:
            requirements['nvidia_docker'] = True
            print_success("NVIDIA Container Toolkit: Working")
        else:
            print_warning("NVIDIA Container Toolkit: Not working")
            print_info("Install from: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html")
    except:
        print_warning("NVIDIA Container Toolkit: Not working")
    
    # Check GPU
    try:
        result = run_command("nvidia-smi", capture_output=True)
        if result.returncode == 0:
            requirements['gpu'] = True
            print_success("NVIDIA GPU: Detected")
            # Parse GPU memory
            lines = result.stdout.split('\n')
            for line in lines:
                if 'MiB' in line and 'Memory' in line:
                    print_info(f"GPU Memory: {line.strip()}")
        else:
            print_warning("NVIDIA GPU: Not detected")
    except:
        print_warning("NVIDIA GPU: Not detected")
    
    # Check memory
    try:
        if system == 'linux':
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
            for line in meminfo.split('\n'):
                if 'MemTotal' in line:
                    mem_kb = int(line.split()[1])
                    mem_gb = mem_kb / 1024 / 1024
                    if mem_gb >= 16:
                        requirements['memory'] = True
                        print_success(f"Memory: {mem_gb:.1f} GB")
                    else:
                        print_warning(f"Memory: {mem_gb:.1f} GB (Recommended: 16+ GB)")
                    break
        elif system == 'darwin':
            result = run_command("sysctl hw.memsize", capture_output=True)
            if result.returncode == 0:
                mem_bytes = int(result.stdout.split()[1])
                mem_gb = mem_bytes / 1024 / 1024 / 1024
                if mem_gb >= 16:
                    requirements['memory'] = True
                    print_success(f"Memory: {mem_gb:.1f} GB")
                else:
                    print_warning(f"Memory: {mem_gb:.1f} GB (Recommended: 16+ GB)")
    except:
        print_warning("Could not check memory")
    
    return requirements

def get_user_input() -> Dict[str, str]:
    """Get configuration from user"""
    print_header("Backend Configuration Setup")
    
    config = {}
    
    # Get NVIDIA NGC API key
    print_info("NVIDIA NGC API Key is required for Vista3D access")
    print_info("Get your free API key at: https://ngc.nvidia.com/")
    while True:
        api_key = input("Enter your NVIDIA NGC API key (starts with 'nvapi-'): ").strip()
        if api_key.startswith('nvapi-'):
            config['NGC_API_KEY'] = api_key
            break
        else:
            print_error("API key must start with 'nvapi-'")
    
    # Get NVIDIA Org ID
    org_id = input("Enter your NVIDIA Org ID (optional, press Enter to skip): ").strip()
    if org_id:
        config['NGC_ORG_ID'] = org_id
    else:
        config['NGC_ORG_ID'] = ""
    
    # Get output directory (where Vista3D will write results)
    print_info("Output directory (where Vista3D will write segmentation results)")
    default_output = os.path.join(os.getcwd(), "..", "output")
    output_path = input(f"Output folder path [{default_output}]: ").strip()
    if not output_path:
        output_path = default_output
    config['OUTPUT_FOLDER'] = os.path.abspath(output_path)
    
    # Get image server URL (where Vista3D can access images)
    image_server_url = input("Image server URL [http://localhost:8888]: ").strip()
    if not image_server_url:
        image_server_url = "http://localhost:8888"
    config['IMAGE_SERVER'] = image_server_url
    
    # Segmentation settings
    vessels = input("Vessels of interest [all]: ").strip()
    if not vessels:
        vessels = "all"
    config['VESSELS_OF_INTEREST'] = vessels
    
    # Set default values for other required fields
    config['VISTA3D_SERVER'] = "http://localhost:8000"
    config['DICOM_FOLDER'] = os.path.join(os.getcwd(), "..", "dicom")
    
    return config

def create_directories(config: Dict[str, str]) -> None:
    """Create necessary directories"""
    print_header("Creating Directory Structure")
    
    directories = [
        config['DICOM_FOLDER'],
        config['OUTPUT_FOLDER']
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print_success(f"Created: {directory}")
        except Exception as e:
            print_error(f"Failed to create {directory}: {e}")

def create_env_file(config: Dict[str, str]) -> None:
    """Create .env file with configuration"""
    print_header("Creating Environment Configuration")
    
    env_content = f"""# HPE NVIDIA Vista3D Backend Configuration
# Generated by setup_backend.py

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

def verify_docker_setup() -> bool:
    """Verify Docker is properly configured"""
    print_header("Verifying Docker Setup")
    
    # Check if Docker daemon is running
    try:
        result = run_command("docker info", capture_output=True)
        if result.returncode != 0:
            print_error("Docker daemon is not running")
            return False
        print_success("Docker daemon is running")
    except:
        print_error("Docker daemon is not running")
        return False
    
    # Check NVIDIA Container Toolkit
    try:
        result = run_command("docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu22.04 nvidia-smi", capture_output=True)
        if result.returncode == 0:
            print_success("NVIDIA Container Toolkit is working")
            return True
        else:
            print_warning("NVIDIA Container Toolkit may not be working properly")
            return False
    except:
        print_warning("NVIDIA Container Toolkit may not be working properly")
        return False

def pull_docker_images() -> None:
    """Pull required Docker images"""
    print_header("Pulling Docker Images")
    
    images = [
        "nvcr.io/nim/nvidia/vista3d:1.0.0"
    ]
    
    for image in images:
        print_info(f"Pulling {image}...")
        print_info("This may take a considerable amount of time depending on your internet connection...")
        print_info("The Vista3D image is approximately 30GB in size")
        print("")
        try:
            # Don't capture output so users can see Docker's progress bars
            result = run_command(f"docker pull {image}", capture_output=False)
            print("")  # Add blank line after Docker output
            if result.returncode == 0:
                print_success(f"Successfully pulled: {image}")
            else:
                print_error(f"Failed to pull: {image}")
        except Exception as e:
            print_error(f"Failed to pull {image}: {e}")

def create_startup_script() -> None:
    """Create a startup script for the backend"""
    print_header("Creating Startup Script")
    
    startup_script = """#!/bin/bash
# HPE NVIDIA Vista3D Backend Startup Script

set -e

echo "🚀 Starting HPE NVIDIA Vista3D Backend..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please run setup_backend.py first."
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if NVIDIA Container Toolkit is working
if ! docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu22.04 nvidia-smi > /dev/null 2>&1; then
    echo "⚠️  NVIDIA Container Toolkit may not be working properly."
    echo "   Vista3D may not start correctly."
fi

# Start the Vista3D server
echo "🧠 Starting Vista3D server..."
docker-compose up -d

# Wait for the service to be ready
echo "⏳ Waiting for Vista3D server to be ready..."
sleep 10

# Check if the service is running
if docker ps | grep -q vista3d-server-standalone; then
    echo "✅ Vista3D server is running on http://localhost:8000"
    echo "📊 Check logs with: docker logs -f vista3d-server-standalone"
else
    echo "❌ Vista3D server failed to start"
    echo "📊 Check logs with: docker logs vista3d-server-standalone"
    exit 1
fi

echo "🎉 Backend setup complete!"
echo "🌐 Vista3D API: http://localhost:8000"
echo "📚 API docs: http://localhost:8000/docs"
"""
    
    script_path = os.path.join(os.getcwd(), 'start_backend.sh')
    try:
        with open(script_path, 'w') as f:
            f.write(startup_script)
        os.chmod(script_path, 0o755)
        print_success(f"Created: {script_path}")
    except Exception as e:
        print_error(f"Failed to create startup script: {e}")

def main():
    """Main setup function"""
    print_header("HPE NVIDIA Vista3D Backend Setup")
    print_info("This script will set up the Vista3D backend service")
    
    # Check if we're in the right directory
    if not os.path.exists('docker-compose.yml'):
        print_error("docker-compose.yml not found. Please run this script from the backend directory.")
        sys.exit(1)
    
    # Check system requirements
    requirements = check_system_requirements()
    
    # Check critical requirements
    critical_requirements = ['os', 'python', 'docker']
    missing_critical = [req for req in critical_requirements if not requirements[req]]
    
    if missing_critical:
        print_error(f"Missing critical requirements: {', '.join(missing_critical)}")
        print_info("Please install the missing requirements and run the script again.")
        sys.exit(1)
    
    # Warn about optional requirements
    optional_requirements = ['nvidia_docker', 'gpu', 'memory']
    missing_optional = [req for req in optional_requirements if not requirements[req]]
    
    if missing_optional:
        print_warning(f"Missing optional requirements: {', '.join(missing_optional)}")
        print_info("Vista3D may not work properly without these requirements.")
        
        response = input("Continue anyway? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print_info("Setup cancelled.")
            sys.exit(0)
    
    # Get user configuration
    config = get_user_input()
    
    # Create directories
    create_directories(config)
    
    # Create .env file
    create_env_file(config)
    
    # Verify Docker setup
    if not verify_docker_setup():
        print_warning("Docker setup verification failed, but continuing...")
    
    # Pull Docker images
    pull_docker_images()
    
    # Create startup script
    create_startup_script()
    
    # Final instructions
    print_header("Setup Complete!")
    print_success("Backend setup completed successfully!")
    print_info("Next steps:")
    print_info("1. Start the backend: ./start_backend.sh")
    print_info("2. Or use Docker Compose: docker-compose up -d")
    print_info("3. Check logs: docker logs -f vista3d-server-standalone")
    print_info("4. Test API: curl http://localhost:8000/v1/vista3d/info")
    print_info("5. View API docs: http://localhost:8000/docs")
    
    print_info("\nConfiguration saved to .env file")
    print_info(f"DICOM folder: {config['DICOM_FOLDER']}")
    print_info(f"Output folder: {config['OUTPUT_FOLDER']}")
    print_info(f"Vista3D server: {config['VISTA3D_SERVER']}")

if __name__ == "__main__":
    main()
