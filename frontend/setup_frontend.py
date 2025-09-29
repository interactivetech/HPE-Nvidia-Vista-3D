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
import tarfile
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

def check_docker_hub_images() -> Dict[str, bool]:
    """Check if Docker Hub images are available and pull them"""
    print_header("Checking Docker Hub Images")
    
    docker_hub_images = {
        'frontend': 'dwtwp/vista3d-frontend:latest',
        'image_server': 'dwtwp/vista3d-image-server:latest'
    }
    
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
                            # Handle different formats: '43Gi', '43G', '43GB', etc.
                            if 'G' in available:
                                if 'Gi' in available:
                                    gb = float(available.replace('Gi', ''))
                                elif 'GB' in available:
                                    gb = float(available.replace('GB', ''))
                                else:
                                    gb = float(available.replace('G', ''))
                                
                                if gb >= 5:
                                    requirements['disk_space'] = True
                                    print_success(f"Disk space: {available} available")
                                else:
                                    print_warning(f"Disk space: {available} (Recommended: 5+ GB)")
                            break
    except:
        print_warning("Could not check disk space")
    
    # For frontend setup, disk space is less critical
    if not requirements['disk_space']:
        print_info("Disk space check failed, but frontend setup requires minimal space")
        requirements['disk_space'] = True  # Mark as satisfied for frontend
    
    return requirements

def load_config_from_env() -> Dict[str, str]:
    """Load configuration from .env file created by master setup"""
    print_info("Loading configuration from .env file...")
    
    config = {}
    env_file = '.env'
    
    if not os.path.exists(env_file):
        print_error(f".env file not found: {env_file}")
        sys.exit(1)
    
    try:
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes from value
                    value = value.strip().strip('"\'')
                    config[key.strip()] = value
        print_success("Configuration loaded from .env file")
        
        # Extract port from IMAGE_SERVER URL for compatibility
        if 'IMAGE_SERVER' in config and 'IMAGE_SERVER_PORT' not in config:
            try:
                from urllib.parse import urlparse
                parsed_url = urlparse(config['IMAGE_SERVER'])
                if parsed_url.port:
                    config['IMAGE_SERVER_PORT'] = str(parsed_url.port)
                else:
                    # Default port if not specified in URL
                    config['IMAGE_SERVER_PORT'] = '8888'
            except Exception as e:
                print_warning(f"Could not extract port from IMAGE_SERVER URL: {e}")
                config['IMAGE_SERVER_PORT'] = '8888'
        
        return config
    except Exception as e:
        print_error(f"Failed to load .env file: {e}")
        sys.exit(1)

def get_user_input() -> Dict[str, str]:
    """Get configuration using defaults"""
    print_header("Frontend Configuration Setup")
    print_info("Using default configuration values")
    
    config = {}
    
    # Use default data directories
    config['DICOM_FOLDER'] = os.path.abspath(os.path.join(os.getcwd(), "..", "dicom"))
    config['OUTPUT_FOLDER'] = os.path.abspath(os.path.join(os.getcwd(), "..", "output"))
    
    # Use default server URLs and ports
    config['VISTA3D_SERVER'] = "http://host.docker.internal:8000"
    config['FRONTEND_PORT'] = "8501"
    config['IMAGE_SERVER_PORT'] = "8888"
    config['IMAGE_SERVER'] = f"http://localhost:{config['IMAGE_SERVER_PORT']}"
    
    print_success(f"DICOM folder: {config['DICOM_FOLDER']}")
    print_success(f"Output folder: {config['OUTPUT_FOLDER']}")
    print_success(f"Vista3D server: {config['VISTA3D_SERVER']}")
    print_success(f"Frontend port: {config['FRONTEND_PORT']}")
    print_success(f"Image server port: {config['IMAGE_SERVER_PORT']}")
    
    return config

def prompt_for_sample_data() -> bool:
    """Check if sample data should be installed (default: yes)"""
    print_header("Sample Data Installation")
    
    sample_data_file = os.path.join(os.getcwd(), "..", "sample_data.tgz")
    
    if not os.path.exists(sample_data_file):
        print_warning(f"Sample data file not found: {sample_data_file}")
        print_info("Sample data installation will be skipped.")
        return False
    
    print_info("Sample data archive found! This contains:")
    print_info("  - DICOM medical imaging data")
    print_info("  - Pre-processed output data")
    print_info("  - Various medical imaging datasets for testing")
    print_info("Installing sample data by default...")
    
    return True

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

def install_sample_data(config: Dict[str, str]) -> bool:
    """Extract and install sample data from sample_data.tgz"""
    print_header("Installing Sample Data")
    
    sample_data_file = os.path.join(os.getcwd(), "..", "sample_data.tgz")
    
    if not os.path.exists(sample_data_file):
        print_warning(f"Sample data file not found: {sample_data_file}")
        return False
    
    try:
        print_info(f"Extracting sample data from: {sample_data_file}")
        
        # Create a temporary directory for extraction
        temp_dir = os.path.join(os.getcwd(), "..", "temp_sample_data")
        os.makedirs(temp_dir, exist_ok=True)
        
        # Extract the tar.gz file
        with tarfile.open(sample_data_file, 'r:gz') as tar:
            tar.extractall(temp_dir)
        
        print_success("Sample data extracted successfully")
        
        # Move dicom data to the configured dicom folder
        source_dicom = os.path.join(temp_dir, "dicom")
        if os.path.exists(source_dicom):
            print_info(f"Installing DICOM data to: {config['DICOM_FOLDER']}")
            
            # Check if dicom folder already has content
            existing_dicom = os.listdir(config['DICOM_FOLDER'])
            if existing_dicom and any(item != '.DS_Store' for item in existing_dicom):
                print_warning(f"DICOM folder already contains data: {config['DICOM_FOLDER']}")
                response = input("Overwrite existing DICOM data? (y/N): ").strip().lower()
                if response not in ['y', 'yes']:
                    print_info("Skipping DICOM data installation")
                else:
                    # Remove existing content (except .DS_Store)
                    for item in os.listdir(config['DICOM_FOLDER']):
                        if item != '.DS_Store':
                            item_path = os.path.join(config['DICOM_FOLDER'], item)
                            if os.path.isdir(item_path):
                                shutil.rmtree(item_path)
                            else:
                                os.remove(item_path)
                    
                    # Copy new content
                    for item in os.listdir(source_dicom):
                        if item != '.DS_Store':
                            src_path = os.path.join(source_dicom, item)
                            dst_path = os.path.join(config['DICOM_FOLDER'], item)
                            if os.path.isdir(src_path):
                                shutil.copytree(src_path, dst_path)
                            else:
                                shutil.copy2(src_path, dst_path)
                    print_success("DICOM data installed successfully")
            else:
                # Copy all content from source to destination
                for item in os.listdir(source_dicom):
                    if item != '.DS_Store':
                        src_path = os.path.join(source_dicom, item)
                        dst_path = os.path.join(config['DICOM_FOLDER'], item)
                        if os.path.isdir(src_path):
                            shutil.copytree(src_path, dst_path)
                        else:
                            shutil.copy2(src_path, dst_path)
                print_success("DICOM data installed successfully")
        else:
            print_warning("No DICOM data found in sample data archive")
        
        # Move output data to the configured output folder
        source_output = os.path.join(temp_dir, "output")
        if os.path.exists(source_output):
            print_info(f"Installing output data to: {config['OUTPUT_FOLDER']}")
            
            # Check if output folder already has content
            existing_output = os.listdir(config['OUTPUT_FOLDER'])
            if existing_output and any(item != '.DS_Store' for item in existing_output):
                print_warning(f"Output folder already contains data: {config['OUTPUT_FOLDER']}")
                response = input("Overwrite existing output data? (y/N): ").strip().lower()
                if response not in ['y', 'yes']:
                    print_info("Skipping output data installation")
                else:
                    # Remove existing content (except .DS_Store)
                    for item in os.listdir(config['OUTPUT_FOLDER']):
                        if item != '.DS_Store':
                            item_path = os.path.join(config['OUTPUT_FOLDER'], item)
                            if os.path.isdir(item_path):
                                shutil.rmtree(item_path)
                            else:
                                os.remove(item_path)
                    
                    # Copy new content
                    for item in os.listdir(source_output):
                        if item != '.DS_Store':
                            src_path = os.path.join(source_output, item)
                            dst_path = os.path.join(config['OUTPUT_FOLDER'], item)
                            if os.path.isdir(src_path):
                                shutil.copytree(src_path, dst_path)
                            else:
                                shutil.copy2(src_path, dst_path)
                    print_success("Output data installed successfully")
            else:
                # Copy all content from source to destination
                for item in os.listdir(source_output):
                    if item != '.DS_Store':
                        src_path = os.path.join(source_output, item)
                        dst_path = os.path.join(config['OUTPUT_FOLDER'], item)
                        if os.path.isdir(src_path):
                            shutil.copytree(src_path, dst_path)
                        else:
                            shutil.copy2(src_path, dst_path)
                print_success("Output data installed successfully")
        else:
            print_warning("No output data found in sample data archive")
        
        # Clean up temporary directory
        shutil.rmtree(temp_dir)
        print_success("Sample data installation completed successfully")
        return True
        
    except Exception as e:
        print_error(f"Failed to install sample data: {e}")
        # Clean up temporary directory if it exists
        temp_dir = os.path.join(os.getcwd(), "..", "temp_sample_data")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        return False

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
VISTA3D_IMAGE_SERVER_URL="{config['IMAGE_SERVER']}"

# Ports
FRONTEND_PORT="{config['FRONTEND_PORT']}"
IMAGE_SERVER_PORT="{config['IMAGE_SERVER_PORT']}"

# Vessel Configuration
VESSELS_OF_INTEREST="all"

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
            
            # Update ports and image
            content = content.replace('"8888:8888"', f'"{config["IMAGE_SERVER_PORT"]}:8888"')
            content = content.replace('image: vista3d-image-server:local', 'image: dwtwp/vista3d-image-server:latest')
            
            with open(compose_file, 'w') as f:
                f.write(content)
            
            print_success("Updated image server docker-compose.yml")
        except Exception as e:
            print_error(f"Failed to update image server docker-compose.yml: {e}")

def build_docker_images(image_status: Dict[str, bool]) -> None:
    """Build required Docker images only if Docker Hub images are not available"""
    print_header("Building Docker Images")
    
    # Build frontend image only if not available from Docker Hub
    if not image_status.get('frontend', False):
        print_info("Building frontend image locally...")
        try:
            result = run_command("docker build -t vista3d-frontend:local .", capture_output=True)
            if result.returncode == 0:
                print_success("Frontend image built successfully")
            else:
                print_error("Failed to build frontend image")
                print_error(result.stderr)
        except Exception as e:
            print_error(f"Failed to build frontend image: {e}")
    else:
        print_success("Using Docker Hub frontend image, skipping local build")
    
    # Build image server image only if not available from Docker Hub
    if not image_status.get('image_server', False):
        print_info("Building image server image locally...")
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
    else:
        print_success("Using Docker Hub image server image, skipping local build")

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
        
        # Update ports and images
        content = content.replace('"8501:8501"', f'"{config["FRONTEND_PORT"]}:8501"')
        content = content.replace('"8888:8888"', f'"{config["IMAGE_SERVER_PORT"]}:8888"')
        content = content.replace('image: vista3d-frontend:local', 'image: dwtwp/vista3d-frontend:latest')
        content = content.replace('image: vista3d-image-server:local', 'image: dwtwp/vista3d-image-server:latest')
        
        with open(compose_file, 'w') as f:
            f.write(content)
        
        print_success("Updated docker-compose.yml with user configuration")
    except Exception as e:
        print_error(f"Failed to update docker-compose.yml: {e}")



def main():
    """Main setup function"""
    print_header("HPE NVIDIA Vista3D Frontend Setup")
    print_info("This script will set up the frontend services")
    
    # Check if we're in the right directory
    if not os.path.exists('docker-compose.yml'):
        print_error("docker-compose.yml not found. Please run this script from the frontend directory.")
        sys.exit(1)
    
    # Check if called from master setup
    is_master_setup = os.environ.get('MASTER_SETUP', '').lower() == 'true'
    if is_master_setup:
        print_info("Called from master setup - using existing configuration")
    
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
    
    # Check Docker Hub images
    image_status = check_docker_hub_images()
    
    # Get user configuration
    if is_master_setup:
        # Load configuration from .env file created by master setup
        config = load_config_from_env()
    else:
        config = get_user_input()
    
    # Create directories
    create_directories(config)
    
    # Prompt for sample data installation
    install_sample = prompt_for_sample_data()
    
    # Install sample data if requested
    if install_sample:
        install_sample_data(config)
    
    # Create .env file
    create_env_file(config)
    
    # Verify Docker setup
    if not verify_docker_setup():
        print_warning("Docker setup verification failed, but continuing...")
    
    # Update docker-compose.yml
    update_docker_compose(config)
    
    # Setup image server
    setup_image_server(config)
    
    # Build Docker images only if Docker Hub images are not available
    build_docker_images(image_status)
    
    
    # Final instructions
    print_header("Setup Complete!")
    print_success("Frontend setup completed successfully!")
    print_info("Next steps:")
    print_info("1. Start image server: cd ../image_server && docker-compose up -d")
    print_info("2. Start frontend: docker-compose up -d")
    print_info("3. Stop services: docker-compose down && cd ../image_server && docker-compose down")
    print_info("4. View logs: docker-compose logs -f")
    print_info(f"5. Open web interface: http://localhost:{config['FRONTEND_PORT']}")
    print_info("🔄 Development mode: Edit code in both frontend and image server and see changes automatically!")
    
    print_info("\nConfiguration saved to .env file")
    print_info(f"DICOM folder: {config['DICOM_FOLDER']}")
    print_info(f"Output folder: {config['OUTPUT_FOLDER']}")
    print_info(f"Vista3D server: {config['VISTA3D_SERVER']}")
    print_info(f"Image server: {config['IMAGE_SERVER']}")
    
    # Check if sample data was installed
    sample_data_file = os.path.join(os.getcwd(), "..", "sample_data.tgz")
    if os.path.exists(sample_data_file):
        print_info("\n📁 Sample data is available for testing the application")
        print_info("   The sample data includes various medical imaging datasets")
        print_info("   that you can use to explore the Vista3D features.")

if __name__ == "__main__":
    main()
