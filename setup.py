#!/usr/bin/env python3
"""
HPE NVIDIA Vista3D - Unified Setup Script
Simplified setup for single GPU-enabled host running all services locally
"""

import os
import sys
import subprocess
import argparse
import logging
import shutil
import json
import platform
from pathlib import Path
from typing import Dict, List, Optional
import time
import requests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class Vista3DUnifiedSetup:
    """Unified setup for Vista3D on single GPU-enabled host"""
    
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.project_root = self.script_dir
        self.env_file = self.project_root / '.env'
        self.env_template = self.project_root / 'dot_env_template'
        
        # System information
        self.system_info = {
            'platform': platform.system(),
            'release': platform.release(),
            'architecture': platform.machine(),
            'python_version': platform.python_version()
        }
        
        # Configuration storage
        self.config = {}
        
    def print_banner(self):
        """Print setup banner"""
        print("\n" + "="*80)
        print("🚀 HPE NVIDIA Vista3D - Unified Setup")
        print("="*80)
        print("This script will set up the complete Vista3D platform on your GPU-enabled host.")
        print("It will configure and start all services (frontend, image server, and Vista3D AI).")
        print("="*80)
        
        print("\n📋 WHAT THIS SETUP DOES:")
        print("-" * 40)
        print("✅ Sets up Python environment with all dependencies")
        print("✅ Configures Docker containers for all services")
        print("✅ Sets up Vista3D AI server (requires NVIDIA GPU)")
        print("✅ Configures web interface and image server")
        print("✅ Creates all necessary directories and files")
        print("✅ Starts all services automatically")
        
        print("\n🔧 REQUIREMENTS:")
        print("-" * 40)
        print("• Ubuntu Linux (18.04+) or macOS")
        print("• NVIDIA GPU with CUDA support (8GB+ VRAM recommended)")
        print("• 16GB+ RAM")
        print("• Docker and NVIDIA Container Toolkit (REQUIRED)")
        print("• NVIDIA NGC account and API key")
        print("• Internet connectivity")
        
        print("="*80 + "\n")
    
    def check_system_requirements(self) -> bool:
        """Check system requirements"""
        print("\n" + "="*60)
        print("🔍 CHECKING SYSTEM REQUIREMENTS")
        print("="*60)
        
        issues = []
        
        # Check Python version
        print("\n📍 Checking Python version...")
        python_version = tuple(map(int, platform.python_version().split('.')[:2]))
        if python_version < (3, 11):
            print(f"❌ Python version check failed")
            print(f"   Required: Python 3.11 or higher")
            print(f"   Found: Python {platform.python_version()}")
            issues.append(f"Python 3.11+ required, found {platform.python_version()}")
        else:
            print(f"✅ Python version check passed")
            print(f"   Found: Python {platform.python_version()}")
        
        # Check operating system
        print("\n📍 Checking operating system...")
        if self.system_info['platform'] not in ['Linux', 'Darwin']:
            print(f"❌ Operating system check failed")
            print(f"   Required: Linux or macOS")
            print(f"   Found: {self.system_info['platform']}")
            issues.append(f"Linux or macOS required, found {self.system_info['platform']}")
        else:
            print(f"✅ Operating system check passed")
            print(f"   Platform: {self.system_info['platform']} {self.system_info['release']}")
        
        # Check Docker
        print("\n📍 Checking Docker...")
        if not shutil.which('docker'):
            print("❌ Docker not found")
            print("   Docker is required for Vista3D containers")
            issues.append("Docker not found")
        else:
            try:
                result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
                if result.returncode != 0:
                    print("❌ Docker daemon not running")
                    print("   Start Docker with: sudo systemctl start docker")
                    issues.append("Docker daemon not running")
                else:
                    print("✅ Docker is available and running")
            except Exception as e:
                print(f"❌ Docker error: {e}")
                issues.append(f"Docker error: {e}")
        
        # Check NVIDIA GPU
        print("\n📍 Checking NVIDIA GPU...")
        nvidia_gpus = self.check_nvidia_gpus()
        if nvidia_gpus['has_gpus']:
            print(f"✅ NVIDIA GPU(s) detected:")
            for i, gpu in enumerate(nvidia_gpus['gpus']):
                print(f"   {i+1}. {gpu['name']} ({gpu['memory']})")
            print("   This system can run Vista3D AI models")
        else:
            print("❌ No NVIDIA GPUs detected")
            print("   NVIDIA GPUs are required for Vista3D")
            issues.append("NVIDIA GPU required for Vista3D")
        
        # Check NVIDIA Container Toolkit
        print("\n📍 Checking NVIDIA Container Toolkit...")
        if not self.check_nvidia_container_toolkit():
            print("❌ NVIDIA Container Toolkit not found")
            print("   Required for GPU access in Docker containers")
            issues.append("NVIDIA Container Toolkit not found")
        else:
            print("✅ NVIDIA Container Toolkit is available")
        
        # Summary
        print("\n" + "-"*60)
        if issues:
            print("❌ SYSTEM REQUIREMENTS SUMMARY:")
            print(f"   Found {len(issues)} issue(s) that need attention:")
            for i, issue in enumerate(issues, 1):
                print(f"   {i}. {issue}")
            return False
        else:
            print("✅ SYSTEM REQUIREMENTS SUMMARY:")
            print("   All system requirements are met!")
            print("   Your system is ready for Vista3D setup.")
        
        return True
    
    def check_nvidia_gpus(self) -> Dict:
        """Check for NVIDIA GPUs"""
        try:
            result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader,nounits'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout.strip():
                gpus = []
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        parts = line.split(',')
                        if len(parts) >= 2:
                            name = parts[0].strip()
                            memory_mb = parts[1].strip()
                            try:
                                memory_gb = int(memory_mb) / 1024
                                gpus.append({
                                    'name': name,
                                    'memory': f"{memory_gb:.1f} GB",
                                    'memory_mb': int(memory_mb)
                                })
                            except:
                                gpus.append({
                                    'name': name,
                                    'memory': f"{memory_mb} MB",
                                    'memory_mb': 0
                                })
                
                return {
                    'has_gpus': len(gpus) > 0,
                    'gpu_count': len(gpus),
                    'gpus': gpus,
                    'total_memory_gb': sum(gpu['memory_mb'] for gpu in gpus) / 1024 if gpus else 0
                }
            else:
                return {'has_gpus': False, 'gpu_count': 0, 'gpus': [], 'total_memory_gb': 0}
                
        except Exception:
            return {'has_gpus': False, 'gpu_count': 0, 'gpus': [], 'total_memory_gb': 0}
    
    def check_nvidia_container_toolkit(self) -> bool:
        """Check if NVIDIA Container Toolkit is installed"""
        try:
            result = subprocess.run(['which', 'nvidia-ctk'], capture_output=True, text=True)
            if result.returncode == 0:
                result = subprocess.run(['docker', 'info'], capture_output=True, text=True)
                if 'nvidia' in result.stdout.lower():
                    return True
            return False
        except Exception:
            return False
    
    def setup_python_environment(self) -> bool:
        """Set up Python environment"""
        print("\n" + "="*60)
        print("🐍 SETTING UP PYTHON ENVIRONMENT")
        print("="*60)
        
        # Check for uv package manager
        print("\n📍 Checking for 'uv' package manager...")
        if not shutil.which('uv'):
            print("⚠️  'uv' package manager not found")
            print("   Installing uv package manager...")
            if not self.install_uv():
                print("❌ Failed to install uv package manager")
                return False
            else:
                print("✅ uv package manager installed successfully")
        else:
            print("✅ uv package manager is available")
        
        # Install dependencies
        print("\n📍 Installing project dependencies...")
        try:
            print("🔧 Running 'uv sync' to install dependencies...")
            result = subprocess.run(['uv', 'sync'], cwd=self.project_root, 
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                 text=True, universal_newlines=True)
            
            if result.returncode == 0:
                print("✅ Dependencies installed successfully")
                return True
            else:
                print("❌ Dependency installation failed")
                print(result.stdout)
                return False
                
        except Exception as e:
            print(f"❌ Error during dependency installation: {e}")
            return False
    
    def install_uv(self) -> bool:
        """Install uv package manager"""
        try:
            if self.system_info['platform'] == 'Darwin':  # macOS
                subprocess.run([
                    'curl', '-LsSf', 'https://astral.sh/uv/install.sh'
                ], stdout=subprocess.PIPE, check=True)
            else:  # Linux
                subprocess.run([
                    'curl', '-LsSf', 'https://astral.sh/uv/install.sh'
                ], stdout=subprocess.PIPE, check=True)
            
            # Verify installation
            result = subprocess.run(['uv', '--version'], capture_output=True, text=True, check=True)
            logger.info(f"✅ uv installed successfully: {result.stdout.strip()}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to install uv: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error installing uv: {e}")
            return False
    
    def gather_configuration(self) -> Dict:
        """Gather configuration from user"""
        print("\n" + "="*60)
        print("📝 CONFIGURATION")
        print("="*60)
        
        config = {}
        
        # Project paths
        print("\n📍 Setting up project paths...")
        print(f"✅ Project root: {self.project_root.absolute()}")
        
        config['DICOM_FOLDER'] = str(self.project_root / "dicom")
        config['OUTPUT_FOLDER'] = str(self.project_root / "output")
        print(f"✅ DICOM folder: {config['DICOM_FOLDER']}")
        print(f"✅ Output folder: {config['OUTPUT_FOLDER']}")
        
        # Server URLs
        config['IMAGE_SERVER'] = "http://localhost:8888"
        config['VISTA3D_SERVER'] = "http://localhost:8000"
        print(f"✅ Image server: {config['IMAGE_SERVER']}")
        print(f"✅ Vista3D server: {config['VISTA3D_SERVER']}")
        
        # NGC credentials
        print("\n📍 NVIDIA NGC Configuration:")
        print("   Get your API key from: https://ngc.nvidia.com/")
        
        while True:
            api_key = input("Enter your NGC API Key (starts with 'nvapi-'): ").strip()
            if api_key.startswith('nvapi-') and len(api_key) > 10:
                config['NGC_API_KEY'] = api_key
                print("✅ API key accepted")
                break
            print("❌ Invalid API key. Must start with 'nvapi-' and be longer than 10 characters.")
        
        config['NGC_ORG_ID'] = input("Enter NGC Organization ID [nvidia]: ").strip() or "nvidia"
        config['LOCAL_NIM_CACHE'] = str(Path.home() / ".cache" / "nim")
        
        # Segmentation settings
        config['VESSELS_OF_INTEREST'] = "all"
        print("✅ Segmentation: All detectable structures")
        
        return config
    
    def create_env_file(self, config: Dict) -> bool:
        """Create .env file"""
        logger.info("📄 Creating .env file...")
        
        try:
            # Read template
            if not self.env_template.exists():
                logger.error(f"Template file not found: {self.env_template}")
                return False
            
            with open(self.env_template, 'r') as f:
                env_content = f.read()
            
            # Replace template values
            for key, value in config.items():
                lines = env_content.split('\n')
                for i, line in enumerate(lines):
                    if line.startswith(f'{key}='):
                        lines[i] = f'{key}="{value}"'
                        break
                env_content = '\n'.join(lines)
            
            # Write .env file
            with open(self.env_file, 'w') as f:
                f.write(env_content)
            
            logger.info(f"✅ Created .env file: {self.env_file}")
            os.chmod(self.env_file, 0o600)
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create .env file: {e}")
            return False
    
    def create_directories(self, config: Dict) -> bool:
        """Create required directories"""
        logger.info("📁 Creating required directories...")
        
        try:
            directories = [
                Path(config['DICOM_FOLDER']),
                Path(config['OUTPUT_FOLDER']),
                Path(config['OUTPUT_FOLDER']) / "nifti",
                Path(config['OUTPUT_FOLDER']) / "scans",
                Path(config['OUTPUT_FOLDER']) / "voxels"
            ]
            
            for directory in directories:
                directory.mkdir(parents=True, exist_ok=True)
                logger.info(f"✅ Created directory: {directory}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create directories: {e}")
            return False
    
    def print_next_steps(self, config: Dict):
        """Print next steps"""
        print("\n" + "="*80)
        print("🎉 SETUP COMPLETE!")
        print("="*80)
        
        print("\n📋 NEXT STEPS:")
        print("\n1. 🚀 Start all services:")
        print("   python start.py")
        print("   • This starts the web interface, image server, and Vista3D AI")
        print("   • All services will run in Docker containers")
        
        print("\n2. 📁 Add your medical images:")
        print(f"   • Place DICOM files in: {config['DICOM_FOLDER']}")
        print("   • Or place NIFTI files in: output/nifti/")
        
        print("\n3. 🌐 Access the web interface:")
        print("   • Open your browser to: http://localhost:8501")
        print("   • Use the Tools page to convert DICOM to NIFTI")
        print("   • Use the Tools page to run AI segmentation")
        print("   • View 3D visualizations of your results")
        
        print(f"\n📄 Configuration saved to: {self.env_file}")
        print("🔐 Keep your .env file secure - it contains your API key")
        
        print("\n" + "="*80)
    
    def run_setup(self) -> bool:
        """Run the complete setup process"""
        try:
            self.print_banner()
            
            # Step 1: Check system requirements
            if not self.check_system_requirements():
                print("\n❌ System requirements not met. Please resolve issues and try again.")
                return False
            
            # Step 2: Set up Python environment
            if not self.setup_python_environment():
                print("\n❌ Python environment setup failed.")
                return False
            
            # Step 3: Gather configuration
            config = self.gather_configuration()
            
            # Step 4: Create .env file
            if not self.create_env_file(config):
                print("\n❌ Failed to create .env file")
                return False
            
            # Step 5: Create directories
            if not self.create_directories(config):
                print("\n❌ Failed to create directories")
                return False
            
            # Final step: Show next steps
            self.print_next_steps(config)
            
            return True
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Setup interrupted by user")
            return False
        except Exception as e:
            print(f"\n❌ Unexpected error during setup: {e}")
            return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="HPE NVIDIA Vista3D - Unified Setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script sets up the complete Vista3D platform on a single GPU-enabled host.

Requirements:
  • Ubuntu Linux (18.04+) or macOS
  • NVIDIA GPU with CUDA support (8GB+ VRAM recommended)
  • 16GB+ RAM
  • Docker and NVIDIA Container Toolkit
  • NVIDIA NGC account and API key

The setup will:
  1. Check system requirements
  2. Set up Python environment with dependencies
  3. Configure Docker containers
  4. Set up Vista3D AI server
  5. Create necessary directories and files
  6. Provide instructions for starting services

After setup, run 'python start.py' to start all services.
        """
    )
    
    args = parser.parse_args()
    
    setup = Vista3DUnifiedSetup()
    
    try:
        success = setup.run_setup()
        sys.exit(0 if success else 1)
            
    except KeyboardInterrupt:
        logger.info("\nSetup cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
