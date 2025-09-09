#!/usr/bin/env python3
"""
NVIDIA Vista3D NIM Setup Script
Automates the complete setup of NVIDIA Vista3D NIM on Ubuntu Linux including:
- System requirements verification
- Docker and NVIDIA Container Toolkit installation
- NVIDIA API key configuration
- Vista3D container download and startup
- Output directory creation
- Virtual environment setup with uv
- HTTPS image server startup
- DICOM to NIFTI conversion
"""

import os
import sys
import subprocess
import time
import signal
import psutil
import getpass
import platform
import shutil
from pathlib import Path
from typing import Optional, Tuple

def print_status(message: str, status: str = "info"):
    """Print a formatted status message."""
    status_icons = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌",
        "progress": "🔄",
        "server": "🌐",
        "conversion": "🔄",
        "directory": "📁",
        "package": "📦",
        "environment": "🔌"
    }
    
    icon = status_icons.get(status, "ℹ️")
    print(f"{icon} {message}")

def run_command(command: list, check: bool = True, capture_output: bool = False) -> Tuple[bool, str]:
    """Run a shell command and return success status and output."""
    try:
        if capture_output:
            result = subprocess.run(command, check=check, capture_output=True, text=True)
            return result.returncode == 0, result.stdout
        else:
            result = subprocess.run(command, check=check)
            return result.returncode == 0, ""
    except subprocess.CalledProcessError as e:
        if capture_output:
            return False, e.stderr
        return False, str(e)
    except FileNotFoundError:
        return False, "Command not found"

def check_uv_installed() -> bool:
    """Check if uv is installed."""
    success, _ = run_command(["uv", "--version"], check=False, capture_output=True)
    return success

def check_system_requirements() -> bool:
    """Check if the system meets Vista3D requirements."""
    print_status("Checking system requirements...", "info")
    
    # Check if running on Linux
    if platform.system() != "Linux":
        print_status("Error: This script requires Linux (preferably Ubuntu)", "error")
        return False
    
    print_status("✅ Running on Linux", "success")
    
    # Check for Ubuntu (recommended)
    try:
        with open("/etc/os-release", "r") as f:
            os_release = f.read()
            if "ubuntu" in os_release.lower():
                print_status("✅ Running on Ubuntu", "success")
            else:
                print_status("⚠️  Not running on Ubuntu - proceeding anyway", "warning")
    except FileNotFoundError:
        print_status("⚠️  Could not detect OS distribution", "warning")
    
    # Check if running as root or with sudo access
    if os.geteuid() == 0:
        print_status("✅ Running with root privileges", "success")
    else:
        # Check if user has sudo access
        success, _ = run_command(["sudo", "-n", "true"], check=False, capture_output=True)
        if success:
            print_status("✅ User has sudo access", "success")
        else:
            print_status("❌ This script requires sudo access for system package installation", "error")
            print_status("Please run with sudo or ensure your user is in the sudo group", "error")
            return False
    
    return True

def check_nvidia_gpu() -> bool:
    """Check if NVIDIA GPU is available."""
    print_status("Checking for NVIDIA GPU...", "info")
    
    # Check nvidia-smi command
    success, output = run_command(["nvidia-smi"], check=False, capture_output=True)
    if success:
        print_status("✅ NVIDIA GPU detected", "success")
        # Show GPU info
        gpu_lines = [line for line in output.split('\n') if 'GeForce' in line or 'RTX' in line or 'GTX' in line or 'Tesla' in line or 'Quadro' in line]
        if gpu_lines:
            print_status(f"   GPU: {gpu_lines[0].strip()}", "info")
        return True
    else:
        print_status("❌ NVIDIA GPU not detected or drivers not installed", "error")
        print_status("Please install NVIDIA drivers first:", "info")
        print_status("   sudo apt update && sudo apt install nvidia-driver-535", "info")
        return False

def check_docker_installed() -> bool:
    """Check if Docker is installed."""
    print_status("Checking Docker installation...", "info")
    
    success, _ = run_command(["docker", "--version"], check=False, capture_output=True)
    if success:
        print_status("✅ Docker is installed", "success")
        return True
    else:
        print_status("❌ Docker is not installed", "error")
        return False

def install_docker() -> bool:
    """Install Docker on Ubuntu."""
    print_status("Installing Docker...", "package")
    
    commands = [
        ["sudo", "apt", "update"],
        ["sudo", "apt", "install", "-y", "apt-transport-https", "ca-certificates", "curl", "gnupg", "lsb-release"],
        ["curl", "-fsSL", "https://download.docker.com/linux/ubuntu/gpg"],
        ["sudo", "gpg", "--dearmor", "-o", "/usr/share/keyrings/docker-archive-keyring.gpg"],
        ["sudo", "apt", "update"],
        ["sudo", "apt", "install", "-y", "docker-ce", "docker-ce-cli", "containerd.io"]
    ]
    
    for i, cmd in enumerate(commands):
        if i == 2:  # Special handling for GPG key
            success, output = run_command(cmd, check=False, capture_output=True)
            if success:
                # Pipe the output to gpg
                proc = subprocess.Popen(["sudo", "gpg", "--dearmor", "-o", "/usr/share/keyrings/docker-archive-keyring.gpg"], 
                                      stdin=subprocess.PIPE, text=True)
                proc.communicate(input=output)
                if proc.returncode != 0:
                    print_status("Failed to add Docker GPG key", "error")
                    return False
            else:
                print_status("Failed to download Docker GPG key", "error")
                return False
        elif i == 3:  # Skip this step as it's handled above
            continue
        else:
            success, _ = run_command(cmd, check=False)
            if not success:
                print_status(f"Failed to execute: {' '.join(cmd)}", "error")
                return False
    
    # Add Docker APT repository
    repo_cmd = 'echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"'
    success, _ = run_command([f'sudo bash -c \'{repo_cmd} > /etc/apt/sources.list.d/docker.list\''], check=False)
    if not success:
        print_status("Failed to add Docker repository", "error")
        return False
    
    print_status("✅ Docker installed successfully", "success")
    return True

def install_nvidia_container_toolkit() -> bool:
    """Install NVIDIA Container Toolkit."""
    print_status("Installing NVIDIA Container Toolkit...", "package")
    
    commands = [
        ["curl", "-fsSL", "https://nvidia.github.io/libnvidia-container/gpgkey"],
        ["curl", "-s", "-L", "https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list"],
        ["sudo", "apt", "update"],
        ["sudo", "apt", "install", "-y", "nvidia-container-toolkit"],
        ["sudo", "systemctl", "restart", "docker"]
    ]
    
    # Add NVIDIA GPG key
    success, output = run_command(commands[0], check=False, capture_output=True)
    if success:
        proc = subprocess.Popen(["sudo", "apt-key", "add", "-"], stdin=subprocess.PIPE, text=True)
        proc.communicate(input=output)
        if proc.returncode != 0:
            print_status("Failed to add NVIDIA Container Toolkit GPG key", "error")
            return False
    else:
        print_status("Failed to download NVIDIA Container Toolkit GPG key", "error")
        return False
    
    # Add repository
    success, output = run_command(commands[1], check=False, capture_output=True)
    if success:
        with open("/tmp/nvidia-container-toolkit.list", "w") as f:
            f.write(output)
        success, _ = run_command(["sudo", "cp", "/tmp/nvidia-container-toolkit.list", "/etc/apt/sources.list.d/"], check=False)
        if not success:
            print_status("Failed to add NVIDIA Container Toolkit repository", "error")
            return False
    else:
        print_status("Failed to get NVIDIA Container Toolkit repository", "error")
        return False
    
    # Update and install
    for cmd in commands[2:]:
        success, _ = run_command(cmd, check=False)
        if not success:
            print_status(f"Failed to execute: {' '.join(cmd)}", "error")
            return False
    
    print_status("✅ NVIDIA Container Toolkit installed successfully", "success")
    return True

def test_nvidia_docker() -> bool:
    """Test NVIDIA Docker integration."""
    print_status("Testing NVIDIA Docker integration...", "info")
    
    success, _ = run_command([
        "sudo", "docker", "run", "--rm", "--gpus", "all", 
        "nvidia/cuda:11.0-base-ubuntu20.04", "nvidia-smi"
    ], check=False)
    
    if success:
        print_status("✅ NVIDIA Docker integration working", "success")
        return True
    else:
        print_status("❌ NVIDIA Docker integration failed", "error")
        return False

def prompt_nvidia_credentials() -> Tuple[str, str]:
    """Prompt user for NVIDIA NGC credentials."""
    print_status("NVIDIA NGC Credentials Required", "info")
    print()
    print("To download Vista3D, you need NVIDIA NGC credentials.")
    print("Sign up at: https://ngc.nvidia.com/")
    print()
    
    # Get API Key
    while True:
        api_key = getpass.getpass("Enter your NVIDIA NGC API Key (starts with 'nvapi-'): ").strip()
        if api_key.startswith('nvapi-') and len(api_key) > 10:
            break
        print_status("Invalid API key format. Should start with 'nvapi-'", "error")
    
    # Get Org ID (optional)
    org_id = input("Enter your NGC Organization ID (press Enter to skip): ").strip()
    if not org_id:
        org_id = "nvidia"  # Default org
    
    return api_key, org_id

def create_env_file(api_key: str, org_id: str):
    """Create .env file with NVIDIA credentials."""
    print_status("Creating .env configuration file...", "info")
    
    env_content = f"""# NVIDIA NGC Credentials
NGC_API_KEY={api_key}
NGC_ORG_ID={org_id}

# Vista3D Configuration
VISTA3D_CONTAINER_NAME=vista3d
VISTA3D_PORT=8000
LOCAL_NIM_CACHE=~/.cache/nim

# GPU Configuration
CUDA_VISIBLE_DEVICES=0
NVIDIA_VISIBLE_DEVICES=0
NVIDIA_DRIVER_CAPABILITIES=compute,utility

# Image Server Configuration
EXTERNAL_IMAGE_SERVER=https://host.docker.internal:8888
EXTERNAL_IMAGE_SERVER_HOST=host.docker.internal
EXTERNAL_IMAGE_SERVER_PORT=8888
EXTERNAL_IMAGE_SERVER_PROTOCOL=https

# File Access Configuration
ALLOW_LOCAL_FILES=True
ENABLE_FILE_ACCESS=True
ALLOW_FILE_PROTOCOL=True
WORKSPACE_IMAGES_PATH=/workspace/output/nifti
WORKSPACE_OUTPUTS_PATH=/workspace/output
IGNORE_SSL_ERRORS=True
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    print_status("✅ .env file created", "success")

def docker_login_ngc(api_key: str) -> bool:
    """Login to NVIDIA NGC Docker registry."""
    print_status("Logging into NVIDIA NGC registry...", "info")
    
    # Use API key as password, username is $oauthtoken
    proc = subprocess.Popen(
        ["sudo", "docker", "login", "nvcr.io", "-u", "$oauthtoken", "--password-stdin"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    stdout, stderr = proc.communicate(input=api_key)
    
    if proc.returncode == 0:
        print_status("✅ Successfully logged into NGC registry", "success")
        return True
    else:
        print_status("❌ Failed to login to NGC registry", "error")
        print_status(f"Error: {stderr}", "error")
        return False

def pull_vista3d_image() -> bool:
    """Pull the Vista3D Docker image."""
    print_status("Downloading Vista3D Docker image...", "info")
    print_status("This may take several minutes...", "info")
    
    # Use the correct Vista3D image
    image_name = "nvcr.io/nim/nvidia/vista3d:1.0.0"
    
    success, _ = run_command(["sudo", "docker", "pull", image_name], check=False)
    
    if success:
        print_status("✅ Vista3D image downloaded successfully", "success")
        return True
    else:
        print_status("❌ Failed to download Vista3D image", "error")
        return False

def start_vista3d_container(api_key: str, org_id: str) -> bool:
    """Start the Vista3D Docker container."""
    print_status("Starting Vista3D container...", "server")
    
    # Stop any existing container
    run_command(["sudo", "docker", "stop", "vista3d"], check=False)
    run_command(["sudo", "docker", "rm", "vista3d"], check=False)
    
    # Create output directory
    output_dir = Path("output").absolute()
    output_dir.mkdir(exist_ok=True)
    
    # Start container
    cmd = [
        "sudo", "docker", "run", "-d", "--name", "vista3d",
        "--gpus", "all", "--runtime=nvidia",
        "--shm-size=8G",
        "-p", "8000:8000",
        "-v", f"{output_dir}:/workspace/output",
        "-e", f"NGC_API_KEY={api_key}",
        "-e", f"NGC_ORG_ID={org_id}",
        "-e", "CUDA_VISIBLE_DEVICES=0",
        "-e", "NVIDIA_VISIBLE_DEVICES=0",
        "nvcr.io/nim/nvidia/vista3d:1.0.0"
    ]
    
    success, _ = run_command(cmd, check=False)
    
    if success:
        print_status("✅ Vista3D container started successfully", "success")
        print_status("Container is initializing... this may take a few minutes", "info")
        return True
    else:
        print_status("❌ Failed to start Vista3D container", "error")
        return False

def check_vista3d_health() -> bool:
    """Check if Vista3D is running and healthy."""
    print_status("Checking Vista3D health...", "info")
    
    # Wait for container to be ready
    max_attempts = 30
    for attempt in range(max_attempts):
        # Check container status
        success, output = run_command(["sudo", "docker", "ps", "--filter", "name=vista3d", "--format", "{{.Status}}"], 
                                    check=False, capture_output=True)
        
        if success and "Up" in output:
            print_status(f"✅ Vista3D container is running (attempt {attempt + 1})", "success")
            return True
        
        print_status(f"Waiting for Vista3D to start... ({attempt + 1}/{max_attempts})", "info")
        time.sleep(10)
    
    print_status("❌ Vista3D failed to start within expected time", "error")
    return False

def setup_vista3d_complete() -> bool:
    """Complete Vista3D setup process."""
    print_status("=== NVIDIA Vista3D NIM Setup ===", "info")
    print()
    
    # Check system requirements
    if not check_system_requirements():
        return False
    
    # Check NVIDIA GPU
    if not check_nvidia_gpu():
        return False
    
    # Check/Install Docker
    if not check_docker_installed():
        if not install_docker():
            return False
    
    # Install NVIDIA Container Toolkit
    if not install_nvidia_container_toolkit():
        return False
    
    # Test NVIDIA Docker
    if not test_nvidia_docker():
        return False
    
    # Get NVIDIA credentials
    api_key, org_id = prompt_nvidia_credentials()
    
    # Create .env file
    create_env_file(api_key, org_id)
    
    # Login to NGC
    if not docker_login_ngc(api_key):
        return False
    
    # Pull Vista3D image
    if not pull_vista3d_image():
        return False
    
    # Start Vista3D container
    if not start_vista3d_container(api_key, org_id):
        return False
    
    # Check health
    if not check_vista3d_health():
        return False
    
    print_status("🎉 Vista3D setup completed successfully!", "success")
    print()
    print_status("Vista3D is running on: http://localhost:8000", "server")
    print_status("API endpoint: http://localhost:8000/v1/vista3d/inference", "server")
    print()
    print_status("Next steps:", "info")
    print("  1. Run: python setup.py  (for full project setup)")
    print("  2. Place NIFTI files in: output/nifti/")
    print("  3. Start the viewer: streamlit run app.py")
    print()
    print_status("Useful commands:", "info")
    print("  • Check container logs: sudo docker logs vista3d")
    print("  • Stop Vista3D: sudo docker stop vista3d")
    print("  • Restart Vista3D: sudo docker restart vista3d")
    
    return True

def create_output_directories():
    """Create output directories for the project."""
    print_status("Creating output directories...", "directory")
    
    directories = [
        "output",
        "output/nifti", 
        "output/certs"
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print_status(f"   Created {directory}/", "success")
        else:
            print_status(f"   {directory}/ already exists", "info")
    
    print_status("   Output directory structure ready", "directory")

def setup_virtual_environment():
    """Set up virtual environment using uv."""
    print_status("Creating virtual environment...", "environment")
    
    # Create virtual environment
    success, _ = run_command(["uv", "venv"])
    if not success:
        print_status("Failed to create virtual environment", "error")
        return False
    
    print_status("Virtual environment created successfully", "success")
    return True

def install_dependencies():
    """Install dependencies from pyproject.toml."""
    print_status("Installing dependencies from pyproject.toml...", "package")
    
    # Activate virtual environment and install dependencies
    if os.name == 'nt':  # Windows
        activate_script = ".venv/Scripts/activate"
        pip_cmd = [".venv/Scripts/python", "-m", "pip", "install", "-e", "."]
    else:  # Unix/Linux/macOS
        activate_script = ".venv/bin/activate"
        pip_cmd = [".venv/bin/python", "-m", "pip", "install", "-e", "."]
    
    success, _ = run_command(pip_cmd)
    if not success:
        print_status("Failed to install dependencies", "error")
        return False
    
    print_status("Dependencies installed successfully", "success")
    return True

def is_server_running() -> bool:
    """Check if the HTTPS image server is already running."""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['cmdline'] and any('image_server.py' in cmd for cmd in proc.info['cmdline']):
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False

def start_http_server() -> Optional[int]:
    """Start HTTP image server in background."""
    print_status("Starting HTTP image server in background...", "server")
    
    # Check if server is already running
    if is_server_running():
        print_status("   HTTP image server is already running", "info")
        return None
    
    # Check if the server script exists
    server_script = Path("utils/image_server.py")
    if not server_script.exists():
        print_status("   Warning: utils/image_server.py not found, skipping server startup", "warning")
        return None
    
    # Start the server in background
    try:
        if os.name == 'nt':  # Windows
            python_cmd = ".venv/Scripts/python"
        else:  # Unix/Linux/macOS
            python_cmd = ".venv/bin/python"
        
        # Start server process
        process = subprocess.Popen(
            [python_cmd, str(server_script)],
            stdout=open("output/server.log", "w"),
            stderr=subprocess.STDOUT,
            start_new_session=True
        )
        
        # Wait a moment for server to start
        time.sleep(2)
        
        # Check if server started successfully
        if process.poll() is None:  # Process is still running
            print_status(f"   HTTP image server started successfully (PID: {process.pid})", "success")
            print_status("   Server logs: output/server.log", "info")
            print_status(f"   To stop server: kill {process.pid}", "info")
            return process.pid
        else:
            print_status("   Failed to start HTTP image server", "error")
            return None
            
    except Exception as e:
        print_status(f"   Error starting server: {e}", "error")
        return None

def run_dicom_conversion() -> bool:
    """Run DICOM to NIFTI conversion."""
    print_status("Running DICOM to NIFTI conversion...", "conversion")
    
    # Check if the conversion script exists
    conversion_script = Path("utils/dicom2nifti.py")
    if not conversion_script.exists():
        print_status("   Error: utils/dicom2nifti.py not found", "error")
        return False
    
    # Check if .env file exists
    if not Path(".env").exists():
        print_status("   Warning: .env file not found, conversion may fail", "warning")
        print_status("   Please ensure PROJECT_ROOT and DICOM_FOLDER are set in .env", "warning")
    
    # Check if output/nifti directory exists
    nifti_dir = Path("output/nifti")
    if not nifti_dir.exists():
        print_status("   Creating output/nifti directory...", "directory")
        nifti_dir.mkdir(parents=True, exist_ok=True)
    
    print_status("   Starting conversion process...", "conversion")
    print_status("   Conversion logs will be displayed below:", "info")
    print("-" * 60)
    
    # Run the conversion script
    try:
        if os.name == 'nt':  # Windows
            python_cmd = ".venv/Scripts/python"
        else:  # Unix/Linux/macOS
            python_cmd = ".venv/bin/python"
        
        result = subprocess.run([python_cmd, str(conversion_script)], check=False)
        
        print("-" * 60)
        
        if result.returncode == 0:
            print_status("   DICOM to NIFTI conversion completed successfully!", "success")
            
            # Count converted files
            nifti_files = list(nifti_dir.glob("*.nii.gz"))
            if nifti_files:
                print_status(f"   Converted files: {len(nifti_files)} NIFTI files", "info")
            else:
                print_status("   No NIFTI files found in output/nifti/", "info")
            
            return True
        else:
            print_status("   DICOM to NIFTI conversion failed!", "error")
            return False
            
    except Exception as e:
        print_status(f"   Error during conversion: {e}", "error")
        return False

def get_server_status() -> Tuple[bool, Optional[int]]:
    """Get current server status."""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['cmdline'] and any('image_server.py' in cmd for cmd in proc.info['cmdline']):
                return True, proc.info['pid']
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False, None

def get_conversion_status() -> int:
    """Get count of converted NIFTI files."""
    nifti_dir = Path("output/nifti")
    if nifti_dir.exists():
        return len(list(nifti_dir.glob("*.nii.gz")))
    return 0

def print_final_status():
    """Print final setup status."""
    print_status("Setup completed successfully!", "success")
    print()
    
    print_status("Output directories created:", "directory")
    print("   • output/")
    print("   • output/nifti/")
    print("   • output/certs/")
    
    # Server status
    server_running, server_pid = get_server_status()
    print()
    print_status("HTTPS image server status:", "server")
    if server_running:
        print(f"   • Running (PID: {server_pid})")
        print("   • Logs: output/server.log")
    else:
        print("   • Not running")
    
    # Conversion status
    print()
    print_status("DICOM conversion status:", "conversion")
    nifti_count = get_conversion_status()
    if nifti_count > 0:
        print(f"   • Converted files: {nifti_count} NIFTI files")
        print("   • Location: output/nifti/")
    else:
        print("   • No NIFTI files found")
    
    print()
    print_status("To activate the environment in the future, run:", "info")
    if os.name == 'nt':  # Windows
        print("   .venv\\Scripts\\activate")
    else:  # Unix/Linux/macOS
        print("   source .venv/bin/activate")
    
    print()
    print_status("To deactivate, run:", "info")
    print("   deactivate")
    
    print()
    print_status("To start the HTTPS server manually:", "info")
    print("   python setup.py --start-server")
    
    print()
    print_status("To run DICOM conversion manually:", "info")
    print("   python setup.py --convert-dicom")

def main():
    """Main setup function."""
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--setup-vista3d":
            print_status("Starting NVIDIA Vista3D NIM setup...", "info")
            success = setup_vista3d_complete()
            sys.exit(0 if success else 1)
        elif sys.argv[1] == "--start-server":
            pid = start_http_server()
            if pid:
                print(f"Server started with PID: {pid}")
            return
        elif sys.argv[1] == "--convert-dicom":
            success = run_dicom_conversion()
            sys.exit(0 if success else 1)
        elif sys.argv[1] == "--help":
            print("Usage: python setup.py [OPTION]")
            print("Options:")
            print("  --setup-vista3d   Complete Vista3D NIM setup on Ubuntu")
            print("  --start-server    Start HTTPS image server only")
            print("  --convert-dicom   Run DICOM conversion only")
            print("  --help           Show this help message")
            print("  (no args)        Run standard project setup")
            return
    
    print_status("Setting up NV project environment...", "info")
    
    # Check if uv is installed
    if not check_uv_installed():
        print_status("Error: uv is not installed. Please install uv first:", "error")
        print("   curl -LsSf https://astral.sh/uv/install.sh | sh")
        sys.exit(1)
    
    print_status("uv is installed", "success")
    
    # Create output directories
    create_output_directories()
    
    # Set up virtual environment
    if not setup_virtual_environment():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Start HTTPS image server
    start_http_server()
    
    # Run DICOM to NIFTI conversion
    run_dicom_conversion()
    
    # Print final status
    print_final_status()

if __name__ == "__main__":
    main()
