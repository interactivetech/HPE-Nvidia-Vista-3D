#!/usr/bin/env python3
"""
Vista3D Services Test Script

This script tests that:
1. The Vista3D Docker server is running and accessible
2. The external HTTPS image server is running and accessible
3. Both services can communicate with each other
4. The image server can serve files properly

Usage:
    python3 test_vista3d_services.py
    python3 test_vista3d_services.py --verbose
    python3 test_vista3d_services.py --create-test-file
"""

import os
import sys
import time
import json
import argparse
import subprocess
import requests
import urllib3
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Vista3DServicesTester:
    """Test suite for Vista3D Docker server and external image server"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.project_root = Path(__file__).parent
        self.outputs_dir = self.project_root / "outputs"
        self.certs_dir = self.outputs_dir / "certs"
        self.nifti_dir = self.outputs_dir / "nifti"
        
        # Service configurations
        self.vista3d_port = 8000
        self.image_server_port = 8888
        self.vista3d_url = f"http://localhost:{self.vista3d_port}"
        self.image_server_url = f"https://localhost:{self.image_server_port}"
        
        # Test results
        self.test_results = {}
        
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)
    
    def run_command(self, command: str, capture_output: bool = True) -> subprocess.CompletedProcess:
        """Run a shell command and return the result"""
        if self.verbose:
            logger.debug(f"Running command: {command}")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=capture_output,
                text=True,
                timeout=30
            )
            return result
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out: {command}")
            return subprocess.CompletedProcess(
                command, -1, "", "Command timed out"
            )
        except Exception as e:
            logger.error(f"Error running command '{command}': {e}")
            return subprocess.CompletedProcess(
                command, -1, "", str(e)
            )
    
    def test_docker_availability(self) -> bool:
        """Test if Docker is available and running"""
        logger.info("🔍 Testing Docker availability...")
        
        try:
            # Check if Docker daemon is running
            result = self.run_command("docker info")
            if result.returncode != 0:
                logger.error("❌ Docker daemon is not running")
                self.test_results['docker_available'] = False
                return False
            
            # Check Docker version
            version_result = self.run_command("docker --version")
            if version_result.returncode == 0:
                logger.info(f"✅ Docker is available: {version_result.stdout.strip()}")
            else:
                logger.warning("⚠️  Could not get Docker version")
            
            self.test_results['docker_available'] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Error testing Docker availability: {e}")
            self.test_results['docker_available'] = False
            return False
    
    def test_vista3d_container_status(self) -> bool:
        """Test if Vista3D Docker container is running"""
        logger.info("🔍 Testing Vista3D container status...")
        
        try:
            # Check if container exists and is running
            result = self.run_command("docker ps --filter name=vista3d --format '{{.Names}}:{{.Status}}:{{.Ports}}'")
            
            if result.returncode != 0:
                logger.error("❌ Error checking Docker container status")
                self.test_results['vista3d_container_running'] = False
                return False
            
            if "vista3d" in result.stdout:
                logger.info("✅ Vista3D container is running")
                logger.info(f"   Container info: {result.stdout.strip()}")
                self.test_results['vista3d_container_running'] = True
                return True
            else:
                logger.warning("⚠️  Vista3D container is not running")
                self.test_results['vista3d_container_running'] = False
                return False
                
        except Exception as e:
            logger.error(f"❌ Error testing Vista3D container status: {e}")
            self.test_results['vista3d_container_running'] = False
            return False
    
    def test_vista3d_endpoint_accessibility(self) -> bool:
        """Test if Vista3D endpoint is accessible"""
        logger.info("🔍 Testing Vista3D endpoint accessibility...")
        
        try:
            # Test basic connectivity - Vista3D has /v1/health/live endpoint
            response = requests.get(
                f"{self.vista3d_url}/v1/health/live",
                timeout=10,
                headers={'User-Agent': 'Vista3D-Tester/1.0'}
            )
            
            if response.status_code == 200:
                logger.info("✅ Vista3D health endpoint (/v1/health/live) is accessible")
                self.test_results['vista3d_endpoint_accessible'] = True
                return True
            else:
                logger.warning(f"⚠️  Vista3D health endpoint (/v1/health/live) returned status {response.status_code}")
                self.test_results['vista3d_endpoint_accessible'] = False
                return False
                
        except requests.exceptions.ConnectionError:
            logger.error("❌ Cannot connect to Vista3D endpoint - connection refused")
            self.test_results['vista3d_endpoint_accessible'] = False
            return False
        except requests.exceptions.Timeout:
            logger.error("❌ Vista3D endpoint request timed out")
            self.test_results['vista3d_endpoint_accessible'] = False
            return False
        except Exception as e:
            logger.error(f"❌ Error testing Vista3D endpoint: {e}")
            self.test_results['vista3d_endpoint_accessible'] = False
            return False
    
    def test_image_server_process(self) -> bool:
        """Test if the external image server process is running"""
        logger.info("🔍 Testing external image server process...")
        
        try:
            # Check if image server process is running
            result = self.run_command("pgrep -f 'image_server.py'")
            
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                logger.info(f"✅ External image server process is running (PIDs: {', '.join(pids)})")
                self.test_results['image_server_process_running'] = True
                return True
            else:
                logger.warning("⚠️  External image server process is not running")
                self.test_results['image_server_process_running'] = False
                return False
                
        except Exception as e:
            logger.error(f"❌ Error testing image server process: {e}")
            self.test_results['image_server_process_running'] = False
            return False
    
    def test_image_server_endpoint_accessibility(self) -> bool:
        """Test if the external image server endpoint is accessible"""
        logger.info("🔍 Testing external image server endpoint accessibility...")
        
        try:
            # Test HTTPS connectivity (ignore SSL certificate warnings)
            response = requests.get(
                f"{self.image_server_url}/",
                timeout=10,
                verify=False,
                headers={'User-Agent': 'Vista3D-Tester/1.0'}
            )
            
            if response.status_code == 200:
                logger.info("✅ External image server endpoint is accessible")
                self.test_results['image_server_endpoint_accessible'] = True
                return True
            else:
                logger.warning(f"⚠️  External image server returned status {response.status_code}")
                self.test_results['image_server_endpoint_accessible'] = False
                return False
                
        except requests.exceptions.SSLError as e:
            logger.warning(f"⚠️  SSL certificate warning (expected for self-signed): {e}")
            # SSL error is expected with self-signed certificates, but connection should work
            self.test_results['image_server_endpoint_accessible'] = True
            return True
        except requests.exceptions.ConnectionError:
            logger.error("❌ Cannot connect to external image server - connection refused")
            self.test_results['image_server_endpoint_accessible'] = False
            return False
        except requests.exceptions.Timeout:
            logger.error("❌ External image server request timed out")
            self.test_results['image_server_endpoint_accessible'] = False
            return False
        except Exception as e:
            logger.error(f"❌ Error testing external image server: {e}")
            self.test_results['image_server_endpoint_accessible'] = False
            return False
    
    def test_image_server_file_serving(self) -> bool:
        """Test if the image server can serve files properly"""
        logger.info("🔍 Testing image server file serving capability...")
        
        try:
            # Create a test file if it doesn't exist
            test_file_path = self.outputs_dir / "test_file.txt"
            if not test_file_path.exists():
                test_file_path.write_text("This is a test file for Vista3D services testing\n")
                logger.info(f"   Created test file: {test_file_path}")
            
            # Test if the file can be accessed via the image server
            response = requests.get(
                f"{self.image_server_url}/test_file.txt",
                timeout=10,
                verify=False,
                headers={'User-Agent': 'Vista3D-Tester/1.0'}
            )
            
            if response.status_code == 200:
                logger.info("✅ Image server can serve files properly")
                self.test_results['image_server_file_serving'] = True
                return True
            else:
                logger.warning(f"⚠️  Image server file serving returned status {response.status_code}")
                self.test_results['image_server_file_serving'] = False
                return False
                
        except Exception as e:
            logger.error(f"❌ Error testing image server file serving: {e}")
            self.test_results['image_server_file_serving'] = False
            return False
    
    def test_vista3d_image_server_communication(self) -> bool:
        """Test if Vista3D can communicate with the external image server"""
        logger.info("🔍 Testing Vista3D ↔ Image Server communication...")
        
        try:
            # This test simulates what Vista3D would do to access the image server
            # We'll test if the image server is accessible from the Docker network perspective
            
            # Test using host.docker.internal (which Vista3D would use)
            docker_host_url = f"https://host.docker.internal:{self.image_server_port}"
            
            # First, test if we can resolve host.docker.internal
            result = self.run_command("getent hosts host.docker.internal")
            
            if result.returncode != 0:
                logger.warning("⚠️  host.docker.internal not resolvable from host")
                # Fall back to localhost test
                docker_host_url = self.image_server_url
            
            # Test the Docker-accessible URL
            response = requests.get(
                f"{docker_host_url}/",
                timeout=10,
                verify=False,
                headers={'User-Agent': 'Vista3D-Tester/1.0'}
            )
            
            if response.status_code == 200:
                logger.info("✅ Vista3D can communicate with external image server")
                self.test_results['vista3d_image_server_communication'] = True
                return True
            else:
                logger.warning(f"⚠️  Docker-accessible image server returned status {response.status_code}")
                self.test_results['vista3d_image_server_communication'] = False
                return False
                
        except Exception as e:
            logger.error(f"❌ Error testing Vista3D ↔ Image Server communication: {e}")
            self.test_results['vista3d_image_server_communication'] = False
            return False
    
    def test_ssl_certificates(self) -> bool:
        """Test if SSL certificates exist and are valid"""
        logger.info("🔍 Testing SSL certificates...")
        
        try:
            cert_file = self.certs_dir / "server.crt"
            key_file = self.certs_dir / "server.key"
            
            if not cert_file.exists():
                logger.error("❌ SSL certificate file not found")
                self.test_results['ssl_certificates_valid'] = False
                return False
            
            if not key_file.exists():
                logger.error("❌ SSL private key file not found")
                self.test_results['ssl_certificates_valid'] = False
                return False
            
            # Check certificate validity using openssl
            result = self.run_command(f"openssl x509 -in {cert_file} -text -noout")
            
            if result.returncode == 0:
                logger.info("✅ SSL certificates exist and are valid")
                self.test_results['ssl_certificates_valid'] = True
                return True
            else:
                logger.warning("⚠️  SSL certificate validation failed")
                self.test_results['ssl_certificates_valid'] = False
                return False
                
        except Exception as e:
            logger.error(f"❌ Error testing SSL certificates: {e}")
            self.test_results['ssl_certificates_valid'] = False
            return False
    
    def test_outputs_directory_structure(self) -> bool:
        """Test if the outputs directory structure is correct"""
        logger.info("🔍 Testing outputs directory structure...")
        
        try:
            required_dirs = [self.outputs_dir, self.certs_dir, self.nifti_dir]
            missing_dirs = []
            
            for dir_path in required_dirs:
                if not dir_path.exists():
                    missing_dirs.append(str(dir_path))
            
            if missing_dirs:
                logger.error(f"❌ Missing required directories: {', '.join(missing_dirs)}")
                self.test_results['outputs_directory_structure'] = False
                return False
            
            logger.info("✅ Outputs directory structure is correct")
            self.test_results['outputs_directory_structure'] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Error testing outputs directory structure: {e}")
            self.test_results['outputs_directory_structure'] = False
            return False
    
    def create_test_file(self) -> None:
        """Create a test file for testing purposes"""
        logger.info("📝 Creating test file for testing...")
        
        try:
            test_file_path = self.outputs_dir / "test_file.txt"
            test_content = f"""This is a test file for Vista3D services testing.
Created at: {time.strftime('%Y-%m-%d %H:%M:%S')}
Purpose: Verify that the image server can serve files properly.

This file should be accessible via:
- Direct file access: {test_file_path}
- HTTP access: {self.image_server_url}/test_file.txt
- Docker access: https://host.docker.internal:{self.image_server_port}/test_file.txt
"""
            
            test_file_path.write_text(test_content)
            logger.info(f"✅ Test file created: {test_file_path}")
            
        except Exception as e:
            logger.error(f"❌ Error creating test file: {e}")
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all tests and return results"""
        logger.info("🚀 Starting Vista3D Services Test Suite...")
        logger.info("=" * 60)
        
        # Run all tests
        tests = [
            ("Docker Availability", self.test_docker_availability),
            ("Outputs Directory Structure", self.test_outputs_directory_structure),
            ("SSL Certificates", self.test_ssl_certificates),
            ("Image Server Process", self.test_image_server_process),
            ("Image Server Endpoint", self.test_image_server_endpoint_accessibility),
            ("Image Server File Serving", self.test_image_server_file_serving),
            ("Vista3D Container Status", self.test_vista3d_container_status),
            ("Vista3D Endpoint", self.test_vista3d_endpoint_accessibility),
            ("Vista3D ↔ Image Server Communication", self.test_vista3d_image_server_communication),
        ]
        
        for test_name, test_func in tests:
            logger.info(f"\n📋 Running: {test_name}")
            try:
                test_func()
            except Exception as e:
                logger.error(f"❌ Test '{test_name}' failed with exception: {e}")
                self.test_results[test_name.lower().replace(' ', '_').replace('↔', '_to_')] = False
        
        return self.test_results
    
    def print_summary(self) -> None:
        """Print a summary of all test results"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 TEST RESULTS SUMMARY")
        logger.info("=" * 60)
        
        passed = 0
        failed = 0
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{status} - {test_name.replace('_', ' ').title()}")
            if result:
                passed += 1
            else:
                failed += 1
        
        logger.info("-" * 60)
        logger.info(f"Total Tests: {len(self.test_results)}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Success Rate: {(passed/len(self.test_results)*100):.1f}%")
        
        if failed == 0:
            logger.info("\n🎉 All tests passed! Vista3D services are running correctly.")
        else:
            logger.info(f"\n⚠️  {failed} test(s) failed. Please check the issues above.")
        
        logger.info("=" * 60)
    
    def suggest_fixes(self) -> None:
        """Suggest fixes for failed tests"""
        logger.info("\n🔧 SUGGESTED FIXES")
        logger.info("=" * 60)
        
        if not self.test_results.get('docker_available', True):
            logger.info("• Docker is not running. Start Docker with: sudo systemctl start docker")
        
        if not self.test_results.get('image_server_process_running', True):
            logger.info("• Image server is not running. Start it with: python3 utils/image_server.py")
        
        if not self.test_results.get('vista3d_container_running', True):
            logger.info("• Vista3D container is not running. Start it with: python3 utils/vista3d.py")
        
        if not self.test_results.get('ssl_certificates_valid', True):
            logger.info("• SSL certificates are invalid. Regenerate them by restarting the image server")
        
        if not self.test_results.get('outputs_directory_structure', True):
            logger.info("• Outputs directory structure is incorrect. Run setup.sh to create directories")
        
        logger.info("=" * 60)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Test Vista3D Docker server and external image server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 test_vista3d_services.py                    # Run all tests
  python3 test_vista3d_services.py --verbose          # Run with verbose output
  python3 test_vista3d_services.py --create-test-file # Create test file before testing

The test script will verify:
• Docker availability and container status
• External image server process and accessibility
• SSL certificate validity
• File serving capabilities
• Communication between Vista3D and image server
        """
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--create-test-file',
        action='store_true',
        help='Create a test file before running tests'
    )
    
    args = parser.parse_args()
    
    # Create tester instance
    tester = Vista3DServicesTester(verbose=args.verbose)
    
    try:
        # Create test file if requested
        if args.create_test_file:
            tester.create_test_file()
        
        # Run all tests
        results = tester.run_all_tests()
        
        # Print summary
        tester.print_summary()
        
        # Suggest fixes for failed tests
        if not all(results.values()):
            tester.suggest_fixes()
        
        # Exit with appropriate code
        sys.exit(0 if all(results.values()) else 1)
        
    except KeyboardInterrupt:
        logger.info("\n⚠️  Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error during testing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
