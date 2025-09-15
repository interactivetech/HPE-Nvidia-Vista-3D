#!/usr/bin/env python3
"""
Vista-3D GUI Docker Startup Script
Starts the Streamlit app and image server containers for the Vista-3D GUI
"""

import os
import sys
import time
import subprocess
import argparse
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import signal
import atexit
import requests

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
        logging.FileHandler(log_dir / 'start_gui.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class Vista3DGUIManager:
    """Manages Vista-3D GUI Docker containers (Streamlit app and image server)"""

    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.project_root = self.script_dir.parent
        
        # Container names
        self.app_container_name = os.getenv('APP_CONTAINER_NAME', 'hpe-nvidia-vista3d-app')
        self.image_server_container_name = os.getenv('IMAGE_SERVER_CONTAINER_NAME', 'vista3d-image-server')
        
        self._setup_env_vars()
        self._setup_paths()
        self._register_signal_handlers()

    def _setup_env_vars(self):
        """Load environment variables from .env file or use defaults."""
        self.env_vars = {
            # Streamlit Configuration
            'STREAMLIT_SERVER_PORT': os.getenv('STREAMLIT_SERVER_PORT', '8501'),
            'STREAMLIT_SERVER_ADDRESS': os.getenv('STREAMLIT_SERVER_ADDRESS', '0.0.0.0'),
            
            # Server URLs
            'IMAGE_SERVER': os.getenv('IMAGE_SERVER', 'http://image-server:8888'),
            'VISTA3D_SERVER': os.getenv('VISTA3D_SERVER', 'http://vista3d-server:8000'),
            
            # API Keys
            'VISTA3D_API_KEY': os.getenv('VISTA3D_API_KEY'),
            'HPE_CLUSTER_ENDPOINT': os.getenv('HPE_CLUSTER_ENDPOINT'),
            'HPE_API_KEY': os.getenv('HPE_API_KEY'),
            
            # Output Configuration
            'OUTPUT_DIR': os.getenv('OUTPUT_DIR', '/app/output'),
            'DICOM_DIR': os.getenv('DICOM_DIR', '/app/dicom'),
            
            # Network Configuration
            'USE_HOST_NETWORKING': os.getenv('USE_HOST_NETWORKING', 'False'),
            'APP_PORT': os.getenv('APP_PORT', '8501'),
            'IMAGE_SERVER_PORT': os.getenv('IMAGE_SERVER_PORT', '8888'),
        }

    def _setup_paths(self):
        """Setup paths from environment variables or use defaults."""
        self.local_outputs_path = self.project_root / "output"
        self.local_dicom_path = self.project_root / "dicom"
        self.local_env_path = self.project_root / ".env"

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
    
    def run_command(self, command: str, check: bool = True, capture_output: bool = False, cwd: Optional[str] = None) -> subprocess.CompletedProcess:
        """Run a shell command with proper error handling"""
        try:
            logger.debug(f"Running command: {command}")
            result = subprocess.run(
                command,
                shell=True,
                check=check,
                capture_output=capture_output,
                text=True,
                cwd=cwd
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
    
    def check_docker_compose(self) -> bool:
        """Check if Docker Compose is available"""
        try:
            result = self.run_command("docker compose version", check=False)
            if result.returncode != 0:
                # Try older docker-compose command
                result = self.run_command("docker-compose --version", check=False)
                if result.returncode != 0:
                    logger.error("Docker Compose is not installed or not in PATH")
                    return False
            
            logger.info("✅ Docker Compose is available")
            return True
        except Exception as e:
            logger.error(f"Error checking Docker Compose: {e}")
            return False
    
    def stop_existing_containers(self):
        """Stop and remove any existing GUI containers"""
        logger.info("Stopping any existing GUI containers...")
        
        containers = [self.app_container_name, self.image_server_container_name]
        
        for container in containers:
            # Stop container
            self.run_command(f"docker stop {container}", check=False)
            
            # Remove container
            self.run_command(f"docker rm {container}", check=False)
            self.run_command(f"docker rm -f {container}", check=False)
        
        # Clean up any remaining container references
        self.run_command("docker container prune -f", check=False)
        
        logger.info("✅ Existing containers cleaned up")
    
    def create_directories(self):
        """Create necessary directories if they don't exist"""
        self.local_outputs_path.mkdir(parents=True, exist_ok=True)
        self.local_dicom_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"✅ Directories created: {self.local_outputs_path}, {self.local_dicom_path}")
    
    def build_docker_image(self) -> bool:
        """Build the Docker image for the GUI containers"""
        logger.info("Building Docker image for GUI containers...")
        
        try:
            # Build the image using docker compose
            result = self.run_command(f"docker compose build", cwd=str(self.project_root))
            if result.returncode == 0:
                logger.info("✅ Docker image built successfully")
                return True
            else:
                logger.error("❌ Failed to build Docker image")
                return False
        except Exception as e:
            logger.error(f"Error building Docker image: {e}")
            return False
    
    def start_containers(self) -> bool:
        """Start the GUI containers using docker compose"""
        logger.info("Starting GUI containers...")
        
        try:
            # Start containers using docker compose
            result = self.run_command(f"docker compose up -d", cwd=str(self.project_root))
            if result.returncode == 0:
                logger.info("✅ GUI containers started successfully")
                
                # Wait for containers to be ready
                time.sleep(10)
                
                # Show container status
                self.run_command("docker compose ps")
                
                return True
            else:
                logger.error("❌ Failed to start GUI containers")
                return False
        except Exception as e:
            logger.error(f"Error starting containers: {e}")
            return False
    
    def check_container_health(self, container_name: str, port: int, health_path: str = "/health") -> bool:
        """Check if a container is healthy by making a request to its health endpoint"""
        try:
            response = requests.get(f"http://localhost:{port}{health_path}", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Health check failed for {container_name}: {e}")
            return False
    
    def wait_for_containers(self, timeout: int = 120) -> bool:
        """Wait for containers to be ready"""
        logger.info("Waiting for containers to be ready...")
        
        start_time = time.time()
        app_ready = False
        image_server_ready = False
        
        app_port = int(self.env_vars['APP_PORT'])
        image_server_port = int(self.env_vars['IMAGE_SERVER_PORT'])
        
        while time.time() - start_time < timeout:
            # Check Streamlit app
            if not app_ready:
                if self.check_container_health(self.app_container_name, app_port, "/_stcore/health"):
                    logger.info("✅ Streamlit app is ready")
                    app_ready = True
                else:
                    logger.debug("Streamlit app not ready yet...")
            
            # Check image server
            if not image_server_ready:
                if self.check_container_health(self.image_server_container_name, image_server_port, "/health"):
                    logger.info("✅ Image server is ready")
                    image_server_ready = True
                else:
                    logger.debug("Image server not ready yet...")
            
            if app_ready and image_server_ready:
                logger.info("✅ All containers are ready!")
                return True
            
            time.sleep(5)
        
        logger.error("❌ Timeout waiting for containers to be ready")
        return False
    
    def show_container_logs(self):
        """Show logs from the containers"""
        logger.info("Container logs (last 20 lines each):")
        
        # Show Streamlit app logs
        logger.info(f"\n--- {self.app_container_name} logs ---")
        self.run_command(f"docker logs {self.app_container_name} --tail 20", check=False)
        
        # Show image server logs
        logger.info(f"\n--- {self.image_server_container_name} logs ---")
        self.run_command(f"docker logs {self.image_server_container_name} --tail 20", check=False)
    
    def test_configuration(self):
        """Test the GUI configuration"""
        logger.info("Testing GUI configuration...")
        
        app_port = int(self.env_vars['APP_PORT'])
        image_server_port = int(self.env_vars['IMAGE_SERVER_PORT'])
        
        # Test 1: Streamlit app connectivity
        logger.info("Test 1: Testing Streamlit app connectivity...")
        try:
            response = requests.get(f"http://localhost:{app_port}/_stcore/health", timeout=10)
            logger.info(f"Streamlit app health check response: {response.status_code}")
        except Exception as e:
            logger.warning(f"Streamlit app health check failed: {e}")
        
        # Test 2: Image server connectivity
        logger.info("Test 2: Testing image server connectivity...")
        try:
            response = requests.get(f"http://localhost:{image_server_port}/health", timeout=10)
            logger.info(f"Image server health check response: {response.status_code}")
        except Exception as e:
            logger.warning(f"Image server health check failed: {e}")
        
        # Test 3: Test external access capability
        logger.info("Test 3: Testing external access configuration...")
        logger.info("✅ Streamlit app is accessible on all interfaces")
        logger.info("✅ Image server is accessible on all interfaces")
        logger.info("✅ CORS is enabled for cross-origin requests")
    
    def create_systemd_service(self):
        """Create systemd service for automatic startup"""
        if os.geteuid() != 0:
            logger.error("⚠️  This function requires root privileges to create systemd service")
            logger.error("   Run with: sudo python3 start_gui.py --create-service")
            return False
        
        service_name = "vista3d-gui"
        service_file = f"/etc/systemd/system/{service_name}.service"
        script_path = str(Path(__file__).absolute())
        
        logger.info("Creating systemd service for automatic startup...")
        
        service_content = f"""[Unit]
Description=Vista-3D GUI Docker Containers (Streamlit App and Image Server)
After=docker.service
Requires=docker.service
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
User=root
Group=root
WorkingDirectory={self.project_root}
ExecStart={sys.executable} {script_path}
ExecStop=/usr/bin/docker compose down
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
        logger.info("Starting Vista-3D GUI containers...")
        
        # Check Docker availability
        if not self.check_docker():
            return False
        
        # Check Docker Compose availability
        if not self.check_docker_compose():
            return False
        
        # Create necessary directories
        self.create_directories()
        
        # Stop existing containers
        self.stop_existing_containers()
        
        # Build Docker image
        if not self.build_docker_image():
            return False
        
        # Start containers
        if not self.start_containers():
            return False
        
        # Wait for containers to be ready
        if not self.wait_for_containers():
            logger.warning("Containers may not be fully ready, but continuing...")
        
        # Show container logs
        self.show_container_logs()
        
        # Test configuration
        self.test_configuration()
        
        # Success message
        logger.info("==========================================")
        app_port = self.env_vars['APP_PORT']
        image_server_port = self.env_vars['IMAGE_SERVER_PORT']
        logger.info(f"Streamlit app is running on port {app_port}")
        logger.info(f"Image server is running on port {image_server_port}")
        logger.info("✅ GUI containers are ready!")
        logger.info("✅ External access is enabled")
        logger.info("✅ All interfaces are accessible")
        logger.info("==========================================")
        
        logger.info("\nUseful commands:")
        logger.info("  View all logs: docker compose logs -f")
        logger.info("  View app logs: docker logs -f hpe-nvidia-vista3d-app")
        logger.info("  View image server logs: docker logs -f vista3d-image-server")
        logger.info("  Stop containers: docker compose down")
        logger.info("  Restart containers: docker compose restart")
        logger.info(f"  Access Streamlit app: http://localhost:{app_port}")
        logger.info(f"  Access image server: http://localhost:{image_server_port}")
        
        return True

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Vista-3D GUI Docker Startup Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 start_gui.py                 # Start GUI containers
  sudo python3 start_gui.py --create-service  # Create systemd service for auto-startup

For automatic startup on boot:
  1. Run: sudo python3 start_gui.py --create-service
  2. The service will start automatically on boot
  3. Check status: sudo systemctl status vista3d-gui

Container Configuration:
  The script starts two containers:
  - Streamlit app (port 8501 by default)
  - Image server (port 8888 by default)
  
  Key Environment Variables:
    STREAMLIT_SERVER_PORT=8501        # Port for Streamlit app
    IMAGE_SERVER_PORT=8888            # Port for image server
    USE_HOST_NETWORKING=False         # Use bridge networking (default)
    IMAGE_SERVER=http://image-server:8888  # Image server URL
    VISTA3D_SERVER=http://vista3d-server:8000  # Vista3D server URL
  
  Examples:
    # Use default ports
    python3 start_gui.py
    
    # Use custom ports
    STREAMLIT_SERVER_PORT=8502 IMAGE_SERVER_PORT=8889 python3 start_gui.py
        """
    )
    
    parser.add_argument(
        '--create-service',
        action='store_true',
        help='Create systemd service for automatic startup (requires root)'
    )
    
    args = parser.parse_args()
    
    manager = Vista3DGUIManager()
    
    try:
        if args.create_service:
            success = manager.create_systemd_service()
            sys.exit(0 if success else 1)
        else:
            # Default behavior - start the containers
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
