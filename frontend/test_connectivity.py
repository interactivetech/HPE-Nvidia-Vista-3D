#!/usr/bin/env python3
"""
Vista3D Connectivity Test Script

This script tests all the connections needed for Vista3D to work:
1. Frontend -> Vista3D Backend (Mac -> Ubuntu via SSH tunnel)
2. Vista3D Backend -> Image Server (Ubuntu -> Mac via reverse SSH tunnel)
3. Image files are accessible

Run this instead of full segmentation to diagnose issues quickly.
"""

import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(70)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")

def test_environment_variables():
    """Test that all required environment variables are set"""
    print_header("Test 1: Environment Variables")
    
    load_dotenv()
    
    vars_to_check = {
        'VISTA3D_SERVER': os.getenv('VISTA3D_SERVER'),
        'VISTA3D_IMAGE_SERVER_URL': os.getenv('VISTA3D_IMAGE_SERVER_URL'),
        'IMAGE_SERVER': os.getenv('IMAGE_SERVER'),
        'OUTPUT_FOLDER': os.getenv('OUTPUT_FOLDER'),
    }
    
    all_ok = True
    for var_name, var_value in vars_to_check.items():
        if var_value:
            print_success(f"{var_name} = {var_value}")
        else:
            print_error(f"{var_name} is not set!")
            all_ok = False
    
    return all_ok

def test_frontend_to_backend():
    """Test if frontend can reach Vista3D backend"""
    print_header("Test 2: Frontend -> Vista3D Backend")
    
    vista3d_server = os.getenv('VISTA3D_SERVER', 'http://localhost:8000')
    info_url = f"{vista3d_server}/v1/vista3d/info"
    
    print_info(f"Testing connection to: {info_url}")
    
    try:
        response = requests.get(info_url, timeout=10)
        if response.status_code == 200:
            print_success(f"Backend is reachable! Status: {response.status_code}")
            data = response.json()
            print_info(f"Backend version: {data.get('version', 'unknown')}")
            print_info(f"Available labels: {len(data.get('labels', {}))} labels")
            return True
        else:
            print_error(f"Backend returned error: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError as e:
        print_error(f"Cannot connect to backend: {e}")
        print_warning("Check: Is SSH tunnel running? (ssh -L 8000:localhost:8000 ...)")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_image_server_local():
    """Test if image server is accessible locally"""
    print_header("Test 3: Local Image Server")
    
    image_server = os.getenv('IMAGE_SERVER', 'http://localhost:8888')
    health_url = f"{image_server}/health"
    
    print_info(f"Testing connection to: {health_url}")
    
    try:
        response = requests.get(health_url, timeout=5)
        if response.status_code == 200:
            print_success(f"Image server is reachable! Status: {response.status_code}")
            return True
        else:
            print_error(f"Image server returned error: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError as e:
        print_error(f"Cannot connect to image server: {e}")
        print_warning("Check: Is image server container running? (docker ps)")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_backend_to_image_server():
    """Test if Vista3D backend can reach image server (critical test!)"""
    print_header("Test 4: Backend -> Image Server (CRITICAL)")
    
    vista3d_server = os.getenv('VISTA3D_SERVER', 'http://localhost:8000')
    vista3d_image_server_url = os.getenv('VISTA3D_IMAGE_SERVER_URL', 'http://localhost:8888')
    output_folder = os.getenv('OUTPUT_FOLDER', '/app/output')
    
    print_info(f"Vista3D will try to fetch images from: {vista3d_image_server_url}")
    print_info(f"This should work via SSH reverse tunnel: -R 8888:0.0.0.0:8888")
    
    # Find a test NIfTI file
    output_path = Path(output_folder)
    nifti_files = list(output_path.glob('*/nifti/*.nii.gz'))
    
    if not nifti_files:
        print_warning("No NIfTI files found to test with")
        print_info(f"Searched in: {output_path}")
        return None
    
    test_file = nifti_files[0]
    relative_path = test_file.relative_to(output_path)
    test_image_url = f"{vista3d_image_server_url}/output/{relative_path}"
    
    print_info(f"Test file: {test_file.name}")
    print_info(f"Image URL that backend will use: {test_image_url}")
    
    # Test inference with this image
    inference_url = f"{vista3d_server}/v1/vista3d/inference"
    payload = {
        "image": test_image_url,
        "prompts": {"labels": ["liver"]}  # Just test with one label
    }
    
    print_info("Sending test inference request to backend...")
    
    try:
        response = requests.post(inference_url, json=payload, timeout=30)
        if response.status_code == 200:
            print_success("Backend successfully fetched the image!")
            print_success("The reverse SSH tunnel is working correctly!")
            return True
        else:
            print_error(f"Backend inference failed: {response.status_code}")
            try:
                error_detail = response.json()
                print_error(f"Error details: {error_detail}")
                
                # Check for specific image fetch errors
                error_msg = str(error_detail.get('error', ''))
                if 'Failed to fetch image' in error_msg:
                    print_error("\n🚨 PROBLEM FOUND:")
                    print_error("Backend cannot fetch images from image server!")
                    print_warning("\nPossible causes:")
                    print_warning("1. SSH reverse tunnel not working: -R 8888:0.0.0.0:8888")
                    print_warning("2. Image server not accessible from Ubuntu server")
                    print_warning("3. VISTA3D_IMAGE_SERVER_URL is incorrect")
                    
                    if 'host.docker.internal' in error_msg:
                        print_error("\n❌ Backend is using 'host.docker.internal' - this won't work on Ubuntu!")
                        print_info("Fix: Set VISTA3D_IMAGE_SERVER_URL=http://localhost:8888")
                    elif 'Connection refused' in error_msg:
                        print_error("\n❌ Backend cannot connect to the image server")
                        print_info("Fix: Check SSH reverse tunnel is running")
            except:
                print_error(f"Response: {response.text[:500]}")
            return False
    except requests.exceptions.ConnectionError as e:
        print_error(f"Cannot connect to backend: {e}")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_ssh_tunnel():
    """Check if SSH tunnel appears to be running"""
    print_header("Test 5: SSH Tunnel Check")
    
    import subprocess
    
    try:
        result = subprocess.run(
            "ps aux | grep 'ssh.*8000.*8888' | grep -v grep",
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0 and result.stdout:
            print_success("SSH tunnel process found:")
            for line in result.stdout.strip().split('\n'):
                print_info(f"  {line}")
            
            # Check if ports are actually listening
            result2 = subprocess.run(
                "lsof -nP -iTCP:8000 -sTCP:LISTEN 2>/dev/null",
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result2.returncode == 0 and result2.stdout:
                print_success("Port 8000 is listening (forward tunnel working)")
            else:
                print_warning("Port 8000 not listening - forward tunnel may not be active")
            
            return True
        else:
            print_error("No SSH tunnel process found!")
            print_info("Expected command: ssh -L 8000:localhost:8000 -R 8888:0.0.0.0:8888 user@server")
            return False
    except Exception as e:
        print_warning(f"Could not check SSH tunnel: {e}")
        return None

def test_file_accessibility():
    """Test if NIfTI files are accessible via image server"""
    print_header("Test 6: File Accessibility via Image Server")
    
    image_server = os.getenv('IMAGE_SERVER', 'http://localhost:8888')
    output_folder = os.getenv('OUTPUT_FOLDER', '/app/output')
    
    output_path = Path(output_folder)
    nifti_files = list(output_path.glob('*/nifti/*.nii.gz'))
    
    if not nifti_files:
        print_warning("No NIfTI files found to test")
        return None
    
    test_file = nifti_files[0]
    relative_path = test_file.relative_to(output_path)
    file_url = f"{image_server}/output/{relative_path}"
    
    print_info(f"Testing file access: {file_url}")
    
    try:
        response = requests.head(file_url, timeout=5)
        if response.status_code == 200:
            print_success(f"File is accessible! Size: {response.headers.get('content-length', 'unknown')} bytes")
            return True
        else:
            print_error(f"File not accessible: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error accessing file: {e}")
        return False

def main():
    print(f"\n{Colors.BOLD}{'='*70}")
    print(f"Vista3D Connectivity Test Script")
    print(f"{'='*70}{Colors.END}\n")
    
    print_info("This script tests all connections needed for Vista3D segmentation")
    print_info("Run this to diagnose issues quickly without running full segmentation\n")
    
    results = {}
    
    # Run all tests
    results['env_vars'] = test_environment_variables()
    results['frontend_to_backend'] = test_frontend_to_backend()
    results['image_server_local'] = test_image_server_local()
    results['backend_to_image_server'] = test_backend_to_image_server()
    results['ssh_tunnel'] = test_ssh_tunnel()
    results['file_access'] = test_file_accessibility()
    
    # Summary
    print_header("SUMMARY")
    
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)
    
    print(f"\nTests: {Colors.GREEN}{passed} passed{Colors.END}, "
          f"{Colors.RED}{failed} failed{Colors.END}, "
          f"{Colors.YELLOW}{skipped} skipped{Colors.END}\n")
    
    if failed == 0 and passed > 0:
        print_success("✅ ALL TESTS PASSED! Vista3D should work correctly.")
    else:
        print_error("❌ SOME TESTS FAILED. Fix the issues above before running segmentation.")
        print_info("\nQuick fixes:")
        if not results['ssh_tunnel']:
            print_info("  • Start SSH tunnel: ssh -L 8000:localhost:8000 -R 8888:0.0.0.0:8888 user@server")
        if not results['frontend_to_backend']:
            print_info("  • Check backend is running on Ubuntu server")
        if not results['backend_to_image_server']:
            print_info("  • Verify VISTA3D_IMAGE_SERVER_URL=http://localhost:8888 (not host.docker.internal)")
            print_info("  • Check reverse SSH tunnel: -R 8888:0.0.0.0:8888")
        if not results['image_server_local']:
            print_info("  • Check image server container: docker ps")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

