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
    BRIGHT_YELLOW = '\033[93m'  # Bright yellow for important instructions
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

def print_highlight(text: str) -> None:
    """Print highlighted instruction in bright yellow"""
    print(f"{Colors.BOLD}{Colors.BRIGHT_YELLOW}{text}{Colors.END}")

def run_command(command: str, check: bool = True, capture_output: bool = False, env: dict = None) -> subprocess.CompletedProcess:
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=check, 
            capture_output=capture_output,
            text=True,
            env=env
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
    - 40+ GB free disk space (Vista3D Docker image is ~30GB)
    
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

def get_user_input_non_interactive(setup_choice: str = 'both') -> Dict[str, str]:
    """Get configuration using defaults for non-interactive mode"""
    print_info("Running in non-interactive mode with defaults")
    
    config = {
        'DICOM_FOLDER': os.path.abspath(os.path.join(os.getcwd(), "dicom")),
        'OUTPUT_FOLDER': os.path.abspath(os.path.join(os.getcwd(), "output")),
        'VISTA3D_SERVER': 'http://host.docker.internal:8000',
        'IMAGE_SERVER': 'http://localhost:8888',
        'FRONTEND_PORT': '8501',
        'VESSELS_OF_INTEREST': 'all'
    }
    
    # Only add NVIDIA credentials for backend setups
    if setup_choice in ['backend', 'both']:
        config['NGC_API_KEY'] = 'nvapi-REPLACE_WITH_YOUR_API_KEY'
        config['NGC_ORG_ID'] = ''
        print_warning("Using default configuration. Please update .env file with your actual API key.")
    else:
        # Frontend-only setup - no NVIDIA credentials needed
        config['NGC_API_KEY'] = ''
        config['NGC_ORG_ID'] = ''
        print_info("Frontend-only setup - no NVIDIA API key needed.")
    
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
    min_disk_gb = 5 if setup_choice == 'frontend' else 40
    try:
        result = run_command("df -h .", capture_output=True)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            for line in lines[1:]:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 4:
                        available = parts[3]  # Available space is in 4th column
                        # Handle different formats: '43Gi', '43G', '43GB', etc.
                        if 'G' in available:
                            # Extract numeric value and convert to GB
                            if 'Gi' in available:
                                gb = float(available.replace('Gi', ''))
                            elif 'GB' in available:
                                gb = float(available.replace('GB', ''))
                            else:
                                gb = float(available.replace('G', ''))
                            
                            if gb >= min_disk_gb:
                                requirements['disk_space'] = True
                                print_success(f"Disk space: {available} available")
                            else:
                                print_warning(f"Disk space: {available} (Recommended: {min_disk_gb}+ GB)")
                            break
        else:
            print_warning("Could not check disk space - df command failed")
    except Exception as e:
        print_warning(f"Could not check disk space: {e}")
    
    # For frontend-only setups, disk space is less critical
    if setup_choice == 'frontend' and not requirements['disk_space']:
        print_info("Disk space check failed, but frontend-only setup requires minimal space")
        requirements['disk_space'] = True  # Mark as satisfied for frontend-only
    
    return requirements

def get_user_input(setup_choice: str = 'both') -> Dict[str, str]:
    """Get configuration using defaults"""
    print_header("Configuration Setup")
    print_info("Using default configuration values")
    
    config = {}
    
    # Get NVIDIA NGC API key (required for backend, not needed for frontend-only)
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
        # Frontend-only setup - no API key needed
        print_info("NVIDIA NGC API Key is not needed for frontend-only setup")
        print_info("The frontend will connect to a remote Vista3D server")
        config['NGC_API_KEY'] = ""
    
    # Get NVIDIA Org ID (only needed for backend)
    if setup_choice in ['backend', 'both']:
        org_id = input("Enter your NVIDIA Org ID (optional, press Enter to skip): ").strip()
        if not org_id:
            org_id = ""
        config['NGC_ORG_ID'] = org_id
    else:
        # Frontend-only setup - no Org ID needed
        config['NGC_ORG_ID'] = ""
    
    # Use default data directories
    config['DICOM_FOLDER'] = os.path.abspath(os.path.join(os.getcwd(), "dicom"))
    config['OUTPUT_FOLDER'] = os.path.abspath(os.path.join(os.getcwd(), "output"))
    
    # Use default server URLs and ports
    config['VISTA3D_SERVER'] = "http://host.docker.internal:8000"
    config['IMAGE_SERVER'] = "http://localhost:8888"
    config['FRONTEND_PORT'] = "8501"
    config['VESSELS_OF_INTEREST'] = "all"
    
    print_success(f"DICOM folder: {config['DICOM_FOLDER']}")
    print_success(f"Output folder: {config['OUTPUT_FOLDER']}")
    print_success(f"Vista3D server: {config['VISTA3D_SERVER']}")
    print_success(f"Image server: {config['IMAGE_SERVER']}")
    print_success(f"Frontend port: {config['FRONTEND_PORT']}")
    
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
VISTA3D_IMAGE_SERVER_URL="http://host.docker.internal:{config['IMAGE_SERVER_PORT']}"

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
        print_info("This may take several minutes, especially when pulling Docker images...")
        print_info("Progress will be shown below:")
        print("")
        # Don't capture output so users can see real-time progress from Docker pulls
        result = run_command(f"cd {backend_dir} && python3 setup_backend.py", capture_output=False)
        if result.returncode == 0:
            print_success("Backend setup completed")
        else:
            print_error("Backend setup failed")
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
        # Set environment variable to indicate this is called from master setup
        env = os.environ.copy()
        env['MASTER_SETUP'] = 'true'
        result = run_command(f"cd {frontend_dir} && python3 setup_frontend.py", capture_output=False, env=env)
        if result.returncode == 0:
            print_success("Frontend setup completed")
        else:
            print_error("Frontend setup failed")
    except Exception as e:
        print_error(f"Failed to run frontend setup: {e}")

def get_setup_choice_interactive() -> str:
    """Get setup choice from user interactively"""
    print_header("Setup Options")
    print_info("What would you like to set up?")
    print("1. Frontend only (Web Interface) - No GPU required")
    print("2. Backend only (Vista3D Server) - Requires NVIDIA GPU")
    print("3. Both frontend and backend - Full platform")
    print("")
    
    while True:
        choice = input("Enter your choice (1-3): ").strip()
        if choice == '1':
            return 'frontend'
        elif choice == '2':
            return 'backend'
        elif choice == '3':
            return 'both'
        else:
            print_error("Invalid choice. Please enter 1, 2, or 3.")

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
    
    # Determine setup choice
    setup_choice = args.setup
    if not args.non_interactive and not args.check_only and not args.config_file:
        # If no specific setup choice was provided via command line, ask the user
        if args.setup == 'both':  # This is the default from argparse
            setup_choice = get_setup_choice_interactive()
    
    # Show what will be set up based on the choice
    if setup_choice == 'frontend':
        print_info("This script will set up the frontend (Web Interface) only")
        print_info("No NVIDIA GPU required - can run on any system")
    elif setup_choice == 'backend':
        print_info("This script will set up the backend (Vista3D Server) only")
        print_info("Requires NVIDIA GPU and NVIDIA Container Toolkit")
    else:
        print_info("This script will set up the entire Vista3D platform")
        print_info("Backend requires NVIDIA GPU, frontend can run on any system")
    
    # Check if we're in the right directory
    if not os.path.exists('backend') or not os.path.exists('frontend'):
        print_error("Backend or frontend directories not found. Please run this script from the project root.")
        sys.exit(1)
    
    # Check system requirements
    requirements = check_system_requirements(setup_choice)
    
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
        image_status = check_docker_hub_images(setup_choice)
        
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
        config = get_user_input_non_interactive(setup_choice)
    else:
        config = get_user_input(setup_choice)
    
    # Create directories
    create_directories(config)
    
    # Create master .env file
    create_master_env_file(config)
    
    # Copy .env to all services
    copy_env_to_services(config)
    
    # Run setup based on user choice
    if setup_choice in ['backend', 'both']:
        run_backend_setup()
    
    if setup_choice in ['frontend', 'both']:
        run_frontend_setup()
    
    # Master management scripts removed - using direct Docker Compose commands instead
    
    # Final instructions
    print_header("🎉 Setup Complete!")
    print_success("Platform setup completed successfully!")
    
    # Show what was set up
    setup_components = []
    if setup_choice in ['backend', 'both']:
        setup_components.append("Backend (Vista3D Server)")
    if setup_choice in ['frontend', 'both']:
        setup_components.append("Frontend (Web Interface)")
    
    print_info(f"✅ Components set up: {', '.join(setup_components)}")
    
    print_header("📁 Configuration Details")
    print_info("Configuration saved to .env files:")
    print_info(f"• DICOM folder: {config['DICOM_FOLDER']}")
    print_info(f"• Output folder: {config['OUTPUT_FOLDER']}")
    if setup_choice in ['backend', 'both']:
        print_info(f"• Vista3D server: {config['VISTA3D_SERVER']}")
    if setup_choice in ['frontend', 'both']:
        print_info(f"• Image server: {config['IMAGE_SERVER']}")
    
    print_header("🔧 Troubleshooting")
    print_info("If you encounter issues:")
    print_info("• Check service status: ./status.sh (or cd <service> && docker compose ps)")
    print_info("• View logs: cd <service> && docker compose logs")
    print_info("• Restart services: ./stop_all.sh && ./start_all.sh")
    print_info("• Check Docker: docker ps")
    
    print_header("📚 Additional Resources")
    print_info("• Documentation: Check the docs/ folder")
    print_info("• Quick Start Guide: QUICK_START.md")
    print_info("• Setup Guide: docs/SETUP_GUIDE.md")
    
    # Provide specific next steps based on what was set up
    print_header("🚀 Next Steps - How to Run Your Setup")
    
    if setup_choice == 'both':
        print_info("🎉 You have set up the COMPLETE Vista3D platform!")
        print_info("   This includes both the backend server and frontend web interface.")
        print_info("")
        print_highlight("📋 TO RUN EVERYTHING:")
        print_highlight("1. Start frontend: cd frontend && docker compose up -d")
        print_highlight("2. Wait 30-60 seconds for services to start")
        print_highlight("3. Check status: docker ps")
        print_highlight(f"4. Open web interface: http://localhost:{config['FRONTEND_PORT']}")
        print_info("")
        print_info("🛑 TO STOP EVERYTHING: cd frontend && docker compose down")
        print_info("")
        print_info("📊 WHAT YOU'LL HAVE RUNNING:")
        print_info(f"• Web Interface: http://localhost:{config['FRONTEND_PORT']}")
        print_info(f"• Vista3D API: {config['VISTA3D_SERVER']}")
        print_info(f"• Image Server: {config['IMAGE_SERVER']}")
        
    elif setup_choice == 'backend':
        print_info("🎉 You have set up the VISTA3D BACKEND SERVER!")
        print_info("   This provides the AI processing and API endpoints.")
        print_info("")
        print_highlight("📋 TO RUN THE BACKEND:")
        print_highlight("1. Start backend: cd backend && docker compose up -d")
        print_highlight("2. Wait 30-60 seconds for the server to start")
        print_highlight("3. Check status: docker ps")
        print_info("")
        print_info("🛑 TO STOP THE BACKEND: cd backend && docker compose down")
        print_info("")
        print_info("📊 WHAT YOU'LL HAVE RUNNING:")
        print_info(f"• Vista3D API: {config['VISTA3D_SERVER']}")
        print_info("• API Documentation: http://localhost:8000/docs")
        print_info("")
        print_info("💡 This backend can be used by:")
        print_info("   • Frontend applications (like the Vista3D web interface)")
        print_info("   • Direct API calls for processing DICOM files")
        print_info("   • Other applications that need AI-powered medical imaging")
        
    elif setup_choice == 'frontend':
        print_info("🎉 You have set up the VISTA3D FRONTEND WEB INTERFACE!")
        print_info("   This provides the user-friendly web interface for Vista3D.")
        print_info("")
        print_highlight("📋 TO RUN THE FRONTEND:")
        print_highlight("1. Start frontend: cd frontend && docker compose up -d")
        print_highlight("2. Wait 30-60 seconds for services to start")
        print_highlight("3. Check status: docker ps")
        print_highlight(f"4. Open web interface: http://localhost:{config['FRONTEND_PORT']}")
        print_info("")
        print_info("🛑 TO STOP THE FRONTEND: cd frontend && docker compose down")
        print_info("")
        print_info("📊 WHAT YOU'LL HAVE RUNNING:")
        print_info(f"• Web Interface: http://localhost:{config['FRONTEND_PORT']}")
        print_info(f"• Image Server: {config['IMAGE_SERVER']}")
        print_info("")
        print_info("💡 IMPORTANT: This frontend needs a Vista3D backend server to work!")
        print_info("   • Connect to a remote Vista3D server, OR")
        print_info("   • Set up the backend separately using: python3 setup.py --setup backend")
        print_info("   • Update the Vista3D server URL in the .env file if needed")
    
    print_success("🎉 You're all set! Run the commands above to start using Vista3D.")

if __name__ == "__main__":
    main()
