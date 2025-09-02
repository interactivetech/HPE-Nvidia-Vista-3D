#!/usr/bin/env python3
"""
Image Server Test Utility

This script tests the image server connectivity and lists the folder structure
of files being served. It reads configuration from the .env file and provides
detailed information about what directories and files are available.
"""

import os
import sys
import requests
import json
from pathlib import Path
from dotenv import load_dotenv
import re
from urllib.parse import urljoin, urlparse
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def load_config():
    """Load configuration from .env file"""
    # Load environment variables
    load_dotenv()
    
    # Get image server URL from environment
    image_server_url = os.getenv('IMAGE_SERVER', 'https://localhost:8888')
    project_root = os.getenv('PROJECT_ROOT', '.')
    
    return {
        'image_server_url': image_server_url,
        'project_root': project_root
    }

def test_server_connectivity(base_url):
    """Test basic connectivity to the image server"""
    print(f"Testing connectivity to: {base_url}")
    print("-" * 50)
    
    try:
        # Test basic connectivity
        response = requests.get(base_url, verify=False, timeout=10)
        print(f"✅ Server is reachable")
        print(f"   Status Code: {response.status_code}")
        print(f"   Server: {response.headers.get('server', 'Unknown')}")
        print(f"   Content-Type: {response.headers.get('content-type', 'Unknown')}")
        
        # Check if it's FastAPI
        if response.headers.get('server', '').lower() == 'uvicorn':
            print(f"   🔍 Detected FastAPI/Uvicorn server")
            
            # Try to access docs
            docs_url = urljoin(base_url, '/docs')
            docs_response = requests.get(docs_url, verify=False, timeout=5)
            if docs_response.status_code == 200:
                print(f"   📚 FastAPI docs available at: {docs_url}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to server at {base_url}")
        print(f"   Make sure the image server is running")
        return False
    except requests.exceptions.Timeout:
        print(f"⏰ Connection timeout to {base_url}")
        return False
    except Exception as e:
        print(f"❌ Error connecting to server: {e}")
        return False

def parse_directory_listing(html_content):
    """Parse HTML directory listing to extract folders and files"""
    folders = []
    files = []
    
    # Common patterns for directory listings
    patterns = [
        # Standard Apache/Nginx directory listing
        r'<a href="([^"]+)/"[^>]*>([^<]+)/?</a>',
        # Alternative pattern
        r'href="([^"]+)/"[^>]*>([^<]+)</a>',
        # FastAPI StaticFiles pattern
        r'<a[^>]*href="([^"]+)/"[^>]*>([^<]+)</a>'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        for href, display_name in matches:
            if href not in ['.', '..', '../'] and not href.startswith('/'):
                folder_name = href.rstrip('/')
                if folder_name and folder_name not in folders:
                    folders.append(folder_name)
    
    # Look for files
    file_patterns = [
        r'<a href="([^"]+\.[^"]+)"[^>]*>([^<]+)</a>',
        r'href="([^"]+\.[^"]+)"[^>]*>([^<]+)</a>'
    ]
    
    for pattern in file_patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        for href, display_name in matches:
            if not href.startswith('/') and href not in ['.', '..'] and '/' not in href:
                if href not in files:
                    files.append(href)
    
    return sorted(folders), sorted(files)

def explore_directory(base_url, path=""):
    """Explore a directory on the server and return its contents"""
    url = urljoin(base_url.rstrip('/') + '/', path.lstrip('/'))
    if not url.endswith('/'):
        url += '/'
    
    try:
        response = requests.get(url, verify=False, timeout=10)
        
        if response.status_code == 200:
            # Check if it's a JSON error response
            if response.headers.get('content-type', '').startswith('application/json'):
                try:
                    json_data = response.json()
                    if 'detail' in json_data:
                        return None, None, f"Server error: {json_data['detail']}"
                except:
                    pass
            
            # Parse HTML directory listing
            folders, files = parse_directory_listing(response.text)
            return folders, files, None
            
        elif response.status_code == 404:
            return None, None, "Directory not found"
        else:
            return None, None, f"HTTP {response.status_code}"
            
    except Exception as e:
        return None, None, f"Error: {e}"

def explore_server_structure(base_url, max_depth=3):
    """Recursively explore the server structure"""
    print(f"\n🔍 Exploring server structure at: {base_url}")
    print("=" * 60)
    
    def explore_recursive(path="", depth=0, prefix=""):
        if depth > max_depth:
            return
        
        indent = "  " * depth
        folders, files, error = explore_directory(base_url, path)
        
        if error:
            print(f"{indent}{prefix}❌ {path or '/'}: {error}")
            return
        
        # Print current directory
        current_dir = path or "/"
        print(f"{indent}{prefix}📁 {current_dir}")
        
        # Print files in current directory
        if files:
            for file in files:
                print(f"{indent}  📄 {file}")
        
        # Recursively explore subdirectories
        if folders:
            for i, folder in enumerate(folders):
                is_last = i == len(folders) - 1
                folder_prefix = "└── " if is_last else "├── "
                new_path = f"{path.rstrip('/')}/{folder}" if path else folder
                explore_recursive(new_path, depth + 1, folder_prefix)
    
    explore_recursive()

def test_direct_file_access(base_url):
    """Test direct access to known files"""
    print(f"\n📋 Testing direct file access")
    print("-" * 35)
    
    # Test files that should exist based on project structure
    test_files = [
        "conf/label_dict.json",
        "conf/label_colors.json", 
        "conf/model_info.json",
        "assets/niivue.umd.js",
        "assets/z_script.js",
        "README.md",
        "pyproject.toml",
        "app.py"
    ]
    
    accessible_files = []
    
    for file_path in test_files:
        try:
            file_url = urljoin(base_url.rstrip('/') + '/', file_path)
            response = requests.get(file_url, verify=False, timeout=5)
            
            if response.status_code == 200:
                file_size = len(response.content)
                content_type = response.headers.get('content-type', 'unknown')
                print(f"✅ {file_path} ({file_size} bytes, {content_type})")
                accessible_files.append(file_path)
            elif response.status_code == 404:
                print(f"❌ {file_path}: Not found")
            else:
                print(f"⚠️  {file_path}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ {file_path}: Error - {e}")
    
    return accessible_files

def scan_local_filesystem(project_root):
    """Scan the local filesystem to see what should be served"""
    print(f"\n💾 Local filesystem scan")
    print("-" * 30)
    
    project_path = Path(project_root).resolve()
    
    if not project_path.exists():
        print(f"❌ Project root not found: {project_path}")
        return []
    
    print(f"📁 Scanning: {project_path}")
    
    all_files = []
    important_dirs = ['outputs', 'conf', 'assets', 'pages', 'utils', 'docs']
    
    # Scan important directories
    for dir_name in important_dirs:
        dir_path = project_path / dir_name
        if dir_path.exists():
            files_in_dir = []
            for file_path in dir_path.rglob('*'):
                if file_path.is_file():
                    rel_path = file_path.relative_to(project_path)
                    files_in_dir.append(str(rel_path))
                    all_files.append(str(rel_path))
            
            print(f"  📁 {dir_name}/: {len(files_in_dir)} files")
            if files_in_dir:
                # Show first few files as examples
                examples = files_in_dir[:3]
                more = f" (+{len(files_in_dir)-3} more)" if len(files_in_dir) > 3 else ""
                for example in examples:
                    print(f"     📄 {example}")
                if more:
                    print(f"     {more}")
        else:
            print(f"  ❌ {dir_name}/: Directory not found")
    
    # Scan root files
    root_files = [f for f in project_path.iterdir() if f.is_file()]
    print(f"  📄 Root files: {len(root_files)}")
    for file_path in root_files[:5]:  # Show first 5
        rel_path = file_path.relative_to(project_path)
        print(f"     📄 {rel_path}")
        all_files.append(str(rel_path))
    
    if len(root_files) > 5:
        print(f"     (+{len(root_files)-5} more)")
    
    return all_files

def test_server_vs_filesystem(base_url, project_root):
    """Compare what's accessible via server vs what exists locally"""
    print(f"\n🔍 Server vs Filesystem comparison")
    print("-" * 45)
    
    # Get local files
    local_files = scan_local_filesystem(project_root)
    
    # Test a sample of local files on the server
    sample_files = local_files[:20]  # Test first 20 files
    accessible_count = 0
    
    print(f"\n🧪 Testing {len(sample_files)} sample files on server:")
    
    for file_path in sample_files:
        try:
            file_url = urljoin(base_url.rstrip('/') + '/', file_path)
            response = requests.get(file_url, verify=False, timeout=3)
            
            if response.status_code == 200:
                print(f"  ✅ {file_path}")
                accessible_count += 1
            else:
                print(f"  ❌ {file_path} (HTTP {response.status_code})")
                
        except Exception:
            print(f"  ❌ {file_path} (Connection error)")
    
    print(f"\n📊 Summary:")
    print(f"  Local files found: {len(local_files)}")
    print(f"  Sample tested: {len(sample_files)}")
    print(f"  Accessible via server: {accessible_count}")
    
    if accessible_count > 0:
        print(f"  ✅ Server is serving files from the project directory")
    else:
        print(f"  ❌ Server may not be configured correctly")

def test_common_paths(base_url):
    """Test common paths that might exist on the server"""
    print(f"\n🧪 Testing common paths (directory listings)")
    print("-" * 50)
    
    common_paths = [
        "",  # Root
        "outputs",
        "outputs/nifti",
        "outputs/segments", 
        "conf",
        "assets",
        "docs",
        "utils",
        "pages"
    ]
    
    for path in common_paths:
        folders, files, error = explore_directory(base_url, path)
        
        if error:
            print(f"❌ /{path}: {error}")
        else:
            folder_count = len(folders) if folders else 0
            file_count = len(files) if files else 0
            print(f"✅ /{path}: {folder_count} folders, {file_count} files")
            
            # Show first few items as examples
            if folders:
                example_folders = folders[:3]
                more = f" (+{len(folders)-3} more)" if len(folders) > 3 else ""
                print(f"   📁 Folders: {', '.join(example_folders)}{more}")
            
            if files:
                example_files = files[:3]
                more = f" (+{len(files)-3} more)" if len(files) > 3 else ""
                print(f"   📄 Files: {', '.join(example_files)}{more}")

def test_medical_imaging_files(base_url):
    """Look specifically for medical imaging files"""
    print(f"\n🏥 Searching for medical imaging files")
    print("-" * 40)
    
    search_paths = ["outputs/nifti", "outputs/segments", "outputs", ""]
    medical_extensions = ['.nii', '.nii.gz', '.dcm', '.nrrd']
    
    found_files = []
    
    for search_path in search_paths:
        folders, files, error = explore_directory(base_url, search_path)
        
        if not error and files:
            for file in files:
                for ext in medical_extensions:
                    if file.lower().endswith(ext.lower()):
                        full_path = f"{search_path}/{file}" if search_path else file
                        found_files.append((full_path, ext))
                        break
        
        # Also check subdirectories for patient folders
        if not error and folders:
            for folder in folders:
                subfolder_path = f"{search_path}/{folder}" if search_path else folder
                sub_folders, sub_files, sub_error = explore_directory(base_url, subfolder_path)
                
                if not sub_error and sub_files:
                    for file in sub_files:
                        for ext in medical_extensions:
                            if file.lower().endswith(ext.lower()):
                                full_path = f"{subfolder_path}/{file}"
                                found_files.append((full_path, ext))
                                break
    
    if found_files:
        print(f"✅ Found {len(found_files)} medical imaging files:")
        for file_path, ext in found_files[:10]:  # Show first 10
            print(f"   🏥 {file_path} ({ext})")
        if len(found_files) > 10:
            print(f"   ... and {len(found_files) - 10} more files")
    else:
        print("❌ No medical imaging files found")
        print("   💡 Tip: Create sample directories with:")
        print("      mkdir -p outputs/nifti/PA00001 outputs/segments/PA00001")

def main():
    """Main function to run all tests"""
    print("🔬 Image Server Test Utility")
    print("=" * 60)
    
    # Load configuration
    config = load_config()
    base_url = config['image_server_url']
    project_root = config['project_root']
    
    print(f"Configuration:")
    print(f"  IMAGE_SERVER: {base_url}")
    print(f"  PROJECT_ROOT: {project_root}")
    print()
    
    # Test server connectivity
    if not test_server_connectivity(base_url):
        print("\n❌ Cannot proceed with tests - server is not accessible")
        print("\n💡 Troubleshooting tips:")
        print("   1. Make sure the image server is running:")
        print("      python utils/image_server.py")
        print("   2. Check your .env file for correct IMAGE_SERVER URL")
        print("   3. Verify SSL certificate is working")
        sys.exit(1)
    
    # Test direct file access (most reliable method)
    accessible_files = test_direct_file_access(base_url)
    
    # Compare server vs filesystem
    test_server_vs_filesystem(base_url, project_root)
    
    # Test common paths (directory listings - likely to fail with FastAPI StaticFiles)
    test_common_paths(base_url)
    
    # Search for medical imaging files
    test_medical_imaging_files(base_url)
    
    # Explore full structure (likely to show limited results)
    explore_server_structure(base_url)
    
    print(f"\n📋 Summary:")
    print(f"=" * 30)
    print(f"🌐 Server URL: {base_url}")
    print(f"📁 Project Root: {project_root}")
    print(f"✅ Directly accessible files: {len(accessible_files)}")
    
    if accessible_files:
        print(f"   Examples: {', '.join(accessible_files[:3])}")
        if len(accessible_files) > 3:
            print(f"   (+{len(accessible_files)-3} more)")
    
    print(f"\n💡 Key findings:")
    if accessible_files:
        print(f"   ✅ Server is serving static files from project directory")
        print(f"   ❌ Directory listings are disabled (FastAPI StaticFiles default)")
        print(f"   🔧 Files must be accessed by direct URL path")
    else:
        print(f"   ❌ Server may not be serving files correctly")
        print(f"   🔧 Check server configuration and file permissions")
    
    print(f"\n✅ Test completed successfully!")

if __name__ == "__main__":
    main()
