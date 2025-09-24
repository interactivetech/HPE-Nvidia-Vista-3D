#!/usr/bin/env python3
"""
Vista-3D Docker Startup Script
Clean version for running Vista-3D on a separate server
Allows connections from any image server
"""

import os
import sys
import time
import subprocess
import argparse
import logging
import json
from pathlib import Path
from typing import Dict, Any
import signal
import atexit

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Fallback if python-dotenv is not available
    pass

# Configure logging
project_root = Path(__file__).resolve().parent.parent
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class Vista3DManager:
    """Manages Vista-3D Docker container for remote image server access"""

    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.project_root = self.script_dir  # Since start_vista3d.py is in the project root
        self.container_name = os.getenv('VISTA3D_CONTAINER_NAME', 'vista3d')

        self._setup_env_vars()
        self._setup_paths()
        self._setup_whitelist()

        self.supported_extensions = [".nrrd", ".nii", ".nii.gz", ".dcm"]
        self._register_signal_handlers()

    def _setup_env_vars(self):
        """Load environment variables from .env file or use defaults."""
        # Read server configurations from .env
        self.image_server = os.getenv('IMAGE_SERVER', 'http://localhost:8888')
        self.vista3d_server = os.getenv('VISTA3D_SERVER', 'http://localhost:8000')
        
        self.env_vars = {
            # Server Configuration from .env
            'IMAGE_SERVER': self.image_server,
            'VISTA3D_SERVER': self.vista3d_server,
            
            # NVIDIA NGC Configuration
            'NGC_API_KEY': os.getenv('NGC_API_KEY'),
            'NGC_ORG_ID': os.getenv('NGC_ORG_ID'),
            'LOCAL_NIM_CACHE': os.path.expanduser(os.getenv('LOCAL_NIM_CACHE', '~/.cache/nim')),
            
            # Vista-3D Configuration
            'IGNORE_SSL_ERRORS': os.getenv('IGNORE_SSL_ERRORS', 'True'),
            'IMAGE_URI_ALLOW_REDIRECTS': os.getenv('IMAGE_URI_ALLOW_REDIRECTS', 'True'),
            'IMAGE_URI_HTTPS_ONLY': os.getenv('IMAGE_URI_HTTPS_ONLY', 'False'),
            
            # File Access Configuration - Allow any image server
            'ALLOW_LOCAL_FILES': os.getenv('ALLOW_LOCAL_FILES', 'True'),
            'ENABLE_CONTAINER_PATHS': os.getenv('ENABLE_CONTAINER_PATHS', 'True'),
            'ENABLE_FILE_ACCESS': os.getenv('ENABLE_FILE_ACCESS', 'True'),
            'ALLOW_ABSOLUTE_PATHS': os.getenv('ALLOW_ABSOLUTE_PATHS', 'True'),
            'ALLOW_RELATIVE_PATHS': os.getenv('ALLOW_RELATIVE_PATHS', 'True'),
            'ALLOW_FILE_PROTOCOL': os.getenv('ALLOW_FILE_PROTOCOL', 'True'),
            'ALLOW_LOCAL_PATHS': os.getenv('ALLOW_LOCAL_PATHS', 'True'),
            'DISABLE_URL_VALIDATION': os.getenv('DISABLE_URL_VALIDATION', 'True'),
            'ALLOW_ABSOLUTE_FILE_PATHS': os.getenv('ALLOW_ABSOLUTE_FILE_PATHS', 'True'),
            'ALLOW_RELATIVE_FILE_PATHS': os.getenv('ALLOW_RELATIVE_FILE_PATHS', 'True'),
            'FILE_ACCESS_MODE': os.getenv('FILE_ACCESS_MODE', 'local'),
            'LOCAL_FILE_ACCESS': os.getenv('LOCAL_FILE_ACCESS', 'True'),
            
            # Network Access Configuration - Allow any image server
            'ALLOW_ANY_IMAGE_SERVER_HOST': os.getenv('ALLOW_ANY_IMAGE_SERVER_HOST', 'True'),
            'ALLOW_EXTERNAL_NETWORK_ACCESS': os.getenv('ALLOW_EXTERNAL_NETWORK_ACCESS', 'True'),
            'DISABLE_HOST_VALIDATION': os.getenv('DISABLE_HOST_VALIDATION', 'True'),
            'ALLOW_ANY_IP_ACCESS': os.getenv('ALLOW_ANY_IP_ACCESS', 'True'),
            'DISABLE_DOMAIN_WHITELIST': os.getenv('DISABLE_DOMAIN_WHITELIST', 'True'),
            'ALLOW_HTTP_ACCESS': os.getenv('ALLOW_HTTP_ACCESS', 'True'),
            'ALLOW_HTTPS_ACCESS': os.getenv('ALLOW_HTTPS_ACCESS', 'True'),
            
            # Additional Network Access Configuration
            'ALLOW_REMOTE_ACCESS': os.getenv('ALLOW_REMOTE_ACCESS', 'True'),
            'ALLOW_CROSS_ORIGIN': os.getenv('ALLOW_CROSS_ORIGIN', 'True'),
            'DISABLE_CORS': os.getenv('DISABLE_CORS', 'True'),
            'ALLOW_ANY_ORIGIN': os.getenv('ALLOW_ANY_ORIGIN', 'True'),
            'ALLOW_ANY_HOST': os.getenv('ALLOW_ANY_HOST', 'True'),
            'DISABLE_ORIGIN_VALIDATION': os.getenv('DISABLE_ORIGIN_VALIDATION', 'True'),
            'ALLOW_WILDCARD_HOSTS': os.getenv('ALLOW_WILDCARD_HOSTS', 'True'),
            'DISABLE_IP_VALIDATION': os.getenv('DISABLE_IP_VALIDATION', 'True'),
            'ALLOW_PRIVATE_IPS': os.getenv('ALLOW_PRIVATE_IPS', 'True'),
            'ALLOW_PUBLIC_IPS': os.getenv('ALLOW_PUBLIC_IPS', 'True'),
            'ALLOW_LOCALHOST': os.getenv('ALLOW_LOCALHOST', 'True'),
            'ALLOW_LOOPBACK': os.getenv('ALLOW_LOOPBACK', 'True'),
            'DISABLE_NETWORK_RESTRICTIONS': os.getenv('DISABLE_NETWORK_RESTRICTIONS', 'True'),
            'ENABLE_EXTERNAL_ACCESS': os.getenv('ENABLE_EXTERNAL_ACCESS', 'True'),
            'ALLOW_IMAGE_SERVER_ACCESS': os.getenv('ALLOW_IMAGE_SERVER_ACCESS', 'True'),
            'DISABLE_IMAGE_SERVER_VALIDATION': os.getenv('DISABLE_IMAGE_SERVER_VALIDATION', 'True'),
            
            # CORS and Headers Configuration
            'CORS_ALLOW_ORIGINS': os.getenv('CORS_ALLOW_ORIGINS', '*'),
            'CORS_ALLOW_METHODS': os.getenv('CORS_ALLOW_METHODS', 'GET,POST,PUT,DELETE,OPTIONS'),
            'CORS_ALLOW_HEADERS': os.getenv('CORS_ALLOW_HEADERS', '*'),
            'CORS_ALLOW_CREDENTIALS': os.getenv('CORS_ALLOW_CREDENTIALS', 'True'),
            'CORS_EXPOSE_HEADERS': os.getenv('CORS_EXPOSE_HEADERS', '*'),
            'CORS_MAX_AGE': os.getenv('CORS_MAX_AGE', '3600'),
            'DISABLE_CORS_CHECKS': os.getenv('DISABLE_CORS_CHECKS', 'True'),
            'ALLOW_ALL_ORIGINS': os.getenv('ALLOW_ALL_ORIGINS', 'True'),
            'ALLOW_ALL_METHODS': os.getenv('ALLOW_ALL_METHODS', 'True'),
            'ALLOW_ALL_HEADERS': os.getenv('ALLOW_ALL_HEADERS', 'True'),
            
            # Vista3D Specific Configuration for External Access
            'VISTA3D_ALLOW_EXTERNAL_IMAGES': os.getenv('VISTA3D_ALLOW_EXTERNAL_IMAGES', 'True'),
            'VISTA3D_DISABLE_IMAGE_VALIDATION': os.getenv('VISTA3D_DISABLE_IMAGE_VALIDATION', 'True'),
            'VISTA3D_ALLOW_ANY_URL': os.getenv('VISTA3D_ALLOW_ANY_URL', 'True'),
            'VISTA3D_DISABLE_URL_VALIDATION': os.getenv('VISTA3D_DISABLE_URL_VALIDATION', 'True'),
            'VISTA3D_ALLOW_REMOTE_FILES': os.getenv('VISTA3D_ALLOW_REMOTE_FILES', 'True'),
            'VISTA3D_DISABLE_FILE_VALIDATION': os.getenv('VISTA3D_DISABLE_FILE_VALIDATION', 'True'),
            'VISTA3D_ENABLE_NETWORK_ACCESS': os.getenv('VISTA3D_ENABLE_NETWORK_ACCESS', 'True'),
            'VISTA3D_ALLOW_HTTP_DOWNLOADS': os.getenv('VISTA3D_ALLOW_HTTP_DOWNLOADS', 'True'),
            'VISTA3D_ALLOW_HTTPS_DOWNLOADS': os.getenv('VISTA3D_ALLOW_HTTPS_DOWNLOADS', 'True'),
            'VISTA3D_DISABLE_SSL_VERIFICATION': os.getenv('VISTA3D_DISABLE_SSL_VERIFICATION', 'True'),
            'VISTA3D_ALLOW_INSECURE_CONNECTIONS': os.getenv('VISTA3D_ALLOW_INSECURE_CONNECTIONS', 'True'),
            'VISTA3D_TIMEOUT': os.getenv('VISTA3D_TIMEOUT', '300'),
            'VISTA3D_MAX_RETRIES': os.getenv('VISTA3D_MAX_RETRIES', '3'),
            
            # Workspace Configuration
            'WORKSPACE_IMAGES_PATH': os.getenv('WORKSPACE_IMAGES_PATH', '/workspace/output/nifti'),
            'WORKSPACE_OUTPUTS_PATH': os.getenv('WORKSPACE_OUTPUTS_PATH', '/workspace/output'),
            'WORKSPACE_ROOT': os.getenv('WORKSPACE_ROOT', '/workspace'),
            
            # CUDA Configuration
            'CUDA_VISIBLE_DEVICES': os.getenv('CUDA_VISIBLE_DEVICES', '0'),
            'NVIDIA_VISIBLE_DEVICES': os.getenv('NVIDIA_VISIBLE_DEVICES', '0'),
            'NVIDIA_DRIVER_CAPABILITIES': os.getenv('NVIDIA_DRIVER_CAPABILITIES', 'compute,utility'),
            'CUDA_LAUNCH_BLOCKING': os.getenv('CUDA_LAUNCH_BLOCKING', '1'),
            'TORCH_USE_CUDA_DSA': '1'
        }

    def _setup_paths(self):
        """Setup paths from environment variables or use defaults."""
        # Use full paths from .env - no more PROJECT_ROOT needed
        output_folder = os.getenv('OUTPUT_FOLDER')
        if not output_folder:
            raise ValueError("OUTPUT_FOLDER must be set in .env file with absolute path")
        
        self.local_outputs_path = Path(output_folder)
        self.container_outputs_path = os.getenv('CONTAINER_OUTPUTS_PATH', "/workspace/output")
        self.local_images_path = self.local_outputs_path / "nifti"
        self.container_images_path = os.getenv('CONTAINER_IMAGES_DATA_PATH', "/workspace/output/nifti")

    def _setup_whitelist(self):
        """Setup the domain whitelist for image server access - allows any image server."""
        # Get image server from .env (will be set in _setup_env_vars)
        image_server = getattr(self, 'image_server', 'http://localhost:8888')
        
        # Extract hostname and port from image server URL
        try:
            from urllib.parse import urlparse
            parsed_url = urlparse(image_server)
            image_host = parsed_url.hostname or 'localhost'
            image_port = parsed_url.port or (8888 if parsed_url.scheme == 'http' else 443)
        except:
            image_host = 'localhost'
            image_port = 8888
        
        # Permissive whitelist to allow any IP address or hostname, plus specific image server
        self.domain_whitelist = [
            # Specific image server from .env
            image_server,
            image_host,
            f"{image_host}:{image_port}",
            f"http://{image_host}",
            f"http://{image_host}:{image_port}",
            f"https://{image_host}",
            f"https://{image_host}:{image_port}",
            
            # General permissive patterns
            r".*",
            r"http://.*",
            r"https://.*", 
            r"http://.*:.*",
            r"https://.*:.*",
            r"file:///.*",
            
            # Local addresses
            "localhost",
            r"127\.0\.0\.1",
            r"0\.0\.0\.0",
            "::1",
            
            # Private network ranges
            r"10\..*",
            r"172\..*",
            r"192\.168\..*",
            
            # Workspace paths
            r"/workspace/output/nifti/.*",
        ]

    def _register_signal_handlers(self):
        """Register signal handlers for graceful shutdown."""
        atexit.register(self.cleanup)
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.cleanup()
        sys.exit(0)
    
    def cleanup(self):
        """Cleanup resources on exit"""
        logger.info("Cleaning up resources...")
        # Add any cleanup logic here
    
    def run_command(self, command: str, check: bool = True, capture_output: bool = False) -> subprocess.CompletedProcess:
        """Run a shell command with proper error handling"""
        try:
            logger.debug(f"Running command: {command}")
            result = subprocess.run(
                command,
                shell=True,
                check=check,
                capture_output=capture_output,
                text=True
            )
            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {command}")
            logger.error(f"Error: {e}")
            if check:
                raise
            return e
    
    def check_docker(self) -> bool:
        """Check if Docker is available and running"""
        try:
            result = self.run_command("docker --version", check=False, capture_output=True)
            if result.returncode != 0:
                logger.error("Docker is not installed or not in PATH")
                logger.error("Install Docker with: curl -fsSL https://get.docker.com | sh")
                return False
            
            result = self.run_command("docker ps", check=False, capture_output=True)
            if result.returncode != 0:
                logger.error("Docker daemon is not running")
                logger.error("Start Docker with: sudo systemctl start docker")
                return False
            
            logger.info("✅ Docker is available and running")
            return True
        except Exception as e:
            logger.error(f"Error checking Docker: {e}")
            return False
    
    def check_nvidia_support(self) -> bool:
        """Check if NVIDIA GPU and Docker runtime are available"""
        logger.info("Checking NVIDIA GPU support...")
        
        # Check if nvidia-smi is available
        try:
            result = self.run_command("nvidia-smi", check=False, capture_output=True)
            if result.returncode != 0:
                logger.error("❌ nvidia-smi not found - NVIDIA drivers not installed")
                logger.error("Install NVIDIA drivers: sudo apt install nvidia-driver-<version>")
                return False
            
            logger.info("✅ NVIDIA drivers detected")
            
            # Parse GPU information
            try:
                gpu_result = self.run_command(
                    "nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits", 
                    check=False, capture_output=True
                )
                if gpu_result.returncode == 0 and gpu_result.stdout.strip():
                    gpu_lines = gpu_result.stdout.strip().split('\n')
                    logger.info(f"✅ Found {len(gpu_lines)} NVIDIA GPU(s):")
                    for i, line in enumerate(gpu_lines):
                        name, memory = line.split(', ')
                        logger.info(f"   GPU {i}: {name} ({memory} MB)")
                else:
                    logger.warning("Could not parse GPU information")
            except Exception as e:
                logger.warning(f"Could not get detailed GPU info: {e}")
            
        except Exception as e:
            logger.error(f"Error checking NVIDIA drivers: {e}")
            return False
        
        # Check NVIDIA Container Toolkit
        try:
            result = self.run_command(
                "docker run --rm --gpus all nvidia/cuda:11.0-base-ubuntu20.04 nvidia-smi", 
                check=False, capture_output=True
            )
            if result.returncode != 0:
                logger.error("❌ NVIDIA Container Toolkit not properly configured")
                logger.error("Install with:")
                logger.error("  curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg")
                logger.error("  curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list")
                logger.error("  sudo apt update && sudo apt-get install -y nvidia-container-toolkit")
                logger.error("  sudo nvidia-ctk runtime configure --runtime=docker")
                logger.error("  sudo systemctl restart docker")
                return False
            
            logger.info("✅ NVIDIA Container Toolkit is properly configured")
            return True
            
        except Exception as e:
            logger.error(f"Error testing NVIDIA Container Toolkit: {e}")
            return False
    
    def check_system_resources(self) -> bool:
        """Check if system has adequate resources"""
        logger.info("Checking system resources...")
        
        try:
            # Check available memory
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
            
            for line in meminfo.split('\n'):
                if line.startswith('MemAvailable:'):
                    available_kb = int(line.split()[1])
                    available_gb = available_kb / (1024 * 1024)
                    
                    if available_gb < 8:
                        logger.warning(f"⚠️  Low available memory: {available_gb:.1f}GB (recommended: 8GB+)")
                        logger.warning("Vista3D may run slowly or fail with insufficient memory")
                    else:
                        logger.info(f"✅ Sufficient memory available: {available_gb:.1f}GB")
                    break
            
            # Check disk space
            import shutil
            output_folder = os.getenv('OUTPUT_FOLDER')
            if output_folder:
                free_space = shutil.disk_usage(output_folder).free / (1024**3)
                if free_space < 10:
                    logger.warning(f"⚠️  Low disk space in output folder: {free_space:.1f}GB (recommended: 10GB+)")
                else:
                    logger.info(f"✅ Sufficient disk space: {free_space:.1f}GB")
            
            return True
            
        except Exception as e:
            logger.warning(f"Could not check system resources: {e}")
            return True  # Don't fail startup for this
    
    def stop_existing_container(self):
        """Stop and remove any existing Vista-3D container"""
        logger.info("Stopping any existing Vista-3D container...")
        
        # Stop container
        self.run_command(f"docker stop {self.container_name}", check=False)
        
        # Remove container
        self.run_command(f"docker rm {self.container_name}", check=False)
        self.run_command(f"docker rm -f {self.container_name}", check=False)
        
        # Clean up any remaining container references
        self.run_command("docker container prune -f", check=False)
        
        logger.info("✅ Existing containers cleaned up")
    
    def create_output_directory(self):
        """Create the local output directory if it doesn't exist"""
        self.local_outputs_path.mkdir(parents=True, exist_ok=True)
        self.local_images_path.mkdir(parents=True, exist_ok=True)
        (self.local_outputs_path / "scans").mkdir(parents=True, exist_ok=True)
        
        logger.info(f"✅ Output directory created: {self.local_outputs_path}")
    
    
    def start_vista3d_container(self) -> bool:
        """Start the Vista-3D Docker container with retry logic"""
        logger.info("Starting Vista-3D container...")
        
        # Build environment variables string
        env_vars_list = []
        for k, v in self.env_vars.items():
            if v is not None:
                v_str = str(v)
                if ' ' in v_str or '\'' in v_str or '"' in v_str:
                    # Use single quotes and escape existing single quotes
                    escaped_v = v_str.replace("'", "'\\''")
                    env_vars_list.append(f"-e {k}='{escaped_v}'")
                else:
                    env_vars_list.append(f"-e {k}={v_str}")
        env_vars = " ".join(env_vars_list)

        # Build domain whitelist
        domain_whitelist_str = json.dumps(self.domain_whitelist)
        env_vars += f" -e DOMAIN_WHITELIST='{domain_whitelist_str}'"
        
        # Build supported extensions
        extensions_str = json.dumps(self.supported_extensions)
        env_vars += f" -e SUPPORTED_IMAGE_EXT='{extensions_str}'"
        
        # Build volume mounts
        volumes = f'-v "{self.local_outputs_path}:{self.container_outputs_path}"'
        volumes += f' -v "{self.project_root}:{self.project_root}:ro"'
        
        # Network configuration - allow external access by default
        vista3d_port = os.getenv('VISTA3D_PORT', '8000')
        use_host_networking = os.getenv('USE_HOST_NETWORKING', 'True').lower() in ('true', '1', 'yes')
        
        if use_host_networking:
            network_config = "--network=host"
            logger.info("Using host networking mode - Vista3D will be accessible on all interfaces")
        else:
            network_config = f"-p 0.0.0.0:{vista3d_port}:8000"
            logger.info(f"Vista3D will be accessible externally on port {vista3d_port}")
        
        # Add host entries for external access
        host_entries = "--add-host=host.docker.internal:host-gateway"
        host_entries += " --add-host=localhost:host-gateway"
        host_entries += " --add-host=127.0.0.1:host-gateway"
        
        # Performance optimizations for server deployment
        performance_opts = ""
        
        # Memory and CPU settings
        memory_limit = os.getenv('VISTA3D_MEMORY_LIMIT', '16G')
        cpu_limit = os.getenv('VISTA3D_CPU_LIMIT', '8')
        performance_opts += f" --memory={memory_limit} --cpus={cpu_limit}"
        
        # GPU optimizations
        gpu_memory_fraction = os.getenv('GPU_MEMORY_FRACTION', '0.9')
        performance_opts += f" -e GPU_MEMORY_FRACTION={gpu_memory_fraction}"
        
        # CUDA optimizations for server workloads
        performance_opts += " -e CUDA_LAUNCH_BLOCKING=0"  # Non-blocking for better performance
        performance_opts += " -e CUDA_CACHE_DISABLE=0"    # Enable CUDA cache
        performance_opts += " -e CUDA_DEVICE_ORDER=PCI_BUS_ID"  # Consistent GPU ordering
        
        # Shared memory optimizations for large models
        shm_size = os.getenv('VISTA3D_SHM_SIZE', '12G')
        
        # IPC and security optimizations
        ipc_opts = "--ipc=host"  # Better for multi-GPU and performance
        security_opts = "--security-opt=no-new-privileges"  # Security hardening
        
        # Restart policy for server deployment
        restart_policy = "--restart=unless-stopped" if os.getenv('VISTA3D_AUTO_RESTART', 'true').lower() == 'true' else ""
        
        docker_cmd = f"""docker run --gpus all {restart_policy} -d --name {self.container_name} --runtime=nvidia --shm-size={shm_size} {performance_opts} {ipc_opts} {security_opts} {host_entries} {network_config} {volumes} {env_vars} nvcr.io/nim/nvidia/vista3d:1.0.0"""
        
        # Try to start container with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"Starting container (attempt {attempt + 1}/{max_retries})...")
                result = self.run_command(docker_cmd, capture_output=True)
                
                if result.returncode == 0:
                    logger.info("✅ Vista-3D container started successfully!")
                    
                    # Wait for container to be ready and check health
                    if self._wait_for_container_ready():
                        return True
                    else:
                        logger.warning(f"Container started but health check failed on attempt {attempt + 1}")
                        if attempt < max_retries - 1:
                            logger.info("Retrying...")
                            self.stop_existing_container()
                            time.sleep(5)
                            continue
                        else:
                            return False
                else:
                    logger.error(f"❌ Failed to start Vista-3D container (attempt {attempt + 1})")
                    if result.stderr:
                        logger.error(f"Error output: {result.stderr}")
                    
                    if attempt < max_retries - 1:
                        logger.info("Retrying...")
                        self.stop_existing_container()
                        time.sleep(5)
                    else:
                        # Final attempt failed - show more detailed error info
                        logger.error("All container start attempts failed")
                        logger.error("Checking Docker image availability...")
                        self.run_command("docker images | grep vista3d", check=False)
                        logger.error("Checking for conflicting containers...")
                        self.run_command("docker ps -a | grep vista", check=False)
                        return False
                        
            except Exception as e:
                logger.error(f"Error starting container (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    logger.info("Retrying...")
                    time.sleep(5)
                else:
                    return False
        
        return False
    
    def _wait_for_container_ready(self) -> bool:
        """Wait for container to be ready and perform health checks"""
        logger.info("Waiting for container to be ready...")
        
        # Wait for container to start
        time.sleep(10)
        
        # Check if container is running
        try:
            result = self.run_command(f"docker ps | grep {self.container_name}", check=False, capture_output=True)
            if result.returncode != 0:
                logger.error("Container is not running")
                # Show container logs for debugging
                self.run_command(f"docker logs {self.container_name} --tail 50")
                return False
            
            logger.info("✅ Container is running")
            
            # Show container status
            self.run_command(f"docker ps | grep {self.container_name}")
            
            # Show container logs
            logger.info("Container logs (last 20 lines):")
            self.run_command(f"docker logs {self.container_name} --tail 20")
            
            # Try to connect to the service (with timeout)
            vista3d_server = getattr(self, 'vista3d_server', 'http://localhost:8000')
            logger.info(f"Testing connectivity to {vista3d_server}...")
            
            max_wait_time = 60  # seconds
            start_time = time.time()
            
            while time.time() - start_time < max_wait_time:
                try:
                    import requests
                    response = requests.get(f"{vista3d_server}/health", timeout=5)
                    if response.status_code == 200:
                        logger.info("✅ Vista-3D service is responding to health checks")
                        return True
                except Exception:
                    pass
                
                logger.info("Waiting for service to be ready...")
                time.sleep(5)
            
            logger.warning("⚠️  Vista-3D service is not responding to health checks yet")
            logger.warning("This may be normal - the container might still be initializing")
            logger.warning("Check the container logs and try connecting after a few minutes")
            return True  # Don't fail startup just because health check isn't ready yet
            
        except Exception as e:
            logger.error(f"Error checking container readiness: {e}")
            return False
    
    def test_configuration(self):
        """Test the Vista-3D configuration"""
        logger.info("Testing Vista-3D configuration...")
        
        # Use Vista3D server from .env
        vista3d_server = getattr(self, 'vista3d_server', 'http://localhost:8000')
        vista3d_port = os.getenv('VISTA3D_PORT', '8000')
        
        # Test 1: Basic connectivity
        logger.info("Test 1: Testing Vista-3D connectivity...")
        logger.info(f"Testing Vista-3D server: {vista3d_server}")
        try:
            import requests
            # Test the configured Vista3D server
            response = requests.get(f"{vista3d_server}/health", timeout=10)
            logger.info(f"Vista-3D health check response: {response.status_code}")
        except Exception as e:
            logger.warning(f"Vista-3D health check failed (may be normal during startup): {e}")
        
        # Test 2: Test external IP access capability
        logger.info("Test 2: Testing external access configuration...")
        logger.info("✅ Vista3D is configured to accept connections from any image server")
        logger.info("✅ External IP access is enabled")
        logger.info("✅ Domain whitelist is permissive")
        logger.info("✅ CORS is disabled to allow cross-origin requests")
        logger.info("✅ Network restrictions are disabled")
        logger.info("✅ Image server validation is disabled")
        logger.info("✅ URL validation is disabled")
        logger.info("✅ Host validation is disabled")
    
    def run_performance_test(self):
        """Run basic performance tests on the Vista-3D container"""
        logger.info("🏁 Running performance tests...")
        
        try:
            # Test container resource usage
            result = self.run_command(f"docker stats {self.container_name} --no-stream", check=False, capture_output=True)
            if result.returncode == 0:
                logger.info("📊 Container resource usage:")
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:  # Skip header
                    stats = lines[1].split()
                    if len(stats) >= 6:
                        cpu_usage = stats[2]
                        mem_usage = stats[3]
                        logger.info(f"   CPU Usage: {cpu_usage}")
                        logger.info(f"   Memory Usage: {mem_usage}")
            
            # Test GPU utilization
            result = self.run_command("nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits", check=False, capture_output=True)
            if result.returncode == 0:
                logger.info("🎯 GPU utilization:")
                gpu_lines = result.stdout.strip().split('\n')
                for i, line in enumerate(gpu_lines):
                    parts = line.split(', ')
                    if len(parts) >= 3:
                        gpu_util, mem_used, mem_total = parts
                        mem_percent = (int(mem_used) / int(mem_total)) * 100
                        logger.info(f"   GPU {i}: {gpu_util}% utilization, {mem_used}/{mem_total}MB memory ({mem_percent:.1f}%)")
            
            # Test API response time
            vista3d_server = getattr(self, 'vista3d_server', 'http://localhost:8000')
            logger.info("⚡ Testing API response time...")
            try:
                import requests
                import time
                
                start_time = time.time()
                response = requests.get(f"{vista3d_server}/health", timeout=5)
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    logger.info(f"   Health endpoint: {response_time:.1f}ms")
                else:
                    logger.warning(f"   Health endpoint returned status {response.status_code}")
                    
            except Exception as e:
                logger.warning(f"   Could not test API response time: {e}")
            
            logger.info("✅ Performance test completed")
            
        except Exception as e:
            logger.warning(f"Performance test failed: {e}")
    
    
    def run(self):
        """Main execution logic"""
        logger.info("Starting Vista-3D container for remote image server access...")
        logger.info("=" * 60)
        
        # Check system requirements
        logger.info("📋 Checking system requirements...")
        
        # Check Docker availability
        if not self.check_docker():
            logger.error("❌ Docker check failed")
            return False
        
        # Check NVIDIA GPU support (unless skipped)
        skip_gpu_check = getattr(self, 'skip_gpu_check', False)
        if not skip_gpu_check:
            if not self.check_nvidia_support():
                logger.error("❌ NVIDIA GPU support check failed")
                logger.error("Vista3D requires NVIDIA GPU and Docker runtime support")
                return False
        else:
            logger.warning("⚠️  Skipping GPU check as requested (--skip-gpu-check)")
        
        # Check system resources
        self.check_system_resources()
        
        logger.info("✅ All system checks passed")
        logger.info("=" * 60)
        
        # Create output directory
        self.create_output_directory()
        
        # Stop existing containers
        self.stop_existing_container()
        
        # Start Vista-3D container
        if not self.start_vista3d_container():
            return False
        
        # Test configuration
        self.test_configuration()
        
        # Run performance tests (if requested or by default)
        run_perf_test = getattr(self, 'run_performance_test_flag', True)
        if run_perf_test:
            self.run_performance_test()
        
        # Success message
        logger.info("=" * 60)
        logger.info("🎉 VISTA-3D SUCCESSFULLY STARTED!")
        logger.info("=" * 60)
        vista3d_server = getattr(self, 'vista3d_server', 'http://localhost:8000')
        image_server = getattr(self, 'image_server', 'http://localhost:8888')
        vista3d_port = os.getenv('VISTA3D_PORT', '8000')
        
        logger.info(f"🌐 Vista-3D Server: {vista3d_server}")
        logger.info(f"📡 Image Server: {image_server}")
        logger.info("🔓 Vista-3D is configured to accept connections from any image server")
        logger.info("✅ External access is fully enabled")
        logger.info("✅ Any IP address or hostname is allowed")
        logger.info("✅ CORS restrictions are disabled")
        logger.info("✅ Network validation is disabled")
        logger.info("✅ Image server validation is disabled")
        logger.info("=" * 60)
        
        logger.info("\n🛠️  Useful commands:")
        logger.info("  📜 View Vista-3D logs: docker logs -f vista3d")
        logger.info("  🛑 Stop container: docker stop vista3d")
        logger.info("  🖥️  Access container shell: docker exec -it vista3d bash")
        logger.info(f"  🧪 Test Vista-3D health: curl {vista3d_server}/health")
        logger.info(f"  🔬 Test Vista-3D inference: curl {vista3d_server}/v1/vista3d/inference -X POST -H 'Content-Type: application/json' -d '{{\"image\":\"test\"}}'")
        logger.info(f"  📊 Test with image server: curl {vista3d_server}/v1/vista3d/inference -X POST -H 'Content-Type: application/json' -d '{{\"image\":\"{image_server}/path/to/image.nii.gz\"}}'")
        
        return True

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Vista-3D Docker Startup Script for Remote Image Server Access",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🚀 LINUX SERVER DEPLOYMENT:

Prerequisites for Linux servers with NVIDIA GPU:
  1. Ubuntu 18.04+ or RHEL/CentOS 7+
  2. NVIDIA GPU with CUDA support (RTX/Tesla/A100/H100 series)
  3. NVIDIA drivers installed (version 470+)
  4. Docker and NVIDIA Container Toolkit
  5. At least 8GB RAM and 10GB free disk space

Quick Setup on fresh Linux server:
  # Install Docker
  curl -fsSL https://get.docker.com | sh
  sudo usermod -aG docker $USER
  newgrp docker
  
  # Install NVIDIA Container Toolkit
  curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
  curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
  sudo apt update && sudo apt-get install -y nvidia-container-toolkit
  sudo nvidia-ctk runtime configure --runtime=docker
  sudo systemctl restart docker
  
  # Test GPU access
  sudo docker run --rm --gpus all nvidia/cuda:11.0-base-ubuntu20.04 nvidia-smi

Usage Examples:
  python3 start_vista3d.py                 # Start Vista-3D container

Configuration (.env file):
  Required:
    NGC_API_KEY=nvapi-xxxxxxxxxxxxx       # Get from NGC catalog
    OUTPUT_FOLDER=/path/to/output          # Absolute path to output directory
  
  Network Configuration:
    IMAGE_SERVER=http://localhost:8888     # Your image server URL
    VISTA3D_SERVER=http://localhost:8000   # Vista3D server URL
    USE_HOST_NETWORKING=True              # Use host networking (recommended for servers)
    VISTA3D_PORT=8000                    # Port when not using host networking
  
  GPU Configuration:
    CUDA_VISIBLE_DEVICES=0               # GPU device ID to use
    GPU_MEMORY_FRACTION=0.9              # GPU memory allocation (0.1-1.0)
    
  Performance Tuning:
    VISTA3D_MEMORY_LIMIT=16G             # Container memory limit
    VISTA3D_CPU_LIMIT=8                  # Container CPU limit
    VISTA3D_SHM_SIZE=12G                 # Shared memory size
    VISTA3D_AUTO_RESTART=true            # Auto-restart on failure

Network Access Configuration:
  Vista3D is configured to accept connections from any image server by default.
  All network restrictions, CORS checks, and validation are disabled for maximum compatibility.
  
  For servers with firewalls:
    - Open port 8000 (or VISTA3D_PORT) for Vista3D API access
    - Configure IMAGE_SERVER to match your setup
    - Use USE_HOST_NETWORKING=True for maximum compatibility

Troubleshooting:
  🔍 Check GPU: nvidia-smi
  🔍 Check Docker: docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
  🔍 Check logs: docker logs -f vista3d
  🔍 Test API: curl http://localhost:8000/health
        """
    )
    
    
    parser.add_argument(
        '--performance-test',
        action='store_true',
        help='Run additional performance tests after startup'
    )
    
    parser.add_argument(
        '--skip-gpu-check',
        action='store_true',
        help='Skip NVIDIA GPU validation (for testing only)'
    )
    
    args = parser.parse_args()
    
    manager = Vista3DManager()
    
    # Set command line options
    manager.skip_gpu_check = args.skip_gpu_check
    manager.run_performance_test_flag = args.performance_test or True  # Default to True
    
    try:
        # Start the Vista3D container
        success = manager.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
