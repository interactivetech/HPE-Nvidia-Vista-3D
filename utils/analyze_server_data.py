#!/usr/bin/env python3
"""
Script to analyze the image server data and generate a comprehensive report.
Scans output/nifti and output/segments folders to count:
- Number of patients (PA00000002 format folders)
- Number of CT scans per patient (nii.gz files)
- Number of voxel files per CT scan in segments folder

Usage:
    python utils/analyze_server_data.py
    python utils/analyze_server_data.py --url https://localhost:8888
    python utils/analyze_server_data.py --verify-ssl
"""

import os
import sys
import requests
import urllib3
import json
from pathlib import Path
from urllib.parse import urljoin, urlparse
from dotenv import load_dotenv
import argparse
from typing import List, Dict, Optional, Tuple
import re
from bs4 import BeautifulSoup
from collections import defaultdict
import time

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

def is_patient_folder(folder_name: str) -> bool:
    """Check if a folder name matches the patient pattern (PA00000002)."""
    return bool(re.match(r'^PA\d{8}$', folder_name))

def get_ct_scan_files(patient_folder_contents: List[Dict[str, str]]) -> List[str]:
    """Extract CT scan files (nii.gz) from patient folder contents."""
    ct_scans = []
    for item in patient_folder_contents:
        if not item['is_directory'] and item['name'].endswith('.nii.gz'):
            ct_scans.append(item['name'])
    return ct_scans

def get_voxel_files(segments_folder_contents: List[Dict[str, str]]) -> List[str]:
    """Extract voxel files from segments folder contents."""
    voxel_files = []
    for item in segments_folder_contents:
        if not item['is_directory'] and item['name'].endswith('.nii.gz'):
            voxel_files.append(item['name'])
    return voxel_files

def get_voxel_folder_contents(base_url: str, patient_id: str, verify_ssl: bool = False) -> Optional[List[Dict[str, str]]]:
    """Get contents of the voxels folder for a patient."""
    voxel_folder_path = f"segments/{patient_id}/voxels"
    
    return get_folder_contents(base_url, voxel_folder_path, verify_ssl)

def analyze_patient_data(base_url: str, patient_id: str, verify_ssl: bool = False) -> Dict:
    """Analyze data for a single patient."""
    print(f"  📊 Analyzing patient: {patient_id}")
    
    # Get nifti folder contents for this patient
    nifti_folder_path = f"nifti/{patient_id}"
    nifti_contents = get_folder_contents(base_url, nifti_folder_path, verify_ssl)
    
    if not nifti_contents:
        return {
            'patient_id': patient_id,
            'ct_scans': [],
            'total_ct_scans': 0,
            'voxel_data': {},
            'total_voxel_files': 0,
            'error': 'Could not access nifti folder'
        }
    
    # Get CT scan files
    ct_scans = get_ct_scan_files(nifti_contents)
    
    # Get segments folder contents for this patient
    segments_folder_path = f"segments/{patient_id}"
    segments_contents = get_folder_contents(base_url, segments_folder_path, verify_ssl)
    
    voxel_data = {}
    total_voxel_files = 0
    
    # Get voxel folder contents once for the patient
    voxel_folder_contents = get_voxel_folder_contents(base_url, patient_id, verify_ssl)
    
    if segments_contents:
        # For each CT scan, check for corresponding voxel data
        for ct_scan in ct_scans:
            # Check for direct voxel file (segmentation result)
            voxel_file_name = ct_scan  # Same name as CT scan
            voxel_files = get_voxel_files(segments_contents)
            
            # Check if there's a voxel file with the same name
            has_voxel_file = voxel_file_name in voxel_files
            
            # Count voxel files for this specific scan
            scan_voxel_files = []
            if voxel_folder_contents:
                # Find voxel files that start with the scan name (without .nii.gz)
                scan_base_name = ct_scan.replace('.nii.gz', '')
                scan_voxel_files = [item['name'] for item in voxel_folder_contents 
                                  if not item['is_directory'] and item['name'].startswith(scan_base_name + '_')]
            
            voxel_data[ct_scan] = {
                'has_voxel_file': has_voxel_file,
                'voxel_file_name': voxel_file_name if has_voxel_file else None,
                'voxel_folder_files': scan_voxel_files,
                'voxel_count': len(scan_voxel_files)
            }
            
            total_voxel_files += len(scan_voxel_files)
            if has_voxel_file:
                total_voxel_files += 1
    
    return {
        'patient_id': patient_id,
        'ct_scans': ct_scans,
        'total_ct_scans': len(ct_scans),
        'voxel_data': voxel_data,
        'total_voxel_files': total_voxel_files,
        'error': None
    }

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

def generate_report(analysis_data: List[Dict], output_file: Optional[str] = None) -> str:
    """Generate a comprehensive report from the analysis data."""
    
    total_patients = len(analysis_data)
    total_ct_scans = sum(patient['total_ct_scans'] for patient in analysis_data)
    
    # Calculate statistics
    patients_with_data = len([p for p in analysis_data if p['total_ct_scans'] > 0])
    patients_with_voxels = len([p for p in analysis_data if p['total_voxel_files'] > 0])
    
    # Generate report
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("🏥 MEDICAL IMAGING SERVER DATA ANALYSIS REPORT")
    report_lines.append("=" * 80)
    report_lines.append(f"📅 Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    
    # Summary statistics
    report_lines.append("📊 SUMMARY STATISTICS")
    report_lines.append("-" * 40)
    report_lines.append(f"Total Patients Found: {total_patients}")
    report_lines.append(f"Patients with CT Scans: {patients_with_data}")
    report_lines.append(f"Patients with Voxel Data: {patients_with_voxels}")
    report_lines.append(f"Total CT Scans: {total_ct_scans}")
    report_lines.append("")
    
    # Detailed patient breakdown
    report_lines.append("👥 DETAILED PATIENT BREAKDOWN")
    report_lines.append("-" * 40)
    
    for patient in analysis_data:
        report_lines.append(f"\n🏷️  Patient ID: {patient['patient_id']}")
        
        if patient['error']:
            report_lines.append(f"   ❌ Error: {patient['error']}")
            continue
        
        report_lines.append(f"   📊 CT Scans: {patient['total_ct_scans']}")
        report_lines.append(f"   🧬 Voxel Files: {patient['total_voxel_files']}")
        
        if patient['ct_scans']:
            report_lines.append("   📋 CT Scan Details:")
            for ct_scan in patient['ct_scans']:
                voxel_info = patient['voxel_data'].get(ct_scan, {})
                has_voxel_file = voxel_info.get('has_voxel_file', False)
                voxel_count = voxel_info.get('voxel_count', 0)
                
                # Remove .nii.gz extension for display
                scan_display_name = ct_scan.replace('.nii.gz', '')
                
                voxel_status = "✅" if has_voxel_file or voxel_count > 0 else "❌"
                voxel_details = []
                if has_voxel_file:
                    voxel_details.append("segmentation file")
                if voxel_count > 0:
                    voxel_details.append(f"{voxel_count} voxels")
                
                voxel_text = f" ({', '.join(voxel_details)})" if voxel_details else " (no voxel data)"
                report_lines.append(f"      {voxel_status} {scan_display_name}{voxel_text}")
    
    # File structure overview
    report_lines.append("\n📁 FILE STRUCTURE OVERVIEW")
    report_lines.append("-" * 40)
    report_lines.append("output/")
    report_lines.append("├── nifti/")
    report_lines.append("│   ├── PA00000002/")
    report_lines.append("│   │   ├── 01_2.5MM_ARTERIAL.nii.gz")
    report_lines.append("│   │   ├── 02_VENOUS_PHASE.nii.gz")
    report_lines.append("│   │   └── ...")
    report_lines.append("│   └── ...")
    report_lines.append("└── segments/")
    report_lines.append("    ├── PA00000002/")
    report_lines.append("    │   ├── 01_2.5MM_ARTERIAL.nii.gz  (segmentation)")
    report_lines.append("    │   ├── 01_2.5MM_ARTERIAL_voxel/  (voxel files)")
    report_lines.append("    │   │   ├── voxel_file_1.nii.gz")
    report_lines.append("    │   │   └── ...")
    report_lines.append("    │   └── ...")
    report_lines.append("    └── ...")
    
    report_lines.append("\n" + "=" * 80)
    report_lines.append("✅ Analysis Complete")
    report_lines.append("=" * 80)
    
    report_content = "\n".join(report_lines)
    
    # Save to file if requested
    if output_file:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            print(f"📄 Report saved to: {output_file}")
        except Exception as e:
            print(f"❌ Error saving report: {e}")
    
    return report_content

def main():
    """Main function to analyze server data and generate report."""
    parser = argparse.ArgumentParser(description="Analyze image server data and generate comprehensive report")
    parser.add_argument("--verify-ssl", action="store_true", help="Verify SSL certificates (disable for self-signed certs)")
    parser.add_argument("--url", help="Override IMAGE_SERVER URL from environment")
    parser.add_argument("--output", "-o", help="Save report to file")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress progress output")
    
    args = parser.parse_args()
    
    # Load configuration
    image_server_url = args.url or load_environment_config()
    
    if not args.quiet:
        print(f"🌐 Image Server URL: {image_server_url}")
        print(f"🔒 SSL Verification: {'Enabled' if args.verify_ssl else 'Disabled (for self-signed certs)'}")
    
    # Test server connection
    if not test_server_connection(image_server_url, args.verify_ssl):
        print("\n❌ Cannot connect to image server. Please ensure:")
        print("   1. The image server is running (python utils/image_server.py)")
        print("   2. The IMAGE_SERVER URL in .env is correct")
        print("   3. SSL certificates are properly configured")
        sys.exit(1)
    
    # Get nifti folder contents to find patients
    if not args.quiet:
        print("\n🔍 Scanning for patients...")
    
    nifti_contents = get_folder_contents(image_server_url, "nifti", args.verify_ssl)
    if not nifti_contents:
        print("❌ Could not access nifti folder")
        sys.exit(1)
    
    # Filter for patient folders
    patient_folders = [item for item in nifti_contents if item['is_directory'] and is_patient_folder(item['name'])]
    
    if not patient_folders:
        print("❌ No patient folders found (expected format: PA00000002)")
        sys.exit(1)
    
    if not args.quiet:
        print(f"✅ Found {len(patient_folders)} patient folders")
    
    # Analyze each patient
    analysis_data = []
    for i, patient_folder in enumerate(patient_folders, 1):
        if not args.quiet:
            print(f"\n📊 Processing patient {i}/{len(patient_folders)}: {patient_folder['name']}")
        
        patient_data = analyze_patient_data(image_server_url, patient_folder['name'], args.verify_ssl)
        analysis_data.append(patient_data)
    
    # Generate and display report
    if not args.quiet:
        print("\n📋 Generating report...")
    
    report = generate_report(analysis_data, args.output)
    
    if not args.quiet:
        print("\n" + report)
    else:
        print(report)

if __name__ == "__main__":
    main()
