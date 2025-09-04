#!/usr/bin/env python3
"""
Script to list contents of nifti and segments folders from the image server.
Reads IMAGE_SERVER configuration from .env file.
"""

import os
import sys
import requests
import urllib3
from pathlib import Path
from urllib.parse import urljoin, urlparse
from dotenv import load_dotenv
import argparse
from typing import List, Dict, Optional
import re
from bs4 import BeautifulSoup

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def load_environment_config():
    """Load environment configuration from .env file."""
    project_root = Path(__file__).parent.parent
    
    # Try to load .env file
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✓ Loaded configuration from .env")
    else:
        print("⚠️  No .env file found, using defaults")
    
    # Get IMAGE_SERVER URL with default
    image_server_url = os.getenv("IMAGE_SERVER", "https://localhost:8888")
    return image_server_url

def parse_directory_listing(html_content: str) -> List[Dict[str, str]]:
    """Parse HTML directory listing to extract file and folder information."""
    items = []
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all list items in the directory listing
        list_items = soup.find_all('li')
        
        for item in list_items:
            link = item.find('a')
            if link and link.get('href'):
                href = link.get('href')
                text = link.get_text().strip()
                
                # Skip parent directory links
                if text == "📁 ../" or href.endswith('../'):
                    continue
                
                # Determine if it's a directory or file
                is_directory = text.startswith('📁') or href.endswith('/')
                
                # Extract name (remove emoji and trailing slash)
                name = re.sub(r'^📁\s*|📄\s*', '', text)
                if name.endswith('/'):
                    name = name[:-1]
                
                # Extract size info if present
                size_info = ""
                size_span = item.find('span', style=re.compile(r'color.*#666'))
                if size_span:
                    size_info = size_span.get_text().strip()
                
                items.append({
                    'name': name,
                    'href': href,
                    'is_directory': is_directory,
                    'size': size_info,
                    'full_text': text
                })
    
    except Exception as e:
        print(f"❌ Error parsing directory listing: {e}")
    
    return items

def get_folder_contents(base_url: str, folder_path: str, verify_ssl: bool = False) -> Optional[List[Dict[str, str]]]:
    """Get contents of a folder from the image server."""
    
    # Construct the full URL
    folder_url = urljoin(base_url.rstrip('/') + '/', f"output/{folder_path}/")
    
    try:
        print(f"🔍 Fetching: {folder_url}")
        
        # Make request with SSL verification disabled for self-signed certs
        response = requests.get(folder_url, verify=verify_ssl, timeout=10)
        
        if response.status_code == 200:
            items = parse_directory_listing(response.text)
            return items
        elif response.status_code == 404:
            print(f"❌ Folder not found: {folder_path}")
            return None
        else:
            print(f"❌ HTTP {response.status_code}: {response.reason}")
            return None
            
    except requests.exceptions.SSLError as e:
        print(f"❌ SSL Error: {e}")
        print("💡 Try using --verify-ssl flag if you have proper certificates")
        return None
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection Error: {e}")
        print("💡 Make sure the image server is running")
        return None
    except requests.exceptions.Timeout:
        print(f"❌ Request timed out")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def print_folder_contents(folder_name: str, items: List[Dict[str, str]]):
    """Print formatted folder contents."""
    print(f"\n📂 {folder_name.upper()} FOLDER CONTENTS:")
    print("=" * 50)
    
    if not items:
        print("  (empty)")
        return
    
    # Separate directories and files
    directories = [item for item in items if item['is_directory']]
    files = [item for item in items if not item['is_directory']]
    
    # Print directories first
    for item in sorted(directories, key=lambda x: x['name']):
        print(f"  📁 {item['name']}/")
    
    # Print files
    for item in sorted(files, key=lambda x: x['name']):
        size_info = f" {item['size']}" if item['size'] else ""
        print(f"  📄 {item['name']}{size_info}")

def test_server_connection(base_url: str, verify_ssl: bool = False) -> bool:
    """Test if the image server is accessible."""
    try:
        print(f"🔗 Testing connection to: {base_url}")
        
        # Test with a known file first (README.md)
        test_url = urljoin(base_url.rstrip('/') + '/', 'README.md')
        response = requests.get(test_url, verify=verify_ssl, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Server is accessible (tested with README.md)")
            return True
        else:
            print(f"⚠️  Server responded with HTTP {response.status_code} for README.md")
            
            # Fallback: try root path
            response = requests.get(base_url, verify=verify_ssl, timeout=10)
            if response.status_code in [200, 404]:  # 404 is OK for root if no index
                print(f"✅ Server is running (HTTP {response.status_code} from root)")
                return True
            else:
                print(f"❌ Server responded with HTTP {response.status_code}")
                return False
            
    except requests.exceptions.SSLError as e:
        print(f"❌ SSL Error: {e}")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing connection: {e}")
        return False

def main():
    """Main function to list server contents."""
    parser = argparse.ArgumentParser(description="List contents of nifti and segments folders from image server")
    parser.add_argument("--verify-ssl", action="store_true", help="Verify SSL certificates (disable for self-signed certs)")
    parser.add_argument("--url", help="Override IMAGE_SERVER URL from environment")
    parser.add_argument("--folders", nargs="+", default=["nifti", "segments"], help="Folders to list (default: nifti segments)")
    
    args = parser.parse_args()
    
    # Load configuration
    image_server_url = args.url or load_environment_config()
    
    print(f"🌐 Image Server URL: {image_server_url}")
    print(f"🔒 SSL Verification: {'Enabled' if args.verify_ssl else 'Disabled (for self-signed certs)'}")
    
    # Test server connection
    if not test_server_connection(image_server_url, args.verify_ssl):
        print("\n❌ Cannot connect to image server. Please ensure:")
        print("   1. The image server is running (python utils/image_server.py)")
        print("   2. The IMAGE_SERVER URL in .env is correct")
        print("   3. SSL certificates are properly configured")
        sys.exit(1)
    
    # List contents of each folder
    for folder in args.folders:
        items = get_folder_contents(image_server_url, folder, args.verify_ssl)
        
        if items is not None:
            print_folder_contents(folder, items)
        else:
            print(f"\n📂 {folder.upper()} FOLDER:")
            print("=" * 50)
            print(f"  ❌ Could not access {folder} folder")
    
    print(f"\n✅ Finished listing server contents")

if __name__ == "__main__":
    main()
