#!/usr/bin/env python3
"""
HPE NVIDIA Vista3D Image Server Setup Script

This script sets up the image server service including:
- System requirements validation
- Docker verification
- Environment configuration
- Directory structure creation
- Docker Hub image management
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
        # Return a CompletedProcess object with the error information
        return subprocess.CompletedProcess(
            args=command,
            returncode=e.returncode,
            stdout=e.stdout if hasattr(e, 'stdout') else '',
            stderr=e.stderr if hasattr(e, 'stderr') else str(e)
        )

def check_docker_hub_image() -> bool:
    """Check if Docker Hub image is available and pull it"""
    print_header("Checking Docker Hub Image")
    
    image = 'dwtwp/vista3d-image-server:latest'
    print_info(f"Checking image server image: {image}")
    
    # Check if image exists locally first
    try:
        result = run_command(f"docker image inspect {image}", capture_output=True)
        if result.returncode == 0:
            print_success(f"Image server image found locally: {image}")
            return True
    except:
        pass
    
    # Try to pull from Docker Hub
    try:
        print_info(f"Pulling {image} from Docker Hub...")
        result = run_command(f"docker pull {image}", capture_output=True)
        if result.returncode == 0:
            print_success(f"Successfully pulled {image}")
            return True
        else:
            print_warning(f"Failed to pull {image}: {result.stderr}")
            return False
    except Exception as e:
        print_warning(f"Failed to pull {image}: {e}")
        return False

def check_system_requirements() -> Dict[str, bool]:
    """Check if system meets requirements"""
    print_header("Checking System Requirements")
    
    requirements = {
        'os': False,
        'python': False,
        'docker': False,
        'memory': False,
        'disk_space': False
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
    
    # Check memory
    try:
        if system == 'linux':
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
            for line in meminfo.split('\n'):
                if 'MemTotal' in line:
                    mem_kb = int(line.split()[1])
                    mem_gb = mem_kb / 1024 / 1024
                    if mem_gb >= 4:
                        requirements['memory'] = True
                        print_success(f"Memory: {mem_gb:.1f} GB")
                    else:
                        print_warning(f"Memory: {mem_gb:.1f} GB (Recommended: 4+ GB)")
                    break
        elif system == 'darwin':
            result = run_command("sysctl hw.memsize", capture_output=True)
            if result.returncode == 0:
                mem_bytes = int(result.stdout.split()[1])
                mem_gb = mem_bytes / 1024 / 1024 / 1024
                if mem_gb >= 4:
                    requirements['memory'] = True
                    print_success(f"Memory: {mem_gb:.1f} GB")
                else:
                    print_warning(f"Memory: {mem_gb:.1f} GB (Recommended: 4+ GB)")
    except:
        print_warning("Could not check memory")
    
    # Check disk space
    try:
        result = run_command("df -h .", capture_output=True)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            for line in lines[1:]:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 4:
                        available = parts[3]
                        if 'G' in available:
                            gb = float(available.replace('G', ''))
                            if gb >= 2:
                                requirements['disk_space'] = True
                                print_success(f"Disk space: {available} available")
                            else:
                                print_warning(f"Disk space: {available} (Recommended: 2+ GB)")
                            break
    except:
        print_warning("Could not check disk space")
    
    return requirements

def get_user_input() -> Dict[str, str]:
    """Get configuration using defaults"""
    print_header("Configuration Setup")
    print_info("Using default configuration values")
    
    config = {}
    
    # Check if .env file exists from master setup
    master_env = os.path.join(os.getcwd(), "..", ".env")
    if os.path.exists(master_env):
        print_info("Found master .env file, using existing configuration")
        try:
            with open(master_env, 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        # Remove quotes from value
                        value = value.strip('"')
                        config[key] = value
        except Exception as e:
            print_warning(f"Failed to read master .env file: {e}")
    
    # Use defaults for missing fields
    if not config.get('DICOM_FOLDER'):
        config['DICOM_FOLDER'] = os.path.abspath(os.path.join(os.getcwd(), "..", "dicom"))
    
    if not config.get('OUTPUT_FOLDER'):
        config['OUTPUT_FOLDER'] = os.path.abspath(os.path.join(os.getcwd(), "..", "output"))
    
    if not config.get('IMAGE_SERVER_PORT'):
        config['IMAGE_SERVER_PORT'] = "8888"
    
    # Set default values for other required fields
    config['IMAGE_SERVER'] = f"http://localhost:{config['IMAGE_SERVER_PORT']}"
    
    print_success(f"DICOM folder: {config['DICOM_FOLDER']}")
    print_success(f"Output folder: {config['OUTPUT_FOLDER']}")
    print_success(f"Image server port: {config['IMAGE_SERVER_PORT']}")
    
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
    
    env_content = f"""# HPE NVIDIA Vista3D Image Server Configuration
# Generated by setup_image_server.py

# Data Directories
DICOM_FOLDER="{config['DICOM_FOLDER']}"
OUTPUT_FOLDER="{config['OUTPUT_FOLDER']}"

# Server URLs
IMAGE_SERVER="{config['IMAGE_SERVER']}"

# Ports
IMAGE_SERVER_PORT="{config['IMAGE_SERVER_PORT']}"

# Docker Configuration
COMPOSE_PROJECT_NAME=vista3d-image-server

# Docker Hub Images
IMAGE_SERVER_IMAGE=dwtwp/vista3d-image-server:latest
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
    
    return True

def update_docker_compose(config: Dict[str, str]) -> None:
    """Update docker-compose.yml with user configuration"""
    print_header("Updating Docker Compose Configuration")
    
    compose_file = os.path.join(os.getcwd(), 'docker-compose.yml')
    
    if not os.path.exists(compose_file):
        print_error("docker-compose.yml not found")
        return
    
    try:
        with open(compose_file, 'r') as f:
            content = f.read()
        
        # Update ports and image
        content = content.replace('"8888:8888"', f'"{config["IMAGE_SERVER_PORT"]}:8888"')
        content = content.replace('image: vista3d-image-server:local', 'image: dwtwp/vista3d-image-server:latest')
        
        with open(compose_file, 'w') as f:
            f.write(content)
        
        print_success("Updated docker-compose.yml with user configuration")
    except Exception as e:
        print_error(f"Failed to update docker-compose.yml: {e}")

def build_docker_image(image_available: bool) -> None:
    """Build Docker image only if Docker Hub image is not available"""
    print_header("Building Docker Image")
    
    if not image_available:
        print_info("Building image server image locally...")
        try:
            result = run_command("docker build -t vista3d-image-server:local .", capture_output=True)
            if result.returncode == 0:
                print_success("Image server image built successfully")
            else:
                print_error("Failed to build image server image")
                print_error(result.stderr)
        except Exception as e:
            print_error(f"Failed to build image server image: {e}")
    else:
        print_success("Using Docker Hub image server image, skipping local build")

def create_startup_script() -> None:
    """Create a startup script for the image server"""
    print_header("Creating Startup Script")
    
    startup_script = """#!/bin/bash
# HPE NVIDIA Vista3D Image Server Startup Script

set -e

echo "🚀 Starting HPE NVIDIA Vista3D Image Server..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please run setup_image_server.py first."
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if required image exists, pull from Docker Hub if needed
echo "🔍 Checking Docker Hub image..."

# Check image server image
if ! docker image inspect ${IMAGE_SERVER_IMAGE:-dwtwp/vista3d-image-server:latest} > /dev/null 2>&1; then
    echo "📥 Pulling image server image from Docker Hub..."
    if ! docker pull ${IMAGE_SERVER_IMAGE:-dwtwp/vista3d-image-server:latest}; then
        echo "❌ Failed to pull image server image. Please check your internet connection and Docker Hub access."
        exit 1
    fi
fi

# Start the image server
echo "🖼️  Starting image server..."
docker-compose up -d

# Wait for the service to be ready
echo "⏳ Waiting for image server to be ready..."
sleep 10

# Check if the service is running
if docker ps | grep -q vista3d-image-server-standalone; then
    echo "✅ Image server is running on http://localhost:${IMAGE_SERVER_PORT:-8888}"
else
    echo "❌ Image server failed to start"
    echo "📊 Check logs with: docker logs vista3d-image-server-standalone"
    exit 1
fi

echo "🎉 Image server setup complete!"
echo "🖼️  Image Server: http://localhost:${IMAGE_SERVER_PORT:-8888}"
echo "📊 Check logs with: docker-compose logs -f"
"""
    
    script_path = os.path.join(os.getcwd(), 'start_image_server.sh')
    try:
        with open(script_path, 'w') as f:
            f.write(startup_script)
        os.chmod(script_path, 0o755)
        print_success(f"Created: {script_path}")
    except Exception as e:
        print_error(f"Failed to create startup script: {e}")

def create_stop_script() -> None:
    """Create a stop script for the image server"""
    print_header("Creating Stop Script")
    
    stop_script = """#!/bin/bash
# HPE NVIDIA Vista3D Image Server Stop Script

echo "🛑 Stopping HPE NVIDIA Vista3D Image Server..."

# Stop the image server
docker-compose down

echo "✅ Image server stopped"
"""
    
    script_path = os.path.join(os.getcwd(), 'stop_image_server.sh')
    try:
        with open(script_path, 'w') as f:
            f.write(stop_script)
        os.chmod(script_path, 0o755)
        print_success(f"Created: {script_path}")
    except Exception as e:
        print_error(f"Failed to create stop script: {e}")

def create_logs_script() -> None:
    """Create a logs viewing script"""
    print_header("Creating Logs Script")
    
    logs_script = """#!/bin/bash
# HPE NVIDIA Vista3D Image Server Logs Script

echo "📊 Viewing HPE NVIDIA Vista3D Image Server logs..."

# Show logs for image server
echo "🖼️  Image server logs:"
docker-compose logs -f --tail=50
"""
    
    script_path = os.path.join(os.getcwd(), 'logs_image_server.sh')
    try:
        with open(script_path, 'w') as f:
            f.write(logs_script)
        os.chmod(script_path, 0o755)
        print_success(f"Created: {script_path}")
    except Exception as e:
        print_error(f"Failed to create logs script: {e}")

def main():
    """Main setup function"""
    print_header("HPE NVIDIA Vista3D Image Server Setup")
    print_info("This script will set up the image server service")
    
    # Check if we're in the right directory
    if not os.path.exists('docker-compose.yml'):
        print_error("docker-compose.yml not found. Please run this script from the image_server directory.")
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
    optional_requirements = ['memory', 'disk_space']
    missing_optional = [req for req in optional_requirements if not requirements[req]]
    
    if missing_optional:
        print_warning(f"Missing optional requirements: {', '.join(missing_optional)}")
        print_info("Image server may not work properly without these requirements.")
        
        response = input("Continue anyway? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print_info("Setup cancelled.")
            sys.exit(0)
    
    # Check Docker Hub image
    image_available = check_docker_hub_image()
    
    # Get user configuration
    config = get_user_input()
    
    # Create directories
    create_directories(config)
    
    # Create .env file
    create_env_file(config)
    
    # Verify Docker setup
    if not verify_docker_setup():
        print_warning("Docker setup verification failed, but continuing...")
    
    # Update docker-compose.yml
    update_docker_compose(config)
    
    # Build Docker image only if Docker Hub image is not available
    build_docker_image(image_available)
    
    # Create management scripts
    create_startup_script()
    create_stop_script()
    create_logs_script()
    
    # Final instructions
    print_header("Setup Complete!")
    print_success("Image server setup completed successfully!")
    print_info("Next steps:")
    print_info("1. Start the image server: ./start_image_server.sh")
    print_info("2. Or use Docker Compose: docker-compose up -d")
    print_info("3. Stop service: ./stop_image_server.sh")
    print_info("4. View logs: ./logs_image_server.sh")
    print_info(f"5. Access image server: http://localhost:{config['IMAGE_SERVER_PORT']}")
    
    print_info("\nConfiguration saved to .env file")
    print_info(f"DICOM folder: {config['DICOM_FOLDER']}")
    print_info(f"Output folder: {config['OUTPUT_FOLDER']}")
    print_info(f"Image server: {config['IMAGE_SERVER']}")

if __name__ == "__main__":
    main()
