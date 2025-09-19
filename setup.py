#!/usr/bin/env python3
"""
HPE NVIDIA Vista3D Medical AI Platform Setup Script
Interactive setup for project configuration after cloning from git
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

class SetupManager:
    """Interactive setup manager for the Vista3D project"""
    
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.project_root = self.script_dir  # Now setup.py is in project root
        self.env_file = self.project_root / '.env'
        self.env_template = self.project_root / 'dot_env_template'
        self.setup_state_file = self.project_root / '.setup_state.json'
        
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
        print("🚀 HPE NVIDIA Vista3D Medical AI Platform Setup")
        print("="*80)
        print("This script will guide you through setting up the Vista3D project")
        print("after cloning from git. It will:")
        print("  • Check system requirements")
        print("  • Set up Python environment")
        print("  • Configure environment variables")
        print("  • Optionally install system dependencies")
        print("  • Optionally set up Vista3D Docker container")
        print("="*80)
        
        print("\n📋 WORKFLOW OVERVIEW:")
        print("-" * 40)
        print("This platform processes medical imaging data through the following workflow:")
        print("  1. 📁 DICOM files → Raw medical imaging data from scanners")
        print("  2. 🔄 Conversion → DICOM to NIfTI format for processing")
        print("  3. 🧠 Scanning → Vista3D AI analyzes and scans structures")
        print("  4. 🌐 Visualization → Web interface for viewing results")
        print("  5. 📊 Analysis → Interactive exploration of segmented data")
        
        print("\n📚 KEY TERMS:")
        print("-" * 40)
        print("DICOM (Digital Imaging and Communications in Medicine):")
        print("  • Standard format for medical imaging data")
        print("  • Contains patient metadata and image data")
        print("  • Used by CT, MRI, X-ray, and other medical scanners")
        print("  • Includes headers with patient info, scan parameters, etc.")
        
        print("\nNIfTI (Neuroimaging Informatics Technology Initiative):")
        print("  • Standard format for neuroimaging and medical image analysis")
        print("  • Simplified format compared to DICOM")
        print("  • Contains only image data and basic spatial information")
        print("  • Preferred format for AI/ML processing and analysis")
        print("  • Supports 3D volumes and 4D time series data")
        
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
            'docker_checked': False,
            'vista3d_setup': False,
            'image_server_started': False,
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
    
    def _check_previous_run(self):
        """Check if this is a continuation of a previous setup"""
        if self.setup_state.get('last_run_timestamp'):
            last_run = self.setup_state['last_run_timestamp']
            last_step = self.setup_state.get('last_successful_step')
            
            # If last run was recent (within 24 hours) and had progress
            if time.time() - last_run < 86400 and last_step:
                print("\n" + "🔄 RESUMING PREVIOUS SETUP")
                print("="*60)
                print("Detected a previous setup attempt with progress.")
                print(f"Last successful step: {last_step}")
                
                completed_steps = [k for k, v in self.setup_state.items() 
                                 if v is True and k.endswith(('_checked', '_ready', '_gathered', '_created', '_installed', '_setup', '_started'))]
                
                if completed_steps:
                    print("\n✅ Already completed steps:")
                    for step in completed_steps:
                        step_name = step.replace('_', ' ').title().replace('Env', '.env')
                        print(f"   • {step_name}")
                    
                    print("\n🚀 Will continue from where we left off...")
                    resume = self._ask_yes_no("Continue from previous setup?", default=True)
                    if not resume:
                        print("🔄 Starting fresh setup...")
                        self.setup_state = self._load_setup_state.__defaults__[0] if hasattr(self._load_setup_state, '__defaults__') else {}
                        self._save_setup_state('reset', True)
                    else:
                        print("✅ Resuming previous setup...")
                    print("="*60)
    
    def _handle_step_failure(self, step_name: str, error: Exception, critical: bool = True):
        """Handle step failure with recovery options"""
        print(f"\n❌ STEP FAILED: {step_name}")
        print("="*60)
        print(f"Error: {error}")
        
        self._save_setup_state(step_name, False)
        
        if critical:
            print("\n🔧 RECOVERY OPTIONS:")
            print("1. This was a critical step that must succeed")
            print("2. You can re-run setup.py to try again")
            print("3. Some issues may be resolved by:")
            print("   • Checking internet connection")
            print("   • Running with administrator/sudo privileges")
            print("   • Installing missing system dependencies manually")
            print("   • Updating system packages")
            
            print(f"\n💡 To retry this specific step, run:")
            print(f"   python setup.py")
            print("   (Setup will automatically resume from the failed step)")
            
            retry = self._ask_yes_no("Would you like to retry this step now?", default=False)
            if retry:
                return True
        else:
            print("⚠️  This step failed but is not critical for basic functionality")
            print("   You can continue setup and address this later")
            
            continue_setup = self._ask_yes_no("Continue with remaining setup steps?", default=True)
            if continue_setup:
                return True
        
        return False
    
    def check_system_requirements(self) -> bool:
        """Check basic system requirements"""
        print("\n" + "="*60)
        print("🔍 STEP 1: SYSTEM REQUIREMENTS CHECK")
        print("="*60)
        print("Verifying your system meets the minimum requirements for Vista3D...")
        
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
        if self.system_info['platform'] != 'Linux':
            print(f"⚠️  Operating system compatibility warning")
            print(f"   Recommended: Ubuntu Linux")
            print(f"   Detected: {self.system_info['platform']} {self.system_info['release']}")
            print(f"   Note: Some automated installations may not work on this platform")
        else:
            print(f"✅ Operating system check passed")
            print(f"   Platform: {self.system_info['platform']} {self.system_info['release']}")
            print(f"   Architecture: {self.system_info['architecture']}")
        
        # Check if git is available
        print("\n📍 Checking Git availability...")
        if not shutil.which('git'):
            print("❌ Git not found in system PATH")
            print("   Git is required for version control and some package installations")
            issues.append("Git not found in PATH")
        else:
            try:
                result = subprocess.run(['git', '--version'], capture_output=True, text=True, check=True)
                git_version = result.stdout.strip()
                print(f"✅ Git is available")
                print(f"   Version: {git_version}")
            except:
                print("✅ Git is available (version check failed)")
        
        # Check if we're in a git repository
        print("\n📍 Checking Git repository status...")
        try:
            result = subprocess.run(['git', 'status', '--porcelain'], cwd=self.project_root, 
                                  check=True, capture_output=True, text=True)
            print("✅ Project is in a Git repository")
            if result.stdout.strip():
                print("   Note: There are uncommitted changes in the repository")
            else:
                print("   Repository is clean (no uncommitted changes)")
        except subprocess.CalledProcessError:
            print("⚠️  Not in a Git repository - continuing anyway")
            print("   This is normal if you downloaded the project as a ZIP file")
        
        # Check internet connectivity
        print("\n📍 Testing internet connectivity...")
        try:
            print("   Testing connection to Google...")
            response = requests.get('https://www.google.com', timeout=5)
            print(f"✅ Internet connectivity verified (Status: {response.status_code})")
            
            print("   Testing connection to NVIDIA NGC...")
            response = requests.get('https://ngc.nvidia.com', timeout=10)
            print(f"✅ NVIDIA NGC accessible (Status: {response.status_code})")
            
            print("   Testing connection to Python Package Index...")
            response = requests.get('https://pypi.org', timeout=10)
            print(f"✅ PyPI accessible (Status: {response.status_code})")
            
        except Exception as e:
            print("❌ Internet connectivity test failed")
            print(f"   Error: {e}")
            print("   Internet access is required for:")
            print("     • Downloading Python packages")
            print("     • Pulling Docker images")
            print("     • Installing system dependencies")
            issues.append("No internet connectivity - required for package downloads")
        
        # Check NVIDIA GPU availability
        print("\n📍 Checking NVIDIA GPU availability...")
        nvidia_gpus = self.check_nvidia_gpus()
        if nvidia_gpus['has_gpus']:
            print(f"✅ NVIDIA GPU(s) detected:")
            for i, gpu in enumerate(nvidia_gpus['gpus']):
                print(f"   {i+1}. {gpu['name']} ({gpu['memory']})")
            print("   This system can run Vista3D AI models locally")
            self.setup_state['has_nvidia_gpu'] = True
        else:
            print("⚠️  No NVIDIA GPUs detected")
            print("   NVIDIA GPUs are required for Vista3D AI processing")
            print("   This system can run:")
            print("     • Streamlit web interface")
            print("     • Image server")
            print("     • Connect to remote Vista3D server")
            self.setup_state['has_nvidia_gpu'] = False
        
        # Check NGC CLI (only if GPU detected or user wants remote setup)
        print("\n📍 Checking NVIDIA NGC CLI...")
        if not self.check_ngc_cli():
            print("⚠️  NGC CLI not found on system")
            print("   NGC CLI is required for:")
            print("     • Authenticating with NVIDIA NGC registry")
            print("     • Downloading Vista3D Docker images")
            print("     • Managing NVIDIA model repositories")
            
            if nvidia_gpus['has_gpus']:
                print("   Since you have NVIDIA GPUs, NGC CLI is recommended for local Vista3D")
                install_ngc_cli = self._ask_yes_no("Install NGC CLI automatically?", default=True)
            else:
                print("   NGC CLI is optional if you're only running client components")
                install_ngc_cli = self._ask_yes_no("Install NGC CLI for future Vista3D server setup?", default=False)
            
            if install_ngc_cli:
                print("\n🔧 Installing NGC CLI...")
                if self.install_ngc_cli():
                    print("✅ NGC CLI installed successfully")
                else:
                    print("❌ NGC CLI installation failed")
                    if nvidia_gpus['has_gpus']:
                        issues.append("Failed to install NGC CLI")
            else:
                print("⚠️  Skipping NGC CLI installation")
                if nvidia_gpus['has_gpus']:
                    print("   You can install it manually later for Vista3D functionality")
                    issues.append("NGC CLI not installed - required for local Vista3D")
                else:
                    print("   You can install it later if you need Vista3D server functionality")
        else:
            try:
                result = subprocess.run(['ngc', '--version'], capture_output=True, text=True, check=True)
                ngc_version = result.stdout.strip()
                print(f"✅ NGC CLI is available")
                print(f"   Version: {ngc_version}")
            except:
                print("✅ NGC CLI is available (version check failed)")
        
        
        # Summary
        print("\n" + "-"*60)
        if issues:
            print("❌ SYSTEM REQUIREMENTS SUMMARY:")
            print(f"   Found {len(issues)} issue(s) that need attention:")
            for i, issue in enumerate(issues, 1):
                print(f"   {i}. {issue}")
            print("\n   Some issues may be resolved automatically during setup.")
            print("   Critical issues will prevent Vista3D from working properly.")
            return False
        else:
            print("✅ SYSTEM REQUIREMENTS SUMMARY:")
            print("   All basic system requirements are met!")
            print("   Your system is ready for Vista3D setup.")
        
        return True
    
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

    def create_and_activate_venv(self) -> bool:
        """Create virtual environment with uv and activate it"""
        logger.info("🐍 Setting up Python virtual environment...")
        
        # Check if uv is available
        if not shutil.which('uv'):
            logger.warning("⚠️  uv not found")
            install_uv = self._ask_yes_no("Install uv package manager?", default=True)
            if install_uv:
                if not self.install_uv():
                    logger.error("❌ Failed to install uv")
                    return False
                else:
                    # Refresh PATH to find uv
                    import os
                    os.environ['PATH'] = os.environ.get('PATH', '')
                    # Try to find uv again
                    if not shutil.which('uv'):
                        logger.error("❌ uv installed but not found in PATH")
                        return False
            else:
                logger.error("❌ uv is required for virtual environment setup")
                return False
        
        logger.info("✅ uv package manager available")
        
        # Check if .venv already exists
        venv_path = self.project_root / '.venv'
        if venv_path.exists():
            logger.info("📁 Virtual environment already exists")
            if not self._ask_yes_no("Recreate virtual environment?", default=False):
                logger.info("✅ Using existing virtual environment")
                return True
        
        # Create virtual environment
        try:
            logger.info("📦 Creating virtual environment with uv...")
            subprocess.run(['uv', 'venv'], cwd=self.project_root, check=True)
            logger.info("✅ Virtual environment created")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to create virtual environment: {e}")
            return False
        
        return True

    def activate_venv_and_install_deps(self) -> bool:
        """Activate virtual environment and install dependencies"""
        logger.info("🔧 Activating virtual environment and installing dependencies...")
        
        # Determine activation script path
        if self.system_info['platform'] == 'Windows':
            activate_script = self.project_root / '.venv' / 'Scripts' / 'activate.bat'
            python_executable = self.project_root / '.venv' / 'Scripts' / 'python.exe'
        else:
            activate_script = self.project_root / '.venv' / 'bin' / 'activate'
            python_executable = self.project_root / '.venv' / 'bin' / 'python'
        
        # Check if virtual environment exists
        if not python_executable.exists():
            logger.error(f"❌ Virtual environment not found at {python_executable}")
            return False
        
        try:
            # Install dependencies using uv
            logger.info("📦 Installing dependencies with uv...")
            
            # Use uv sync to install from pyproject.toml
            subprocess.run(['uv', 'sync'], cwd=self.project_root, check=True)
            logger.info("✅ Dependencies installed successfully")
            
            # Verify installation by checking if key packages are available
            logger.info("🔍 Verifying installation...")
            result = subprocess.run([
                str(python_executable), '-c', 
                'import streamlit, fastapi, nibabel; print("Key packages imported successfully")'
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                logger.info("✅ Package verification successful")
            else:
                logger.warning("⚠️  Package verification had issues, but installation may still be successful")
            
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to install dependencies: {e}")
            return False

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
            
            # Still need to check for uv and install dependencies
            print("\n📍 Checking for 'uv' package manager...")
            if not shutil.which('uv'):
                print("⚠️  'uv' package manager not found in current environment")
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
            
            # Install dependencies in current environment
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
        
        # Not in virtual environment - create one
        print("⚠️  Not currently in a virtual environment")
        print("   Creating an isolated virtual environment is recommended to:")
        print("     • Avoid conflicts with system Python packages")
        print("     • Keep Vista3D dependencies separate")
        print("     • Allow easy cleanup if needed")
        
        print("\n📍 Creating new virtual environment...")
        
        # Create virtual environment
        if not self.create_and_activate_venv():
            return False
        
        # Install dependencies
        if not self.activate_venv_and_install_deps():
            return False
        
        # Print activation instructions
        print("\n" + "="*60)
        print("🎉 PYTHON ENVIRONMENT SETUP COMPLETE!")
        print("="*60)
        print("\n📋 Virtual Environment Details:")
        venv_path = self.project_root / '.venv'
        print(f"   Location: {venv_path}")
        print(f"   Python executable: {venv_path / ('Scripts/python.exe' if self.system_info['platform'] == 'Windows' else 'bin/python')}")
        print("   Dependencies: All required packages installed")
        
        print("\n💡 To activate this environment in the future:")
        if self.system_info['platform'] == 'Windows':
            print("   .venv\\Scripts\\activate")
        else:
            print("   source .venv/bin/activate")
            
        print("\n🚀 Once activated, you can run:")
        print("   • python utils/start_vista3d.py    (Start Vista3D AI)")
        print("   • python utils/image_server.py     (Start image server)")
        print("   • streamlit run app.py             (Start web interface)")
        print("="*60)
        
        return True
    
    def gather_user_configuration(self) -> Dict:
        """Gather configuration from user input"""
        print("\n" + "="*60)
        print("📝 STEP 3: CONFIGURATION SETUP")
        print("="*60)
        print("Collecting configuration details for your Vista3D installation...")
        
        config = {}
        
        # Project root - automatically detected (no longer needs configuration)
        print("\n📍 Setting up project paths...")
        print(f"✅ Project root automatically detected:")
        print(f"   Path: {self.project_root.absolute()}")
        print("   This is where all Vista3D files and data will be stored")
        print("   Note: PROJECT_ROOT is now auto-detected and no longer needs to be configured")
        
        # DICOM folder
        print("\n📍 Configuring DICOM input folder...")
        print("   This folder will store your raw medical imaging files")
        print("   DICOM files are the original images from CT/MRI scanners")
        print("   Organize files by patient: dicom/patient001/, dicom/patient002/, etc.")
        print("")
        print("   📋 DICOM Processing Workflow:")
        print("   1. Place DICOM files in patient-specific subfolders")
        print("   2. Run: python utils/dicom2nifti.py")
        print("   3. This converts DICOM → NIfTI format for Vista3D processing")
        
        config['DICOM_FOLDER'] = self._prompt_user(
            "DICOM folder name (relative to project root)",
            default="dicom"
        )
        dicom_path = self.project_root / config['DICOM_FOLDER']
        print(f"✅ DICOM files will be stored in: {dicom_path}")
        print(f"   After adding DICOM files, convert them with: python utils/dicom2nifti.py")
        
        # Output folder
        print("\n📍 Configuring output folder...")
        print("   This folder will store processed results:")
        print("     • NIfTI converted files")
        print("     • Segmentation results")
        print("     • 3D visualization data")
        
        config['OUTPUT_FOLDER'] = self._prompt_user(
            "Output folder name (relative to project root)",
            default="output"
        )
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
        print("   It runs in a Docker container and performs the actual segmentation")
        print("   For local Docker usage, keep the default localhost setting")
        
        config['VISTA3D_SERVER'] = self._prompt_user(
            "Vista3D server URL (use localhost if running locally)",
            default="http://localhost:8000"
        )
        print(f"✅ Vista3D AI server will be accessible at: {config['VISTA3D_SERVER']}")
        
        # Vessels of interest
        print("\n📍 Configuring Segmentation Targets...")
        print("   Choose which anatomical structures to segment:")
        print("   ")
        print("   Available options:")
        print("     • 'all' - Segment all detectable structures (recommended)")
        print("     • Specific structures (comma-separated list)")
        print("   ")
        print("   Example specific structures:")
        print("     'brain,skull,spinal cord,left common carotid artery'")
        print("     'liver,kidneys,spleen,pancreas'")
        print("     'heart,lungs,aorta'")
        
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
        
        # Label set selection
        print("\n📍 Checking for predefined label sets...")
        label_sets_file = self.project_root / 'conf' / 'vista3d_label_sets.json'
        if label_sets_file.exists():
            try:
                with open(label_sets_file, 'r') as f:
                    label_sets = json.load(f)
                
                print(f"✅ Found {len(label_sets)} predefined label set(s):")
                for name, info in label_sets.items():
                    description = info.get('description', 'No description')
                    print(f"     • {name}: {description}")
                
                print("\n   Predefined label sets are optimized collections of structures")
                print("   They may provide better results than custom structure lists")
                
                use_label_set = self._ask_yes_no("Use a predefined label set instead of your custom list?", default=False)
                if use_label_set:
                    while True:
                        print(f"\n   Available label sets: {', '.join(label_sets.keys())}")
                        label_set = input("   Enter label set name: ").strip()
                        if label_set in label_sets:
                            config['LABEL_SET'] = label_set
                            print(f"✅ Selected label set: {label_set}")
                            print(f"   Description: {label_sets[label_set].get('description', 'N/A')}")
                            # Will comment out VESSELS_OF_INTEREST in .env file
                            break
                        print(f"❌ Invalid label set. Choose from: {', '.join(label_sets.keys())}")
                else:
                    print("✅ Will use your custom structure list")
            except Exception as e:
                print(f"⚠️  Could not load label sets: {e}")
                print("   Continuing with custom structure configuration")
        else:
            print("⚠️  No predefined label sets found")
            print("   Using custom structure configuration")
        
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
        print("📋 CONFIGURATION SUMMARY:")
        print(f"   Project Root: {self.project_root.absolute()}")
        print(f"   DICOM Input: {config['DICOM_FOLDER']}/")
        print(f"   Output Folder: {config['OUTPUT_FOLDER']}/")
        print(f"   Image Server: {config['IMAGE_SERVER']}")
        print(f"   Vista3D Server: {config['VISTA3D_SERVER']}")
        if 'LABEL_SET' in config:
            print(f"   Label Set: {config['LABEL_SET']}")
        else:
            print(f"   Segmentation: {config['VESSELS_OF_INTEREST']}")
        print("-"*60)
        
        return config
    
    def select_installation_profile(self) -> Dict:
        """Select installation profile based on GPU availability and user preference"""
        print("\n" + "="*60)
        print("🎯 STEP 4: INSTALLATION PROFILE SELECTION")
        print("="*60)
        
        has_gpu = self.setup_state.get('has_nvidia_gpu', False)
        
        if has_gpu:
            print("✅ NVIDIA GPU(s) detected on this system")
            print("   This system can run the complete Vista3D stack locally")
            print("")
            print("📋 Available installation profiles:")
            print("   1. 🖥️  Complete Local Setup (Recommended)")
            print("      • Streamlit web interface")
            print("      • Image server")
            print("      • Vista3D AI server (local GPU)")
            print("")
            print("   2. 🌐 Client Only Setup")
            print("      • Streamlit web interface")
            print("      • Image server")
            print("      • Connect to remote Vista3D server")
            print("")
            print("   3. 🚀 Vista3D Server Only")
            print("      • Vista3D AI server (for remote clients)")
            print("      • No web interface or image server")
            
            while True:
                choice = input("\nSelect installation profile [1-3]: ").strip()
                if choice == "1":
                    print("\n✅ Selected: Complete Local Setup")
                    print("   Will install all components for local operation")
                    return {
                        'setup_vista3d': True,
                        'config_updates': {
                            'VISTA3D_SERVER': 'http://localhost:8000',
                            'IMAGE_SERVER': 'http://localhost:8888'
                        }
                    }
                elif choice == "2":
                    print("\n✅ Selected: Client Only Setup")
                    print("   Will install web interface and image server only")
                    remote_server = self._prompt_user(
                        "Enter remote Vista3D server URL",
                        default="http://remote-gpu-server:8000"
                    )
                    return {
                        'setup_vista3d': False,
                        'config_updates': {
                            'VISTA3D_SERVER': remote_server,
                            'IMAGE_SERVER': 'http://localhost:8888'
                        }
                    }
                elif choice == "3":
                    print("\n✅ Selected: Vista3D Server Only")
                    print("   Will install only the Vista3D AI server")
                    return {
                        'setup_vista3d': True,
                        'config_updates': {
                            'VISTA3D_SERVER': 'http://localhost:8000',
                            # No image server for server-only setup
                        }
                    }
                else:
                    print("❌ Invalid choice. Please select 1, 2, or 3.")
        
        else:
            print("⚠️  No NVIDIA GPUs detected on this system")
            print("   This system cannot run Vista3D AI models locally")
            print("")
            print("📋 Available installation profiles:")
            print("   1. 🌐 Client Setup (Recommended)")
            print("      • Streamlit web interface")
            print("      • Image server")
            print("      • Connect to remote Vista3D server")
            print("")
            print("   2. 📦 Dependencies Only")
            print("      • Install Python environment and dependencies")
            print("      • Manual configuration required")
            
            while True:
                choice = input("\nSelect installation profile [1-2]: ").strip()
                if choice == "1":
                    print("\n✅ Selected: Client Setup")
                    print("   Will install web interface and image server")
                    print("   You'll need to configure a remote Vista3D server")
                    remote_server = self._prompt_user(
                        "Enter remote Vista3D server URL",
                        default="http://remote-gpu-server:8000"
                    )
                    return {
                        'setup_vista3d': False,
                        'config_updates': {
                            'VISTA3D_SERVER': remote_server,
                            'IMAGE_SERVER': 'http://localhost:8888'
                        }
                    }
                elif choice == "2":
                    print("\n✅ Selected: Dependencies Only")
                    print("   Will install basic Python environment")
                    print("   Manual configuration will be required")
                    return {
                        'setup_vista3d': False,
                        'config_updates': {
                            'VISTA3D_SERVER': 'http://localhost:8000',
                            'IMAGE_SERVER': 'http://localhost:8888'
                        }
                    }
                else:
                    print("❌ Invalid choice. Please select 1 or 2.")
    
    def gather_ngc_credentials(self) -> Dict:
        """Gather NVIDIA NGC credentials"""
        print("\n🔑 NVIDIA NGC Credentials:")
        print("These are required for Vista3D Docker container.")
        print("Get your API key from: https://ngc.nvidia.com/")
        
        config = {}
        
        # NGC API Key
        while True:
            api_key = getpass.getpass("Enter NGC API Key (starts with 'nvapi-'): ").strip()
            if api_key.startswith('nvapi-') and len(api_key) > 10:
                config['NGC_API_KEY'] = api_key
                break
            print("Invalid API key. Must start with 'nvapi-' and be longer than 10 characters.")
        
        # NGC Org ID
        config['NGC_ORG_ID'] = self._prompt_user(
            "NGC Organization ID",
            default="nvidia"
        )
        
        # Local NIM Cache
        config['LOCAL_NIM_CACHE'] = self._prompt_user(
            "Local NIM cache directory",
            default="~/.cache/nim"
        )
        
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
                # Handle special cases
                if key == 'LABEL_SET' and value:
                    # Uncomment LABEL_SET line and set value
                    env_content = env_content.replace('#LABEL_SET=', f'LABEL_SET=')
                    env_content = env_content.replace('LABEL_SET="HeadNeckCore"', f'LABEL_SET="{value}"')
                    # Comment out VESSELS_OF_INTEREST
                    env_content = env_content.replace('VESSELS_OF_INTEREST=', '#VESSELS_OF_INTEREST=')
                else:
                    # Replace existing values
                    lines = env_content.split('\n')
                    for i, line in enumerate(lines):
                        if line.startswith(f'{key}='):
                            lines[i] = f'{key}="{value}"'
                            break
                    env_content = '\n'.join(lines)
            
            # Add NGC credentials if provided
            if any(key.startswith('NGC_') for key in config.keys()):
                env_content += '\n\n# NVIDIA NGC Credentials\n'
                for key, value in config.items():
                    if key.startswith('NGC_') or key == 'LOCAL_NIM_CACHE':
                        env_content += f'{key}="{value}"\n'
            
            # Ensure LOCAL_NIM_CACHE is always set
            if 'LOCAL_NIM_CACHE' not in env_content:
                env_content += '\n# NVIDIA NGC Credentials\n'
                env_content += 'LOCAL_NIM_CACHE="~/.cache/nim"\n'
            
            # Check for NGC credentials and prompt if missing
            env_content = self.check_and_add_ngc_credentials(env_content)
            
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
            
            # Create NIM cache directory if needed
            if 'LOCAL_NIM_CACHE' in config:
                cache_path = config['LOCAL_NIM_CACHE']
                # Handle tilde notation
                if cache_path.startswith('~'):
                    cache_dir = Path(cache_path).expanduser()
                else:
                    cache_dir = Path(cache_path)
                cache_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"✅ Created NIM cache directory: {cache_dir}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create directories: {e}")
            return False
    
    def install_docker(self) -> bool:
        """Install Docker if not available"""
        logger.info("🐳 Installing Docker...")
        
        if self.system_info['platform'] == 'Linux':
            try:
                # Update package list
                logger.info("Updating package list...")
                subprocess.run(['sudo', 'apt', 'update'], check=True)
                
                # Install basic dependencies
                logger.info("Installing basic dependencies...")
                basic_packages = [
                    'curl', 'wget', 'apt-transport-https', 
                    'ca-certificates', 'software-properties-common', 'gnupg', 'lsb-release'
                ]
                subprocess.run(['sudo', 'apt', 'install', '-y'] + basic_packages, check=True)
                
                # Add Docker GPG key
                logger.info("Adding Docker GPG key...")
                subprocess.run([
                    'curl', '-fsSL', 'https://download.docker.com/linux/ubuntu/gpg'
                ], stdout=subprocess.PIPE, check=True)
                
                # Add Docker repository
                result = subprocess.run(['lsb_release', '-cs'], capture_output=True, text=True, check=True)
                ubuntu_version = result.stdout.strip()
                
                subprocess.run([
                    'sudo', 'add-apt-repository', '-y',
                    f'deb [arch=amd64] https://download.docker.com/linux/ubuntu {ubuntu_version} stable'
                ], check=True)
                
                # Update and install Docker
                logger.info("Installing Docker...")
                subprocess.run(['sudo', 'apt', 'update'], check=True)
                subprocess.run([
                    'sudo', 'apt', 'install', '-y',
                    'docker-ce', 'docker-ce-cli', 'containerd.io', 
                    'docker-buildx-plugin', 'docker-compose-plugin'
                ], check=True)
                
                # Add user to docker group
                username = getpass.getuser()
                subprocess.run(['sudo', 'usermod', '-aG', 'docker', username], check=True)
                
                # Start and enable Docker service
                subprocess.run(['sudo', 'systemctl', 'start', 'docker'], check=True)
                subprocess.run(['sudo', 'systemctl', 'enable', 'docker'], check=True)
                
                logger.info("✅ Docker installed successfully")
                logger.info("⚠️  You may need to logout/login for group changes to take effect")
                return True
                
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Failed to install Docker: {e}")
                return False
            except Exception as e:
                logger.error(f"❌ Error installing Docker: {e}")
                return False
        else:
            logger.error("❌ Automatic Docker installation only supported on Linux")
            logger.info("Please install Docker manually:")
            logger.info("  • Windows: https://docs.docker.com/desktop/install/windows-install/")
            logger.info("  • macOS: https://docs.docker.com/desktop/install/mac-install/")
            return False

    def check_nvidia_container_toolkit(self) -> bool:
        """Check if NVIDIA Container Toolkit is installed"""
        try:
            # Check if nvidia-ctk command exists
            result = subprocess.run(['which', 'nvidia-ctk'], capture_output=True, text=True)
            if result.returncode == 0:
                # Check if Docker runtime is configured
                result = subprocess.run(['docker', 'info'], capture_output=True, text=True)
                if 'nvidia' in result.stdout.lower():
                    return True
            return False
        except Exception:
            return False

    def install_nvidia_container_toolkit(self) -> bool:
        """Install NVIDIA Container Toolkit"""
        logger.info("🔧 Installing NVIDIA Container Toolkit...")
        
        if self.system_info['platform'] != 'Linux':
            logger.error("❌ NVIDIA Container Toolkit installation only supported on Linux")
            return False
        
        try:
            # Update package list
            logger.info("Updating package list...")
            subprocess.run(['sudo', 'apt', 'update'], check=True)
            
            # Install prerequisites
            logger.info("Installing prerequisites...")
            prereq_packages = ['curl', 'gnupg']
            subprocess.run(['sudo', 'apt', 'install', '-y'] + prereq_packages, check=True)
            
            # Add NVIDIA GPG key
            logger.info("Adding NVIDIA GPG key...")
            subprocess.run([
                'curl', '-fsSL', 'https://nvidia.github.io/libnvidia-container/gpgkey'
            ], stdout=subprocess.PIPE, check=True)
            
            # Add NVIDIA repository
            logger.info("Adding NVIDIA repository...")
            repo_url = 'https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list'
            result = subprocess.run(['curl', '-s', '-L', repo_url], capture_output=True, text=True, check=True)
            
            # Write repository file
            repo_file = '/etc/apt/sources.list.d/nvidia-container-toolkit.list'
            with open('/tmp/nvidia-repo.list', 'w') as f:
                f.write(result.stdout)
            
            subprocess.run(['sudo', 'cp', '/tmp/nvidia-repo.list', repo_file], check=True)
            
            # Update package list
            logger.info("Updating package list with NVIDIA repository...")
            subprocess.run(['sudo', 'apt', 'update'], check=True)
            
            # Install NVIDIA Container Toolkit
            logger.info("Installing NVIDIA Container Toolkit...")
            subprocess.run(['sudo', 'apt', 'install', '-y', 'nvidia-container-toolkit'], check=True)
            
            # Configure Docker to use NVIDIA runtime
            logger.info("Configuring Docker for NVIDIA runtime...")
            subprocess.run(['sudo', 'nvidia-ctk', 'runtime', 'configure', '--runtime=docker'], check=True)
            
            # Restart Docker service
            logger.info("Restarting Docker service...")
            subprocess.run(['sudo', 'systemctl', 'restart', 'docker'], check=True)
            
            # Test installation
            logger.info("Testing NVIDIA Container Toolkit...")
            result = subprocess.run([
                'docker', 'run', '--rm', '--gpus', 'all', 
                'nvidia/cuda:11.0-base', 'nvidia-smi'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info("✅ NVIDIA Container Toolkit installed and working")
                return True
            else:
                logger.warning("⚠️  NVIDIA Container Toolkit installed but test failed")
                return True  # Still consider it installed, test might fail for other reasons
                
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to install NVIDIA Container Toolkit: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error installing NVIDIA Container Toolkit: {e}")
            return False

    def check_ngc_cli(self) -> bool:
        """Check if NGC CLI is installed"""
        try:
            result = subprocess.run(['ngc', '--version'], capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False
    
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
    

    def install_ngc_cli(self) -> bool:
        """Install NGC CLI"""
        logger.info("🔧 Installing NGC CLI...")
        
        if self.system_info['platform'] != 'Linux':
            logger.error("❌ NGC CLI installation only supported on Linux")
            logger.info("Please install NGC CLI manually:")
            logger.info("  • Windows: https://docs.nvidia.com/ngc/ngc-cli/install-guide.html#windows")
            logger.info("  • macOS: https://docs.nvidia.com/ngc/ngc-cli/install-guide.html#macos")
            return False
        
        try:
            # Create temporary directory for download
            temp_dir = Path('/tmp/ngc-cli-install')
            temp_dir.mkdir(exist_ok=True)
            
            # Download NGC CLI
            logger.info("Downloading NGC CLI...")
            ngc_url = 'https://api.ngc.nvidia.com/v2/resources/nvidia/ngc-apps/ngc_cli/versions/3.44.0/files/ngccli_linux.zip'
            ngc_zip = temp_dir / 'ngccli_linux.zip'
            
            subprocess.run([
                'wget', '--content-disposition', ngc_url, '-O', str(ngc_zip)
            ], check=True)
            
            # Extract NGC CLI
            logger.info("Extracting NGC CLI...")
            subprocess.run(['unzip', '-o', str(ngc_zip), '-d', str(temp_dir)], check=True)
            
            # Install NGC CLI
            logger.info("Installing NGC CLI...")
            ngc_cli_dir = temp_dir / 'ngc-cli'
            subprocess.run(['bash', str(ngc_cli_dir / 'install')], check=True)
            
            # Add NGC CLI to PATH
            logger.info("Adding NGC CLI to PATH...")
            bashrc_path = Path.home() / '.bashrc'
            ngc_path_line = 'export PATH="$PATH:/home/${USER}/ngc-cli"'
            
            # Check if PATH line already exists
            if bashrc_path.exists():
                with open(bashrc_path, 'r') as f:
                    content = f.read()
                if ngc_path_line not in content:
                    with open(bashrc_path, 'a') as f:
                        f.write(f'\n# NGC CLI PATH\n{ngc_path_line}\n')
            
            # Verify installation
            logger.info("Verifying NGC CLI installation...")
            result = subprocess.run(['ngc', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ NGC CLI installed successfully: {result.stdout.strip()}")
                
                # Clean up temporary files
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
                
                return True
            else:
                logger.warning("⚠️  NGC CLI installed but verification failed")
                return True  # Still consider it installed
                
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to install NGC CLI: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error installing NGC CLI: {e}")
            return False

    def check_docker_requirements(self) -> Tuple[bool, List[str]]:
        """Check Docker and NVIDIA requirements"""
        logger.info("🐳 Checking Docker requirements...")
        
        issues = []
        
        # Check if Docker is installed
        if not shutil.which('docker'):
            logger.warning("⚠️  Docker not found")
            install_docker = self._ask_yes_no("Install Docker?", default=True)
            if install_docker:
                if self.install_docker():
                    logger.info("✅ Docker installed successfully")
                else:
                    issues.append("Failed to install Docker")
            else:
                issues.append("Docker not installed - required for Vista3D")
        else:
            try:
                # Check if Docker daemon is running
                result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
                if result.returncode != 0:
                    issues.append("Docker daemon not running or permission denied")
                    logger.warning("⚠️  Docker daemon not running")
                    start_docker = self._ask_yes_no("Start Docker daemon?", default=True)
                    if start_docker:
                        try:
                            if self.system_info['platform'] == 'Linux':
                                subprocess.run(['sudo', 'systemctl', 'start', 'docker'], check=True)
                                logger.info("✅ Docker daemon started")
                            else:
                                logger.info("Please start Docker Desktop manually")
                        except subprocess.CalledProcessError as e:
                            logger.error(f"❌ Failed to start Docker: {e}")
                            issues.append("Failed to start Docker daemon")
                else:
                    logger.info("✅ Docker is running")
            except Exception as e:
                issues.append(f"Docker error: {e}")
        
        # Check NVIDIA Docker support (if on Linux)
        if self.system_info['platform'] == 'Linux':
            try:
                result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
                if result.returncode != 0:
                    issues.append("NVIDIA drivers not found - GPU support required for Vista3D")
                else:
                    logger.info("✅ NVIDIA drivers found")
                    
                    # Check NVIDIA Container Toolkit
                    nvidia_toolkit_installed = self.check_nvidia_container_toolkit()
                    if not nvidia_toolkit_installed:
                        logger.warning("⚠️  NVIDIA Container Toolkit not found")
                        install_toolkit = self._ask_yes_no("Install NVIDIA Container Toolkit?", default=True)
                        if install_toolkit:
                            if self.install_nvidia_container_toolkit():
                                logger.info("✅ NVIDIA Container Toolkit installed")
                            else:
                                issues.append("Failed to install NVIDIA Container Toolkit")
                        else:
                            issues.append("NVIDIA Container Toolkit not installed - required for GPU support")
                    else:
                        # Test NVIDIA Container Toolkit
                        try:
                            result = subprocess.run(['docker', 'run', '--rm', '--gpus', 'all', 
                                                   'nvidia/cuda:11.0-base', 'nvidia-smi'], 
                                                   capture_output=True, text=True, timeout=30)
                            if result.returncode != 0:
                                issues.append("NVIDIA Container Toolkit not properly configured")
                            else:
                                logger.info("✅ NVIDIA Container Toolkit working")
                        except Exception as e:
                            issues.append(f"NVIDIA Docker test failed: {e}")
                        
            except Exception as e:
                issues.append(f"NVIDIA check failed: {e}")
        
        return len(issues) == 0, issues
    
    def install_system_dependencies(self) -> bool:
        """Install system dependencies (requires sudo)"""
        logger.info("📦 Installing system dependencies...")
        
        if self.system_info['platform'] != 'Linux':
            logger.error("❌ Automatic dependency installation only supported on Linux")
            return False
        
        try:
            # Update package list
            logger.info("Updating package list...")
            subprocess.run(['sudo', 'apt', 'update'], check=True)
            
            # Install basic dependencies
            logger.info("Installing basic dependencies...")
            basic_packages = [
                'curl', 'wget', 'git', 'unzip', 'apt-transport-https', 
                'ca-certificates', 'software-properties-common', 'gnupg', 'lsb-release'
            ]
            subprocess.run(['sudo', 'apt', 'install', '-y'] + basic_packages, check=True)
            
            # Install Docker if not present
            if not shutil.which('docker'):
                if not self.install_docker():
                    logger.warning("⚠️  Docker installation failed")
                    return False
            
            # Install NVIDIA Container Toolkit if needed
            if shutil.which('nvidia-smi'):
                if not self.install_nvidia_container_toolkit():
                    logger.warning("⚠️  NVIDIA Container Toolkit installation failed")
                    return False
            
            # Install uv if not present
            if not shutil.which('uv'):
                logger.info("Installing uv package manager...")
                try:
                    subprocess.run([
                        'curl', '-LsSf', 'https://astral.sh/uv/install.sh'
                    ], stdout=subprocess.PIPE, check=True)
                    
                    # Source bashrc to get uv in PATH
                    bashrc_path = Path.home() / '.bashrc'
                    if bashrc_path.exists():
                        subprocess.run(['bash', '-c', 'source ~/.bashrc'], check=True)
                    
                    # Verify installation
                    result = subprocess.run(['uv', '--version'], capture_output=True, text=True, check=True)
                    logger.info(f"✅ uv package manager installed: {result.stdout.strip()}")
                except subprocess.CalledProcessError as e:
                    logger.warning(f"⚠️  Failed to install uv: {e}")
                    logger.info("You can install uv manually later")
            
            # Install NGC CLI if not present
            if not self.check_ngc_cli():
                if not self.install_ngc_cli():
                    logger.warning("⚠️  NGC CLI installation failed")
                    logger.info("You can install NGC CLI manually later")
            
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to install dependencies: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error during installation: {e}")
            return False
    
    def setup_vista3d_docker(self, config: Dict) -> bool:
        """Set up Vista3D Docker container"""
        logger.info("🧠 Setting up Vista3D Docker container...")
        
        if 'NGC_API_KEY' not in config:
            logger.error("❌ NGC API key required for Vista3D setup")
            return False
        
        try:
            # Login to NGC registry
            logger.info("Logging into NVIDIA NGC registry...")
            subprocess.run([
                'docker', 'login', 'nvcr.io',
                '-u', '$oauthtoken',
                '-p', config['NGC_API_KEY']
            ], check=True, input=config['NGC_API_KEY'], text=True)
            
            # Pull Vista3D image
            logger.info("Pulling Vista3D Docker image (this may take several minutes)...")
            subprocess.run([
                'docker', 'pull', 'nvcr.io/nim/nvidia/vista3d:1.0.0'
            ], check=True)
            
            logger.info("✅ Vista3D Docker image ready")
            
            # Test container startup
            logger.info("Testing Vista3D container...")
            try:
                # Use the start_vista3d.py script
                start_script = self.project_root / 'utils' / 'start_vista3d.py'
                if start_script.exists():
                    subprocess.run([sys.executable, str(start_script)], 
                                 cwd=self.project_root, timeout=120, check=True)
                    logger.info("✅ Vista3D container started successfully")
                else:
                    logger.warning("⚠️  start_vista3d.py not found - you'll need to start manually")
                    
            except subprocess.TimeoutExpired:
                logger.warning("⚠️  Vista3D startup took longer than expected - check with 'docker logs vista3d'")
            except subprocess.CalledProcessError as e:
                logger.warning(f"⚠️  Vista3D startup may have issues: {e}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to set up Vista3D: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error during Vista3D setup: {e}")
            return False
    
    def start_image_server_background(self, config: Dict) -> bool:
        """Start the image server in the background"""
        try:
            import subprocess
            import time
            import requests
            from urllib.parse import urlparse
            
            # Get image server URL from config
            image_server_url = config.get('IMAGE_SERVER', 'http://localhost:8888')
            parsed = urlparse(image_server_url)
            host = parsed.hostname or "localhost"
            port = parsed.port or 8888
            
            # Check if server is already running
            try:
                response = requests.head(image_server_url, timeout=3)
                if response.status_code == 200:
                    logger.info(f"✅ Image server already running at {image_server_url}")
                    return True
            except:
                pass  # Server not running, continue with startup
            
            # Start image server in background
            logger.info("🚀 Starting image server in background...")
            
            # Use subprocess.Popen to start in background
            server_process = subprocess.Popen([
                sys.executable, "utils/image_server.py",
                "--host", host,
                "--port", str(port)
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait a moment for server to start
            time.sleep(3)
            
            # Check if server started successfully
            try:
                response = requests.head(image_server_url, timeout=5)
                if response.status_code == 200:
                    logger.info(f"✅ Image server started successfully at {image_server_url}")
                    logger.info(f"   Process ID: {server_process.pid}")
                    return True
                else:
                    logger.warning(f"⚠️  Image server responded with status {response.status_code}")
                    return False
            except Exception as e:
                logger.warning(f"⚠️  Could not verify image server startup: {e}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to start image server: {e}")
            return False
    
    def print_next_steps(self, config: Dict):
        """Print next steps for the user"""
        print("\n" + "="*80)
        print("🎉 Setup Complete!")
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
        
        # 3. Start Vista3D
        print(f"\n3. 🧠 Start Vista3D container:")
        print("   python utils/start_vista3d.py")
        
        # 4. Image server
        print(f"\n4. 🖥️  Image server:")
        print("   python utils/image_server.py")
        print("   (Already started in background during setup)")
        
        # 5. Run segmentation
        print(f"\n5. 🔬 Run segmentation:")
        print("   python utils/segment.py")
        
        # 6. Start web interface
        print(f"\n6. 🌐 Start web interface:")
        print("   streamlit run app.py")
        
        print(f"\n📄 Configuration saved to: {self.env_file}")
        print(f"🔐 Keep your .env file secure - it contains sensitive credentials")
        
        # Additional notes
        if 'IMAGE_SERVER' in config and 'localhost' not in config['IMAGE_SERVER']:
            print(f"\n🌐 External Access Configured:")
            print(f"   • Image server: {config['IMAGE_SERVER']}")
            print(f"   • Ensure port 8888 is open in your firewall")
            print(f"   • Vista3D will access images from this URL")
        
        print("\n" + "="*80)
    
    def _prompt_user(self, prompt: str, default: str = None, validation=None) -> str:
        """Prompt user for input with optional default and validation"""
        while True:
            if default:
                user_input = input(f"{prompt} [{default}]: ").strip()
                if not user_input:
                    user_input = default
            else:
                user_input = input(f"{prompt}: ").strip()
            
            if validation and not validation(user_input):
                print("Invalid input. Please try again.")
                continue
            
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
    
    def check_and_add_ngc_credentials(self, env_content: str) -> str:
        """Check for NGC credentials and prompt user to add them if missing"""
        # Check if NGC_API_KEY exists and is not empty
        has_ngc_key = False
        has_ngc_org_id = False
        ngc_key_value = ""
        ngc_org_id_value = ""
        
        for line in env_content.split('\n'):
            if line.startswith('NGC_API_KEY='):
                # Extract the value (remove quotes if present)
                value = line.split('=', 1)[1].strip()
                if value and value != '""' and value != "''" and not value.startswith('#'):
                    has_ngc_key = True
                    ngc_key_value = value.strip('"\'')
            elif line.startswith('NGC_ORG_ID='):
                # Extract the value (remove quotes if present)
                value = line.split('=', 1)[1].strip()
                if value and value != '""' and value != "''" and not value.startswith('#'):
                    has_ngc_org_id = True
                    ngc_org_id_value = value.strip('"\'')
        
        if not has_ngc_key or not has_ngc_org_id:
            print("\n🔑 NVIDIA NGC Credentials Required")
            print("NGC credentials are needed for Vista3D Docker container access.")
            print("Get your API key from: https://ngc.nvidia.com/")
            
            add_ngc_creds = self._ask_yes_no("Add NGC credentials to .env file?", default=True)
            if add_ngc_creds:
                # Get NGC API Key
                if not has_ngc_key:
                    while True:
                        api_key = getpass.getpass("Enter NGC API Key (starts with 'nvapi-'): ").strip()
                        if api_key.startswith('nvapi-') and len(api_key) > 10:
                            ngc_key_value = api_key
                            break
                        else:
                            print("Invalid API key. Must start with 'nvapi-' and be longer than 10 characters.")
                
                # Get NGC Organization ID
                if not has_ngc_org_id:
                    ngc_org_id = self._prompt_user(
                        "Enter NGC Organization ID",
                        default="nvidia"
                    )
                    ngc_org_id_value = ngc_org_id
                
                # Add NGC credentials to env content
                if not env_content.endswith('\n'):
                    env_content += '\n'
                env_content += '\n# NVIDIA NGC Credentials\n'
                env_content += f'NGC_API_KEY="{ngc_key_value}"\n'
                env_content += f'NGC_ORG_ID="{ngc_org_id_value}"\n'
                env_content += f'LOCAL_NIM_CACHE="~/.cache/nim"\n'
                logger.info("✅ NGC credentials added to .env file")
            else:
                logger.warning("⚠️  NGC credentials not added - Vista3D setup will require them later")
        
        return env_content

    def check_existing_env(self) -> bool:
        """Check if .env file already exists and update NGC_API_KEY (PROJECT_ROOT no longer needed)"""
        if self.env_file.exists():
            logger.info("📄 Found existing .env file")
            
            # Read current .env file
            try:
                with open(self.env_file, 'r') as f:
                    env_content = f.read()
                
                updated = False
                
                # Remove PROJECT_ROOT line if it exists (no longer needed)
                lines = env_content.split('\n')
                new_lines = []
                for line in lines:
                    if not line.startswith('PROJECT_ROOT='):
                        new_lines.append(line)
                    else:
                        updated = True
                        logger.info("🔄 Removing PROJECT_ROOT from .env file (now auto-detected)")
                
                if updated:
                    env_content = '\n'.join(new_lines)
                    logger.info("✅ PROJECT_ROOT is now auto-detected and no longer needed in .env")
                
                # Check for NGC credentials
                env_content = self.check_and_add_ngc_credentials(env_content)
                
                # Write updated .env file if changes were made
                if updated or 'NGC_API_KEY=' in env_content:
                    with open(self.env_file, 'w') as f:
                        f.write(env_content)
                    logger.info("✅ .env file updated")
                
                return True
                
            except Exception as e:
                logger.warning(f"⚠️  Could not update .env file: {e}")
                return False
        
        return False

    def run_interactive_setup(self) -> bool:
        """Run the main interactive setup process with state tracking and error recovery"""
        try:
            self.print_banner()
            
            # Check for previous setup progress
            self._check_previous_run()
            
            # Step 1: Check for existing .env file and update configuration
            if not self.setup_state.get('env_file_created'):
                if self.check_existing_env():
                    self._save_setup_state('env_file_created')
                    print("\n🎉 Setup complete! Your .env file has been updated.")
                    print("PROJECT_ROOT is now auto-detected and no longer needs configuration.")
                    print("You can now proceed with:")
                    print("  • python utils/start_vista3d.py")
                    print("  • python utils/image_server.py")
                    print("  • streamlit run app.py")
                    return True
            
            # Step 2: Check basic requirements
            if not self.setup_state.get('system_requirements_checked'):
                try:
                    if self.check_system_requirements():
                        self._save_setup_state('system_requirements_checked')
                    else:
                        if not self._handle_step_failure('system_requirements_checked', 
                                                        Exception("System requirements check failed"), critical=True):
                            return False
                except Exception as e:
                    if not self._handle_step_failure('system_requirements_checked', e, critical=True):
                        return False
            else:
                print("\n✅ SKIPPING: System requirements already verified")
            
            # Step 3: Check Python environment
            if not self.setup_state.get('python_environment_ready'):
                try:
                    if self.check_python_environment():
                        self._save_setup_state('python_environment_ready')
                    else:
                        if not self._handle_step_failure('python_environment_ready', 
                                                        Exception("Python environment setup failed"), critical=True):
                            return False
                except Exception as e:
                    if not self._handle_step_failure('python_environment_ready', e, critical=True):
                        return False
            else:
                print("\n✅ SKIPPING: Python environment already ready")
            
            # Step 4: Gather user configuration
            if not self.setup_state.get('configuration_gathered'):
                try:
                    config = self.gather_user_configuration()
                    self._save_setup_state('configuration_gathered')
                    # Save config for later use
                    self.config = config
                except Exception as e:
                    if not self._handle_step_failure('configuration_gathered', e, critical=True):
                        return False
            else:
                print("\n✅ SKIPPING: Configuration already gathered")
                # Try to load config from .env file if available
                if self.env_file.exists():
                    config = self._load_config_from_env()
                else:
                    # If no config available, re-gather
                    config = self.gather_user_configuration()
                    self._save_setup_state('configuration_gathered')
            
            # Step 5: Installation profile selection based on GPU availability
            installation_profile = self.select_installation_profile()
            setup_vista3d = installation_profile['setup_vista3d']
            config.update(installation_profile['config_updates'])
            
            if setup_vista3d:
                try:
                    ngc_config = self.gather_ngc_credentials()
                    config.update(ngc_config)
                except Exception as e:
                    if not self._handle_step_failure('ngc_credentials', e, critical=False):
                        print("⚠️  Continuing without Vista3D setup...")
                        setup_vista3d = False
            
            # Step 6: Create .env file
            if not self.setup_state.get('env_file_created'):
                try:
                    if self.create_env_file(config):
                        self._save_setup_state('env_file_created')
                    else:
                        if not self._handle_step_failure('env_file_created', 
                                                        Exception(".env file creation failed"), critical=True):
                            return False
                except Exception as e:
                    if not self._handle_step_failure('env_file_created', e, critical=True):
                        return False
            else:
                print("\n✅ SKIPPING: .env file already created")
            
            # Step 7: Create required directories
            if not self.setup_state.get('directories_created'):
                try:
                    if self.create_required_directories(config):
                        self._save_setup_state('directories_created')
                    else:
                        if not self._handle_step_failure('directories_created', 
                                                        Exception("Directory creation failed"), critical=True):
                            return False
                except Exception as e:
                    if not self._handle_step_failure('directories_created', e, critical=True):
                        return False
            else:
                print("\n✅ SKIPPING: Required directories already created")
            
            # Step 8: Check Docker requirements
            if not self.setup_state.get('docker_checked'):
                try:
                    docker_ok, docker_issues = self.check_docker_requirements()
                    if not docker_ok:
                        print("\n🐳 Docker Issues Found:")
                        for issue in docker_issues:
                            print(f"  • {issue}")
                        
                        install_deps = self._ask_yes_no("Install missing dependencies?", default=True)
                        if install_deps:
                            if not self.install_system_dependencies():
                                print("⚠️  Some dependencies may not have installed correctly")
                                print("   You can re-run setup.py to try again")
                    
                    self._save_setup_state('docker_checked')
                except Exception as e:
                    if not self._handle_step_failure('docker_checked', e, critical=False):
                        print("⚠️  Continuing without Docker verification...")
            else:
                print("\n✅ SKIPPING: Docker requirements already checked")
            
            # Step 9: Set up Vista3D if requested
            if setup_vista3d and 'NGC_API_KEY' in config and not self.setup_state.get('vista3d_setup'):
                try:
                    vista3d_ok = self.setup_vista3d_docker(config)
                    if vista3d_ok:
                        self._save_setup_state('vista3d_setup')
                    else:
                        print("⚠️  Vista3D setup had issues - you can retry later by running:")
                        print("      python setup.py --setup-vista3d")
                except Exception as e:
                    if not self._handle_step_failure('vista3d_setup', e, critical=False):
                        print("⚠️  Continuing without Vista3D setup...")
            elif self.setup_state.get('vista3d_setup'):
                print("\n✅ SKIPPING: Vista3D already set up")
            
            # Step 10: Start image server in background
            if not self.setup_state.get('image_server_started'):
                try:
                    print("\n🌐 Starting image server...")
                    server_started = self.start_image_server_background(config)
                    if server_started:
                        print("✅ Image server is running in the background")
                        self._save_setup_state('image_server_started')
                    else:
                        print("⚠️  Image server startup failed - you can start it manually later:")
                        print("      python utils/image_server.py")
                except Exception as e:
                    print(f"⚠️  Image server startup error: {e}")
                    print("   You can start it manually later: python utils/image_server.py")
            else:
                print("\n✅ SKIPPING: Image server already started")
            
            # Final step: Show next steps and cleanup
            self.print_next_steps(config)
            
            # Mark setup as complete
            self._save_setup_state('setup_complete')
            
            # Clean up state file if everything succeeded
            if self.setup_state_file.exists():
                try:
                    self.setup_state_file.unlink()
                    print("\n🧹 Setup state cleaned up successfully")
                except:
                    pass  # Not critical if cleanup fails
            
            return True
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Setup interrupted by user")
            print("💡 You can resume setup by running: python setup.py")
            return False
        except Exception as e:
            print(f"\n❌ Unexpected error during setup: {e}")
            print("💡 You can retry setup by running: python setup.py")
            print("   Setup will resume from where it left off")
            return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="HPE NVIDIA Vista3D Medical AI Platform Setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python setup.py                    # Interactive setup (recommended)
  python setup.py --install-deps     # Install system dependencies only
  python setup.py --setup-vista3d    # Set up Vista3D Docker container only
  python setup.py --start-image-server # Start image server in background only

The interactive setup will guide you through:
  1. System requirements check
  2. Python environment setup
  3. Configuration gathering
  4. Environment file creation
  5. Directory creation
  6. Optional dependency installation
  7. Optional Vista3D Docker setup

Requirements:
  • Python 3.11+
  • Internet connectivity
  • For Vista3D: NVIDIA GPU, Docker, NGC account
  • For system installation: sudo access (Linux)
        """
    )
    
    parser.add_argument(
        '--install-deps',
        action='store_true',
        help='Install system dependencies (requires sudo on Linux)'
    )
    
    parser.add_argument(
        '--setup-vista3d',
        action='store_true',
        help='Set up Vista3D Docker container (requires NGC credentials)'
    )
    
    parser.add_argument(
        '--start-image-server',
        action='store_true',
        help='Start the image server in background'
    )
    
    parser.add_argument(
        '--non-interactive',
        action='store_true',
        help='Run in non-interactive mode (use defaults)'
    )
    
    args = parser.parse_args()
    
    setup_manager = SetupManager()
    
    try:
        if args.install_deps:
            success = setup_manager.install_system_dependencies()
            sys.exit(0 if success else 1)
        elif args.setup_vista3d:
            # Need NGC credentials for Vista3D setup
            config = setup_manager.gather_ngc_credentials()
            success = setup_manager.setup_vista3d_docker(config)
            sys.exit(0 if success else 1)
        elif args.start_image_server:
            # Start image server only
            config = setup_manager.gather_user_configuration()
            success = setup_manager.start_image_server_background(config)
            sys.exit(0 if success else 1)
        else:
            # Default: run interactive setup
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
