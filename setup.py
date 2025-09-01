#!/usr/bin/env python3
"""
NV Project Setup Script
Automates the setup of the NV project environment including:
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

def create_output_directories():
    """Create output directories for the project."""
    print_status("Creating output directories...", "directory")
    
    directories = [
        "outputs",
        "outputs/nifti", 
        "outputs/certs"
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

def start_https_server() -> Optional[int]:
    """Start HTTPS image server in background."""
    print_status("Starting HTTPS image server in background...", "server")
    
    # Check if server is already running
    if is_server_running():
        print_status("   HTTPS image server is already running", "info")
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
            stdout=open("outputs/server.log", "w"),
            stderr=subprocess.STDOUT,
            start_new_session=True
        )
        
        # Wait a moment for server to start
        time.sleep(2)
        
        # Check if server started successfully
        if process.poll() is None:  # Process is still running
            print_status(f"   HTTPS image server started successfully (PID: {process.pid})", "success")
            print_status("   Server logs: outputs/server.log", "info")
            print_status(f"   To stop server: kill {process.pid}", "info")
            return process.pid
        else:
            print_status("   Failed to start HTTPS image server", "error")
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
    
    # Check if outputs/nifti directory exists
    nifti_dir = Path("outputs/nifti")
    if not nifti_dir.exists():
        print_status("   Creating outputs/nifti directory...", "directory")
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
                print_status("   No NIFTI files found in outputs/nifti/", "info")
            
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
    nifti_dir = Path("outputs/nifti")
    if nifti_dir.exists():
        return len(list(nifti_dir.glob("*.nii.gz")))
    return 0

def print_final_status():
    """Print final setup status."""
    print_status("Setup completed successfully!", "success")
    print()
    
    print_status("Output directories created:", "directory")
    print("   • outputs/")
    print("   • outputs/nifti/")
    print("   • outputs/certs/")
    
    # Server status
    server_running, server_pid = get_server_status()
    print()
    print_status("HTTPS image server status:", "server")
    if server_running:
        print(f"   • Running (PID: {server_pid})")
        print("   • Logs: outputs/server.log")
    else:
        print("   • Not running")
    
    # Conversion status
    print()
    print_status("DICOM conversion status:", "conversion")
    nifti_count = get_conversion_status()
    if nifti_count > 0:
        print(f"   • Converted files: {nifti_count} NIFTI files")
        print("   • Location: outputs/nifti/")
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
    print_status("Setting up NV project environment...", "info")
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--start-server":
            pid = start_https_server()
            if pid:
                print(f"Server started with PID: {pid}")
            return
        elif sys.argv[1] == "--convert-dicom":
            success = run_dicom_conversion()
            sys.exit(0 if success else 1)
        elif sys.argv[1] == "--help":
            print("Usage: python setup.py [OPTION]")
            print("Options:")
            print("  --start-server    Start HTTPS image server only")
            print("  --convert-dicom   Run DICOM conversion only")
            print("  --help           Show this help message")
            print("  (no args)        Run full setup")
            return
    
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
    start_https_server()
    
    # Run DICOM to NIFTI conversion
    run_dicom_conversion()
    
    # Print final status
    print_final_status()

if __name__ == "__main__":
    main()
