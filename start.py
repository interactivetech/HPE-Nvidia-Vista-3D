#!/usr/bin/env python3
"""
HPE NVIDIA Vista3D - Unified Start Script
Starts all services (frontend, image server, and Vista3D AI) on a single GPU-enabled host
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
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class Vista3DUnifiedManager:
    """Manages all Vista3D services on a single GPU-enabled host"""

    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.project_root = self.script_dir
        
        # Container names
        self.app_container_name = 'hpe-nvidia-vista3d-app'
        self.image_server_container_name = 'vista3d-image-server'
        self.vista3d_container_name = 'vista3d-server-local'
        
        self._setup_env_vars()
        self._register_signal_handlers()

    def _setup_env_vars(self):
        """Load environment variables from .env file or use defaults."""
        self.env_vars = {
            # Streamlit Configuration
            'STREAMLIT_SERVER_PORT': os.getenv('STREAMLIT_SERVER_PORT', '8501'),
            'STREAMLIT_SERVER_ADDRESS': os.getenv('STREAMLIT_SERVER_ADDRESS', '0.0.0.0'),
            
            # Server URLs
            'IMAGE_SERVER': os.getenv('IMAGE_SERVER', 'http://localhost:8888'),
            'VISTA3D_SERVER': os.getenv('VISTA3D_SERVER', 'http://localhost:8000'),
            
            # API Keys
            'NGC_API_KEY': os.getenv('NGC_API_KEY'),
            'NGC_ORG_ID': os.getenv('NGC_ORG_ID', 'nvidia'),
            
            # Output Configuration
            'OUTPUT_DIR': os.getenv('OUTPUT_DIR', '/app/output'),
            'DICOM_DIR': os.getenv('DICOM_DIR', '/app/dicom'),
            'OUTPUT_FOLDER': os.getenv('OUTPUT_FOLDER', str(self.project_root / 'output')),
            
            # Network Configuration
            'USE_HOST_NETWORKING': os.getenv('USE_HOST_NETWORKING', 'False'),
            'APP_PORT': os.getenv('APP_PORT', '8501'),
            'IMAGE_SERVER_PORT': os.getenv('IMAGE_SERVER_PORT', '8888'),
            'VISTA3D_PORT': os.getenv('VISTA3D_PORT', '8000'),
            
            # Vista3D Configuration
            'VESSELS_OF_INTEREST': os.getenv('VESSELS_OF_INTEREST', 'all'),
            'CUDA_VISIBLE_DEVICES': os.getenv('CUDA_VISIBLE_DEVICES', '0'),
            'NVIDIA_VISIBLE_DEVICES': os.getenv('NVIDIA_VISIBLE_DEVICES', '0'),
        }

    def _register_signal_handlers(self):
        """Register signal handlers for graceful shutdown."""
        # Only register atexit cleanup for main run mode, not for frontend-only or vista3d-only
        # atexit.register(self.cleanup)
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
        self.stop_all_containers()
    
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
    
    def stop_all_containers(self):
        """Stop and remove all Vista3D containers"""
        logger.info("Stopping all Vista3D containers...")
        
        containers = [self.app_container_name, self.image_server_container_name, self.vista3d_container_name]
        
        # Stop and remove containers started by docker run (old method)
        self.run_command(f"docker stop vista3d", check=False)
        self.run_command(f"docker rm -f vista3d", check=False)

        # Stop and remove containers managed by docker compose
        self.run_command(f"docker compose --profile local-vista3d down", cwd=str(self.project_root), check=False)
        self.run_command(f"docker compose down", cwd=str(self.project_root), check=False)
        
        # Clean up any remaining container references
        self.run_command("docker container prune -f", check=False)
        
        logger.info("✅ All containers stopped and cleaned up")
    
    def create_directories(self):
        """Create necessary directories if they don't exist"""
        directories = [
            self.project_root / "output",
            self.project_root / "dicom"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"✅ Directories created")
    
    def build_docker_images(self) -> bool:
        """Build the Docker images for all services"""
        logger.info("Building Docker images for all services...")
        
        try:
            # Build the image using docker compose
            result = self.run_command(f"docker compose build", cwd=str(self.project_root))
            if result.returncode == 0:
                logger.info("✅ Docker images built successfully")
                return True
            else:
                logger.error("❌ Failed to build Docker images")
                return False
        except Exception as e:
            logger.error(f"Error building Docker images: {e}")
            return False
    
    def start_vista3d_container(self) -> bool:
        """Start the Vista3D AI container"""
        logger.info("Starting Vista3D AI container...")
        
        # Check if NGC API key is available
        if not self.env_vars.get('NGC_API_KEY'):
            logger.error("❌ NGC_API_KEY not found in .env file")
            logger.error("   Please run 'python setup.py' first to configure your API key")
            return False
        
        # Build environment variables string
        env_vars_list = []
        for k, v in self.env_vars.items():
            if v is not None:
                v_str = str(v)
                if ' ' in v_str or '\'' in v_str or '"' in v_str:
                    escaped_v = v_str.replace("'", "'\\''")
                    env_vars_list.append(f"-e {k}='{escaped_v}'")
                else:
                    env_vars_list.append(f"-e {k}={v_str}")
        
        # Add required Vista3D environment variables
        env_vars_list.append("-e IMAGE_URI_HTTPS_ONLY=False")
        
        # Add permissive domain whitelist settings from start_vista3d_server.py
        domain_whitelist = [
            # Specific image server from .env
            self.env_vars.get('IMAGE_SERVER', 'http://localhost:8888'),
            'localhost',
            'localhost:8888',
            'http://localhost',
            'http://localhost:8888',
            'https://localhost',
            'https://localhost:8888',
            
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
        
        # Add domain whitelist as JSON string
        import json
        domain_whitelist_str = json.dumps(domain_whitelist)
        env_vars_list.append(f"-e DOMAIN_WHITELIST='{domain_whitelist_str}'")
        
        # Add all the permissive environment variables from start_vista3d_server.py
        permissive_env_vars = [
            'DISABLE_DOMAIN_WHITELIST=True',
            'VISTA3D_DISABLE_URL_VALIDATION=True',
            'VISTA3D_ALLOW_ANY_URL=True',
            'VISTA3D_DISABLE_IMAGE_VALIDATION=True',
            'VISTA3D_ALLOW_EXTERNAL_IMAGES=True',
            'VISTA3D_ALLOW_REMOTE_FILES=True',
            'VISTA3D_DISABLE_FILE_VALIDATION=True',
            'VISTA3D_ENABLE_NETWORK_ACCESS=True',
            'VISTA3D_ALLOW_HTTP_DOWNLOADS=True',
            'VISTA3D_ALLOW_HTTPS_DOWNLOADS=True',
            'VISTA3D_DISABLE_SSL_VERIFICATION=True',
            'VISTA3D_ALLOW_INSECURE_CONNECTIONS=True',
            'ALLOW_ANY_IMAGE_SERVER_HOST=True',
            'ALLOW_EXTERNAL_NETWORK_ACCESS=True',
            'DISABLE_HOST_VALIDATION=True',
            'ALLOW_ANY_IP_ACCESS=True',
            'ALLOW_HTTP_ACCESS=True',
            'ALLOW_HTTPS_ACCESS=True',
            'ALLOW_REMOTE_ACCESS=True',
            'ALLOW_CROSS_ORIGIN=True',
            'DISABLE_CORS=True',
            'ALLOW_ANY_ORIGIN=True',
            'ALLOW_ANY_HOST=True',
            'DISABLE_ORIGIN_VALIDATION=True',
            'ALLOW_WILDCARD_HOSTS=True',
            'DISABLE_IP_VALIDATION=True',
            'ALLOW_PRIVATE_IPS=True',
            'ALLOW_PUBLIC_IPS=True',
            'ALLOW_LOCALHOST=True',
            'ALLOW_LOOPBACK=True',
            'DISABLE_NETWORK_RESTRICTIONS=True',
            'ENABLE_EXTERNAL_ACCESS=True',
            'ALLOW_IMAGE_SERVER_ACCESS=True',
            'DISABLE_IMAGE_SERVER_VALIDATION=True',
        ]
        
        for env_var in permissive_env_vars:
            env_vars_list.append(f"-e {env_var}")
        
        env_vars = " ".join(env_vars_list)

        # Build volume mounts
        output_folder = self.env_vars.get('OUTPUT_FOLDER', str(self.project_root / 'output'))
        volumes = f'-v "{output_folder}:/workspace/output"'
        volumes += f' -v "{self.project_root / "dicom"}:/app/dicom"'
        volumes += f' -v "{self.project_root}:{self.project_root}:ro"'
        
        # Network configuration
        vista3d_port = self.env_vars.get('VISTA3D_PORT', '8000')
        use_host_networking = self.env_vars.get('USE_HOST_NETWORKING', 'False').lower() in ('true', '1', 'yes')
        
        if use_host_networking:
            network_config = "--network=host"
            logger.info("Using host networking mode")
        else:
            network_config = f"-p 0.0.0.0:{vista3d_port}:8000"
            logger.info(f"Vista3D will be accessible on port {vista3d_port}")
        
        # Add host entries for external access
        host_entries = "--add-host=host.docker.internal:host-gateway"
        host_entries += " --add-host=localhost:host-gateway"
        host_entries += " --add-host=127.0.0.1:host-gateway"
        
        try:
            # Use docker compose to start the vista3d-server service with the local-vista3d profile
            result = self.run_command(f"docker compose --profile local-vista3d up -d vista3d-server", cwd=str(self.project_root))
            if result.returncode == 0:
                logger.info("✅ Vista3D AI container started successfully!")
                
                # Wait for container to be ready
                time.sleep(10)
                
                # Show container status
                self.run_command(f"docker ps | grep {self.vista3d_container_name}")
                
                return True
            else:
                logger.error("❌ Failed to start Vista3D AI container")
                return False
        except Exception as e:
            logger.error(f"Error starting Vista3D container: {e}")
            return False
    
    def start_frontend_containers(self) -> bool:
        """Start the frontend containers (Streamlit app and image server)"""
        logger.info("Starting frontend containers...")
        
        try:
            # Start containers using docker compose
            result = self.run_command(f"docker compose up -d", cwd=str(self.project_root))
            if result.returncode == 0:
                logger.info("✅ Frontend containers started successfully")
                
                # Wait for containers to be ready
                time.sleep(10)
                
                # Show container status
                self.run_command("docker compose ps")
                
                return True
            else:
                logger.error("❌ Failed to start frontend containers")
                return False
        except Exception as e:
            logger.error(f"Error starting frontend containers: {e}")
            return False
    
    def check_container_health(self, container_name: str, port: int, health_path: str = "/health") -> bool:
        """Check if a container is healthy by making a request to its health endpoint"""
        try:
            import urllib.request
            with urllib.request.urlopen(f"http://127.0.0.1:{port}{health_path}", timeout=5) as response:
                return response.status == 200
        except Exception as e:
            logger.debug(f"Health check failed for {container_name}: {e}")
            return False
    
    def wait_for_containers(self, timeout: int = 180) -> bool:
        """Wait for all containers to be ready"""
        logger.info("Waiting for all containers to be ready...")
        
        start_time = time.time()
        app_ready = False
        image_server_ready = False
        vista3d_ready = False
        
        app_port = int(self.env_vars['APP_PORT'])
        image_server_port = int(self.env_vars['IMAGE_SERVER_PORT'])
        vista3d_port = int(self.env_vars['VISTA3D_PORT'])
        
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
            
            # Check Vista3D server
            if not vista3d_ready:
                if self.check_container_health(self.vista3d_container_name, vista3d_port, "/v1/health/ready"):
                    logger.info("✅ Vista3D AI server is ready")
                    vista3d_ready = True
                else:
                    logger.debug("Vista3D AI server not ready yet...")
            
            if app_ready and image_server_ready and vista3d_ready:
                logger.info("✅ All containers are ready!")
                return True
            
            time.sleep(5)
        
        logger.warning("⚠️  Timeout waiting for containers to be ready")
        logger.warning("   Some containers may still be starting up")
        return False
    
    def show_container_logs(self):
        """Show logs from all containers"""
        logger.info("Container logs (last 10 lines each):")
        
        containers = [
            (self.app_container_name, "Streamlit App"),
            (self.image_server_container_name, "Image Server"),
            (self.vista3d_container_name, "Vista3D AI Server")
        ]
        
        for container_name, display_name in containers:
            logger.info(f"\n--- {display_name} logs ---")
            self.run_command(f"docker logs {container_name} --tail 10", check=False)
    
    def test_services(self):
        """Test all services"""
        logger.info("Testing all services...")
        
        app_port = int(self.env_vars['APP_PORT'])
        image_server_port = int(self.env_vars['IMAGE_SERVER_PORT'])
        vista3d_port = int(self.env_vars['VISTA3D_PORT'])
        
        # Test Streamlit app
        logger.info("Test 1: Testing Streamlit app...")
        try:
            response = requests.get(f"http://localhost:{app_port}/_stcore/health", timeout=10)
            logger.info(f"✅ Streamlit app health check: {response.status_code}")
        except Exception as e:
            logger.warning(f"⚠️  Streamlit app health check failed: {e}")
        
        # Test image server
        logger.info("Test 2: Testing image server...")
        try:
            response = requests.get(f"http://localhost:{image_server_port}/health", timeout=10)
            logger.info(f"✅ Image server health check: {response.status_code}")
        except Exception as e:
            logger.warning(f"⚠️  Image server health check failed: {e}")
        
        # Test Vista3D server
        logger.info("Test 3: Testing Vista3D AI server...")
        try:
            import urllib.request
            with urllib.request.urlopen(f"http://127.0.0.1:{vista3d_port}/v1/health/ready", timeout=10) as response:
                logger.info(f"✅ Vista3D AI server health check: {response.status}")
        except Exception as e:
            logger.warning(f"⚠️  Vista3D AI server health check failed: {e}")
    
    def run(self):
        """Main execution logic"""
        logger.info("Starting HPE NVIDIA Vista3D platform...")
        
        # Check Docker availability
        if not self.check_docker():
            return False
        
        # Check Docker Compose availability
        if not self.check_docker_compose():
            return False
        
        # Create necessary directories
        self.create_directories()
        
        # Stop any existing containers
        self.stop_all_containers()
        
        # Build Docker images
        if not self.build_docker_images():
            return False
        
        # Start Vista3D AI container
        if not self.start_vista3d_container():
            logger.error("❌ Failed to start Vista3D AI container")
            logger.error("   Please check your NGC API key and GPU availability")
            return False
        
        # Start frontend containers
        if not self.start_frontend_containers():
            logger.error("❌ Failed to start frontend containers")
            return False
        
        # Wait for containers to be ready
        self.wait_for_containers()
        
        # Show container logs
        self.show_container_logs()
        
        # Test services
        self.test_services()
        
        # Success message
        logger.info("=" * 80)
        logger.info("🎉 HPE NVIDIA VISTA3D PLATFORM STARTED SUCCESSFULLY!")
        logger.info("=" * 80)
        
        app_port = self.env_vars['APP_PORT']
        image_server_port = self.env_vars['IMAGE_SERVER_PORT']
        vista3d_port = self.env_vars['VISTA3D_PORT']
        
        logger.info(f"🌐 Streamlit Web Interface: http://localhost:{app_port}")
        logger.info(f"🖼️  Image Server: http://localhost:{image_server_port}")
        logger.info(f"🧠 Vista3D AI Server: http://localhost:{vista3d_port}")
        
        logger.info("\n📋 Next Steps:")
        logger.info("1. Open your browser to http://localhost:8501")
        logger.info("2. Upload your medical images (DICOM or NIFTI)")
        logger.info("3. Use the Tools page to convert DICOM to NIFTI")
        logger.info("4. Use the Tools page to run AI segmentation")
        logger.info("5. View 3D visualizations of your results")
        
        logger.info("\n🔧 Useful Commands:")
        logger.info("  View all logs: docker compose logs -f")
        logger.info("  View Vista3D logs: docker logs -f vista3d")
        logger.info("  Stop all services: python start.py --stop")
        logger.info("  Restart services: python start.py --restart")
        
        logger.info("=" * 80)
        
        return True

    def run_frontend_only(self):
        """Start only frontend services (Streamlit app and image server)"""
        logger.info("Starting frontend services only (with remote Vista3D)...")
        
        # Check Docker availability
        if not self.check_docker():
            return False
        
        # Check Docker Compose availability
        if not self.check_docker_compose():
            return False
        
        # Create necessary directories
        self.create_directories()
        
        # Stop any existing containers
        self.stop_all_containers()
        
        # Build Docker images
        if not self.build_docker_images():
            return False
        
        # Start only frontend containers (not Vista3D)
        if not self.start_frontend_containers():
            logger.error("❌ Failed to start frontend containers")
            return False
        
        # Wait for containers to be ready
        self.wait_for_containers()
        
        # Show container logs
        self.show_container_logs()
        
        # Test services
        self.test_services()
        
        # Success message
        logger.info("=" * 80)
        logger.info("🎉 FRONTEND SERVICES STARTED SUCCESSFULLY!")
        logger.info("=" * 80)
        
        app_port = self.env_vars['APP_PORT']
        image_server_port = self.env_vars['IMAGE_SERVER_PORT']
        
        logger.info(f"🌐 Streamlit Web Interface: http://localhost:{app_port}")
        logger.info(f"🖼️  Image Server: http://localhost:{image_server_port}")
        logger.info(f"🧠 Vista3D Server: {self.env_vars['VISTA3D_SERVER']} (remote)")
        
        logger.info("\n📝 Note: Vista3D server is running remotely.")
        logger.info("   Make sure your .env file is configured with the correct remote Vista3D URL.")
        
        logger.info("\n🔧 Useful Commands:")
        logger.info("  View all logs: docker compose logs -f")
        logger.info("  View frontend logs: docker logs -f hpe-nvidia-vista3d-app")
        logger.info("  View image server logs: docker logs -f vista3d-image-server")
        logger.info("  Stop all services: python start.py --stop")
        logger.info("  Restart services: python start.py --restart")
        
        logger.info("=" * 80)
        
        return True

    def run_vista3d_only(self):
        """Start only Vista3D server"""
        logger.info("Starting Vista3D server only...")
        
        # Check Docker availability
        if not self.check_docker():
            return False
        
        # Check Docker Compose availability
        if not self.check_docker_compose():
            return False
        
        # Create necessary directories
        self.create_directories()
        
        # Stop any existing containers
        self.stop_all_containers()
        
        # Start only Vista3D container
        if not self.start_vista3d_container():
            logger.error("❌ Failed to start Vista3D container")
            logger.error("   Please check your NGC API key and GPU availability")
            return False
        
        # Wait for Vista3D to be ready with retries
        logger.info("Waiting for Vista3D server to be ready...")
        vista3d_port = self.env_vars['VISTA3D_PORT']
        max_retries = 30  # Total 30 * 5 = 150 seconds
        retry_delay = 5   # seconds
        vista3d_ready = False
        
        import urllib.request
        for i in range(max_retries):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{vista3d_port}/v1/health/ready", timeout=5) as response:
                    if response.status == 200:
                        logger.info(f"✅ Vista3D server health check successful after {i+1} attempts.")
                        vista3d_ready = True
                        break
                    else:
                        logger.warning(f"⚠️  Vista3D server health check returned: {response.status}. Retrying in {retry_delay} seconds...")
            except Exception as e:
                logger.warning(f"⚠️  Vista3D server health check failed (attempt {i+1}/{max_retries}): {e}. Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)

        logger.info("=" * 80)
        if vista3d_ready:
            logger.info("🎉 VISTA3D SERVER STARTED SUCCESSFULLY!")
        else:
            logger.error("❌ VISTA3D SERVER FAILED TO START OR HEALTH CHECK FAILED AFTER MULTIPLE RETRIES.")
            logger.error("   Please check Docker logs for 'vista3d' container for more details.")
            return False # Indicate failure
        logger.info("=" * 80)
        
        vista3d_port = self.env_vars['VISTA3D_PORT']
        
        logger.info(f"🧠 Vista3D Server: http://localhost:{vista3d_port}")
        logger.info(f"🔍 Health Check: http://localhost:{vista3d_port}/health")
        
        logger.info("\n📝 Note: Only Vista3D server is running.")
        logger.info("   Frontend services must be started separately on other machines.")
        logger.info("   Configure frontend .env files to point to this server.")
        
        logger.info("\n🔧 Useful Commands:")
        logger.info("  View Vista3D logs: docker logs -f vista3d-server-local")
        logger.info("  Stop Vista3D: python start.py --stop")
        logger.info("  Restart Vista3D: python start.py --restart")
        
        logger.info("=" * 80)
        
        return True

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="HPE NVIDIA Vista3D - Unified Start Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script starts all Vista3D services on a single GPU-enabled host.

Services started:
  • Streamlit Web Interface (port 8501)
  • Image Server (port 8888) 
  • Vista3D AI Server (port 8000)

Prerequisites:
  • Run 'python setup.py' first to configure the system
  • NVIDIA GPU with CUDA support
  • Docker and NVIDIA Container Toolkit (REQUIRED)
  • NGC API key in .env file

Examples:
  python start.py                    # Start all services
  python start.py --frontend-only   # Start only frontend services (remote Vista3D)
  python start.py --vista3d-only    # Start only Vista3D server (distributed deployment)
  python start.py --stop            # Stop all services
  python start.py --restart         # Restart all services
        """
    )
    
    parser.add_argument(
        '--stop',
        action='store_true',
        help='Stop all Vista3D services'
    )
    
    parser.add_argument(
        '--restart',
        action='store_true',
        help='Restart all Vista3D services'
    )
    
    parser.add_argument(
        '--frontend-only',
        action='store_true',
        help='Start only frontend services (Streamlit app and image server) - Vista3D server must be running remotely'
    )
    
    parser.add_argument(
        '--vista3d-only',
        action='store_true',
        help='Start only Vista3D server - for distributed deployments or GPU server farms'
    )
    
    args = parser.parse_args()
    
    manager = Vista3DUnifiedManager()
    
    try:
        if args.stop:
            logger.info("Stopping all Vista3D services...")
            manager.stop_all_containers()
            logger.info("✅ All services stopped")
            sys.exit(0)
        elif args.restart:
            logger.info("Restarting all Vista3D services...")
            manager.stop_all_containers()
            time.sleep(5)
            success = manager.run()
            sys.exit(0 if success else 1)
        elif args.frontend_only:
            # Start only frontend services
            success = manager.run_frontend_only()
            sys.exit(0 if success else 1)
        elif args.vista3d_only:
            # Start only Vista3D server
            success = manager.run_vista3d_only()
            sys.exit(0 if success else 1)
        else:
            # Default behavior - start all services
            success = manager.run()
            if success:
                # For main run mode, register cleanup to stop containers on exit
                atexit.register(manager.cleanup)
                # Keep the script running to maintain containers
                try:
                    logger.info("Containers are running. Press Ctrl+C to stop all services.")
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    logger.info("Shutting down...")
                    manager.cleanup()
            sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
