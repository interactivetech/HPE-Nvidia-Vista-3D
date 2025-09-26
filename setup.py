#!/usr/bin/env python3
"""
HPE NVIDIA Vista3D Master Setup Script

This script provides a unified setup experience for the entire platform:
- System requirements validation
- Backend setup (Vista3D server)
- Frontend setup (Web interface and image server)
- Environment configuration
- Directory structure creation
"""

import os
import sys
import subprocess
import platform
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
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(70)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}\n")

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
                            if gb >= 10:
                                requirements['disk_space'] = True
                                print_success(f"Disk space: {available} available")
                            else:
                                print_warning(f"Disk space: {available} (Recommended: 10+ GB)")
                            break
    except:
        print_warning("Could not check disk space")
    
    return requirements

def get_user_input() -> Dict[str, str]:
    """Get configuration from user"""
    print_header("Configuration Setup")
    
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
    if not org_id:
        org_id = ""
    config['NGC_ORG_ID'] = org_id
    
    # Get data directories
    print_info("Data directories (use absolute paths for best results)")
    
    # DICOM folder
    default_dicom = os.path.join(os.getcwd(), "dicom")
    dicom_path = input(f"DICOM folder path [{default_dicom}]: ").strip()
    if not dicom_path:
        dicom_path = default_dicom
    config['DICOM_FOLDER'] = os.path.abspath(dicom_path)
    
    # Output folder
    default_output = os.path.join(os.getcwd(), "output")
    output_path = input(f"Output folder path [{default_output}]: ").strip()
    if not output_path:
        output_path = default_output
    config['OUTPUT_FOLDER'] = os.path.abspath(output_path)
    
    # Server URLs
    vista3d_url = input("Vista3D server URL [http://localhost:8000]: ").strip()
    if not vista3d_url:
        vista3d_url = "http://localhost:8000"
    config['VISTA3D_SERVER'] = vista3d_url
    
    image_server_url = input("Image server URL [http://localhost:8888]: ").strip()
    if not image_server_url:
        image_server_url = "http://localhost:8888"
    config['IMAGE_SERVER'] = image_server_url
    
    # Ports
    frontend_port = input("Frontend port [8501]: ").strip()
    if not frontend_port:
        frontend_port = "8501"
    config['FRONTEND_PORT'] = frontend_port
    
    # Segmentation settings
    vessels = input("Vessels of interest [all]: ").strip()
    if not vessels:
        vessels = "all"
    config['VESSELS_OF_INTEREST'] = vessels
    
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

def create_master_env_file(config: Dict[str, str]) -> None:
    """Create master .env file with configuration"""
    print_header("Creating Master Environment Configuration")
    
    env_content = f"""# HPE NVIDIA Vista3D Master Configuration
# Generated by setup.py

# NVIDIA NGC Configuration
NGC_API_KEY="{config['NGC_API_KEY']}"
NGC_ORG_ID="{config['NGC_ORG_ID']}"

# Data Directories
DICOM_FOLDER="{config['DICOM_FOLDER']}"
OUTPUT_FOLDER="{config['OUTPUT_FOLDER']}"

# Server URLs
VISTA3D_SERVER="{config['VISTA3D_SERVER']}"
IMAGE_SERVER="{config['IMAGE_SERVER']}"

# Ports
FRONTEND_PORT="{config['FRONTEND_PORT']}"

# Segmentation Settings
VESSELS_OF_INTEREST="{config['VESSELS_OF_INTEREST']}"

# Docker Configuration
COMPOSE_PROJECT_NAME=vista3d-platform
"""
    
    env_file = os.path.join(os.getcwd(), '.env')
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print_success(f"Created: {env_file}")
    except Exception as e:
        print_error(f"Failed to create .env file: {e}")

def copy_env_to_services(config: Dict[str, str]) -> None:
    """Copy .env file to service directories"""
    print_header("Copying Environment Configuration to Services")
    
    master_env = os.path.join(os.getcwd(), '.env')
    
    # Copy to backend
    backend_env = os.path.join(os.getcwd(), 'backend', '.env')
    try:
        if os.path.exists(master_env):
            with open(master_env, 'r') as src, open(backend_env, 'w') as dst:
                dst.write(src.read())
            print_success("Copied .env to backend/")
    except Exception as e:
        print_error(f"Failed to copy .env to backend: {e}")
    
    # Copy to frontend (image server .env will be created by frontend setup)
    frontend_env = os.path.join(os.getcwd(), 'frontend', '.env')
    try:
        if os.path.exists(master_env):
            with open(master_env, 'r') as src, open(frontend_env, 'w') as dst:
                dst.write(src.read())
            print_success("Copied .env to frontend/")
    except Exception as e:
        print_error(f"Failed to copy .env to frontend: {e}")

def run_backend_setup() -> None:
    """Run backend setup script"""
    print_header("Setting Up Backend (Vista3D Server)")
    
    backend_dir = os.path.join(os.getcwd(), 'backend')
    if not os.path.exists(backend_dir):
        print_error("Backend directory not found")
        return
    
    setup_script = os.path.join(backend_dir, 'setup_backend.py')
    if not os.path.exists(setup_script):
        print_error("Backend setup script not found")
        return
    
    try:
        print_info("Running backend setup...")
        result = run_command(f"cd {backend_dir} && python3 setup_backend.py", capture_output=True)
        if result.returncode == 0:
            print_success("Backend setup completed")
        else:
            print_error("Backend setup failed")
            print_error(result.stderr)
    except Exception as e:
        print_error(f"Failed to run backend setup: {e}")

def run_frontend_setup() -> None:
    """Run frontend setup script"""
    print_header("Setting Up Frontend (Web Interface)")
    
    frontend_dir = os.path.join(os.getcwd(), 'frontend')
    if not os.path.exists(frontend_dir):
        print_error("Frontend directory not found")
        return
    
    setup_script = os.path.join(frontend_dir, 'setup_frontend.py')
    if not os.path.exists(setup_script):
        print_error("Frontend setup script not found")
        return
    
    try:
        print_info("Running frontend setup...")
        result = run_command(f"cd {frontend_dir} && python3 setup_frontend.py", capture_output=True)
        if result.returncode == 0:
            print_success("Frontend setup completed")
        else:
            print_error("Frontend setup failed")
            print_error(result.stderr)
    except Exception as e:
        print_error(f"Failed to run frontend setup: {e}")

def create_master_scripts() -> None:
    """Create master management scripts"""
    print_header("Creating Master Management Scripts")
    
    # Create start all script
    start_all_script = """#!/bin/bash
# HPE NVIDIA Vista3D Master Start Script

set -e

echo "🚀 Starting HPE NVIDIA Vista3D Platform..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please run setup.py first."
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Start backend (Vista3D server)
echo "🧠 Starting Vista3D server..."
cd backend
if [ -f "start_backend.sh" ]; then
    ./start_backend.sh
else
    docker-compose up -d
fi
cd ..

# Wait for backend to be ready
echo "⏳ Waiting for Vista3D server to be ready..."
sleep 30

# Start frontend services (includes image server)
echo "🌐 Starting frontend services (including image server)..."
cd frontend
if [ -f "start_frontend.sh" ]; then
    ./start_frontend.sh
else
    docker-compose up -d
fi
cd ..

echo "🎉 Platform startup complete!"
echo "🌐 Web Interface: http://localhost:${FRONTEND_PORT:-8501}"
echo "🧠 Vista3D API: http://localhost:8000"
echo "🖼️  Image Server: http://localhost:8888"
"""
    
    script_path = os.path.join(os.getcwd(), 'start_all.sh')
    try:
        with open(script_path, 'w') as f:
            f.write(start_all_script)
        os.chmod(script_path, 0o755)
        print_success(f"Created: {script_path}")
    except Exception as e:
        print_error(f"Failed to create start_all.sh: {e}")
    
    # Create stop all script
    stop_all_script = """#!/bin/bash
# HPE NVIDIA Vista3D Master Stop Script

echo "🛑 Stopping HPE NVIDIA Vista3D Platform..."

# Stop frontend services (includes image server)
echo "Stopping frontend services (including image server)..."
cd frontend
if [ -f "stop_frontend.sh" ]; then
    ./stop_frontend.sh
else
    docker-compose down
    # Also stop image server
    cd ../image_server
    docker-compose down
    cd ../frontend
fi
cd ..

# Stop backend services
echo "Stopping backend services..."
cd backend
docker-compose down
cd ..

echo "✅ Platform stopped"
"""
    
    script_path = os.path.join(os.getcwd(), 'stop_all.sh')
    try:
        with open(script_path, 'w') as f:
            f.write(stop_all_script)
        os.chmod(script_path, 0o755)
        print_success(f"Created: {script_path}")
    except Exception as e:
        print_error(f"Failed to create stop_all.sh: {e}")
    
    # Create status script
    status_script = """#!/bin/bash
# HPE NVIDIA Vista3D Master Status Script

echo "📊 HPE NVIDIA Vista3D Platform Status"
echo "======================================"

# Check backend
echo "Backend (Vista3D Server):"
if docker ps | grep -q vista3d-server-standalone; then
    echo "  ✅ Running on http://localhost:8000"
else
    echo "  ❌ Not running"
fi

# Check frontend
echo "Frontend (Web Interface):"
if docker ps | grep -q vista3d-frontend-standalone; then
    echo "  ✅ Running on http://localhost:8501"
else
    echo "  ❌ Not running"
fi

# Check image server
echo "Image Server:"
if docker ps | grep -q vista3d-image-server-standalone; then
    echo "  ✅ Running on http://localhost:8888"
else
    echo "  ❌ Not running"
fi

echo ""
echo "📊 All containers:"
docker ps --format "table {{.Names}}\\t{{.Status}}\\t{{.Ports}}"
"""
    
    script_path = os.path.join(os.getcwd(), 'status.sh')
    try:
        with open(script_path, 'w') as f:
            f.write(status_script)
        os.chmod(script_path, 0o755)
        print_success(f"Created: {script_path}")
    except Exception as e:
        print_error(f"Failed to create status.sh: {e}")

def main():
    """Main setup function"""
    print_header("HPE NVIDIA Vista3D Master Setup")
    print_info("This script will set up the entire Vista3D platform")
    
    # Check if we're in the right directory
    if not os.path.exists('backend') or not os.path.exists('frontend'):
        print_error("Backend or frontend directories not found. Please run this script from the project root.")
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
    optional_requirements = ['nvidia_docker', 'gpu', 'memory', 'disk_space']
    missing_optional = [req for req in optional_requirements if not requirements[req]]
    
    if missing_optional:
        print_warning(f"Missing optional requirements: {', '.join(missing_optional)}")
        print_info("Some features may not work properly without these requirements.")
        
        response = input("Continue anyway? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print_info("Setup cancelled.")
            sys.exit(0)
    
    # Get user configuration
    config = get_user_input()
    
    # Create directories
    create_directories(config)
    
    # Create master .env file
    create_master_env_file(config)
    
    # Copy .env to all services
    copy_env_to_services(config)
    
    # Run backend setup
    run_backend_setup()
    
    # Run frontend setup
    run_frontend_setup()
    
    # Create master management scripts
    create_master_scripts()
    
    # Final instructions
    print_header("Setup Complete!")
    print_success("Platform setup completed successfully!")
    print_info("Next steps:")
    print_info("1. Start all services: ./start_all.sh")
    print_info("2. Check status: ./status.sh")
    print_info("3. Stop all services: ./stop_all.sh")
    print_info(f"4. Open web interface: http://localhost:{config['FRONTEND_PORT']}")
    
    print_info("\nIndividual service management:")
    print_info("• Backend: cd backend && ./start_backend.sh")
    print_info("• Frontend (includes image server): cd frontend && ./start_frontend.sh")
    
    print_info("\nConfiguration saved to .env files")
    print_info(f"DICOM folder: {config['DICOM_FOLDER']}")
    print_info(f"Output folder: {config['OUTPUT_FOLDER']}")
    print_info(f"Vista3D server: {config['VISTA3D_SERVER']}")
    print_info(f"Image server: {config['IMAGE_SERVER']}")

if __name__ == "__main__":
    main()
