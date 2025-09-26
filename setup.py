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
import argparse
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

def print_help():
    """Print detailed help information"""
    help_text = """
HPE NVIDIA Vista3D Master Setup Script

USAGE:
    python3 setup.py [OPTIONS]

DESCRIPTION:
    This script provides a unified setup experience for the entire Vista3D platform.
    It will guide you through system requirements validation, configuration setup,
    and installation of all necessary components.
    
    Cross-platform support: Works on Ubuntu Linux (18.04+) and macOS.

OPTIONS:
    -h, --help              Show this help message and exit
    --version               Show version information and exit
    --check-only            Only check system requirements without running setup
    --skip-docker-check     Skip Docker Hub image availability check
    --non-interactive       Run in non-interactive mode (use defaults)
    --config-file FILE      Use configuration from file instead of interactive input
    --setup {frontend,backend,both}
                           Choose what to set up (default: both)

EXAMPLES:
    # Interactive setup (recommended)
    python3 setup.py

    # Check system requirements only
    python3 setup.py --check-only

    # Non-interactive setup with defaults
    python3 setup.py --non-interactive

    # Setup with custom configuration file
    python3 setup.py --config-file my_config.env

    # Setup only frontend
    python3 setup.py --setup frontend

    # Setup only backend
    python3 setup.py --setup backend

    # Setup both (default behavior)
    python3 setup.py --setup both

REQUIREMENTS:
    - Python 3.8 or higher
    - Docker and Docker Compose
    - Supported OS: Ubuntu Linux (18.04+) or macOS
    
    For Backend Setup (Vista3D Server):
    - NVIDIA Container Toolkit (for GPU acceleration)
    - NVIDIA GPU (recommended)
    - 16+ GB RAM (recommended)
    - 10+ GB free disk space
    
    For Frontend Setup (Web Interface):
    - 8+ GB RAM (minimum)
    - 5+ GB free disk space
    - No GPU required (can run on any system)
    - Works on both Ubuntu and macOS

CONFIGURATION:
    The script will prompt you for:
    - NVIDIA NGC API key (required for backend/both, not needed for frontend-only)
    - NVIDIA Org ID (optional)
    - DICOM folder path
    - Output folder path
    - Server URLs and ports
    - Segmentation settings (backend only)

OUTPUT:
    - Master .env file with all configuration
    - Service-specific .env files
    - Management scripts (start_all.sh, stop_all.sh, status.sh)
    - Directory structure for data and outputs

For more information, visit: https://github.com/your-repo/vista3d
"""
    print(help_text)

def print_version():
    """Print version information"""
    version_text = """
HPE NVIDIA Vista3D Master Setup Script
Version: 1.0.0
Python: {python_version}
Platform: {platform}
"""
    print(version_text.format(
        python_version=sys.version,
        platform=platform.platform()
    ))

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="HPE NVIDIA Vista3D Master Setup Script",
        add_help=False  # We'll handle help manually
    )
    
    parser.add_argument(
        '-h', '--help',
        action='store_true',
        help='Show this help message and exit'
    )
    
    parser.add_argument(
        '--version',
        action='store_true',
        help='Show version information and exit'
    )
    
    parser.add_argument(
        '--check-only',
        action='store_true',
        help='Only check system requirements without running setup'
    )
    
    parser.add_argument(
        '--skip-docker-check',
        action='store_true',
        help='Skip Docker Hub image availability check'
    )
    
    parser.add_argument(
        '--non-interactive',
        action='store_true',
        help='Run in non-interactive mode (use defaults)'
    )
    
    parser.add_argument(
        '--config-file',
        type=str,
        help='Use configuration from file instead of interactive input'
    )
    
    parser.add_argument(
        '--setup',
        choices=['frontend', 'backend', 'both'],
        default='both',
        help='Choose what to set up: frontend only, backend only, or both (default: both)'
    )
    
    return parser.parse_args()

def load_config_from_file(config_file: str) -> Dict[str, str]:
    """Load configuration from file"""
    config = {}
    try:
        with open(config_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip().strip('"\'')
        print_success(f"Loaded configuration from: {config_file}")
        return config
    except Exception as e:
        print_error(f"Failed to load config file {config_file}: {e}")
        sys.exit(1)

def get_user_input_non_interactive() -> Dict[str, str]:
    """Get configuration using defaults for non-interactive mode"""
    print_info("Running in non-interactive mode with defaults")
    
    config = {
        'NGC_API_KEY': 'nvapi-REPLACE_WITH_YOUR_API_KEY',
        'NGC_ORG_ID': '',
        'DICOM_FOLDER': os.path.join(os.getcwd(), "dicom"),
        'OUTPUT_FOLDER': os.path.join(os.getcwd(), "output"),
        'VISTA3D_SERVER': 'http://localhost:8000',
        'IMAGE_SERVER': 'http://localhost:8888',
        'FRONTEND_PORT': '8501',
        'VESSELS_OF_INTEREST': 'all'
    }
    
    print_warning("Using default configuration. Please update .env file with your actual API key.")
    return config

def check_docker_hub_images(setup_choice: str = 'both') -> Dict[str, bool]:
    """Check if Docker Hub images are available and pull them"""
    print_header("Checking Docker Hub Images")
    
    docker_hub_images = {}
    if setup_choice in ['frontend', 'both']:
        docker_hub_images.update({
            'frontend': 'dwtwp/vista3d-frontend:latest',
            'image_server': 'dwtwp/vista3d-image-server:latest'
        })
    if setup_choice in ['backend', 'both']:
        # Backend uses Vista3D server which is pulled from NGC, not Docker Hub
        # So we don't need to check for backend images here
        pass
    
    image_status = {}
    
    for service, image in docker_hub_images.items():
        print_info(f"Checking {service} image: {image}")
        
        # Check if image exists locally first
        try:
            result = run_command(f"docker image inspect {image}", capture_output=True)
            if result.returncode == 0:
                print_success(f"{service} image found locally: {image}")
                image_status[service] = True
                continue
        except:
            pass
        
        # Try to pull from Docker Hub
        try:
            print_info(f"Pulling {image} from Docker Hub...")
            result = run_command(f"docker pull {image}", capture_output=True)
            if result.returncode == 0:
                print_success(f"Successfully pulled {image}")
                image_status[service] = True
            else:
                print_warning(f"Failed to pull {image}: {result.stderr}")
                image_status[service] = False
        except Exception as e:
            print_warning(f"Failed to pull {image}: {e}")
            image_status[service] = False
    
    return image_status

def check_system_requirements(setup_choice: str = 'both') -> Dict[str, bool]:
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
    
    # Check NVIDIA Container Toolkit (only required for backend)
    if setup_choice in ['backend', 'both']:
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
    else:
        # Frontend-only setup - GPU not required
        print_info("NVIDIA Container Toolkit: Not required for frontend-only setup")
        print_info("NVIDIA GPU: Not required for frontend-only setup")
        requirements['nvidia_docker'] = True  # Mark as satisfied since not needed
        requirements['gpu'] = True  # Mark as satisfied since not needed
    
    # Check memory
    min_memory_gb = 8 if setup_choice == 'frontend' else 16
    try:
        if system == 'linux':
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
            for line in meminfo.split('\n'):
                if 'MemTotal' in line:
                    mem_kb = int(line.split()[1])
                    mem_gb = mem_kb / 1024 / 1024
                    if mem_gb >= min_memory_gb:
                        requirements['memory'] = True
                        print_success(f"Memory: {mem_gb:.1f} GB")
                    else:
                        print_warning(f"Memory: {mem_gb:.1f} GB (Recommended: {min_memory_gb}+ GB)")
                    break
        elif system == 'darwin':
            result = run_command("sysctl hw.memsize", capture_output=True)
            if result.returncode == 0:
                mem_bytes = int(result.stdout.split()[1])
                mem_gb = mem_bytes / 1024 / 1024 / 1024
                if mem_gb >= min_memory_gb:
                    requirements['memory'] = True
                    print_success(f"Memory: {mem_gb:.1f} GB")
                else:
                    print_warning(f"Memory: {mem_gb:.1f} GB (Recommended: {min_memory_gb}+ GB)")
    except:
        print_warning("Could not check memory")
    
    # Check disk space
    min_disk_gb = 5 if setup_choice == 'frontend' else 10
    try:
        result = run_command("df -h .", capture_output=True)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            for line in lines[1:]:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 4:
                        available = parts[3]
                        # Handle both 'G' and 'Gi' formats (Linux vs macOS)
                        if 'G' in available:
                            # Extract numeric value and convert to GB
                            if 'Gi' in available:
                                gb = float(available.replace('Gi', ''))
                            else:
                                gb = float(available.replace('G', ''))
                            
                            if gb >= min_disk_gb:
                                requirements['disk_space'] = True
                                print_success(f"Disk space: {available} available")
                            else:
                                print_warning(f"Disk space: {available} (Recommended: {min_disk_gb}+ GB)")
                            break
    except:
        print_warning("Could not check disk space")
    
    return requirements

def get_user_input(setup_choice: str = 'both') -> Dict[str, str]:
    """Get configuration from user"""
    print_header("Configuration Setup")
    
    config = {}
    
    # Get NVIDIA NGC API key (required for backend, optional for frontend)
    if setup_choice in ['backend', 'both']:
        print_info("NVIDIA NGC API Key is required for Vista3D backend access")
        print_info("Get your free API key at: https://ngc.nvidia.com/")
        while True:
            api_key = input("Enter your NVIDIA NGC API key (starts with 'nvapi-'): ").strip()
            if api_key.startswith('nvapi-'):
                config['NGC_API_KEY'] = api_key
                break
            else:
                print_error("API key must start with 'nvapi-'")
    else:
        print_info("NVIDIA NGC API Key is not needed for frontend-only setup")
        print_info("The frontend will connect to a remote Vista3D server")
        api_key = input("Enter your NVIDIA NGC API key (starts with 'nvapi-') or press Enter to skip: ").strip()
        if api_key.startswith('nvapi-'):
            config['NGC_API_KEY'] = api_key
        else:
            config['NGC_API_KEY'] = ""
    
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

# Docker Hub Images
FRONTEND_IMAGE=dwtwp/vista3d-frontend:latest
IMAGE_SERVER_IMAGE=dwtwp/vista3d-image-server:latest
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

def create_master_scripts(setup_choice: str = 'both') -> None:
    """Create master management scripts"""
    print_header("Creating Master Management Scripts")
    
    # Create start all script
    start_all_script = f"""#!/bin/bash
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

# Check if Docker Hub images are available
echo "🔍 Checking Docker Hub images..."

{f'''# Check frontend image
if ! docker image inspect ${{FRONTEND_IMAGE:-dwtwp/vista3d-frontend:latest}} > /dev/null 2>&1; then
    echo "📥 Pulling frontend image from Docker Hub..."
    if ! docker pull ${{FRONTEND_IMAGE:-dwtwp/vista3d-frontend:latest}}; then
        echo "❌ Failed to pull frontend image. Please check your internet connection and Docker Hub access."
        exit 1
    fi
fi

# Check image server image
if ! docker image inspect ${{IMAGE_SERVER_IMAGE:-dwtwp/vista3d-image-server:latest}} > /dev/null 2>&1; then
    echo "📥 Pulling image server image from Docker Hub..."
    if ! docker pull ${{IMAGE_SERVER_IMAGE:-dwtwp/vista3d-image-server:latest}}; then
        echo "❌ Failed to pull image server image. Please check your internet connection and Docker Hub access."
        exit 1
    fi
fi''' if setup_choice in ['frontend', 'both'] else ''}

{f'''# Start backend (Vista3D server)
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
sleep 30''' if setup_choice in ['backend', 'both'] else ''}

{f'''# Start frontend services (includes image server)
echo "🌐 Starting frontend services (including image server)..."
cd frontend
if [ -f "start_frontend.sh" ]; then
    ./start_frontend.sh
else
    docker-compose up -d
fi
cd ..''' if setup_choice in ['frontend', 'both'] else ''}

echo "🎉 Platform startup complete!"
{f'''echo "🌐 Web Interface: http://localhost:${{FRONTEND_PORT:-8501}}"''' if setup_choice in ['frontend', 'both'] else ''}
{f'''echo "🧠 Vista3D API: http://localhost:8000"''' if setup_choice in ['backend', 'both'] else ''}
{f'''echo "🖼️  Image Server: http://localhost:8888"''' if setup_choice in ['frontend', 'both'] else ''}
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
    stop_all_script = f"""#!/bin/bash
# HPE NVIDIA Vista3D Master Stop Script

echo "🛑 Stopping HPE NVIDIA Vista3D Platform..."

{f'''# Stop frontend services (includes image server)
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
cd ..''' if setup_choice in ['frontend', 'both'] else ''}

{f'''# Stop backend services
echo "Stopping backend services..."
cd backend
docker-compose down
cd ..''' if setup_choice in ['backend', 'both'] else ''}

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
    status_script = f"""#!/bin/bash
# HPE NVIDIA Vista3D Master Status Script

echo "📊 HPE NVIDIA Vista3D Platform Status"
echo "======================================"

{f'''# Check backend
echo "Backend (Vista3D Server):"
if docker ps | grep -q vista3d-server-standalone; then
    echo "  ✅ Running on http://localhost:8000"
else
    echo "  ❌ Not running"
fi''' if setup_choice in ['backend', 'both'] else ''}

{f'''# Check frontend
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
fi''' if setup_choice in ['frontend', 'both'] else ''}

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
    # Parse command line arguments
    args = parse_arguments()
    
    # Handle help and version flags
    if args.help:
        print_help()
        sys.exit(0)
    
    if args.version:
        print_version()
        sys.exit(0)
    
    print_header("HPE NVIDIA Vista3D Master Setup")
    
    # Show what will be set up based on the choice
    if args.setup == 'frontend':
        print_info("This script will set up the frontend (Web Interface) only")
    elif args.setup == 'backend':
        print_info("This script will set up the backend (Vista3D Server) only")
    else:
        print_info("This script will set up the entire Vista3D platform")
    
    # Check if we're in the right directory
    if not os.path.exists('backend') or not os.path.exists('frontend'):
        print_error("Backend or frontend directories not found. Please run this script from the project root.")
        sys.exit(1)
    
    # Check system requirements
    requirements = check_system_requirements(args.setup)
    
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
        
        if not args.non_interactive and not args.check_only:
            response = input("Continue anyway? (y/N): ").strip().lower()
            if response not in ['y', 'yes']:
                print_info("Setup cancelled.")
                sys.exit(0)
    
    # Check Docker Hub images (unless skipped)
    if not args.skip_docker_check:
        image_status = check_docker_hub_images(args.setup)
        
        # Warn if images couldn't be pulled
        failed_images = [service for service, status in image_status.items() if not status]
        if failed_images:
            print_warning(f"Could not pull Docker Hub images: {', '.join(failed_images)}")
            print_info("The setup will continue, but you may need to build images locally.")
            
            if not args.non_interactive and not args.check_only:
                response = input("Continue anyway? (y/N): ").strip().lower()
                if response not in ['y', 'yes']:
                    print_info("Setup cancelled.")
                    sys.exit(0)
    
    # If check-only mode, exit here
    if args.check_only:
        print_header("System Requirements Check Complete")
        print_success("All critical requirements met!")
        if missing_optional:
            print_warning(f"Optional requirements missing: {', '.join(missing_optional)}")
        sys.exit(0)
    
    # Get user configuration
    if args.config_file:
        config = load_config_from_file(args.config_file)
    elif args.non_interactive:
        config = get_user_input_non_interactive()
    else:
        config = get_user_input(args.setup)
    
    # Create directories
    create_directories(config)
    
    # Create master .env file
    create_master_env_file(config)
    
    # Copy .env to all services
    copy_env_to_services(config)
    
    # Run setup based on user choice
    if args.setup in ['backend', 'both']:
        run_backend_setup()
    
    if args.setup in ['frontend', 'both']:
        run_frontend_setup()
    
    # Create master management scripts
    create_master_scripts(args.setup)
    
    # Final instructions
    print_header("Setup Complete!")
    print_success("Platform setup completed successfully!")
    
    # Show what was set up
    setup_components = []
    if args.setup in ['backend', 'both']:
        setup_components.append("Backend (Vista3D Server)")
    if args.setup in ['frontend', 'both']:
        setup_components.append("Frontend (Web Interface)")
    
    print_info(f"Components set up: {', '.join(setup_components)}")
    
    print_info("\nNext steps:")
    if args.setup == 'both':
        print_info("1. Start all services: ./start_all.sh")
        print_info("2. Check status: ./status.sh")
        print_info("3. Stop all services: ./stop_all.sh")
        print_info(f"4. Open web interface: http://localhost:{config['FRONTEND_PORT']}")
    else:
        if args.setup == 'backend':
            print_info("1. Start backend: cd backend && ./start_backend.sh")
            print_info("2. Check backend status: cd backend && docker-compose ps")
            print_info(f"3. Backend API: {config['VISTA3D_SERVER']}")
        elif args.setup == 'frontend':
            print_info("1. Start frontend: cd frontend && ./start_frontend.sh")
            print_info("2. Check frontend status: cd frontend && docker-compose ps")
            print_info(f"3. Web interface: http://localhost:{config['FRONTEND_PORT']}")
    
    print_info("\nIndividual service management:")
    if args.setup in ['backend', 'both']:
        print_info("• Backend: cd backend && ./start_backend.sh")
    if args.setup in ['frontend', 'both']:
        print_info("• Frontend (includes image server): cd frontend && ./start_frontend.sh")
    
    print_info("\nConfiguration saved to .env files")
    print_info(f"DICOM folder: {config['DICOM_FOLDER']}")
    print_info(f"Output folder: {config['OUTPUT_FOLDER']}")
    if args.setup in ['backend', 'both']:
        print_info(f"Vista3D server: {config['VISTA3D_SERVER']}")
    if args.setup in ['frontend', 'both']:
        print_info(f"Image server: {config['IMAGE_SERVER']}")

if __name__ == "__main__":
    main()
