#!/usr/bin/env python3
"""
Image Server Test Utility

This script tests the image server found in .env and displays all directories 
and files being served.
"""

import os
import requests
import json
from pathlib import Path
from dotenv import load_dotenv
import re
from urllib.parse import urljoin
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def load_config():
    """Load configuration from .env file"""
    load_dotenv()
    image_server_url = os.getenv('IMAGE_SERVER', 'https://localhost:8888')
    return image_server_url

def test_server_connectivity(base_url):
    """Test if the image server is accessible"""
    try:
        response = requests.get(base_url, verify=False, timeout=10)
        print(f"✅ Server is accessible at {base_url}")
        print(f"   Status: {response.status_code}")
        print(f"   Server: {response.headers.get('server', 'Unknown')}")
        return True
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to server at {base_url}")
        return False
    except Exception as e:
        print(f"❌ Error connecting to server: {e}")
        return False

def parse_directory_listing(html_content):
    """Parse HTML directory listing to extract folders and files"""
    folders = []
    files = []
    
    # Look for directory links (ending with /)
    folder_patterns = [
        r'<a[^>]*href="([^"]+)/"[^>]*>([^<]+)/?</a>',
        r'href="([^"]+)/"[^>]*>([^<]+)</a>',
        r'📁\s*<a[^>]*href="([^"]+)/"[^>]*>([^<]+)</a>'
    ]
    
    for pattern in folder_patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        for href, display_name in matches:
            if href not in ['.', '..', '../'] and not href.startswith('/'):
                folder_name = href.rstrip('/')
                if folder_name and folder_name not in folders:
                    folders.append(folder_name)
    
    # Look for file links (not ending with /)
    file_patterns = [
        r'<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>',
        r'📄\s*<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>'
    ]
    
    for pattern in file_patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        for href, display_name in matches:
            if (not href.startswith('/') and 
                href not in ['.', '..'] and 
                not href.endswith('/') and
                '.' in href and
                href not in files):
                files.append(href)
    
    return sorted(folders), sorted(files)

def get_directory_contents(base_url, path=""):
    """Get contents of a directory from the server"""
    url = urljoin(base_url.rstrip('/') + '/', path.lstrip('/'))
    if not url.endswith('/'):
        url += '/'
    
    try:
        response = requests.get(url, verify=False, timeout=10)
        
        if response.status_code == 200:
            # Check if it's HTML content (directory listing)
            if 'text/html' in response.headers.get('content-type', ''):
                folders, files = parse_directory_listing(response.text)
                return folders, files, None
            else:
                return [], [], "Not a directory listing"
                
        elif response.status_code == 404:
            return [], [], "Directory not found"
        else:
            return [], [], f"HTTP {response.status_code}"
            
    except Exception as e:
        return [], [], f"Error: {e}"

def explore_directory_tree(base_url, path="", depth=0, max_depth=4):
    """Recursively explore directory structure"""
    if depth > max_depth:
        return
    
    indent = "  " * depth
    folders, files, error = get_directory_contents(base_url, path)
    
    if error:
        if depth == 0:
            print(f"❌ Root directory: {error}")
        return
    
    # Print current directory
    current_dir = f"/{path}" if path else "/"
    if depth == 0:
        print(f"📁 Root Directory: {current_dir}")
    else:
        print(f"{indent}📁 {path.split('/')[-1]}/")
    
    # Print files in current directory
    if files:
        for file in files:
            file_path = f"{path}/{file}" if path else file
            print(f"{indent}  📄 {file}")
    
    # Print directories and explore them
    if folders:
        for folder in folders:
            new_path = f"{path}/{folder}" if path else folder
            explore_directory_tree(base_url, new_path, depth + 1, max_depth)

def test_medical_imaging_paths(base_url):
    """Test specific paths for medical imaging files"""
    print(f"\n🏥 Checking medical imaging directories:")
    print("-" * 50)
    
    medical_paths = [
        "outputs",
        "outputs/nifti", 
        "outputs/segments",
        "conf"
    ]
    
    found_any = False
    
    for path in medical_paths:
        folders, files, error = get_directory_contents(base_url, path)
        
        if not error:
            print(f"✅ /{path}:")
            if folders:
                print(f"   📁 Folders: {', '.join(folders)}")
                # Check patient folders for medical files
                for folder in folders:
                    patient_path = f"{path}/{folder}"
                    patient_folders, patient_files, patient_error = get_directory_contents(base_url, patient_path)
                    if not patient_error and patient_files:
                        medical_files = [f for f in patient_files if any(ext in f.lower() for ext in ['.nii', '.dcm', '.nrrd'])]
                        if medical_files:
                            print(f"     🏥 {folder}/: {len(medical_files)} medical files")
                            found_any = True
            if files:
                medical_files = [f for f in files if any(ext in f.lower() for ext in ['.nii', '.dcm', '.nrrd', '.json'])]
                if medical_files:
                    print(f"   🏥 Medical files: {', '.join(medical_files)}")
                    found_any = True
                else:
                    print(f"   📄 Files: {', '.join(files[:3])}{' (+more)' if len(files) > 3 else ''}")
        else:
            print(f"❌ /{path}: {error}")
    
    if not found_any:
        print(f"\n💡 No medical imaging files found. Consider creating:")
        print(f"   mkdir -p outputs/nifti/PA00001 outputs/segments/PA00001")

def main():
    """Main function to test image server and list contents"""
    print("🔬 Image Server Directory Listing")
    print("=" * 50)
    
    # Load configuration
    base_url = load_config()
    print(f"Image Server: {base_url}")
    print()
    
    # Test server connectivity
    if not test_server_connectivity(base_url):
        print("\n💡 Make sure the image server is running:")
        print("   python utils/image_server.py")
        return
    
    print(f"\n🗂️  Complete Directory Structure:")
    print("=" * 40)
    
    # Explore the complete directory tree
    explore_directory_tree(base_url)
    
    # Test medical imaging specific paths
    test_medical_imaging_paths(base_url)
    
    print(f"\n✅ Directory listing complete!")
    print(f"🌐 Access the server at: {base_url}")

if __name__ == "__main__":
    main()