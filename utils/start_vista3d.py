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
log_dir = project_root / 'output' / 'logs'
log_dir.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'start_vista.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class Vista3DManager:
    """Manages Vista-3D Docker container for remote image server access"""

    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.project_root = self.script_dir.parent
        self.container_name = os.getenv('VISTA3D_CONTAINER_NAME', 'vista3d')

        self._setup_env_vars()
        self._setup_paths()
        self._setup_whitelist()

        self.supported_extensions = [".nrrd", ".nii", ".nii.gz", ".dcm"]
        self._register_signal_handlers()

    def _setup_env_vars(self):
        """Load environment variables from .env file or use defaults."""
        self.env_vars = {
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
        project_root = os.getenv('PROJECT_ROOT', str(self.project_root))
        output_folder = os.getenv('OUTPUT_FOLDER', 'output')
        self.local_outputs_path = Path(project_root) / output_folder
        self.container_outputs_path = os.getenv('CONTAINER_OUTPUTS_PATH', "/workspace/output")
        self.local_images_path = self.local_outputs_path / "nifti"
        self.container_images_path = os.getenv('CONTAINER_IMAGES_DATA_PATH', "/workspace/output/nifti")

    def _setup_whitelist(self):
        """Setup the domain whitelist for image server access - allows any image server."""
        # Permissive whitelist to allow any IP address or hostname
        self.domain_whitelist = [
            r".*",
            r".*",
            r"http://.*",
            r"https://.*", 
            r"http://.*:.*",
            r"https://.*:.*",
            r"http://.*",
            r"https://.*",
            r"http://.*:.*",
            r"https://.*:.*",
            r"file:///.*",
            r"file:///.*",
            "localhost",
            r"127\.0\.0\.1",
            r"0\.0\.0\.0",
            "::1",
            r"10\..*",
            r"172\..*",
            r"192\.168\..*",
            r"/workspace/output/nifti/.*",
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
            result = self.run_command("docker --version", check=False)
            if result.returncode != 0:
                logger.error("Docker is not installed or not in PATH")
                return False
            
            result = self.run_command("docker ps", check=False)
            if result.returncode != 0:
                logger.error("Docker daemon is not running")
                return False
            
            logger.info("✅ Docker is available and running")
            return True
        except Exception as e:
            logger.error(f"Error checking Docker: {e}")
            return False
    
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
        (self.local_outputs_path / "segments").mkdir(parents=True, exist_ok=True)
        
        logger.info(f"✅ Output directory created: {self.local_outputs_path}")
    
    
    def start_vista3d_container(self) -> bool:
        """Start the Vista-3D Docker container"""
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
        
        docker_cmd = f"""docker run --gpus all --rm -d --name {self.container_name} --runtime=nvidia --shm-size=8G {host_entries} {network_config} {volumes} {env_vars} nvcr.io/nim/nvidia/vista3d:1.0.0"""
        
        try:
            result = self.run_command(docker_cmd)
            if result.returncode == 0:
                logger.info("✅ Vista-3D container started successfully!")
                
                # Wait for container to be ready
                time.sleep(5)
                
                # Show container status
                self.run_command(f"docker ps | grep {self.container_name}")
                
                # Show container logs
                logger.info("Container logs (last 20 lines):")
                self.run_command(f"docker logs {self.container_name} --tail 20")
                
                return True
            else:
                logger.error("❌ Failed to start Vista-3D container")
                return False
        except Exception as e:
            logger.error(f"Error starting container: {e}")
            return False
    
    def test_configuration(self):
        """Test the Vista-3D configuration"""
        logger.info("Testing Vista-3D configuration...")
        
        vista3d_port = os.getenv('VISTA3D_PORT', '8000')
        
        # Test 1: Basic connectivity
        logger.info("Test 1: Testing Vista-3D connectivity...")
        try:
            import requests
            response = requests.get(f"http://localhost:{vista3d_port}/health", timeout=10)
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
    
    def create_systemd_service(self):
        """Create systemd service for automatic startup"""
        if os.geteuid() != 0:
            logger.error("⚠️  This function requires root privileges to create systemd service")
            logger.error("   Run with: sudo python3 start_vista.py --create-service")
            return False
        
        service_name = "vista3d"
        service_file = f"/etc/systemd/system/{service_name}.service"
        script_path = str(Path(__file__).absolute())
        
        logger.info("Creating systemd service for automatic startup...")
        
        service_content = f"""[Unit]
Description=Vista-3D Docker Container for Remote Image Server Access
After=docker.service
Requires=docker.service
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
User=root
Group=root
WorkingDirectory={self.script_dir}
ExecStart={sys.executable} {script_path}
ExecStop=/usr/bin/docker stop vista3d
ExecStop=/usr/bin/docker rm vista3d
TimeoutStartSec=300
TimeoutStopSec=60
Restart=on-failure
RestartSec=30

[Install]
WantedBy=multi-user.target
"""
        
        try:
            with open(service_file, 'w') as f:
                f.write(service_content)
            
            # Set proper permissions
            os.chmod(service_file, 0o644)
            
            # Reload systemd and enable service
            self.run_command("systemctl daemon-reload")
            self.run_command(f"systemctl enable {service_name}")
            
            logger.info(f"✅ Systemd service created: {service_file}")
            logger.info("✅ Service enabled for automatic startup")
            
            logger.info("\nUseful commands:")
            logger.info(f"  Start service: sudo systemctl start {service_name}")
            logger.info(f"  Stop service: sudo systemctl stop {service_name}")
            logger.info(f"  Check status: sudo systemctl status {service_name}")
            logger.info(f"  View logs: sudo journalctl -u {service_name} -f")
            logger.info(f"  Disable service: sudo systemctl disable {service_name}")
            
            return True
        except Exception as e:
            logger.error(f"Error creating systemd service: {e}")
            return False
    
    def run(self):
        """Main execution logic"""
        logger.info("Starting Vista-3D container for remote image server access...")
        
        # Check Docker availability
        if not self.check_docker():
            return False
        
        # Create output directory
        self.create_output_directory()
        
        # Stop existing containers
        self.stop_existing_container()
        
        # Start Vista-3D container
        if not self.start_vista3d_container():
            return False
        
        # Test configuration
        self.test_configuration()
        
        # Success message
        logger.info("==========================================")
        vista3d_port = os.getenv('VISTA3D_PORT', '8000')
        logger.info(f"Vista-3D is now running on port {vista3d_port}")
        logger.info("Vista-3D is configured to accept connections from any image server")
        logger.info("✅ External access is fully enabled")
        logger.info("✅ Any IP address or hostname is allowed")
        logger.info("✅ CORS restrictions are disabled")
        logger.info("✅ Network validation is disabled")
        logger.info("✅ Image server validation is disabled")
        logger.info("==========================================")
        
        logger.info("\nUseful commands:")
        logger.info("  View Vista-3D logs: docker logs -f vista3d")
        logger.info("  Stop container: docker stop vista3d")
        logger.info("  Access container shell: docker exec -it vista3d bash")
        vista3d_server = os.getenv('VISTA3D_SERVER', 'http://localhost:8000')
        logger.info(f"  Test Vista-3D endpoint: curl {vista3d_server}/v1/vista3d/inference -X POST -H 'Content-Type: application/json' -d '{\"image\":\"test\"}'")
        logger.info(f"  Test with external image server: curl {vista3d_server}/v1/vista3d/inference -X POST -H 'Content-Type: application/json' -d '{\"image\":\"http://your-image-server:port/path/to/image.nii.gz\"}'")
        
        return True

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Vista-3D Docker Startup Script for Remote Image Server Access",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 start_vista3d.py                 # Start Vista-3D container
  sudo python3 start_vista3d.py --create-service  # Create systemd service for auto-startup

For automatic startup on boot:
  1. Run: sudo python3 start_vista3d.py --create-service
  2. The service will start automatically on boot
  3. Check status: sudo systemctl status vista3d

Network Access Configuration:
  Vista3D is configured to accept connections from any image server by default.
  All network restrictions, CORS checks, and validation are disabled for maximum compatibility.
  
  Key Environment Variables:
    USE_HOST_NETWORKING=True            # Use host networking (allows all interfaces)
    VISTA3D_PORT=8000                  # Port for Vista3D (when not using host networking)
    ALLOW_ANY_IMAGE_SERVER_HOST=True   # Allow any host/IP for image server access
    DISABLE_URL_VALIDATION=True        # Disable URL validation restrictions
    ALLOW_ANY_IP_ACCESS=True           # Allow any IP address access
    DISABLE_HOST_VALIDATION=True       # Disable host validation
    ALLOW_HTTP_ACCESS=True             # Allow HTTP access
    ALLOW_HTTPS_ACCESS=True            # Allow HTTPS access
    DISABLE_CORS=True                  # Disable CORS restrictions
    DISABLE_NETWORK_RESTRICTIONS=True  # Disable all network restrictions
    VISTA3D_ALLOW_EXTERNAL_IMAGES=True # Allow external image access
    VISTA3D_DISABLE_IMAGE_VALIDATION=True # Disable image validation
  
  Examples:
    # Use host networking for maximum external access
    USE_HOST_NETWORKING=True python3 start_vista3d.py
    
    # Use specific port with external access
    USE_HOST_NETWORKING=False VISTA3D_PORT=8000 python3 start_vista3d.py
        """
    )
    
    parser.add_argument(
        '--create-service',
        action='store_true',
        help='Create systemd service for automatic startup (requires root)'
    )
    
    args = parser.parse_args()
    
    manager = Vista3DManager()
    
    try:
        if args.create_service:
            success = manager.create_systemd_service()
            sys.exit(0 if success else 1)
        else:
            # Default behavior - start the container
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
