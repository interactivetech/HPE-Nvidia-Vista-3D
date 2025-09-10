#!/usr/bin/env python3
"""
Vista-3D Docker Startup Script
Python version with enhanced error handling and monitoring capabilities
"""

import os
import sys
import time
import subprocess
import argparse
import logging
import requests
import json
from pathlib import Path
from typing import Optional, Dict, Any
import signal
import atexit
import urllib.parse

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
    """Manages Vista-3D Docker container with external image server access"""

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
            'NGC_API_KEY': os.getenv('NGC_API_KEY'),
            'NGC_ORG_ID': os.getenv('NGC_ORG_ID'),
            'LOCAL_NIM_CACHE': os.getenv('LOCAL_NIM_CACHE', '~/.cache/nim'),
            'IGNORE_SSL_ERRORS': os.getenv('IGNORE_SSL_ERRORS', 'True'),
            'IMAGE_URI_ALLOW_REDIRECTS': os.getenv('IMAGE_URI_ALLOW_REDIRECTS', 'True'),
            'IMAGE_URI_HTTPS_ONLY': os.getenv('IMAGE_URI_HTTPS_ONLY', 'False'),
            'ALLOW_LOCAL_FILES': os.getenv('ALLOW_LOCAL_FILES', 'True'),
            'ENABLE_CONTAINER_PATHS': os.getenv('ENABLE_CONTAINER_PATHS', 'True'),
            'ENABLE_FILE_ACCESS': os.getenv('ENABLE_FILE_ACCESS', 'True'),
            'ALLOW_ABSOLUTE_PATHS': os.getenv('ALLOW_ABSOLUTE_PATHS', 'True'),
            'ALLOW_RELATIVE_PATHS': os.getenv('ALLOW_RELATIVE_PATHS', 'True'),
            'WORKSPACE_IMAGES_PATH': os.getenv('WORKSPACE_IMAGES_PATH', '/workspace/output/nifti'),
            'WORKSPACE_OUTPUTS_PATH': os.getenv('WORKSPACE_OUTPUTS_PATH', '/workspace/output'),
            'WORKSPACE_ROOT': os.getenv('WORKSPACE_ROOT', '/workspace'),
            'ALLOW_FILE_PROTOCOL': os.getenv('ALLOW_FILE_PROTOCOL', 'True'),
            'ALLOW_LOCAL_PATHS': os.getenv('ALLOW_LOCAL_PATHS', 'True'),
            'DISABLE_URL_VALIDATION': os.getenv('DISABLE_URL_VALIDATION', 'True'),
            'ALLOW_ABSOLUTE_FILE_PATHS': os.getenv('ALLOW_ABSOLUTE_FILE_PATHS', 'True'),
            'ALLOW_RELATIVE_FILE_PATHS': os.getenv('ALLOW_RELATIVE_FILE_PATHS', 'True'),
            'FILE_ACCESS_MODE': os.getenv('FILE_ACCESS_MODE', 'local'),
            'LOCAL_FILE_ACCESS': os.getenv('LOCAL_FILE_ACCESS', 'True'),
            'EXTERNAL_IMAGE_SERVER': os.getenv('EXTERNAL_IMAGE_SERVER', 'https://host.docker.internal:8888'),
            'EXTERNAL_IMAGE_SERVER_HOST': os.getenv('EXTERNAL_IMAGE_SERVER_HOST', 'host.docker.internal'),
            'EXTERNAL_IMAGE_SERVER_PORT': os.getenv('EXTERNAL_IMAGE_SERVER_PORT', '8888'),
            'ALLOW_ANY_IMAGE_SERVER_HOST': os.getenv('ALLOW_ANY_IMAGE_SERVER_HOST', 'True'),
            'ALLOW_EXTERNAL_NETWORK_ACCESS': os.getenv('ALLOW_EXTERNAL_NETWORK_ACCESS', 'True'),
            'DISABLE_HOST_VALIDATION': os.getenv('DISABLE_HOST_VALIDATION', 'True'),
            'ALLOW_ANY_IP_ACCESS': os.getenv('ALLOW_ANY_IP_ACCESS', 'True'),
            'DISABLE_DOMAIN_WHITELIST': os.getenv('DISABLE_DOMAIN_WHITELIST', 'False'),
            'ALLOW_HTTP_ACCESS': os.getenv('ALLOW_HTTP_ACCESS', 'True'),
            'ALLOW_HTTPS_ACCESS': os.getenv('ALLOW_HTTPS_ACCESS', 'True'),
            'CUDA_VISIBLE_DEVICES': os.getenv('CUDA_VISIBLE_DEVICES', '1'),
            'NVIDIA_VISIBLE_DEVICES': os.getenv('NVIDIA_VISIBLE_DEVICES', '1'),
            'NVIDIA_DRIVER_CAPABILITIES': os.getenv('NVIDIA_DRIVER_CAPABILITIES', 'compute,utility'),
            'CUDA_LAUNCH_BLOCKING': os.getenv('CUDA_LAUNCH_BLOCKING', '1'),
            'TORCH_USE_CUDA_DSA': '1'
        }

    def _setup_paths(self):
        """Setup paths from environment variables or use defaults."""
        project_root = os.getenv('PROJECT_ROOT', str(self.project_root))
        self.local_outputs_path = Path(project_root) / "output"
        self.container_outputs_path = os.getenv('CONTAINER_OUTPUTS_PATH', "/workspace/output")
        self.local_images_path = self.local_outputs_path / "nifti"
        self.container_images_path = os.getenv('CONTAINER_IMAGES_DATA_PATH', "/workspace/output/nifti")

    def _setup_whitelist(self):
        """Setup the domain whitelist for image server access."""
        allow_any_host = self.env_vars.get('ALLOW_ANY_IMAGE_SERVER_HOST', 'True').lower() in ('true', '1', 'yes')

        if allow_any_host:
            # Simplified and permissive whitelist to allow any IP address or hostname
            self.domain_whitelist = [
                "*",
                "http://*", "https://*",
                "http://*:*", "https://*:*",
                "file:///*",
            ]
        else:
            # Original restrictive configuration, cleaned up for clarity
            image_server_url = os.getenv('IMAGE_SERVER', 'https://localhost:8888')
            parsed_url = urllib.parse.urlparse(image_server_url)
            image_server_host = parsed_url.hostname or 'localhost'
            image_server_port = parsed_url.port or 8888
            image_server_protocol = parsed_url.scheme or 'https'
            
            external_server_url = f"{image_server_protocol}://{image_server_host}:{image_server_port}"
            external_server_http = f"http://{image_server_host}:{image_server_port}"
            project_root = os.getenv('PROJECT_ROOT', str(self.project_root))

            self.domain_whitelist = [
                f"{external_server_url}",
                f"{external_server_http}",
                f"{image_server_protocol}://{image_server_host}:*",
                f"http://{image_server_host}:*",
                "https://host.docker.internal:*",
                "http://host.docker.internal:*",
                "file:///*",
                "/workspace/output/nifti/*",
                "localhost",
                "127.0.0.1",
                f"{project_root}/output/nifti/*",
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
    
    def check_external_image_server(self) -> bool:
        """Check if the external image server is accessible"""
        logger.info("Checking external image server accessibility...")
        
        try:
            # Test local access first
            image_server_host = os.getenv('EXTERNAL_IMAGE_SERVER_HOST', 'localhost')
            image_server_port = os.getenv('EXTERNAL_IMAGE_SERVER_PORT', '8888')
            image_server_protocol = os.getenv('EXTERNAL_IMAGE_SERVER_PROTOCOL', 'http')
            image_server_url = f"{image_server_protocol}://{image_server_host}:{image_server_port}/"
            
            response = requests.get(image_server_url, timeout=10)
            if response.status_code == 200:
                logger.info("✅ External image server is accessible locally")
                return True
        except requests.RequestException as e:
            logger.warning(f"External image server not accessible locally: {e}")
        
        # Check if the image server process is running
        try:
            result = subprocess.run(
                "pgrep -f 'image_server.py'",
                shell=True,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                logger.info("✅ External image server process is running")
                return True
            else:
                logger.warning("⚠️  External image server process not found")
                logger.info("Please start the image server with: python3 utils/image_server.py")
                return False
        except Exception as e:
            logger.error(f"Error checking image server process: {e}")
            return False
    
    def start_external_image_server(self) -> bool:
        """Start the external image server if not already running"""
        logger.info("Starting external image server...")
        
        # Check if already running
        if self.check_external_image_server():
            logger.info("✅ External image server is already running")
            return True
        
        # Start the image server
        image_server_script = self.script_dir / "image_server.py"
        if not image_server_script.exists():
            logger.error(f"❌ Image server script not found: {image_server_script}")
            return False
        
        try:
            # Start image server in background
            cmd = f"nohup {sys.executable} {image_server_script} > /tmp/image_server.log 2>&1 &"
            self.run_command(cmd)
            
            # Wait for server to start
            logger.info("Waiting for external image server to start...")
            time.sleep(5)
            
            # Check if server is now accessible
            if self.check_external_image_server():
                logger.info("✅ External image server started successfully")
                return True
            else:
                logger.error("❌ External image server failed to start")
                return False
                
        except Exception as e:
            logger.error(f"Error starting external image server: {e}")
            return False
    
    def start_vista3d_container(self) -> bool:
        """Start the Vista-3D Docker container"""
        logger.info("Starting Vista-3D container...")
        
        # Build environment variables string
        env_vars = " ".join([f"-e {k}={v}" for k, v in self.env_vars.items()])
        
        # Build domain whitelist
        domain_whitelist_str = json.dumps(self.domain_whitelist)
        env_vars += f" -e DOMAIN_WHITELIST='{domain_whitelist_str}'"
        
        # Build supported extensions
        extensions_str = json.dumps(self.supported_extensions)
        env_vars += f" -e SUPPORTED_IMAGE_EXT='{extensions_str}'"
        
        # Build volume mounts
        volumes = f"-v {self.local_outputs_path}:{self.container_outputs_path}"
        volumes += f" -v {self.project_root}:{self.project_root}:ro"
        
        # Docker run command with configurable networking
        vista3d_port = os.getenv('VISTA3D_PORT', '8000')
        use_host_networking = os.getenv('USE_HOST_NETWORKING', 'False').lower() in ('true', '1', 'yes')
        allow_external_access = os.getenv('ALLOW_EXTERNAL_ACCESS', 'False').lower() in ('true', '1', 'yes')
        
        # Build network configuration
        network_config = ""
        if use_host_networking:
            network_config = "--network=host"
            logger.info("Using host networking mode - Vista3D will be accessible on all interfaces")
        else:
            # Standard port mapping with optional external access
            if allow_external_access:
                network_config = f"-p 0.0.0.0:{vista3d_port}:8000"
                logger.info(f"Vista3D will be accessible externally on port {vista3d_port}")
            else:
                network_config = f"-p {vista3d_port}:8000"
                logger.info(f"Vista3D will be accessible on localhost:{vista3d_port}")
        
        # Add host entries for external access
        host_entries = "--add-host=host.docker.internal:host-gateway"
        if allow_external_access or use_host_networking:
            # Add additional host entries for external access
            host_entries += " --add-host=localhost:host-gateway"
            host_entries += " --add-host=127.0.0.1:host-gateway"
        
        docker_cmd = f"""
            docker run --gpus all --rm -d --name {self.container_name} \
            --runtime=nvidia \
            --shm-size=8G \
            {host_entries} \
            {network_config} \
            {volumes} \
            {env_vars} \
            nvcr.io/nim/nvidia/vista3d:1.0.0
        """
        
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
        
        # Test 1: Local file path access
        vista3d_port = os.getenv('VISTA3D_PORT', '8000')
        logger.info("Test 1: Testing local file path access...")
        test_data = {"image": "/workspace/output/nifti/test.nii.gz"}
        try:
            response = requests.post(
                f"http://localhost:{vista3d_port}/v1/vista3d/inference",
                json=test_data,
                timeout=10
            )
            logger.info(f"Response status: {response.status_code}")
        except requests.RequestException as e:
            logger.warning(f"Test 1 failed (expected for non-existent file): {e}")
        
        # Test 2: File protocol access
        logger.info("Test 2: Testing file:// protocol access...")
        test_data = {"image": "file:///workspace/output/nifti/test.nii.gz"}
        try:
            response = requests.post(
                f"http://localhost:{vista3d_port}/v1/vista3d/inference",
                json=test_data,
                timeout=10
            )
            logger.info(f"Response status: {response.status_code}")
        except requests.RequestException as e:
            logger.warning(f"Test 2 failed (expected for non-existent file): {e}")
        
        # Test 3: External image server access
        logger.info("Test 3: Testing external image server access...")
        try:
            image_server_host = os.getenv('EXTERNAL_IMAGE_SERVER_HOST', 'localhost')
            image_server_port = os.getenv('EXTERNAL_IMAGE_SERVER_PORT', '8888')
            image_server_protocol = os.getenv('EXTERNAL_IMAGE_SERVER_PROTOCOL', 'http')
            image_server_url = f"{image_server_protocol}://{image_server_host}:{image_server_port}/"
            
            response = requests.get(image_server_url, timeout=10)
            logger.info(f"External image server response: {response.status_code}")
        except requests.RequestException as e:
            logger.warning(f"Test 3 failed: {e}")
        
        # Test 4: Test external IP access (if enabled)
        allow_any_host = os.getenv('ALLOW_ANY_IMAGE_SERVER_HOST', 'False').lower() in ('true', '1', 'yes')
        if allow_any_host:
            logger.info("Test 4: Testing external IP access capability...")
            logger.info("✅ External IP access is enabled - Vista3D can accept connections from any IP/host")
        else:
            logger.info("Test 4: External IP access is disabled (use ALLOW_ANY_IMAGE_SERVER_HOST=True to enable)")
    
    def test_external_image_server_access(self, external_url: str) -> bool:
        """Test access to an external image server"""
        logger.info(f"Testing access to external image server: {external_url}")
        
        try:
            response = requests.get(external_url, timeout=10)
            if response.status_code == 200:
                logger.info(f"✅ Successfully connected to external image server: {external_url}")
                return True
            else:
                logger.warning(f"⚠️  External image server returned status {response.status_code}")
                return False
        except requests.RequestException as e:
            logger.error(f"❌ Failed to connect to external image server: {e}")
            return False
    
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
Description=Vista-3D Docker Container with External Image Server Access
After=docker.service
Requires=docker.service
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
User=hpadmin
Group=hpadmin
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
    
    def create_monitoring_script(self):
        """Create a monitoring script for the external image server"""
        monitor_script = self.script_dir / "monitor_image_server.py"
        
        logger.info("Creating external image server monitoring script...")
        
        script_content = '''#!/usr/bin/env python3
"""
External Image Server Health Monitor
Monitors the external image server started by image_server.py
"""

import time
import logging
import requests
import subprocess
from pathlib import Path
import os

# Configure logging
log_dir = Path(__file__).resolve().parent.parent / 'output' / 'logs'
log_dir.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'image_server_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_image_server_process():
    """Check if external image server process is running"""
    try:
        result = subprocess.run(
            "pgrep -f 'image_server.py'",
            shell=True,
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception:
        return False

def restart_image_server():
    """Restart the external image server"""
    try:
        script_path = Path(__file__).parent / "image_server.py"
        cmd = f"nohup python3 {script_path} > /tmp/image_server.log 2>&1 &"
        subprocess.run(cmd, shell=True)
        time.sleep(5)
        return True
    except Exception as e:
        logger.error(f"Error restarting server: {e}")
        return False

def check_server_response():
    """Check if external image server is responding to requests"""
    try:
        image_server_host = os.getenv('EXTERNAL_IMAGE_SERVER_HOST', 'localhost')
        image_server_port = os.getenv('EXTERNAL_IMAGE_SERVER_PORT', '8888')
        image_server_protocol = os.getenv('EXTERNAL_IMAGE_SERVER_PROTOCOL', 'https')
        image_server_url = f"{image_server_protocol}://{image_server_host}:{image_server_port}/"
        
        response = requests.get(
            image_server_url,
            verify=False,
            timeout=10
        )
        return response.status_code == 200
    except Exception:
        return False

def main():
    """Main monitoring loop"""
    logger.info("Starting external image server monitoring...")
    
    while True:
        try:
            # Check if external image server process is running
            if not check_image_server_process():
                logger.warning("⚠️  External image server process not found, restarting...")
                restart_image_server()
                time.sleep(60)
                continue
            
            # Check if server is responding
            if not check_server_response():
                logger.warning("⚠️  External image server not responding, restarting...")
                restart_image_server()
                time.sleep(60)
                continue
            
            logger.info("✅ External image server is healthy and responding")
            time.sleep(60)  # Check every minute
            
        except KeyboardInterrupt:
            logger.info("Shutting down monitor...")
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
'''
        
        try:
            with open(monitor_script, 'w') as f:
                f.write(script_content)
            
            # Make the script executable
            monitor_script.chmod(0o755)
            
            logger.info(f"✅ Monitoring script created: {monitor_script}")
            logger.info("\nTo start monitoring in background:")
            logger.info(f"  nohup {monitor_script} > /dev/null 2>&1 &")
            logger.info("\nTo view monitoring logs:")
            logger.info(f"  tail -f {monitor_script.parent}/image_server_monitor.log")
            
            return True
        except Exception as e:
            logger.error(f"Error creating monitoring script: {e}")
            return False
    
    def check_image_server_health(self) -> bool:
        """Check external image server health and restart if needed"""
        logger.info("Checking external image server health...")
        
        # Check if external image server process is running
        if not self.check_external_image_server():
            logger.warning("⚠️  External image server not accessible, restarting...")
            return self.start_external_image_server()
        
        # Check if server is responding
        try:
            image_server_host = os.getenv('EXTERNAL_IMAGE_SERVER_HOST', 'localhost')
            image_server_port = os.getenv('EXTERNAL_IMAGE_SERVER_PORT', '8888')
            image_server_protocol = os.getenv('EXTERNAL_IMAGE_SERVER_PROTOCOL', 'http')
            image_server_url = f"{image_server_protocol}://{image_server_host}:{image_server_port}/"
            
            response = requests.get(image_server_url, timeout=10)
            if response.status_code == 200:
                logger.info("✅ External image server is healthy and responding")
                return True
            else:
                logger.warning("⚠️  External image server not responding, restarting...")
                return self.start_external_image_server()
        except requests.RequestException:
            logger.warning("⚠️  External image server not responding, restarting...")
            return self.start_external_image_server()
    
    def run(self):
        """Main execution logic"""
        logger.info("Starting Vista-3D container with external image server access...")
        
        # Check Docker availability
        if not self.check_docker():
            return False
        
        # Create output directory
        self.create_output_directory()
        
        # Start external image server
        if not self.start_external_image_server():
            logger.error("❌ Failed to start external image server")
            logger.error("Vista-3D will not be able to access image files")
            logger.error("Continuing with Vista-3D setup...")
        
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
        image_server_port = os.getenv('EXTERNAL_IMAGE_SERVER_PORT', '8888')
        logger.info(f"Vista-3D is now running on port {vista3d_port}")
        logger.info(f"External image server is running on port {image_server_port}")
        logger.info("==========================================")
        
        logger.info("\nUseful commands:")
        logger.info("  View Vista-3D logs: docker logs -f vista3d")
        logger.info("  View external image server logs: tail -f /tmp/image_server.log")
        logger.info("  Stop container: docker stop vista3d")
        logger.info("  Access container shell: docker exec -it vista3d bash")
        logger.info("  Test Vista-3D endpoint: curl http://localhost:8000/v1/vista3d/inference -X POST -H 'Content-Type: application/json' -d '{\"image\":\"test\"}'")
        logger.info(f"  Test external image server: curl http://localhost:{image_server_port}/")
        logger.info("  Start external image server manually: python3 utils/image_server.py")
        
        return True

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Vista-3D Docker Startup Script with External Image Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 start_vista.py                 # Start Vista-3D container with external image server
  sudo python3 start_vista.py --create-service  # Create systemd service for auto-startup
  python3 start_vista.py --create-monitor       # Create monitoring script
  python3 start_vista.py --health-check         # Check external image server health

For automatic startup on boot:
  1. Run: sudo python3 start_vista.py --create-service
  2. The service will start automatically on boot
  3. Check status: sudo systemctl status vista3d

For continuous monitoring:
  1. Run: python3 start_vista.py --create-monitor
  2. Start monitoring: nohup python3 utils/monitor_image_server.py > /dev/null 2>&1 &
  3. View logs: tail -f utils/image_server_monitor.log

External Image Server:
  The script now starts an external image server (image_server.py) that Vista-3D can access
  via host.docker.internal:8888. This provides better separation of concerns and allows
  the image server to run independently of the Docker container.

Network Access Configuration:
  To allow Vista3D to accept image server connections from any IP address or host:
  
  Environment Variables:
    ALLOW_ANY_IMAGE_SERVER_HOST=True    # Allow any host/IP for image server access
    ALLOW_EXTERNAL_ACCESS=True          # Allow external access to Vista3D container
    USE_HOST_NETWORKING=True            # Use host networking (allows all interfaces)
    DISABLE_URL_VALIDATION=True         # Disable URL validation restrictions
    ALLOW_ANY_IP_ACCESS=True            # Allow any IP address access
    DISABLE_HOST_VALIDATION=True        # Disable host validation
    ALLOW_HTTP_ACCESS=True              # Allow HTTP access
    ALLOW_HTTPS_ACCESS=True             # Allow HTTPS access
  
  Examples:
    # Allow any image server host
    ALLOW_ANY_IMAGE_SERVER_HOST=True python3 start_vista3d.py
    
    # Use host networking for maximum external access
    USE_HOST_NETWORKING=True python3 start_vista3d.py
    
    # Allow external access on specific port
    ALLOW_EXTERNAL_ACCESS=True VISTA3D_PORT=8000 python3 start_vista3d.py
        """
    )
    
    parser.add_argument(
        '--create-service',
        action='store_true',
        help='Create systemd service for automatic startup (requires root)'
    )
    parser.add_argument(
        '--create-monitor',
        action='store_true',
        help='Create monitoring script for external image server health checks'
    )
    parser.add_argument(
        '--health-check',
        action='store_true',
        help='Check external image server health and restart if needed'
    )
    parser.add_argument(
        '--test-external',
        type=str,
        metavar='URL',
        help='Test access to an external image server URL'
    )
    
    args = parser.parse_args()
    
    manager = Vista3DManager()
    
    try:
        if args.create_service:
            success = manager.create_systemd_service()
            sys.exit(0 if success else 1)
        elif args.create_monitor:
            success = manager.create_monitoring_script()
            sys.exit(0 if success else 1)
        elif args.health_check:
            success = manager.check_image_server_health()
            sys.exit(0 if success else 1)
        elif args.test_external:
            success = manager.test_external_image_server_access(args.test_external)
            sys.exit(0 if success else 1)
        else:
            # Default behavior - start the container with external image server
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
()
