#!/usr/bin/env python3
"""
HPE NVIDIA Vista3D Frontend Setup Script

This script sets up the frontend services including:
- System requirements validation
- Docker verification
- Environment configuration
- Directory structure creation
- Docker image building
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
                    if mem_gb >= 8:
                        requirements['memory'] = True
                        print_success(f"Memory: {mem_gb:.1f} GB")
                    else:
                        print_warning(f"Memory: {mem_gb:.1f} GB (Recommended: 8+ GB)")
                    break
        elif system == 'darwin':
            result = run_command("sysctl hw.memsize", capture_output=True)
            if result.returncode == 0:
                mem_bytes = int(result.stdout.split()[1])
                mem_gb = mem_bytes / 1024 / 1024 / 1024
                if mem_gb >= 8:
                    requirements['memory'] = True
                    print_success(f"Memory: {mem_gb:.1f} GB")
                else:
                    print_warning(f"Memory: {mem_gb:.1f} GB (Recommended: 8+ GB)")
    except:
        print_warning("Could not check memory")
    
    # Check disk space
    try:
        if system == 'linux':
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
                                if gb >= 5:
                                    requirements['disk_space'] = True
                                    print_success(f"Disk space: {available} available")
                                else:
                                    print_warning(f"Disk space: {available} (Recommended: 5+ GB)")
                            break
        elif system == 'darwin':
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
                                if gb >= 5:
                                    requirements['disk_space'] = True
                                    print_success(f"Disk space: {available} available")
                                else:
                                    print_warning(f"Disk space: {available} (Recommended: 5+ GB)")
                            break
    except:
        print_warning("Could not check disk space")
    
    return requirements

def get_user_input() -> Dict[str, str]:
    """Get configuration from user"""
    print_header("Frontend Configuration Setup")
    
    config = {}
    
    # Get data directories
    print_info("Data directories (use absolute paths for best results)")
    
    # DICOM folder
    default_dicom = os.path.join(os.getcwd(), "..", "dicom")
    dicom_path = input(f"DICOM folder path [{default_dicom}]: ").strip()
    if not dicom_path:
        dicom_path = default_dicom
    config['DICOM_FOLDER'] = os.path.abspath(dicom_path)
    
    # Output folder
    default_output = os.path.join(os.getcwd(), "..", "output")
    output_path = input(f"Output folder path [{default_output}]: ").strip()
    if not output_path:
        output_path = default_output
    config['OUTPUT_FOLDER'] = os.path.abspath(output_path)
    
    # Vista3D server URL (where frontend will connect to)
    vista3d_url = input("Vista3D server URL [http://localhost:8000]: ").strip()
    if not vista3d_url:
        vista3d_url = "http://localhost:8000"
    config['VISTA3D_SERVER'] = vista3d_url
    
    # Frontend port
    frontend_port = input("Frontend port [8501]: ").strip()
    if not frontend_port:
        frontend_port = "8501"
    config['FRONTEND_PORT'] = frontend_port
    
    # Image server port
    img_port = input("Image server port [8888]: ").strip()
    if not img_port:
        img_port = "8888"
    config['IMAGE_SERVER_PORT'] = img_port
    
    # Set default values for other required fields
    config['IMAGE_SERVER'] = f"http://localhost:{img_port}"
    
    return config

def create_directories(config: Dict[str, str]) -> None:
    """Create necessary directories"""
    print_header("Creating Directory Structure")
    
    directories = [
        config['DICOM_FOLDER'],
        config['OUTPUT_FOLDER'],
        os.path.join(config['OUTPUT_FOLDER'], 'nifti'),
        os.path.join(config['OUTPUT_FOLDER'], 'scans'),
        os.path.join(config['OUTPUT_FOLDER'], 'voxels'),
        os.path.join(config['OUTPUT_FOLDER'], 'models'),
        os.path.join(config['OUTPUT_FOLDER'], 'logs')
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
    
    env_content = f"""# HPE NVIDIA Vista3D Frontend Configuration
# Generated by setup_frontend.py

# Data Directories
DICOM_FOLDER="{config['DICOM_FOLDER']}"
OUTPUT_FOLDER="{config['OUTPUT_FOLDER']}"

# Server URLs
VISTA3D_SERVER="{config['VISTA3D_SERVER']}"
IMAGE_SERVER="{config['IMAGE_SERVER']}"

# Ports
FRONTEND_PORT="{config['FRONTEND_PORT']}"
IMAGE_SERVER_PORT="{config['IMAGE_SERVER_PORT']}"

# Docker Configuration
COMPOSE_PROJECT_NAME=vista3d-frontend
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

def setup_image_server(config: Dict[str, str]) -> None:
    """Set up the image server service"""
    print_header("Setting Up Image Server")
    
    image_server_dir = os.path.join(os.getcwd(), "..", "image_server")
    
    if not os.path.exists(image_server_dir):
        print_error("Image server directory not found")
        return
    
    # Create .env file for image server
    image_server_env = os.path.join(image_server_dir, '.env')
    env_content = f"""# HPE NVIDIA Vista3D Image Server Configuration
# Generated by setup_frontend.py

# Data Directories
DICOM_FOLDER="{config['DICOM_FOLDER']}"
OUTPUT_FOLDER="{config['OUTPUT_FOLDER']}"

# Server URLs
IMAGE_SERVER="{config['IMAGE_SERVER']}"

# Ports
IMAGE_SERVER_PORT="{config['IMAGE_SERVER_PORT']}"

# Docker Configuration
COMPOSE_PROJECT_NAME=vista3d-image-server
"""
    
    try:
        with open(image_server_env, 'w') as f:
            f.write(env_content)
        print_success(f"Created image server .env: {image_server_env}")
    except Exception as e:
        print_error(f"Failed to create image server .env: {e}")
    
    # Update image server docker-compose.yml with user configuration
    compose_file = os.path.join(image_server_dir, 'docker-compose.yml')
    if os.path.exists(compose_file):
        try:
            with open(compose_file, 'r') as f:
                content = f.read()
            
            # Update ports
            content = content.replace('"8888:8888"', f'"{config["IMAGE_SERVER_PORT"]}:8888"')
            
            with open(compose_file, 'w') as f:
                f.write(content)
            
            print_success("Updated image server docker-compose.yml")
        except Exception as e:
            print_error(f"Failed to update image server docker-compose.yml: {e}")

def build_docker_images() -> None:
    """Build required Docker images"""
    print_header("Building Docker Images")
    
    # Build frontend image
    print_info("Building frontend image...")
    try:
        result = run_command("docker build -t vista3d-frontend:local .", capture_output=True)
        if result.returncode == 0:
            print_success("Frontend image built successfully")
        else:
            print_error("Failed to build frontend image")
            print_error(result.stderr)
    except Exception as e:
        print_error(f"Failed to build frontend image: {e}")
    
    # Build image server image
    print_info("Building image server image...")
    try:
        image_server_dir = os.path.join(os.getcwd(), "..", "image_server")
        if os.path.exists(image_server_dir):
            result = run_command(f"docker build -t vista3d-image-server:local {image_server_dir}", capture_output=True)
            if result.returncode == 0:
                print_success("Image server image built successfully")
            else:
                print_error("Failed to build image server image")
                print_error(result.stderr)
        else:
            print_warning("Image server directory not found, skipping image server build")
    except Exception as e:
        print_error(f"Failed to build image server image: {e}")

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
        
        # Update ports
        content = content.replace('"8501:8501"', f'"{config["FRONTEND_PORT"]}:8501"')
        content = content.replace('"8888:8888"', f'"{config["IMAGE_SERVER_PORT"]}:8888"')
        
        with open(compose_file, 'w') as f:
            f.write(content)
        
        print_success("Updated docker-compose.yml with user configuration")
    except Exception as e:
        print_error(f"Failed to update docker-compose.yml: {e}")

def create_startup_script() -> None:
    """Create a startup script for the frontend"""
    print_header("Creating Startup Script")
    
    startup_script = """#!/bin/bash
# HPE NVIDIA Vista3D Frontend Startup Script

set -e

echo "🚀 Starting HPE NVIDIA Vista3D Frontend (Development Mode)..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please run setup_frontend.py first."
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if required images exist
if ! docker image inspect vista3d-frontend:local > /dev/null 2>&1; then
    echo "❌ Frontend image not found. Please run setup_frontend.py first."
    exit 1
fi

if ! docker image inspect vista3d-image-server:local > /dev/null 2>&1; then
    echo "❌ Image server image not found. Please run setup_frontend.py first."
    exit 1
fi

# Start the image server first
echo "🖼️  Starting image server..."
cd ../image_server
if [ -f "docker-compose.yml" ]; then
    docker-compose up -d
    echo "✅ Image server started"
else
    echo "❌ Image server docker-compose.yml not found"
    exit 1
fi
cd ../frontend

# Start the frontend services
echo "🌐 Starting frontend services..."
docker-compose up -d

# Wait for the services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 15

# Check if the services are running
if docker ps | grep -q vista3d-frontend-standalone; then
    echo "✅ Frontend is running on http://localhost:${FRONTEND_PORT:-8501}"
    echo "🔄 Development mode: Code changes will auto-reload"
else
    echo "❌ Frontend failed to start"
    echo "📊 Check logs with: docker logs vista3d-frontend-standalone"
    exit 1
fi

if docker ps | grep -q vista3d-image-server-standalone; then
    echo "✅ Image server is running on http://localhost:${IMAGE_SERVER_PORT:-8888}"
else
    echo "❌ Image server failed to start"
    echo "📊 Check logs with: docker logs vista3d-image-server-standalone"
    exit 1
fi

echo "🎉 Frontend setup complete!"
echo "🌐 Web Interface: http://localhost:${FRONTEND_PORT:-8501}"
echo "🖼️  Image Server: http://localhost:${IMAGE_SERVER_PORT:-8888}"
echo "🔄 Development: Edit code and see changes automatically!"
echo "📊 Check logs with: docker-compose logs -f"
"""
    
    script_path = os.path.join(os.getcwd(), 'start_frontend.sh')
    try:
        with open(script_path, 'w') as f:
            f.write(startup_script)
        os.chmod(script_path, 0o755)
        print_success(f"Created: {script_path}")
    except Exception as e:
        print_error(f"Failed to create startup script: {e}")

def create_stop_script() -> None:
    """Create a stop script for the frontend"""
    print_header("Creating Stop Script")
    
    stop_script = """#!/bin/bash
# HPE NVIDIA Vista3D Frontend Stop Script

echo "🛑 Stopping HPE NVIDIA Vista3D Frontend..."

# Stop the frontend services
docker-compose down

# Stop the image server
echo "🖼️  Stopping image server..."
cd ../image_server
if [ -f "docker-compose.yml" ]; then
    docker-compose down
    echo "✅ Image server stopped"
else
    echo "⚠️  Image server docker-compose.yml not found"
fi
cd ../frontend

echo "✅ Frontend services stopped"
"""
    
    script_path = os.path.join(os.getcwd(), 'stop_frontend.sh')
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
# HPE NVIDIA Vista3D Frontend Logs Script

echo "📊 Viewing HPE NVIDIA Vista3D Frontend logs..."

# Show logs for frontend services
echo "🌐 Frontend logs:"
docker-compose logs -f --tail=50

# Show logs for image server
echo "🖼️  Image server logs:"
cd ../image_server
if [ -f "docker-compose.yml" ]; then
    docker-compose logs -f --tail=50
else
    echo "⚠️  Image server not found"
fi
cd ../frontend
"""
    
    script_path = os.path.join(os.getcwd(), 'logs_frontend.sh')
    try:
        with open(script_path, 'w') as f:
            f.write(logs_script)
        os.chmod(script_path, 0o755)
        print_success(f"Created: {script_path}")
    except Exception as e:
        print_error(f"Failed to create logs script: {e}")


def main():
    """Main setup function"""
    print_header("HPE NVIDIA Vista3D Frontend Setup")
    print_info("This script will set up the frontend services")
    
    # Check if we're in the right directory
    if not os.path.exists('docker-compose.yml'):
        print_error("docker-compose.yml not found. Please run this script from the frontend directory.")
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
        print_info("Frontend may not work properly without these requirements.")
        
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
    
    # Update docker-compose.yml
    update_docker_compose(config)
    
    # Setup image server
    setup_image_server(config)
    
    # Build Docker images
    build_docker_images()
    
    # Create management scripts
    create_startup_script()
    create_stop_script()
    create_logs_script()
    
    # Final instructions
    print_header("Setup Complete!")
    print_success("Frontend setup completed successfully!")
    print_info("Next steps:")
    print_info("1. Start the frontend (development mode): ./start_frontend.sh")
    print_info("2. Or use Docker Compose: docker-compose up -d")
    print_info("3. Stop services: ./stop_frontend.sh")
    print_info("4. View logs: ./logs_frontend.sh")
    print_info(f"5. Open web interface: http://localhost:{config['FRONTEND_PORT']}")
    print_info("🔄 Development mode: Edit code and see changes automatically!")
    
    print_info("\nConfiguration saved to .env file")
    print_info(f"DICOM folder: {config['DICOM_FOLDER']}")
    print_info(f"Output folder: {config['OUTPUT_FOLDER']}")
    print_info(f"Vista3D server: {config['VISTA3D_SERVER']}")
    print_info(f"Image server: {config['IMAGE_SERVER']}")

if __name__ == "__main__":
    main()
