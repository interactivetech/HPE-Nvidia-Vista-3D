#!/usr/bin/env python3
"""
HPE NVIDIA Vista3D - Backend Setup Script
Sets up the backend components (Vista3D AI server) for Vista3D
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

class Vista3DBackendSetup:
    """Setup for Vista3D backend components (Vista3D AI server)"""
    
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
        print("🧠 HPE NVIDIA Vista3D - Backend Setup")
        print("="*80)
        print("This script will set up the backend components for Vista3D:")
        print("- Vista3D AI server (port 8000)")
        print("- GPU-accelerated medical image segmentation")
        print("="*80)
        
        print("\n📋 WHAT THIS SETUP DOES:")
        print("-" * 40)
        print("✅ Sets up Python environment with backend dependencies")
        print("✅ Configures Docker containers for Vista3D AI server")
        print("✅ Sets up NVIDIA GPU access and CUDA support")
        print("✅ Configures Vista3D AI server for medical segmentation")
        print("✅ Creates necessary directories and files")
        print("✅ Configures networking for external access")
        
        print("\n🔧 REQUIREMENTS:")
        print("-" * 40)
        print("• Ubuntu Linux (18.04+) or macOS")
        print("• NVIDIA GPU with CUDA support (8GB+ VRAM recommended)")
        print("• 16GB+ RAM for large medical imaging datasets")
        print("• Docker and NVIDIA Container Toolkit (REQUIRED)")
        print("• NVIDIA NGC account and API key")
        print("• Internet connectivity")
        
        print("="*80 + "\n")
    
    def check_system_requirements(self) -> bool:
        """Check system requirements for backend"""
        print("\n" + "="*60)
        print("🔍 CHECKING BACKEND SYSTEM REQUIREMENTS")
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
            print("   NVIDIA GPUs are required for Vista3D backend")
            issues.append("NVIDIA GPU required for Vista3D backend")
        
        # Check NVIDIA Container Toolkit
        print("\n📍 Checking NVIDIA Container Toolkit...")
        if not self.check_nvidia_container_toolkit():
            print("❌ NVIDIA Container Toolkit not found")
            print("   Required for GPU access in Docker containers")
            issues.append("NVIDIA Container Toolkit not found")
        else:
            print("✅ NVIDIA Container Toolkit is available")
        
        # Check memory (more strict for backend)
        print("\n📍 Checking system memory...")
        try:
            if self.system_info['platform'] == 'Linux':
                with open('/proc/meminfo', 'r') as f:
                    meminfo = f.read()
                for line in meminfo.split('\n'):
                    if line.startswith('MemTotal:'):
                        total_kb = int(line.split()[1])
                        total_gb = total_kb / (1024 * 1024)
                        if total_gb < 16:
                            print(f"⚠️  Low memory: {total_gb:.1f}GB (recommended: 16GB+)")
                            print("   Vista3D may run slowly with insufficient memory")
                        else:
                            print(f"✅ Sufficient memory: {total_gb:.1f}GB")
                        break
            else:
                print("✅ Memory check skipped on macOS")
        except Exception as e:
            print(f"⚠️  Could not check memory: {e}")
        
        # Summary
        print("\n" + "-"*60)
        if issues:
            print("❌ BACKEND REQUIREMENTS SUMMARY:")
            print(f"   Found {len(issues)} issue(s) that need attention:")
            for i, issue in enumerate(issues, 1):
                print(f"   {i}. {issue}")
            return False
        else:
            print("✅ BACKEND REQUIREMENTS SUMMARY:")
            print("   All backend requirements are met!")
            print("   Your system is ready for backend setup.")
        
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
    
    def get_ngc_api_key(self) -> Optional[str]:
        """Get NGC API key from environment variable, .env file, or prompt user"""
        # First check environment variable
        api_key = os.getenv('NGC_API_KEY')
        if api_key and api_key.startswith('nvapi-') and len(api_key) > 10:
            print("✅ Found NGC API key in environment variable")
            return api_key
        
        # Then check .env file if it exists
        if self.env_file.exists():
            try:
                with open(self.env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('NGC_API_KEY='):
                            # Extract value, handling both quoted and unquoted values
                            value = line.split('=', 1)[1].strip()
                            if value.startswith('"') and value.endswith('"'):
                                value = value[1:-1]
                            elif value.startswith("'") and value.endswith("'"):
                                value = value[1:-1]
                            
                            if value.startswith('nvapi-') and len(value) > 10:
                                print("✅ Found NGC API key in .env file")
                                return value
            except Exception as e:
                logger.warning(f"Could not read .env file: {e}")
        
        # If not found, return None to prompt user
        return None
    
    def get_ngc_org_id(self) -> Optional[str]:
        """Get NGC Organization ID from environment variable, .env file, or prompt user"""
        # First check environment variable
        org_id = os.getenv('NGC_ORG_ID')
        if org_id and org_id.strip():
            print("✅ Found NGC Organization ID in environment variable")
            return org_id.strip()
        
        # Then check .env file if it exists
        if self.env_file.exists():
            try:
                with open(self.env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('NGC_ORG_ID='):
                            # Extract value, handling both quoted and unquoted values
                            value = line.split('=', 1)[1].strip()
                            if value.startswith('"') and value.endswith('"'):
                                value = value[1:-1]
                            elif value.startswith("'") and value.endswith("'"):
                                value = value[1:-1]
                            
                            if value.strip():
                                print("✅ Found NGC Organization ID in .env file")
                                return value.strip()
            except Exception as e:
                logger.warning(f"Could not read .env file: {e}")
        
        # If not found, return None to prompt user
        return None
    
    def setup_python_environment(self) -> bool:
        """Set up Python environment for backend"""
        print("\n" + "="*60)
        print("🐍 SETTING UP PYTHON ENVIRONMENT (BACKEND)")
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
        print("\n📍 Installing backend dependencies...")
        try:
            print("🔧 Running 'uv sync' to install dependencies...")
            result = subprocess.run(['uv', 'sync'], cwd=self.project_root, 
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                 text=True, universal_newlines=True)
            
            if result.returncode == 0:
                print("✅ Backend dependencies installed successfully")
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
        """Gather configuration for backend"""
        print("\n" + "="*60)
        print("📝 BACKEND CONFIGURATION")
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
        
        # Try to get API key from environment or .env file first
        api_key = self.get_ngc_api_key()
        
        if api_key is None:
            # Prompt user for API key if not found
            print("   No valid API key found in environment or .env file")
            while True:
                api_key = input("Enter your NGC API Key (starts with 'nvapi-'): ").strip()
                if api_key.startswith('nvapi-') and len(api_key) > 10:
                    print("✅ API key accepted")
                    break
                print("❌ Invalid API key. Must start with 'nvapi-' and be longer than 10 characters.")
        
        config['NGC_API_KEY'] = api_key
        
        # Try to get Organization ID from environment or .env file first
        org_id = self.get_ngc_org_id()
        
        if org_id is None:
            # Prompt user for Organization ID if not found
            print("   No Organization ID found in environment or .env file")
            org_id = input("Enter NGC Organization ID [nvidia]: ").strip() or "nvidia"
        else:
            print(f"   Using Organization ID: {org_id}")
        
        config['NGC_ORG_ID'] = org_id
        config['LOCAL_NIM_CACHE'] = str(Path.home() / ".cache" / "nim")
        
        # Segmentation settings
        config['VESSELS_OF_INTEREST'] = "all"
        print("✅ Segmentation: All detectable structures")
        
        # GPU configuration
        print("\n📍 GPU Configuration:")
        cuda_devices = input("CUDA devices to use [0]: ").strip() or "0"
        gpu_memory_fraction = input("GPU memory fraction [0.9]: ").strip() or "0.9"
        
        config['CUDA_VISIBLE_DEVICES'] = cuda_devices
        config['NVIDIA_VISIBLE_DEVICES'] = cuda_devices
        config['GPU_MEMORY_FRACTION'] = gpu_memory_fraction
        print(f"✅ CUDA devices: {cuda_devices}")
        print(f"✅ GPU memory fraction: {gpu_memory_fraction}")
        
        # Performance settings
        print("\n📍 Performance Configuration:")
        memory_limit = input("Container memory limit [16G]: ").strip() or "16G"
        cpu_limit = input("Container CPU limit [8]: ").strip() or "8"
        shm_size = input("Shared memory size [12G]: ").strip() or "12G"
        
        config['VISTA3D_MEMORY_LIMIT'] = memory_limit
        config['VISTA3D_CPU_LIMIT'] = cpu_limit
        config['VISTA3D_SHM_SIZE'] = shm_size
        print(f"✅ Memory limit: {memory_limit}")
        print(f"✅ CPU limit: {cpu_limit}")
        print(f"✅ Shared memory: {shm_size}")
        
        # Network configuration
        print("\n📍 Network Configuration:")
        use_host_networking = input("Use host networking? (Y/n): ").strip().lower() not in ['n', 'no']
        vista3d_port = input("Vista3D port [8000]: ").strip() or "8000"
        
        config['USE_HOST_NETWORKING'] = str(use_host_networking)
        config['VISTA3D_PORT'] = vista3d_port
        print(f"✅ Host networking: {use_host_networking}")
        print(f"✅ Vista3D port: {vista3d_port}")
        
        # Auto-restart configuration
        print("\n📍 Auto-restart Configuration:")
        auto_restart = input("Enable auto-restart on failure? (Y/n): ").strip().lower() not in ['n', 'no']
        config['VISTA3D_AUTO_RESTART'] = str(auto_restart)
        print(f"✅ Auto-restart: {auto_restart}")
        
        return config
    
    def create_env_file(self, config: Dict) -> bool:
        """Create .env file for backend"""
        logger.info("📄 Creating .env file for backend...")
        
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
        """Create required directories for backend"""
        logger.info("📁 Creating required directories...")
        
        try:
            directories = [
                Path(config['DICOM_FOLDER']),
                Path(config['OUTPUT_FOLDER']),
                Path(config['OUTPUT_FOLDER']) / "nifti",
                Path(config['OUTPUT_FOLDER']) / "logs",
                Path(config['OUTPUT_FOLDER']) / "scans",
                Path(config['LOCAL_NIM_CACHE'])
            ]
            
            for directory in directories:
                directory.mkdir(parents=True, exist_ok=True)
                logger.info(f"✅ Created directory: {directory}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create directories: {e}")
            return False
    
    def test_gpu_access(self) -> bool:
        """Test GPU access in Docker"""
        print("\n" + "="*60)
        print("🎯 TESTING GPU ACCESS")
        print("="*60)
        
        print("\n📍 Testing GPU access in Docker container...")
        try:
            result = subprocess.run([
                'docker', 'run', '--rm', '--gpus', 'all',
                'nvidia/cuda:11.0-base-ubuntu20.04', 'nvidia-smi'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ GPU access in Docker is working")
                print("   NVIDIA Container Toolkit is properly configured")
                return True
            else:
                print("❌ GPU access in Docker failed")
                print("   NVIDIA Container Toolkit may not be properly configured")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ GPU test timed out")
            return False
        except Exception as e:
            print(f"❌ Error testing GPU access: {e}")
            return False
    
    def print_next_steps(self, config: Dict):
        """Print next steps for backend"""
        print("\n" + "="*80)
        print("🎉 BACKEND SETUP COMPLETE!")
        print("="*80)
        
        print("\n📋 NEXT STEPS:")
        print("\n1. 🚀 Start Vista3D backend:")
        print("   python start_backend.py")
        print("   • This starts the Vista3D AI server")
        print("   • Requires NVIDIA GPU and NGC API key")
        print("   • Will run in Docker container with GPU access")
        
        print("\n2. 🌐 Start frontend services (on any machine):")
        print("   python start_frontend.py")
        print("   • This starts the Streamlit app and image server")
        print("   • Can run on the same machine or different machine")
        print("   • Will connect to this Vista3D backend")
        
        print("\n3. 📁 Add your medical images:")
        print(f"   • Place DICOM files in: {config['DICOM_FOLDER']}")
        print("   • Or place NIFTI files in: output/nifti/")
        
        print("\n4. 🧠 Test AI segmentation:")
        vista3d_port = config.get('VISTA3D_PORT', '8000')
        print(f"   • Vista3D API available at: http://localhost:{vista3d_port}")
        print("   • Health check: curl http://localhost:8000/health")
        print("   • Use frontend interface to run segmentation")
        
        print(f"\n📄 Configuration saved to: {self.env_file}")
        print("🔐 Keep your .env file secure - it contains your NGC API key")
        
        print("\n" + "="*80)
    
    def run_setup(self) -> bool:
        """Run the complete backend setup process"""
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
            
            # Step 6: Test GPU access
            if not self.test_gpu_access():
                print("\n⚠️  GPU access test failed, but continuing...")
                print("   You may need to configure NVIDIA Container Toolkit")
                print("   See: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html")
            
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
        description="HPE NVIDIA Vista3D - Backend Setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script sets up the backend components of the Vista3D platform.

Backend Components:
  • Vista3D AI server (port 8000)
  • GPU-accelerated medical image segmentation
  • NVIDIA NGC integration

Requirements:
  • Ubuntu Linux (18.04+) or macOS
  • NVIDIA GPU with CUDA support (8GB+ VRAM recommended)
  • 16GB+ RAM for large medical imaging datasets
  • Docker and NVIDIA Container Toolkit (REQUIRED)
  • NVIDIA NGC account and API key

The setup will:
  1. Check system requirements (GPU, Docker, etc.)
  2. Set up Python environment with dependencies
  3. Configure Docker containers for Vista3D AI server
  4. Set up NVIDIA GPU access and CUDA support
  5. Create necessary directories and files
  6. Test GPU access in Docker
  7. Provide instructions for starting services

After setup, run 'python start_backend.py' to start Vista3D AI server.
        """
    )
    
    args = parser.parse_args()
    
    setup = Vista3DBackendSetup()
    
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
