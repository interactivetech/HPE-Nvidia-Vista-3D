#!/usr/bin/env python3
"""
HPE NVIDIA Vista3D Frontend Setup Script
Interactive setup for Vista3D frontend (web interface and image server)
"""

import os
import sys
import subprocess
import argparse
import logging
import shutil
import json
import socket
import getpass
import platform
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import tempfile
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

class Vista3DFrontendSetupManager:
    """Interactive setup manager for the Vista3D frontend"""
    
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.project_root = self.script_dir
        self.env_file = self.project_root / '.env'
        self.env_template = self.project_root / 'dot_env_template'
        self.setup_state_file = self.project_root / '.setup_state_frontend.json'
        
        # System information
        self.system_info = {
            'platform': platform.system(),
            'release': platform.release(),
            'architecture': platform.machine(),
            'python_version': platform.python_version()
        }
        
        # Configuration storage
        self.config = {}
        
        # Setup state tracking
        self.setup_state = self._load_setup_state()
        
    def print_banner(self):
        """Print setup banner"""
        print("\n" + "="*80)
        print("🚀 HPE NVIDIA Vista3D Frontend Setup")
        print("="*80)
        print("This script will guide you through setting up the Vista3D frontend")
        print("(web interface and image server) for medical imaging visualization.")
        print("It will:")
        print("  • Check system requirements")
        print("  • Set up Python environment")
        print("  • Configure web interface and image server")
        print("  • Set up for remote Vista3D server connection")
        print("="*80)
        
        print("\n📋 VISTA3D FRONTEND WORKFLOW:")
        print("-" * 40)
        print("The Vista3D frontend provides web-based medical imaging interface:")
        print("  1. 📁 Upload and manage DICOM files")
        print("  2. 🔄 Convert DICOM to NIfTI format")
        print("  3. 🌐 Serve images via web interface")
        print("  4. 🧠 Send data to Vista3D server for AI processing")
        print("  5. 📊 Visualize and analyze results")
        
        print("\n🔧 FRONTEND REQUIREMENTS:")
        print("-" * 40)
        print("• Python 3.11+")
        print("• Internet connectivity")
        print("• Web browser (Chrome, Firefox, Safari, Edge)")
        print("• Optional: Docker for containerized deployment")
        print("• Optional: NVIDIA GPU for local Vista3D processing")
        
        print("="*80 + "\n")
    
    def _load_setup_state(self) -> Dict:
        """Load setup state from previous runs"""
        try:
            if self.setup_state_file.exists():
                with open(self.setup_state_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load setup state: {e}")
        
        return {
            'system_requirements_checked': False,
            'python_environment_ready': False,
            'configuration_gathered': False,
            'env_file_created': False,
            'directories_created': False,
            'dependencies_installed': False,
            'last_successful_step': None,
            'last_run_timestamp': None
        }
    
    def _save_setup_state(self, step_name: str, success: bool = True):
        """Save current setup state"""
        try:
            if success:
                self.setup_state[step_name] = True
                self.setup_state['last_successful_step'] = step_name
            self.setup_state['last_run_timestamp'] = time.time()
            
            with open(self.setup_state_file, 'w') as f:
                json.dump(self.setup_state, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save setup state: {e}")
    
    def check_system_requirements(self) -> bool:
        """Check basic system requirements"""
        print("\n" + "="*60)
        print("🔍 STEP 1: SYSTEM REQUIREMENTS CHECK")
        print("="*60)
        print("Verifying your system meets the requirements for Vista3D frontend...")
        
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
        print(f"✅ Operating system: {self.system_info['platform']} {self.system_info['release']}")
        print(f"   Architecture: {self.system_info['architecture']}")
        
        # Check if git is available
        print("\n📍 Checking Git availability...")
        if not shutil.which('git'):
            print("⚠️  Git not found in system PATH")
            print("   Git is recommended for version control")
        else:
            try:
                result = subprocess.run(['git', '--version'], capture_output=True, text=True, check=True)
                git_version = result.stdout.strip()
                print(f"✅ Git is available")
                print(f"   Version: {git_version}")
            except:
                print("✅ Git is available (version check failed)")
        
        # Check internet connectivity
        print("\n📍 Testing internet connectivity...")
        try:
            print("   Testing connection to Google...")
            response = requests.get('https://www.google.com', timeout=5)
            print(f"✅ Internet connectivity verified (Status: {response.status_code})")
            
            print("   Testing connection to Python Package Index...")
            response = requests.get('https://pypi.org', timeout=10)
            print(f"✅ PyPI accessible (Status: {response.status_code})")
            
        except Exception as e:
            print("❌ Internet connectivity test failed")
            print(f"   Error: {e}")
            print("   Internet access is required for:")
            print("     • Downloading Python packages")
            print("     • Pulling Docker images (if using containers)")
            issues.append("No internet connectivity - required for package downloads")
        
        # Check for optional GPU (not required for frontend)
        print("\n📍 Checking for optional GPU support...")
        nvidia_gpus = self.check_nvidia_gpus()
        if nvidia_gpus['has_gpus']:
            print(f"✅ NVIDIA GPU(s) detected:")
            for i, gpu in enumerate(nvidia_gpus['gpus']):
                print(f"   {i+1}. {gpu['name']} ({gpu['memory']})")
            print("   This system can run Vista3D AI models locally (optional)")
            self.setup_state['has_nvidia_gpu'] = True
        else:
            print("ℹ️  No NVIDIA GPUs detected")
            print("   This is normal for frontend-only setups")
            print("   You can connect to a remote Vista3D server")
            self.setup_state['has_nvidia_gpu'] = False
        
        # Summary
        print("\n" + "-"*60)
        if issues:
            print("❌ SYSTEM REQUIREMENTS SUMMARY:")
            print(f"   Found {len(issues)} issue(s) that need attention:")
            for i, issue in enumerate(issues, 1):
                print(f"   {i}. {issue}")
            print("\n   Some issues may be resolved automatically during setup.")
            return False
        else:
            print("✅ SYSTEM REQUIREMENTS SUMMARY:")
            print("   All basic system requirements are met!")
            print("   Your system is ready for Vista3D frontend setup.")
        
        return True
    
    def check_nvidia_gpus(self) -> Dict:
        """Check for NVIDIA GPUs and return detailed information"""
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
    
    def check_python_environment(self) -> bool:
        """Check and set up Python environment"""
        print("\n" + "="*60)
        print("🐍 STEP 2: PYTHON ENVIRONMENT SETUP")
        print("="*60)
        print("Setting up isolated Python environment and installing dependencies...")
        
        # Check if we're already in a virtual environment
        in_venv = (hasattr(sys, 'real_prefix') or 
                  (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))
        
        print("\n📍 Checking current Python environment...")
        if in_venv:
            print("✅ Already running in a virtual environment")
            print(f"   Virtual environment path: {sys.prefix}")
            print(f"   Python executable: {sys.executable}")
            print("   This is good! Virtual environments keep dependencies isolated.")
        else:
            print("⚠️  Not currently in a virtual environment")
            print("   Creating an isolated virtual environment is recommended to:")
            print("     • Avoid conflicts with system Python packages")
            print("     • Keep Vista3D dependencies separate")
            print("     • Allow easy cleanup if needed")
        
        # Check for uv package manager
        print("\n📍 Checking for 'uv' package manager...")
        if not shutil.which('uv'):
            print("⚠️  'uv' package manager not found")
            print("   'uv' is a fast Python package installer and dependency manager")
            print("   It's much faster than pip and handles dependency resolution better")
            
            install_uv = self._ask_yes_no("Install uv package manager?", default=True)
            if install_uv:
                print("\n🔧 Installing uv package manager...")
                if not self.install_uv():
                    print("❌ Failed to install uv package manager")
                    return False
                else:
                    print("✅ uv package manager installed successfully")
            else:
                print("❌ Cannot proceed without uv package manager")
                return False
        else:
            try:
                result = subprocess.run(['uv', '--version'], capture_output=True, text=True, check=True)
                uv_version = result.stdout.strip()
                print(f"✅ uv package manager is available")
                print(f"   Version: {uv_version}")
            except:
                print("✅ uv package manager is available (version check failed)")
        
        # Install dependencies
        print("\n📍 Installing project dependencies...")
        print("   Reading dependencies from pyproject.toml...")
        print("   This includes:")
        print("     • Streamlit (web interface)")
        print("     • FastAPI (image server)")
        print("     • NiBabel (medical imaging)")
        print("     • dcm2niix (DICOM conversion)")
        print("     • NumPy, Pandas (data processing)")
        print("     • And many more specialized packages...")
        
        try:
            print("\n🔧 Running 'uv sync' to install dependencies...")
            print("   This may take a few minutes on first run...")
            
            process = subprocess.Popen(['uv', 'sync'], cwd=self.project_root, 
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                     text=True, universal_newlines=True)
            
            # Show real-time output
            for line in process.stdout:
                print(f"   {line.rstrip()}")
            
            process.wait()
            if process.returncode == 0:
                print("✅ Dependencies installed successfully")
                print("   All required packages are now available in your environment")
                return True
            else:
                print("❌ Dependency installation failed")
                return False
                
        except Exception as e:
            print(f"❌ Error during dependency installation: {e}")
            return False
    
    def install_uv(self) -> bool:
        """Install uv package manager if not available"""
        logger.info("📦 Installing uv package manager...")
        
        try:
            if self.system_info['platform'] == 'Windows':
                # Windows installation
                subprocess.run([
                    'powershell', '-c', 
                    'irm https://astral.sh/uv/install.ps1 | iex'
                ], check=True)
            else:
                # Unix-like systems (Linux, macOS)
                subprocess.run([
                    'curl', '-LsSf', 'https://astral.sh/uv/install.sh'
                ], stdout=subprocess.PIPE, check=True)
                
                # Source the installation script
                subprocess.run(['bash', '-c', 'source ~/.bashrc'], check=True)
            
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
    
    def gather_frontend_configuration(self) -> Dict:
        """Gather frontend-specific configuration"""
        print("\n" + "="*60)
        print("📝 STEP 3: FRONTEND CONFIGURATION")
        print("="*60)
        print("Configuring Vista3D frontend for web interface and image server...")
        
        config = {}
        
        # Project root - automatically detected
        print("\n📍 Setting up project paths...")
        print(f"✅ Project root automatically detected:")
        print(f"   Path: {self.project_root.absolute()}")
        print("   This is where all Vista3D files and data will be stored")
        
        # DICOM folder
        print("\n📍 Configuring DICOM input folder...")
        print("   This folder will store your raw medical imaging files")
        print("   DICOM files are the original images from CT/MRI scanners")
        print("   Organize files by patient: dicom/patient001/, dicom/patient002/, etc.")
        
        config['DICOM_FOLDER'] = self._prompt_user(
            "DICOM folder absolute path",
            default=str(self.project_root / "dicom")
        )
        dicom_path = Path(config['DICOM_FOLDER'])
        if not dicom_path.is_absolute():
            dicom_path = self.project_root / config['DICOM_FOLDER']
        print(f"✅ DICOM files will be stored in: {dicom_path}")
        
        # Output folder
        print("\n📍 Configuring output folder...")
        print("   This folder will store processed results:")
        print("     • NIfTI converted files")
        print("     • Segmentation results")
        print("     • 3D visualization data")
        
        config['OUTPUT_FOLDER'] = self._prompt_user(
            "Output folder absolute path",
            default=str(self.project_root / "output")
        )
        output_path = Path(config['OUTPUT_FOLDER'])
        if not output_path.is_absolute():
            output_path = self.project_root / config['OUTPUT_FOLDER']
        print(f"✅ Processed results will be stored in: {output_path}")
        
        # Image server configuration
        print("\n📍 Configuring Image Server...")
        print("   The image server provides web access to your medical images")
        print("   It serves files to the Streamlit web interface")
        print("   For local use, keep the default localhost setting")
        
        config['IMAGE_SERVER'] = self._prompt_user(
            "Image server URL",
            default="http://localhost:8888"
        )
        print(f"✅ Image server will run at: {config['IMAGE_SERVER']}")
        
        # Vista3D server configuration
        print("\n📍 Configuring Vista3D AI Server...")
        print("   This is the NVIDIA Vista3D AI model server")
        print("   It can be local (Docker) or remote")
        print("   For remote server, enter the server's IP address and port")
        
        has_local_gpu = self.setup_state.get('has_nvidia_gpu', False)
        if has_local_gpu:
            print("   ✅ Local GPU detected - you can run Vista3D locally")
            use_local = self._ask_yes_no("Use local Vista3D server?", default=True)
            if use_local:
                config['VISTA3D_SERVER'] = "http://localhost:8000"
                print("✅ Will use local Vista3D server")
            else:
                remote_server = self._prompt_user(
                    "Enter remote Vista3D server URL",
                    default="http://remote-gpu-server:8000"
                )
                config['VISTA3D_SERVER'] = remote_server
                print(f"✅ Will connect to remote Vista3D server: {remote_server}")
        else:
            print("   ℹ️  No local GPU detected - will connect to remote server")
            remote_server = self._prompt_user(
                "Enter remote Vista3D server URL",
                default="http://remote-gpu-server:8000"
            )
            config['VISTA3D_SERVER'] = remote_server
            print(f"✅ Will connect to remote Vista3D server: {remote_server}")
        
        # Vessels of interest
        print("\n📍 Configuring Segmentation Targets...")
        print("   Choose which anatomical structures to segment:")
        print("   Available options:")
        print("     • 'all' - Segment all detectable structures (recommended)")
        print("     • Specific structures (comma-separated list)")
        
        config['VESSELS_OF_INTEREST'] = self._prompt_user(
            "Structures to segment",
            default="all"
        )
        if config['VESSELS_OF_INTEREST'] == "all":
            print("✅ Will segment all detectable anatomical structures")
        else:
            structures = [s.strip() for s in config['VESSELS_OF_INTEREST'].split(',')]
            print(f"✅ Will segment {len(structures)} specific structure(s):")
            for structure in structures[:5]:  # Show first 5
                print(f"     • {structure}")
            if len(structures) > 5:
                print(f"     • ... and {len(structures) - 5} more")
        
        # External access configuration
        print("\n📍 Configuring network access...")
        print("   By default, Vista3D runs locally (localhost only)")
        print("   External access allows other computers to connect to your image server")
        print("   This is useful for team collaboration or remote access")
        
        configure_external = self._ask_yes_no("Configure for external network access?", default=False)
        
        if configure_external:
            print("\n🌐 Setting up external access...")
            print("   For external access, we need your public IP address")
            print("   This allows other computers to connect to your image server")
            
            try:
                print("   Attempting to auto-detect your public IP...")
                public_ip = requests.get('https://ifconfig.me', timeout=10).text.strip()
                print(f"✅ Auto-detected public IP: {public_ip}")
                
                use_detected_ip = self._ask_yes_no(f"Use detected IP address ({public_ip})?", default=True)
                
                if use_detected_ip:
                    config['IMAGE_SERVER'] = f"http://{public_ip}:8888"
                    print(f"✅ Image server configured for external access: {config['IMAGE_SERVER']}")
                    print("   ⚠️  Make sure port 8888 is open in your firewall")
                else:
                    external_ip = self._prompt_user("Enter your public IP address")
                    config['IMAGE_SERVER'] = f"http://{external_ip}:8888"
                    print(f"✅ Image server configured for external access: {config['IMAGE_SERVER']}")
                    print("   ⚠️  Make sure port 8888 is open in your firewall")
                    
            except Exception as e:
                print(f"⚠️  Could not auto-detect public IP: {e}")
                print("   You can find your IP using: curl ifconfig.me")
                external_ip = self._prompt_user("Enter your public IP address")
                config['IMAGE_SERVER'] = f"http://{external_ip}:8888"
                print(f"✅ Image server configured for external access: {config['IMAGE_SERVER']}")
                print("   ⚠️  Make sure port 8888 is open in your firewall")
        else:
            print("✅ Vista3D configured for local access only")
            print("   Image server will be accessible only from this computer")
        
        # Configuration summary
        print("\n" + "-"*60)
        print("📋 FRONTEND CONFIGURATION SUMMARY:")
        print(f"   Project Root: {self.project_root.absolute()}")
        print(f"   DICOM Input: {config['DICOM_FOLDER']}/")
        print(f"   Output Folder: {config['OUTPUT_FOLDER']}/")
        print(f"   Image Server: {config['IMAGE_SERVER']}")
        print(f"   Vista3D Server: {config['VISTA3D_SERVER']}")
        print(f"   Segmentation: {config['VESSELS_OF_INTEREST']}")
        print("-"*60)
        
        return config
    
    def create_env_file(self, config: Dict) -> bool:
        """Create .env file from template and user configuration"""
        logger.info("📄 Creating .env file...")
        
        try:
            # Read template
            if not self.env_template.exists():
                logger.error(f"Template file not found: {self.env_template}")
                return False
            
            with open(self.env_template, 'r') as f:
                env_content = f.read()
            
            # Replace template values with user configuration
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
            
            # Set proper permissions (readable by owner only)
            os.chmod(self.env_file, 0o600)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create .env file: {e}")
            return False
    
    def create_required_directories(self, config: Dict) -> bool:
        """Create required project directories"""
        logger.info("📁 Creating required directories...")
        
        try:
            project_root = self.project_root
            
            # Create directories
            directories = [
                project_root / config['DICOM_FOLDER'],
                project_root / config['OUTPUT_FOLDER'],
                project_root / config['OUTPUT_FOLDER'] / 'nifti',
                project_root / config['OUTPUT_FOLDER'] / 'scans',
                project_root / config['OUTPUT_FOLDER'] / 'voxels'
            ]
            
            for directory in directories:
                directory.mkdir(parents=True, exist_ok=True)
                logger.info(f"✅ Created directory: {directory}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create directories: {e}")
            return False
    
    def print_next_steps(self, config: Dict):
        """Print next steps for the user"""
        print("\n" + "="*80)
        print("🎉 Vista3D Frontend Setup Complete!")
        print("="*80)
        
        print("\n📋 Next Steps:")
        
        # 0. Activate virtual environment
        print(f"\n0. 🐍 Activate virtual environment:")
        if self.system_info['platform'] == 'Windows':
            print("   .venv\\Scripts\\activate")
        else:
            print("   source .venv/bin/activate")
        
        # 1. DICOM files
        dicom_folder = self.project_root / config['DICOM_FOLDER']
        print(f"\n1. 📁 Add DICOM files to: {dicom_folder}")
        print("   • Place each patient's DICOM series in separate folders")
        print("   • Example: dicom/patient001/, dicom/patient002/")
        
        # 2. Convert DICOM to NIfTI
        print(f"\n2. 🔄 Convert DICOM files to NIfTI format:")
        print("   python utils/dicom2nifti.py")
        print("   • This converts DICOM files to NIfTI format for Vista3D processing")
        print("   • Creates optimized files for medical AI analysis")
        print("   • Generates quality reports and metadata")
        
        # 3. Start image server
        print(f"\n3. 🖥️  Start image server:")
        print("   python utils/image_server.py")
        print("   • This serves your medical images via web API")
        print("   • Required for the web interface to access images")
        
        # 4. Start web interface
        print(f"\n4. 🌐 Start web interface:")
        print("   streamlit run app.py")
        print("   • This starts the Streamlit web interface")
        print("   • Open your browser to the displayed URL")
        print("   • Upload and process medical images through the web UI")
        
        # 5. Optional: Start local Vista3D server
        has_local_gpu = self.setup_state.get('has_nvidia_gpu', False)
        if has_local_gpu and 'localhost' in config.get('VISTA3D_SERVER', ''):
            print(f"\n5. 🧠 Start local Vista3D server (optional):")
            print("   python utils/start_vista3d_server.py")
            print("   • This starts the Vista3D AI processing server")
            print("   • Requires NVIDIA GPU and Docker")
            print("   • Only needed if you want local AI processing")
        
        print(f"\n📄 Configuration saved to: {self.env_file}")
        print(f"🔐 Keep your .env file secure - it contains configuration data")
        
        # Additional notes
        if 'IMAGE_SERVER' in config and 'localhost' not in config['IMAGE_SERVER']:
            print(f"\n🌐 External Access Configured:")
            print(f"   • Image server: {config['IMAGE_SERVER']}")
            print(f"   • Ensure port 8888 is open in your firewall")
            print(f"   • Vista3D will access images from this URL")
        
        print("\n" + "="*80)
    
    def _prompt_user(self, prompt: str, default: str = None) -> str:
        """Prompt user for input with optional default"""
        while True:
            if default:
                user_input = input(f"{prompt} [{default}]: ").strip()
                if not user_input:
                    user_input = default
            else:
                user_input = input(f"{prompt}: ").strip()
            
            return user_input
    
    def _ask_yes_no(self, question: str, default: bool = None) -> bool:
        """Ask a yes/no question"""
        while True:
            if default is True:
                prompt = f"{question} [Y/n]: "
            elif default is False:
                prompt = f"{question} [y/N]: "
            else:
                prompt = f"{question} [y/n]: "
            
            answer = input(prompt).strip().lower()
            
            if not answer and default is not None:
                return default
            elif answer in ['y', 'yes']:
                return True
            elif answer in ['n', 'no']:
                return False
            else:
                print("Please answer 'y' or 'n'")
    
    def run_interactive_setup(self) -> bool:
        """Run the main interactive setup process"""
        try:
            self.print_banner()
            
            # Step 1: Check system requirements
            if not self.check_system_requirements():
                print("\n❌ System requirements not met. Please resolve issues and try again.")
                return False
            
            self._save_setup_state('system_requirements_checked')
            
            # Step 2: Check Python environment
            if not self.check_python_environment():
                print("\n❌ Python environment setup failed.")
                return False
            
            self._save_setup_state('python_environment_ready')
            
            # Step 3: Gather frontend configuration
            config = self.gather_frontend_configuration()
            self._save_setup_state('configuration_gathered')
            
            # Step 4: Create .env file
            if not self.create_env_file(config):
                print("\n❌ Failed to create .env file")
                return False
            self._save_setup_state('env_file_created')
            
            # Step 5: Create required directories
            if not self.create_required_directories(config):
                print("\n❌ Failed to create required directories")
                return False
            self._save_setup_state('directories_created')
            
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
        description="HPE NVIDIA Vista3D Frontend Setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python setup_vista3d_frontend.py                    # Interactive frontend setup
  python setup_vista3d_frontend.py --non-interactive  # Use defaults

The interactive setup will guide you through:
  1. System requirements check
  2. Python environment setup
  3. Frontend configuration (web interface, image server)
  4. Environment file creation
  5. Directory creation

Requirements:
  • Python 3.11+
  • Internet connectivity
  • Web browser (Chrome, Firefox, Safari, Edge)
  • Optional: Docker for containerized deployment
  • Optional: NVIDIA GPU for local Vista3D processing
        """
    )
    
    parser.add_argument(
        '--non-interactive',
        action='store_true',
        help='Run in non-interactive mode (use defaults)'
    )
    
    args = parser.parse_args()
    
    setup_manager = Vista3DFrontendSetupManager()
    
    try:
        success = setup_manager.run_interactive_setup()
        sys.exit(0 if success else 1)
            
    except KeyboardInterrupt:
        logger.info("\nSetup cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
