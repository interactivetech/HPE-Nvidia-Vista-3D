#!/usr/bin/env python3
"""
HPE NVIDIA Vista3D - Frontend Setup Script
Sets up the frontend services (web interface and image server) for Vista3D platform
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

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class Vista3DFrontendSetup:
    """Frontend setup for Vista3D web interface and image server"""
    
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
        print("🌐 HPE NVIDIA Vista3D - Frontend Setup")
        print("="*80)
        print("This script will set up the frontend services for the Vista3D platform.")
        print("It will configure the web interface and image server.")
        print("="*80)
        
        print("\n📋 WHAT THIS SETUP DOES:")
        print("-" * 40)
        print("✅ Sets up Python environment with frontend dependencies")
        print("✅ Configures Docker containers for web interface and image server")
        print("✅ Sets up Streamlit web interface (port 8501)")
        print("✅ Sets up image server (port 8888)")
        print("✅ Creates all necessary directories and files")
        print("✅ Configures frontend services to connect to remote Vista3D server")
        
        print("\n🔧 REQUIREMENTS:")
        print("-" * 40)
        print("• Ubuntu Linux (18.04+) or macOS")
        print("• 8GB+ RAM")
        print("• Docker (REQUIRED)")
        print("• Internet connectivity")
        print("• Remote Vista3D server (configured separately)")
        
        print("="*80 + "\n")
    
    def check_system_requirements(self) -> bool:
        """Check system requirements for frontend services"""
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
            print("   Docker is required for frontend containers")
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
        
        # Check Docker Compose
        print("\n📍 Checking Docker Compose...")
        try:
            result = subprocess.run(['docker', 'compose', 'version'], capture_output=True, text=True)
            if result.returncode != 0:
                # Try older docker-compose command
                result = subprocess.run(['docker-compose', '--version'], capture_output=True, text=True)
                if result.returncode != 0:
                    print("❌ Docker Compose not found")
                    print("   Docker Compose is required for frontend services")
                    issues.append("Docker Compose not found")
                else:
                    print("✅ Docker Compose is available")
            else:
                print("✅ Docker Compose is available")
        except Exception as e:
            print(f"❌ Docker Compose error: {e}")
            issues.append(f"Docker Compose error: {e}")
        
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
            print("   Your system is ready for frontend setup.")
        
        return True
    
    def setup_python_environment(self) -> bool:
        """Set up Python environment for frontend services"""
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
        """Gather configuration for frontend services"""
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
        print(f"✅ Image server: {config['IMAGE_SERVER']}")
        
        # Vista3D server URL (remote)
        print("\n📍 Vista3D Server Configuration:")
        print("   The frontend will connect to a remote Vista3D server.")
        vista3d_url = input("Enter Vista3D server URL [http://localhost:8000]: ").strip() or "http://localhost:8000"
        config['VISTA3D_SERVER'] = vista3d_url
        print(f"✅ Vista3D server: {config['VISTA3D_SERVER']}")
        
        # Streamlit configuration
        config['STREAMLIT_SERVER_PORT'] = "8501"
        config['STREAMLIT_SERVER_ADDRESS'] = "0.0.0.0"
        print(f"✅ Streamlit port: {config['STREAMLIT_SERVER_PORT']}")
        
        return config
    
    def create_env_file(self, config: Dict) -> bool:
        """Create .env file for frontend services"""
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
                Path(config['OUTPUT_FOLDER'])
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
        print("🎉 FRONTEND SETUP COMPLETE!")
        print("="*80)
        
        print("\n📋 NEXT STEPS:")
        print("\n1. 🚀 Start frontend services:")
        print("   python start.py --frontend-only")
        print("   • This starts the web interface and image server")
        print("   • Services will run in Docker containers")
        
        print("\n2. 📁 Add your medical images:")
        print(f"   • Place DICOM files in: {config['DICOM_FOLDER']}")
        print("   • Or place NIFTI files in: output/nifti/")
        
        print("\n3. 🌐 Access the web interface:")
        print("   • Open your browser to: http://localhost:8501")
        print("   • Use the Tools page to convert DICOM to NIFTI")
        print("   • Use the Tools page to run AI segmentation (requires Vista3D server)")
        print("   • View 3D visualizations of your results")
        
        print(f"\n📄 Configuration saved to: {self.env_file}")
        print("🔗 Frontend configured to connect to Vista3D server: {config['VISTA3D_SERVER']}")
        
        print("\n⚠️  IMPORTANT NOTES:")
        print("• Make sure the Vista3D server is running and accessible")
        print("• If Vista3D server is not available, AI segmentation will not work")
        print("• You can still use the web interface for file management and visualization")
        
        print("\n" + "="*80)
    
    def run_setup(self) -> bool:
        """Run the complete frontend setup process"""
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
        description="HPE NVIDIA Vista3D - Frontend Setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script sets up the frontend services for the Vista3D platform.

Requirements:
  • Ubuntu Linux (18.04+) or macOS
  • 8GB+ RAM
  • Docker and Docker Compose
  • Internet connectivity

The setup will:
  1. Check system requirements
  2. Set up Python environment with dependencies
  3. Configure Docker containers for frontend services
  4. Create necessary directories and files
  5. Provide instructions for starting services

After setup, run 'python start.py --frontend-only' to start frontend services.
        """
    )
    
    args = parser.parse_args()
    
    setup = Vista3DFrontendSetup()
    
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
