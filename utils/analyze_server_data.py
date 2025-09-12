#!/usr/bin/env python3
"""
Script to analyze the image server data and generate a comprehensive report.
Supports both old and new folder structures. Analyzes all folders in the output directory.

CURRENT STRUCTURE:
- output/{folder_name}/nifti/         (CT scan files)
- output/{folder_name}/segments/      (full segmentation files)
- output/{folder_name}/voxels/{ct_scan_name}/  (individual voxel files)
- output/{folder_name}/mesh/{ct_scan_name}/    (STL mesh files)

OLD STRUCTURE (legacy):
- output/nifti/{folder_name}/         (CT scan files)
- output/segments/{folder_name}/      (segmentation files)
- output/segments/{folder_name}/voxels/  (voxel files)
- output/segments/{folder_name}/mesh/    (STL mesh files)

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

def parse_file_size(size_str: str) -> int:
    """Parse file size string and return size in bytes."""
    if not size_str or size_str.strip() == "":
        return 0
    
    try:
        size_str = size_str.strip()
        
        # Handle formats like "1 (0 B)" or "2 (1.5 MB)" - extract content from parentheses
        if '(' in size_str and ')' in size_str:
            # Extract the part in parentheses
            start = size_str.find('(') + 1
            end = size_str.find(')')
            if start > 0 and end > start:
                size_str = size_str[start:end].strip()
        
        # If we still have a format like "1 39.2 MB", extract the part with units
        parts = size_str.split()
        if len(parts) > 1:
            # Look for any part that contains size units and take it plus the previous part
            for i in range(len(parts)):
                part = parts[i].upper()
                if any(unit in part for unit in ['TB', 'GB', 'MB', 'KB', 'B']):
                    # Take this part and the previous part (which should be the number)
                    if i > 0:
                        size_str = ' '.join(parts[i-1:i+1])
                    else:
                        size_str = parts[i]
                    break
        
        size_str = size_str.upper()
        
        # Handle different size units
        multipliers = {
            'TB': 1024 * 1024 * 1024 * 1024,
            'GB': 1024 * 1024 * 1024,
            'MB': 1024 * 1024,
            'KB': 1024,
            'B': 1
        }
        
        for unit, multiplier in multipliers.items():
            if size_str.endswith(unit):
                try:
                    number_str = size_str[:-len(unit)].strip()
                    number = float(number_str)
                    return int(number * multiplier)
                except (ValueError, TypeError):
                    continue
        
        # Try to parse as plain number (assume bytes)
        try:
            return int(float(size_str))
        except (ValueError, TypeError):
            return 0
            
    except Exception:
        # If anything goes wrong, return 0
        return 0

def format_file_size(size_bytes: int) -> str:
    """Format file size in bytes to human readable format."""
    if size_bytes == 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    size = float(size_bytes)
    unit_index = 0
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.1f} {units[unit_index]}"

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
    image_server_url = os.getenv("IMAGE_SERVER", "http://localhost:8888")
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
                size_bytes = 0
                size_span = item.find('span', style=re.compile(r'color.*#666'))
                if size_span:
                    size_info = size_span.get_text().strip()
                    size_bytes = parse_file_size(size_info)
                
                items.append({
                    'name': name,
                    'href': href,
                    'is_directory': is_directory,
                    'size': size_info,
                    'size_bytes': size_bytes,
                    'full_text': text
                })
    
    except Exception as e:
        print(f"❌ Error parsing directory listing: {e}")
    
    return items

def get_folder_contents(base_url: str, folder_path: str) -> Optional[List[Dict[str, str]]]:
    """Get contents of a folder from the image server."""
    
    # Construct the full URL
    folder_url = urljoin(base_url.rstrip('/') + '/', f"output/{folder_path}/")
    
    try:
        print(f"🔍 Fetching: {folder_url}")
        
        # Make request
        response = requests.get(folder_url, timeout=10)
        
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
    """Check if a folder should be analyzed as a patient folder.
    Skip common non-patient folders like .git, __pycache__, etc."""
    skip_folders = {'.git', '__pycache__', '.DS_Store', 'node_modules', '.env'}
    return folder_name not in skip_folders and not folder_name.startswith('.')

def get_ct_scan_files(patient_folder_contents: List[Dict[str, str]]) -> List[Dict[str, any]]:
    """Extract CT scan files (nii.gz) from patient folder contents with size info."""
    ct_scans = []
    for item in patient_folder_contents:
        if not item['is_directory'] and item['name'].endswith('.nii.gz'):
            ct_scans.append({
                'name': item['name'],
                'size_bytes': item.get('size_bytes', 0),
                'size_display': item.get('size', 'Unknown')
            })
    return ct_scans

def get_voxel_files(segments_folder_contents: List[Dict[str, str]]) -> List[Dict[str, any]]:
    """Extract voxel files from segments folder contents with size info."""
    voxel_files = []
    for item in segments_folder_contents:
        if not item['is_directory'] and item['name'].endswith('.nii.gz'):
            voxel_files.append({
                'name': item['name'],
                'size_bytes': item.get('size_bytes', 0),
                'size_display': item.get('size', 'Unknown')
            })
    return voxel_files

def get_mesh_files(mesh_folder_contents: List[Dict[str, str]]) -> List[Dict[str, any]]:
    """Extract mesh files (STL) from mesh folder contents with size info."""
    mesh_files = []
    for item in mesh_folder_contents:
        if not item['is_directory'] and item['name'].endswith('.stl'):
            mesh_files.append({
                'name': item['name'],
                'size_bytes': item.get('size_bytes', 0),
                'size_display': item.get('size', 'Unknown')
            })
    return mesh_files

def get_ply_files(ply_folder_contents: List[Dict[str, str]]) -> List[Dict[str, any]]:
    """Extract PLY files from PLY folder contents with size info."""
    ply_files = []
    for item in ply_folder_contents:
        if not item['is_directory'] and item['name'].endswith('.ply'):
            ply_files.append({
                'name': item['name'],
                'size_bytes': item.get('size_bytes', 0),
                'size_display': item.get('size', 'Unknown')
            })
    return ply_files

# Removed get_voxel_folder_contents - now handled directly in analyze_patient_data

def analyze_patient_data(base_url: str, patient_id: str, use_old_structure: bool = False) -> Dict:
    """Analyze data for a single patient."""
    print(f"  📊 Analyzing patient: {patient_id}")
    
    # Determine folder paths based on structure
    if use_old_structure:
        nifti_folder_path = f"nifti/{patient_id}"
        segments_folder_path = f"segments/{patient_id}"
        voxel_folder_path = f"segments/{patient_id}/voxels"
        mesh_folder_path = f"segments/{patient_id}/mesh"
        ply_folder_path = f"segments/{patient_id}/ply"
        structure_type = "old"
    else:
        nifti_folder_path = f"{patient_id}/nifti"
        segments_folder_path = f"{patient_id}/segments"
        voxel_folder_path = f"{patient_id}/voxels"
        mesh_folder_path = f"{patient_id}/mesh"
        ply_folder_path = f"{patient_id}/ply"
        structure_type = "current"
    
    print(f"    Using {structure_type} folder structure")
    
    # Get nifti folder contents for this patient
    nifti_contents = get_folder_contents(base_url, nifti_folder_path)
    
    if not nifti_contents:
        return {
            'patient_id': patient_id,
            'ct_scans': [],
            'total_ct_scans': 0,
            'total_ct_size_bytes': 0,
            'voxel_data': {},
            'total_voxel_files': 0,
            'total_voxel_size_bytes': 0,
            'mesh_data': {},
            'total_mesh_files': 0,
            'total_mesh_size_bytes': 0,
            'ply_data': {},
            'total_ply_files': 0,
            'total_ply_size_bytes': 0,
            'total_patient_size_bytes': 0,
            'error': f'Could not access nifti folder ({structure_type} structure)',
            'structure_type': structure_type
        }
    
    # Get CT scan files
    ct_scans = get_ct_scan_files(nifti_contents)
    
    # Calculate total CT scan size
    total_ct_size_bytes = sum(scan.get('size_bytes', 0) for scan in ct_scans)
    
    # Get segments folder contents for this patient
    segments_contents = get_folder_contents(base_url, segments_folder_path)
    
    voxel_data = {}
    total_voxel_files = 0
    total_voxel_size_bytes = 0
    
    mesh_data = {}
    total_mesh_files = 0
    total_mesh_size_bytes = 0
    
    ply_data = {}
    total_ply_files = 0
    total_ply_size_bytes = 0
    
    # Get voxel folder contents (different logic for new vs old structure)
    if use_old_structure:
        voxel_folder_contents = get_folder_contents(base_url, voxel_folder_path)
    else:
        # In current structure, voxels are organized by CT scan subfolders
        voxel_folder_contents = get_folder_contents(base_url, voxel_folder_path)
    
    # Get mesh folder contents (same structure as voxels)
    mesh_folder_contents = get_folder_contents(base_url, mesh_folder_path)
    
    # Get PLY folder contents (same structure as voxels and mesh)
    ply_folder_contents = get_folder_contents(base_url, ply_folder_path)
    
    if segments_contents:
        # For each CT scan, check for corresponding voxel data
        for ct_scan_info in ct_scans:
            ct_scan_name = ct_scan_info['name']
            
            # Check for direct voxel file (segmentation result)
            voxel_files = get_voxel_files(segments_contents)
            voxel_file_names = [vf['name'] for vf in voxel_files]
            has_voxel_file = ct_scan_name in voxel_file_names
            
            # Find the segmentation file size if it exists
            segmentation_size_bytes = 0
            if has_voxel_file:
                for vf in voxel_files:
                    if vf['name'] == ct_scan_name:
                        segmentation_size_bytes = vf['size_bytes']
                        break
            
            # Count voxel files for this specific scan
            scan_voxel_files = []
            scan_voxel_size_bytes = 0
            
            if voxel_folder_contents:
                if use_old_structure:
                    # Old structure: Find voxel files that start with the scan name
                    scan_base_name = ct_scan_name.replace('.nii.gz', '')
                    for item in voxel_folder_contents:
                        if not item['is_directory'] and item['name'].startswith(scan_base_name + '_'):
                            scan_voxel_files.append({
                                'name': item['name'],
                                'size_bytes': item.get('size_bytes', 0),
                                'size_display': item.get('size', 'Unknown')
                            })
                            scan_voxel_size_bytes += item.get('size_bytes', 0)
                else:
                    # Current structure: Look for CT scan subfolder in voxels directory
                    scan_base_name = ct_scan_name.replace('.nii.gz', '').replace('.nii', '')
                    ct_scan_voxel_folder = None
                    
                    # Find the subfolder for this CT scan
                    for item in voxel_folder_contents:
                        if item['is_directory'] and item['name'] == scan_base_name:
                            ct_scan_voxel_folder = item['name']
                            break
                    
                    # If found, get contents of the CT scan voxel subfolder
                    if ct_scan_voxel_folder:
                        ct_scan_voxel_path = f"{voxel_folder_path}/{ct_scan_voxel_folder}"
                        ct_scan_voxel_contents = get_folder_contents(base_url, ct_scan_voxel_path)
                        if ct_scan_voxel_contents:
                            for item in ct_scan_voxel_contents:
                                if not item['is_directory'] and item['name'].endswith('.nii.gz'):
                                    scan_voxel_files.append({
                                        'name': item['name'],
                                        'size_bytes': item.get('size_bytes', 0),
                                        'size_display': item.get('size', 'Unknown')
                                    })
                                    scan_voxel_size_bytes += item.get('size_bytes', 0)
            
            # Count mesh files for this specific scan
            scan_mesh_files = []
            scan_mesh_size_bytes = 0
            
            if mesh_folder_contents:
                if use_old_structure:
                    # Old structure: Find mesh files that start with the scan name
                    scan_base_name = ct_scan_name.replace('.nii.gz', '')
                    for item in mesh_folder_contents:
                        if not item['is_directory'] and item['name'].startswith(scan_base_name + '_') and item['name'].endswith('.stl'):
                            scan_mesh_files.append({
                                'name': item['name'],
                                'size_bytes': item.get('size_bytes', 0),
                                'size_display': item.get('size', 'Unknown')
                            })
                            scan_mesh_size_bytes += item.get('size_bytes', 0)
                else:
                    # Current structure: Look for CT scan subfolder in mesh directory
                    scan_base_name = ct_scan_name.replace('.nii.gz', '').replace('.nii', '')
                    ct_scan_mesh_folder = None
                    
                    # Find the subfolder for this CT scan
                    for item in mesh_folder_contents:
                        if item['is_directory'] and item['name'] == scan_base_name:
                            ct_scan_mesh_folder = item['name']
                            break
                    
                    # If found, get contents of the CT scan mesh subfolder
                    if ct_scan_mesh_folder:
                        ct_scan_mesh_path = f"{mesh_folder_path}/{ct_scan_mesh_folder}"
                        ct_scan_mesh_contents = get_folder_contents(base_url, ct_scan_mesh_path)
                        if ct_scan_mesh_contents:
                            for item in ct_scan_mesh_contents:
                                if not item['is_directory'] and item['name'].endswith('.stl'):
                                    scan_mesh_files.append({
                                        'name': item['name'],
                                        'size_bytes': item.get('size_bytes', 0),
                                        'size_display': item.get('size', 'Unknown')
                                    })
                                    scan_mesh_size_bytes += item.get('size_bytes', 0)
            
            # Count PLY files for this specific scan
            scan_ply_files = []
            scan_ply_size_bytes = 0
            
            if ply_folder_contents:
                if use_old_structure:
                    # Old structure: Find PLY files that start with the scan name
                    scan_base_name = ct_scan_name.replace('.nii.gz', '')
                    for item in ply_folder_contents:
                        if not item['is_directory'] and item['name'].startswith(scan_base_name + '_') and item['name'].endswith('.ply'):
                            scan_ply_files.append({
                                'name': item['name'],
                                'size_bytes': item.get('size_bytes', 0),
                                'size_display': item.get('size', 'Unknown')
                            })
                            scan_ply_size_bytes += item.get('size_bytes', 0)
                else:
                    # Current structure: Look for CT scan subfolder in PLY directory
                    scan_base_name = ct_scan_name.replace('.nii.gz', '').replace('.nii', '')
                    ct_scan_ply_folder = None
                    
                    # Find the subfolder for this CT scan
                    for item in ply_folder_contents:
                        if item['is_directory'] and item['name'] == scan_base_name:
                            ct_scan_ply_folder = item['name']
                            break
                    
                    # If found, get contents of the CT scan PLY subfolder
                    if ct_scan_ply_folder:
                        ct_scan_ply_path = f"{ply_folder_path}/{ct_scan_ply_folder}"
                        ct_scan_ply_contents = get_folder_contents(base_url, ct_scan_ply_path)
                        if ct_scan_ply_contents:
                            for item in ct_scan_ply_contents:
                                if not item['is_directory'] and item['name'].endswith('.ply'):
                                    scan_ply_files.append({
                                        'name': item['name'],
                                        'size_bytes': item.get('size_bytes', 0),
                                        'size_display': item.get('size', 'Unknown')
                                    })
                                    scan_ply_size_bytes += item.get('size_bytes', 0)
            
            voxel_data[ct_scan_name] = {
                'has_voxel_file': has_voxel_file,
                'voxel_file_name': ct_scan_name if has_voxel_file else None,
                'voxel_folder_files': scan_voxel_files,
                'voxel_count': len(scan_voxel_files),
                'segmentation_size_bytes': segmentation_size_bytes,
                'voxel_size_bytes': scan_voxel_size_bytes,
                'total_size_bytes': segmentation_size_bytes + scan_voxel_size_bytes
            }
            
            mesh_data[ct_scan_name] = {
                'mesh_folder_files': scan_mesh_files,
                'mesh_count': len(scan_mesh_files),
                'mesh_size_bytes': scan_mesh_size_bytes
            }
            
            ply_data[ct_scan_name] = {
                'ply_folder_files': scan_ply_files,
                'ply_count': len(scan_ply_files),
                'ply_size_bytes': scan_ply_size_bytes
            }
            
            total_voxel_files += len(scan_voxel_files)
            if has_voxel_file:
                total_voxel_files += 1
            
            total_voxel_size_bytes += segmentation_size_bytes + scan_voxel_size_bytes
            total_mesh_files += len(scan_mesh_files)
            total_mesh_size_bytes += scan_mesh_size_bytes
            total_ply_files += len(scan_ply_files)
            total_ply_size_bytes += scan_ply_size_bytes
    
    # Calculate total patient data size
    total_patient_size_bytes = total_ct_size_bytes + total_voxel_size_bytes + total_mesh_size_bytes + total_ply_size_bytes
    
    return {
        'patient_id': patient_id,
        'ct_scans': ct_scans,
        'total_ct_scans': len(ct_scans),
        'total_ct_size_bytes': total_ct_size_bytes,
        'voxel_data': voxel_data,
        'total_voxel_files': total_voxel_files,
        'total_voxel_size_bytes': total_voxel_size_bytes,
        'mesh_data': mesh_data,
        'total_mesh_files': total_mesh_files,
        'total_mesh_size_bytes': total_mesh_size_bytes,
        'ply_data': ply_data,
        'total_ply_files': total_ply_files,
        'total_ply_size_bytes': total_ply_size_bytes,
        'total_patient_size_bytes': total_patient_size_bytes,
        'structure_type': structure_type,
        'error': None
    }

def test_server_connection(base_url: str) -> bool:
    """Test if the image server is accessible."""
    try:
        print(f"🔗 Testing connection to: {base_url}")
        
        # Test with a known file first (README.md)
        test_url = urljoin(base_url.rstrip('/') + '/', 'README.md')
        response = requests.get(test_url, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Server is accessible (tested with README.md)")
            return True
        else:
            print(f"⚠️  Server responded with HTTP {response.status_code} for README.md")
            
            # Fallback: try root path
            response = requests.get(base_url, timeout=10)
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
    total_ct_scans = sum(patient.get('total_ct_scans', 0) for patient in analysis_data)
    total_ct_size_bytes = sum(patient.get('total_ct_size_bytes', 0) for patient in analysis_data)
    total_voxel_size_bytes = sum(patient.get('total_voxel_size_bytes', 0) for patient in analysis_data)
    total_mesh_size_bytes = sum(patient.get('total_mesh_size_bytes', 0) for patient in analysis_data)
    total_ply_size_bytes = sum(patient.get('total_ply_size_bytes', 0) for patient in analysis_data)
    total_data_size_bytes = sum(patient.get('total_patient_size_bytes', 0) for patient in analysis_data)
    
    # Calculate statistics
    patients_with_data = len([p for p in analysis_data if p.get('total_ct_scans', 0) > 0])
    patients_with_voxels = len([p for p in analysis_data if p.get('total_voxel_files', 0) > 0])
    patients_with_meshes = len([p for p in analysis_data if p.get('total_mesh_files', 0) > 0])
    patients_with_ply = len([p for p in analysis_data if p.get('total_ply_files', 0) > 0])
    
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
    report_lines.append(f"Patients with Mesh Data: {patients_with_meshes}")
    report_lines.append(f"Patients with PLY Data: {patients_with_ply}")
    report_lines.append(f"Total CT Scans: {total_ct_scans}")
    report_lines.append("")
    report_lines.append("💾 DATA SIZE SUMMARY")
    report_lines.append("-" * 40)
    report_lines.append(f"Total CT Scan Data: {format_file_size(total_ct_size_bytes)}")
    report_lines.append(f"Total Voxel Data: {format_file_size(total_voxel_size_bytes)}")
    report_lines.append(f"Total Mesh Data: {format_file_size(total_mesh_size_bytes)}")
    report_lines.append(f"Total PLY Data: {format_file_size(total_ply_size_bytes)}")
    report_lines.append(f"Total Data Size: {format_file_size(total_data_size_bytes)}")
    report_lines.append("")
    
    # Detailed patient breakdown
    report_lines.append("👥 DETAILED PATIENT BREAKDOWN")
    report_lines.append("-" * 40)
    
    for patient in analysis_data:
        data_size_info = f" - {format_file_size(patient.get('total_patient_size_bytes', 0))}" if patient.get('total_patient_size_bytes', 0) > 0 else ""
        report_lines.append(f"\n🏷️  Patient ID: {patient['patient_id']}{data_size_info}")
        
        if patient['error']:
            report_lines.append(f"   ❌ Error: {patient['error']}")
            continue
        
        report_lines.append(f"   📊 CT Scans: {patient.get('total_ct_scans', 0)} ({format_file_size(patient.get('total_ct_size_bytes', 0))})")
        report_lines.append(f"   🧬 Voxel Files: {patient.get('total_voxel_files', 0)} ({format_file_size(patient.get('total_voxel_size_bytes', 0))})")
        report_lines.append(f"   🔺 Mesh Files: {patient.get('total_mesh_files', 0)} ({format_file_size(patient.get('total_mesh_size_bytes', 0))})")
        report_lines.append(f"   🎨 PLY Files: {patient.get('total_ply_files', 0)} ({format_file_size(patient.get('total_ply_size_bytes', 0))})")
        report_lines.append(f"   💾 Total Data: {format_file_size(patient.get('total_patient_size_bytes', 0))}")
        
        if patient.get('ct_scans'):
            report_lines.append("   📋 CT Scan Details:")
            for ct_scan_info in patient['ct_scans']:
                ct_scan_name = ct_scan_info.get('name', 'Unknown')
                ct_scan_size = ct_scan_info.get('size_bytes', 0)
                voxel_info = patient.get('voxel_data', {}).get(ct_scan_name, {})
                mesh_info = patient.get('mesh_data', {}).get(ct_scan_name, {})
                ply_info = patient.get('ply_data', {}).get(ct_scan_name, {})
                has_voxel_file = voxel_info.get('has_voxel_file', False)
                voxel_count = voxel_info.get('voxel_count', 0)
                mesh_count = mesh_info.get('mesh_count', 0)
                ply_count = ply_info.get('ply_count', 0)
                total_scan_size = voxel_info.get('total_size_bytes', 0) + mesh_info.get('mesh_size_bytes', 0) + ply_info.get('ply_size_bytes', 0)
                
                # Remove .nii.gz extension for display
                scan_display_name = ct_scan_name.replace('.nii.gz', '')
                
                voxel_status = "✅" if has_voxel_file or voxel_count > 0 else "❌"
                mesh_status = "✅" if mesh_count > 0 else "❌"
                ply_status = "✅" if ply_count > 0 else "❌"
                voxel_details = []
                if has_voxel_file:
                    voxel_details.append("segmentation file")
                if voxel_count > 0:
                    voxel_details.append(f"{voxel_count} voxels")
                
                mesh_details = []
                if mesh_count > 0:
                    mesh_details.append(f"{mesh_count} meshes")
                
                ply_details = []
                if ply_count > 0:
                    ply_details.append(f"{ply_count} PLY files")
                
                voxel_text = f" ({', '.join(voxel_details)})" if voxel_details else " (no voxel data)"
                mesh_text = f" ({', '.join(mesh_details)})" if mesh_details else " (no mesh data)"
                ply_text = f" ({', '.join(ply_details)})" if ply_details else " (no PLY data)"
                additional_size = max(0, total_scan_size - ct_scan_size)  # Ensure non-negative
                size_text = f" [{format_file_size(ct_scan_size)} + {format_file_size(additional_size)} = {format_file_size(total_scan_size)}]"
                report_lines.append(f"      {voxel_status} {scan_display_name}{voxel_text}")
                report_lines.append(f"      {mesh_status} {scan_display_name}{mesh_text}")
                report_lines.append(f"      {ply_status} {scan_display_name}{ply_text}{size_text}")
    
    # File structure overview
    report_lines.append("\n📁 FILE STRUCTURE OVERVIEW")
    report_lines.append("-" * 40)
    report_lines.append(f"TOTAL DATA SIZE: {format_file_size(total_data_size_bytes)}")
    report_lines.append("output/")
    report_lines.append("├── PA00000002/")
    report_lines.append("│   ├── nifti/")
    report_lines.append("│   │   ├── 1.25_mm_4.nii.gz")
    report_lines.append("│   │   ├── 1.25_mm_4.json")
    report_lines.append("│   │   └── 2.5_mm_STD_-_30%_ASIR_2.nii.gz")
    report_lines.append("│   ├── segments/")
    report_lines.append("│   │   ├── 1.25_mm_4.nii.gz  (full segmentation)")
    report_lines.append("│   │   └── 2.5_mm_STD_-_30%_ASIR_2.nii.gz")
    report_lines.append("│   ├── voxels/")
    report_lines.append("│   │   ├── 1.25_mm_4/")
    report_lines.append("│   │   │   ├── aorta.nii.gz")
    report_lines.append("│   │   │   └── inferior_vena_cava.nii.gz")
    report_lines.append("│   │   └── 2.5_mm_STD_-_30%_ASIR_2/")
    report_lines.append("│   │       ├── aorta.nii.gz")
    report_lines.append("│   │       └── inferior_vena_cava.nii.gz")
    report_lines.append("│   ├── mesh/")
    report_lines.append("│   │   ├── 1.25_mm_4/")
    report_lines.append("│   │   │   ├── aorta.stl")
    report_lines.append("│   │   │   └── inferior_vena_cava.stl")
    report_lines.append("│   │   └── 2.5_mm_STD_-_30%_ASIR_2/")
    report_lines.append("│   │       ├── aorta.stl")
    report_lines.append("│   │       └── inferior_vena_cava.stl")
    report_lines.append("│   └── ply/")
    report_lines.append("│       ├── 1.25_mm_4/")
    report_lines.append("│       │   ├── aorta.ply")
    report_lines.append("│       │   └── inferior_vena_cava.ply")
    report_lines.append("│       └── 2.5_mm_STD_-_30%_ASIR_2/")
    report_lines.append("│           ├── aorta.ply")
    report_lines.append("│           └── inferior_vena_cava.ply")
    report_lines.append("└── PA00000003/")
    report_lines.append("    (same structure...)")
    report_lines.append("")
    report_lines.append("OLD STRUCTURE (still supported):")
    report_lines.append("output/")
    report_lines.append("├── nifti/PA00000002/")
    report_lines.append("├── segments/PA00000002/")
    report_lines.append("│   ├── voxels/")
    report_lines.append("│   ├── mesh/")
    report_lines.append("│   └── ply/")
    
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
    parser.add_argument("--url", help="Override IMAGE_SERVER URL from environment")
    parser.add_argument("--output", "-o", help="Save report to file")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress progress output")
    
    args = parser.parse_args()
    
    # Load configuration
    image_server_url = args.url or load_environment_config()
    
    if not args.quiet:
        print(f"🌐 Image Server URL: {image_server_url}")
    
    # Test server connection
    if not test_server_connection(image_server_url):
        print("\n❌ Cannot connect to image server. Please ensure:")
        print("   1. The image server is running (python utils/image_server.py)")
        print("   2. The IMAGE_SERVER URL in .env is correct")
        sys.exit(1)
    
    # Get output folder contents to find patients (current structure)
    if not args.quiet:
        print("\n🔍 Scanning for patients...")
    
    # First try the current structure (output/ folder with patient directories)
    output_contents = get_folder_contents(image_server_url, "")
    patient_folders = []
    
    if output_contents:
        # Filter for patient folders in the current structure
        patient_folders = [item for item in output_contents if item['is_directory'] and is_patient_folder(item['name'])]
    
    # If no patients found in current structure, fall back to old structure
    if not patient_folders:
        if not args.quiet:
            print("  No patients found in current structure, checking old structure...")
        
        nifti_contents = get_folder_contents(image_server_url, "nifti")
        if nifti_contents:
            patient_folders = [item for item in nifti_contents if item['is_directory'] and is_patient_folder(item['name'])]
            # Mark these as old structure for later processing
            for folder in patient_folders:
                folder['old_structure'] = True
    
    if not patient_folders:
        print("❌ No patient folders found in output directory")
        print("   Checked both current structure (output/{patient}/) and old structure (output/nifti/{patient}/)")
        sys.exit(1)
    
    if not args.quiet:
        print(f"✅ Found {len(patient_folders)} patient folders")
    
    # Analyze each patient
    analysis_data = []
    for i, patient_folder in enumerate(patient_folders, 1):
        if not args.quiet:
            print(f"\n📊 Processing patient {i}/{len(patient_folders)}: {patient_folder['name']}")
        
        # Check if this patient uses old structure
        use_old_structure = patient_folder.get('old_structure', False)
        try:
            patient_data = analyze_patient_data(image_server_url, patient_folder['name'], use_old_structure)
            analysis_data.append(patient_data)
        except Exception as e:
            print(f"❌ Error analyzing patient {patient_folder['name']}: {e}")
            # Add error data for this patient
            analysis_data.append({
                'patient_id': patient_folder['name'],
                'ct_scans': [],
                'total_ct_scans': 0,
                'total_ct_size_bytes': 0,
                'voxel_data': {},
                'total_voxel_files': 0,
                'total_voxel_size_bytes': 0,
                'mesh_data': {},
                'total_mesh_files': 0,
                'total_mesh_size_bytes': 0,
                'ply_data': {},
                'total_ply_files': 0,
                'total_ply_size_bytes': 0,
                'total_patient_size_bytes': 0,
                'error': f'Analysis failed: {str(e)}',
                'structure_type': 'unknown'
            })
    
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
