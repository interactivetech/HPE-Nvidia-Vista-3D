#!/usr/bin/env python3
"""
HPE NVIDIA Vista3D Server Setup Script
Interactive setup for Vista3D server configuration after cloning from git
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

class Vista3DServerSetupManager:
    """Interactive setup manager for the Vista3D server"""
    
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.project_root = self.script_dir
        self.env_file = self.project_root / '.env'
        self.env_template = self.project_root / 'dot_env_template'
        self.setup_state_file = self.project_root / '.setup_state_server.json'
        
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
        print("🚀 HPE NVIDIA Vista3D Server Setup")
        print("="*80)
        print("This script will guide you through setting up the Vista3D server")
        print("for AI processing on a Linux server with NVIDIA GPU. It will:")
        print("  • Check system requirements (NVIDIA GPU, Docker)")
        print("  • Configure environment variables")
        print("  • Set up Vista3D Docker container")
        print("  • Configure for remote client access")
        print("="*80)
        
        print("\n📋 VISTA3D SERVER WORKFLOW:")
        print("-" * 40)
        print("The Vista3D server processes medical imaging data:")
        print("  1. 📥 Receives NIfTI files from image server")
        print("  2. 🧠 AI analyzes and segments anatomical structures")
        print("  3. 📤 Returns segmentation results to clients")
        print("  4. 🌐 Serves processed data to web interfaces")
        
        print("\n🔧 SERVER REQUIREMENTS:")
        print("-" * 40)
        print("• Ubuntu Linux 18.04+ or RHEL/CentOS 7+")
        print("• NVIDIA GPU with CUDA support (RTX/Tesla/A100/H100)")
        print("• NVIDIA drivers (version 470+)")
        print("• Docker and NVIDIA Container Toolkit")
        print("• At least 8GB RAM and 10GB free disk space")
        print("• NVIDIA NGC account and API key")
        
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
            'docker_checked': False,
            'ngc_credentials_gathered': False,
            'env_file_created': False,
            'directories_created': False,
            'vista3d_setup': False,
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
        """Check system requirements for Vista3D server"""
        print("\n" + "="*60)
        print("🔍 STEP 1: SYSTEM REQUIREMENTS CHECK")
        print("="*60)
        print("Verifying your system meets the requirements for Vista3D server...")
        
        issues = []
        
        # Check operating system
        print("\n📍 Checking operating system...")
        if self.system_info['platform'] != 'Linux':
            print(f"❌ Operating system check failed")
            print(f"   Required: Linux (Ubuntu 18.04+ or RHEL/CentOS 7+)")
            print(f"   Found: {self.system_info['platform']} {self.system_info['release']}")
            issues.append(f"Linux required, found {self.system_info['platform']}")
        else:
            print(f"✅ Operating system check passed")
            print(f"   Platform: {self.system_info['platform']} {self.system_info['release']}")
            print(f"   Architecture: {self.system_info['architecture']}")
        
        # Check NVIDIA GPU availability
        print("\n📍 Checking NVIDIA GPU availability...")
        nvidia_gpus = self.check_nvidia_gpus()
        if nvidia_gpus['has_gpus']:
            print(f"✅ NVIDIA GPU(s) detected:")
            for i, gpu in enumerate(nvidia_gpus['gpus']):
                print(f"   {i+1}. {gpu['name']} ({gpu['memory']})")
            print("   This system can run Vista3D AI models")
            self.setup_state['has_nvidia_gpu'] = True
        else:
            print("❌ No NVIDIA GPUs detected")
            print("   NVIDIA GPUs are required for Vista3D server")
            issues.append("NVIDIA GPU required for Vista3D server")
            self.setup_state['has_nvidia_gpu'] = False
        
        # Check Docker availability
        print("\n📍 Checking Docker availability...")
        if not shutil.which('docker'):
            print("❌ Docker not found")
            print("   Docker is required for Vista3D container")
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
        
        # Check NVIDIA Container Toolkit
        print("\n📍 Checking NVIDIA Container Toolkit...")
        if not self.check_nvidia_container_toolkit():
            print("❌ NVIDIA Container Toolkit not found")
            print("   Required for GPU access in Docker containers")
            issues.append("NVIDIA Container Toolkit not found")
        else:
            print("✅ NVIDIA Container Toolkit is available")
        
        # Check NGC CLI
        print("\n📍 Checking NVIDIA NGC CLI...")
        if not self.check_ngc_cli():
            print("❌ NGC CLI not found")
            print("   Required for Vista3D Docker image access")
            issues.append("NGC CLI not found")
        else:
            print("✅ NGC CLI is available")
        
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
            print("   All system requirements are met!")
            print("   Your system is ready for Vista3D server setup.")
        
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
    
    def check_ngc_cli(self) -> bool:
        """Check if NGC CLI is installed"""
        try:
            result = subprocess.run(['ngc', '--version'], capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False
    
    def gather_server_configuration(self) -> Dict:
        """Gather server-specific configuration"""
        print("\n" + "="*60)
        print("📝 STEP 2: SERVER CONFIGURATION")
        print("="*60)
        print("Configuring Vista3D server for remote client access...")
        
        config = {}
        
        # Server port configuration
        print("\n📍 Configuring Vista3D server port...")
        print("   This is the port where Vista3D will listen for client requests")
        print("   Default port 8000 is recommended for server deployments")
        
        config['VISTA3D_PORT'] = self._prompt_user(
            "Vista3D server port",
            default="8000"
        )
        print(f"✅ Vista3D server will listen on port {config['VISTA3D_PORT']}")
        
        # Network configuration
        print("\n📍 Configuring network access...")
        print("   Vista3D server needs to accept connections from remote clients")
        print("   Host networking provides maximum compatibility")
        
        use_host_networking = self._ask_yes_no("Use host networking for maximum compatibility?", default=True)
        config['USE_HOST_NETWORKING'] = str(use_host_networking)
        
        if use_host_networking:
            print("✅ Host networking enabled - Vista3D accessible on all interfaces")
        else:
            print("✅ Bridge networking enabled - Vista3D accessible on configured port")
        
        # Output folder configuration
        print("\n📍 Configuring output folder...")
        print("   This folder will store processed results and temporary files")
        print("   Use an absolute path for server deployments")
        
        config['OUTPUT_FOLDER'] = self._prompt_user(
            "Output folder absolute path",
            default=str(self.project_root / "output")
        )
        output_path = Path(config['OUTPUT_FOLDER'])
        if not output_path.is_absolute():
            output_path = self.project_root / config['OUTPUT_FOLDER']
        print(f"✅ Processed results will be stored in: {output_path}")
        
        # GPU configuration
        print("\n📍 Configuring GPU settings...")
        nvidia_gpus = self.check_nvidia_gpus()
        if nvidia_gpus['has_gpus']:
            print(f"   Found {nvidia_gpus['gpu_count']} GPU(s)")
            if nvidia_gpus['gpu_count'] > 1:
                print("   Multiple GPUs detected - you can specify which GPU(s) to use")
                gpu_devices = self._prompt_user(
                    "CUDA_VISIBLE_DEVICES (comma-separated GPU IDs, or 'all')",
                    default="all"
                )
                config['CUDA_VISIBLE_DEVICES'] = gpu_devices
            else:
                config['CUDA_VISIBLE_DEVICES'] = "0"
                print("✅ Using GPU 0")
        else:
            config['CUDA_VISIBLE_DEVICES'] = "0"
            print("⚠️  No GPUs detected - using default configuration")
        
        # Performance settings
        print("\n📍 Configuring performance settings...")
        print("   These settings affect server performance and resource usage")
        
        memory_limit = self._prompt_user(
            "Container memory limit (e.g., 16G, 32G)",
            default="16G"
        )
        config['VISTA3D_MEMORY_LIMIT'] = memory_limit
        
        cpu_limit = self._prompt_user(
            "Container CPU limit (number of cores, e.g., 8)",
            default="8"
        )
        config['VISTA3D_CPU_LIMIT'] = cpu_limit
        
        shm_size = self._prompt_user(
            "Shared memory size (e.g., 12G, 16G)",
            default="12G"
        )
        config['VISTA3D_SHM_SIZE'] = shm_size
        
        print(f"✅ Performance settings: {memory_limit} RAM, {cpu_limit} CPUs, {shm_size} shared memory")
        
        # Auto-restart configuration
        print("\n📍 Configuring auto-restart...")
        print("   Enable automatic restart if container fails")
        
        auto_restart = self._ask_yes_no("Enable automatic container restart?", default=True)
        config['VISTA3D_AUTO_RESTART'] = str(auto_restart)
        
        if auto_restart:
            print("✅ Auto-restart enabled - container will restart automatically if it fails")
        else:
            print("✅ Auto-restart disabled - manual intervention required if container fails")
        
        # Configuration summary
        print("\n" + "-"*60)
        print("📋 SERVER CONFIGURATION SUMMARY:")
        print(f"   Vista3D Port: {config['VISTA3D_PORT']}")
        print(f"   Host Networking: {config['USE_HOST_NETWORKING']}")
        print(f"   Output Folder: {config['OUTPUT_FOLDER']}")
        print(f"   GPU Devices: {config['CUDA_VISIBLE_DEVICES']}")
        print(f"   Memory Limit: {config['VISTA3D_MEMORY_LIMIT']}")
        print(f"   CPU Limit: {config['VISTA3D_CPU_LIMIT']}")
        print(f"   Shared Memory: {config['VISTA3D_SHM_SIZE']}")
        print(f"   Auto-restart: {config['VISTA3D_AUTO_RESTART']}")
        print("-"*60)
        
        return config
    
    def gather_ngc_credentials(self) -> Dict:
        """Gather NVIDIA NGC credentials"""
        print("\n🔑 NVIDIA NGC Credentials:")
        print("These are required for Vista3D Docker container.")
        print("Get your API key from: https://ngc.nvidia.com/")
        
        config = {}
        
        # Check if NGC API key already exists in .env file
        existing_ngc_key = self._check_existing_ngc_credentials()
        if existing_ngc_key:
            print(f"\n✅ Found existing NGC API key in .env file")
            print(f"   Key: {existing_ngc_key[:10]}...{existing_ngc_key[-4:]}")
            use_existing = self._ask_yes_no("Use existing NGC API key?", default=True)
            
            if use_existing:
                config['NGC_API_KEY'] = existing_ngc_key
                print("✅ Using existing NGC API key")
            else:
                print("🔄 Will prompt for new NGC API key")
                existing_ngc_key = None
        
        # NGC API Key - only prompt if not using existing
        if not existing_ngc_key:
            while True:
                print("\nEnter your NGC API Key:")
                print("(You can paste the key - it will be hidden for security)")
                api_key = getpass.getpass("NGC API Key (starts with 'nvapi-'): ").strip()
                if api_key.startswith('nvapi-') and len(api_key) > 10:
                    config['NGC_API_KEY'] = api_key
                    print("✅ API key accepted")
                    break
                print("❌ Invalid API key. Must start with 'nvapi-' and be longer than 10 characters.")
                print("   Please try again...")
        
        # NGC Org ID - check if already exists
        existing_org_id = self._check_existing_env_value('NGC_ORG_ID')
        if existing_org_id:
            print(f"\n✅ Found existing NGC Organization ID: {existing_org_id}")
            use_existing_org = self._ask_yes_no("Use existing Organization ID?", default=True)
            if use_existing_org:
                config['NGC_ORG_ID'] = existing_org_id
            else:
                config['NGC_ORG_ID'] = self._prompt_user(
                    "NGC Organization ID",
                    default="nvidia"
                )
        else:
            config['NGC_ORG_ID'] = self._prompt_user(
                "NGC Organization ID",
                default="nvidia"
            )
        
        # Local NIM Cache - check if already exists
        existing_cache = self._check_existing_env_value('LOCAL_NIM_CACHE')
        if existing_cache:
            print(f"\n✅ Found existing NIM cache directory: {existing_cache}")
            use_existing_cache = self._ask_yes_no("Use existing NIM cache directory?", default=True)
            if use_existing_cache:
                config['LOCAL_NIM_CACHE'] = existing_cache
            else:
                config['LOCAL_NIM_CACHE'] = self._prompt_user(
                    "Local NIM cache directory",
                    default="~/.cache/nim"
                )
        else:
            config['LOCAL_NIM_CACHE'] = self._prompt_user(
                "Local NIM cache directory",
                default="~/.cache/nim"
            )
        
        return config
    
    def create_env_file(self, config: Dict) -> bool:
        """Create or update .env file for server configuration"""
        logger.info("📄 Creating/updating .env file for Vista3D server...")
        
        try:
            # Read existing .env file if it exists
            existing_env = {}
            if self.env_file.exists():
                logger.info(f"📖 Reading existing .env file: {self.env_file}")
                with open(self.env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()
                            # Remove quotes if present
                            if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                                value = value[1:-1]
                            existing_env[key] = value
                logger.info(f"✅ Found {len(existing_env)} existing environment variables")
            else:
                logger.info("📄 No existing .env file found, will create new one")
            
            # Read template for any missing variables
            template_env = {}
            if self.env_template.exists():
                with open(self.env_template, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()
                            # Remove quotes if present
                            if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                                value = value[1:-1]
                            template_env[key] = value
            
            # Merge configurations: existing -> template -> new config
            merged_env = {}
            merged_env.update(template_env)  # Start with template defaults
            merged_env.update(existing_env)  # Override with existing values
            merged_env.update(config)        # Override with new server config
            
            # Add server-specific configurations if not already present
            server_configs = {
                'VISTA3D_SERVER': f'http://localhost:{config.get("VISTA3D_PORT", "8000")}',
                'IMAGE_SERVER': 'http://localhost:8888',
                'USE_HOST_NETWORKING': config.get('USE_HOST_NETWORKING', 'True')
            }
            
            for key, value in server_configs.items():
                if key not in merged_env:
                    merged_env[key] = value
            
            # Write updated .env file
            with open(self.env_file, 'w') as f:
                f.write("# Vista3D Environment Configuration\n")
                f.write("# Generated/updated by setup_vista3d_server.py\n\n")
                
                # Write all environment variables
                for key, value in sorted(merged_env.items()):
                    f.write(f'{key}="{value}"\n')
            
            logger.info(f"✅ Updated .env file: {self.env_file}")
            logger.info(f"   Total variables: {len(merged_env)}")
            logger.info(f"   Updated variables: {len(config)}")
            
            # Set proper permissions (readable by owner only)
            os.chmod(self.env_file, 0o600)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create/update .env file: {e}")
            return False
    
    def create_required_directories(self, config: Dict) -> bool:
        """Create required directories for server"""
        logger.info("📁 Creating required directories...")
        
        try:
            # Create directories
            directories = [
                Path(config['OUTPUT_FOLDER'])
            ]
            
            for directory in directories:
                directory.mkdir(parents=True, exist_ok=True)
                logger.info(f"✅ Created directory: {directory}")
            
            # Create NIM cache directory if needed
            if 'LOCAL_NIM_CACHE' in config:
                cache_path = config['LOCAL_NIM_CACHE']
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
            ], check=True)
            
            # Pull Vista3D image
            logger.info("Pulling Vista3D Docker image (this may take several minutes)...")
            subprocess.run([
                'docker', 'pull', 'nvcr.io/nim/nvidia/vista3d:1.0.0'
            ], check=True)
            
            logger.info("✅ Vista3D Docker image ready")
            
            # Test container startup
            logger.info("Testing Vista3D container...")
            try:
                # Use the start_vista3d_server.py script
                start_script = self.project_root / 'utils' / 'start_vista3d_server.py'
                if start_script.exists():
                    subprocess.run([sys.executable, str(start_script)], 
                                 cwd=self.project_root, timeout=120, check=True)
                    logger.info("✅ Vista3D container started successfully")
                else:
                    logger.warning("⚠️  start_vista3d_server.py not found - you'll need to start manually")
                    
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
    
    def print_next_steps(self, config: Dict):
        """Print next steps for the user"""
        print("\n" + "="*80)
        print("🎉 Vista3D Server Setup Complete!")
        print("="*80)
        
        print("\n📋 Next Steps:")
        
        # 1. Start Vista3D server
        print(f"\n1. 🧠 Start Vista3D server:")
        print("   python utils/start_vista3d_server.py")
        print("   • This starts the Vista3D Docker container")
        print("   • Server will be accessible on all network interfaces")
        print("   • Check logs with: docker logs -f vista3d")
        
        # 2. Test server
        vista3d_port = config.get('VISTA3D_PORT', '8000')
        print(f"\n2. 🧪 Test server connectivity:")
        print(f"   curl http://localhost:{vista3d_port}/health")
        print("   • Should return HTTP 200 if server is running")
        print("   • Check server status with: docker ps | grep vista3d")
        
        # 3. Configure clients
        print(f"\n3. 🌐 Configure client connections:")
        print("   • Clients should connect to: http://YOUR_SERVER_IP:{vista3d_port}")
        print("   • Replace YOUR_SERVER_IP with this server's IP address")
        print("   • Ensure firewall allows connections on port {vista3d_port}")
        
        # 4. Monitor server
        print(f"\n4. 📊 Monitor server performance:")
        print("   • View logs: docker logs -f vista3d")
        print("   • Check GPU usage: nvidia-smi")
        print("   • Monitor resources: docker stats vista3d")
        
        print(f"\n📄 Configuration saved to: {self.env_file}")
        print(f"🔐 Keep your .env file secure - it contains sensitive credentials")
        
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
    
    def _check_existing_ngc_credentials(self) -> Optional[str]:
        """Check if NGC API key already exists in .env file"""
        if not self.env_file.exists():
            return None
        
        try:
            with open(self.env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('NGC_API_KEY='):
                        # Extract the value, handling both quoted and unquoted values
                        value = line.split('=', 1)[1].strip()
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        
                        if value.startswith('nvapi-') and len(value) > 10:
                            return value
        except Exception as e:
            logger.warning(f"Could not read .env file: {e}")
        
        return None
    
    def _check_existing_env_value(self, key: str) -> Optional[str]:
        """Check if a specific environment variable already exists in .env file"""
        if not self.env_file.exists():
            return None
        
        try:
            with open(self.env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(f'{key}='):
                        # Extract the value, handling both quoted and unquoted values
                        value = line.split('=', 1)[1].strip()
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        
                        if value and value != 'your-ngc-api-key-here':  # Skip placeholder values
                            return value
        except Exception as e:
            logger.warning(f"Could not read .env file: {e}")
        
        return None
    
    def run_interactive_setup(self) -> bool:
        """Run the main interactive setup process"""
        try:
            self.print_banner()
            
            # Step 1: Check system requirements
            if not self.check_system_requirements():
                print("\n❌ System requirements not met. Please resolve issues and try again.")
                return False
            
            self._save_setup_state('system_requirements_checked')
            
            # Step 2: Gather server configuration
            config = self.gather_server_configuration()
            self._save_setup_state('configuration_gathered')
            
            # Step 3: Gather NGC credentials
            ngc_config = self.gather_ngc_credentials()
            config.update(ngc_config)
            self._save_setup_state('ngc_credentials_gathered')
            
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
            
            # Step 6: Set up Vista3D Docker container
            if not self.setup_vista3d_docker(config):
                print("\n❌ Failed to set up Vista3D Docker container")
                return False
            self._save_setup_state('vista3d_setup')
            
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
        description="HPE NVIDIA Vista3D Server Setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python setup_vista3d_server.py                    # Interactive server setup
  python setup_vista3d_server.py --non-interactive  # Use defaults

The interactive setup will guide you through:
  1. System requirements check (NVIDIA GPU, Docker)
  2. Server configuration (ports, networking, performance)
  3. NGC credentials setup
  4. Environment file creation
  5. Directory creation
  6. Vista3D Docker container setup

Requirements:
  • Linux (Ubuntu 18.04+ or RHEL/CentOS 7+)
  • NVIDIA GPU with CUDA support
  • Docker and NVIDIA Container Toolkit
  • NVIDIA NGC account and API key
  • At least 8GB RAM and 10GB free disk space
        """
    )
    
    parser.add_argument(
        '--non-interactive',
        action='store_true',
        help='Run in non-interactive mode (use defaults)'
    )
    
    args = parser.parse_args()
    
    setup_manager = Vista3DServerSetupManager()
    
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
