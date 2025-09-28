#!/usr/bin/env python3
"""
Simple script to read the output folder from .env and print patient folder names.
Uses the image server to gather data instead of reading from local file system.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent))

from utils.data_manager import DataManager

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
    
    # Get IMAGE_SERVER_URL from environment variable
    image_server_url = os.getenv("IMAGE_SERVER", "http://localhost:8888")
    return image_server_url

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

def count_nifti_scans(data_manager: DataManager, patient_id: str) -> int:
    """Count the number of NIfTI scan files in a patient's nifti folder using image server."""
    try:
        nifti_files = data_manager.get_server_data(f"{patient_id}/nifti", 'files', ('.nii.gz', '.nii'))
        return len(nifti_files)
    except Exception as e:
        print(f"Error counting NIfTI scans for {patient_id}: {e}")
        return 0

def get_scan_voxel_counts(data_manager: DataManager, patient_id: str) -> dict:
    """Get voxel counts for each scan in the patient's voxels folder using image server."""
    scan_voxels = {}
    
    try:
        # Get list of scan folders in the voxels directory
        voxels_folder_contents = data_manager.get_folder_contents(f"{patient_id}/voxels")
        if not voxels_folder_contents:
            return scan_voxels
        
        # Look for subfolders (scan directories) in the voxels directory
        for item in voxels_folder_contents:
            if item['is_directory']:
                scan_name = item['name']
                # Check if this scan has enhancement subfolders
                enhancement_folders = data_manager.get_folder_contents(f"{patient_id}/voxels/{scan_name}")
                
                if enhancement_folders:
                    # This scan has enhancement subfolders
                    enhancement_counts = {}
                    total_voxels = 0
                    
                    for enhancement_item in enhancement_folders:
                        if enhancement_item['is_directory']:
                            enhancement_name = enhancement_item['name']
                            # Count .nii.gz files in this enhancement subfolder
                            voxel_files = data_manager.get_server_data(f"{patient_id}/voxels/{scan_name}/{enhancement_name}", 'files', ('.nii.gz',))
                            if voxel_files:
                                enhancement_counts[enhancement_name] = len(voxel_files)
                                total_voxels += len(voxel_files)
                    
                    if enhancement_counts:
                        scan_voxels[scan_name] = {
                            'total_voxels': total_voxels,
                            'enhancements': enhancement_counts
                        }
                else:
                    # This scan is a simple folder with direct .nii.gz files
                    voxel_files = data_manager.get_server_data(f"{patient_id}/voxels/{scan_name}", 'files', ('.nii.gz',))
                    if voxel_files:
                        scan_voxels[scan_name] = {
                            'total_voxels': len(voxel_files),
                            'enhancements': {}
                        }
    except Exception as e:
        print(f"Error getting voxel counts for {patient_id}: {e}")
    
    return scan_voxels

def count_ply_files(data_manager: DataManager, patient_id: str) -> int:
    """Count the number of PLY files in a patient's mesh folder using image server."""
    try:
        ply_files = data_manager.get_server_data(f"{patient_id}/mesh", 'files', ('.ply',))
        return len(ply_files)
    except Exception as e:
        print(f"Error counting PLY files for {patient_id}: {e}")
        return 0

def calculate_patient_folder_size(data_manager: DataManager, patient_id: str) -> int:
    """Calculate total size of all files in a patient folder using image server."""
    total_size = 0
    
    try:
        # Get all subdirectories in the patient folder
        patient_contents = data_manager.get_folder_contents(patient_id)
        if not patient_contents:
            return 0
        
        # Sum up sizes of all files in all subdirectories
        for item in patient_contents:
            if item['is_directory']:
                # Recursively get files in subdirectories
                subdir_contents = data_manager.get_folder_contents(f"{patient_id}/{item['name']}")
                if subdir_contents:
                    for subitem in subdir_contents:
                        if not subitem['is_directory']:
                            total_size += subitem.get('size_bytes', 0)
            else:
                # Direct file in patient folder
                total_size += item.get('size_bytes', 0)
                
    except Exception as e:
        print(f"Error calculating folder size for {patient_id}: {e}")
    
    return total_size

def get_patient_folders(data_manager: DataManager) -> list:
    """Get list of patient folders with their scan counts from the image server."""
    try:
        # Get list of patient folders from the output directory on the server
        patient_folders = []
        
        # Use direct URL access to get the output directory listing
        import requests
        from bs4 import BeautifulSoup
        
        output_url = f"{data_manager.image_server_url}/output/"
        try:
            response = requests.get(output_url, timeout=30)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                output_contents = []
                for item in soup.find_all('li'):
                    link = item.find('a')
                    if link and link.get('href'):
                        text = link.get_text().strip()
                        if text == "📁 ../" or text.endswith('../'):
                            continue
                        is_directory = text.startswith('📁') or text.endswith('/')
                        name = text.replace('📁', '').replace('📄', '').strip('/').strip()
                        if name:  # Only add non-empty names
                            output_contents.append({'name': name, 'is_directory': is_directory})
            else:
                print(f"❌ Image server returned HTTP {response.status_code} for URL: {output_url}")
                return []
        except Exception as e:
            print(f"❌ Error accessing output directory: {e}")
            return []
        
        if not output_contents:
            print("❌ No patient folders found on image server")
            return []
        
        # Filter for directories (patient folders)
        for item in output_contents:
            if item['is_directory'] and not item['name'].startswith('.'):
                patient_id = item['name']
                scan_count = count_nifti_scans(data_manager, patient_id)
                scan_voxels = get_scan_voxel_counts(data_manager, patient_id)
                
                # Calculate total size for this patient folder
                total_size_bytes = calculate_patient_folder_size(data_manager, patient_id)
                size_display = format_file_size(total_size_bytes)
                
                patient_folders.append({
                    'name': patient_id,
                    'size_bytes': total_size_bytes,
                    'size_display': size_display,
                    'scan_count': scan_count,
                    'scan_voxels': scan_voxels
                })
        
        # Sort by folder name
        return sorted(patient_folders, key=lambda x: x['name'])
        
    except Exception as e:
        print(f"❌ Error getting patient folders from image server: {e}")
        return []

def get_patient_cards_data():
    """
    Get patient data formatted for the Image Data page cards.
    
    Returns:
        dict: Dictionary containing patient cards data and summary statistics
    """
    try:
        # Load configuration
        image_server_url = load_environment_config()
        
        # Initialize data manager
        data_manager = DataManager(image_server_url)
        
        # Get patient folders
        patient_folders = get_patient_folders(data_manager)
        
        if not patient_folders:
            return {
                'error': 'No patient folders found on image server',
                'patient_cards': [],
                'summary_stats': {}
            }
        
        # Convert patient folders to card format
        patient_cards = []
        total_nifti_files = 0
        total_voxel_files = 0
        total_ply_files = 0
        
        for folder_info in patient_folders:
            # Count PLY files (mesh files)
            ply_count = count_ply_files(data_manager, folder_info['name'])
            
            # Count total voxel files across all scans
            total_voxels = sum(scan_info['total_voxels'] for scan_info in folder_info['scan_voxels'].values()) if folder_info['scan_voxels'] else 0
            
            # Create patient card
            card = {
                'patient_id': folder_info['name'],
                'status': 'success',
                'nifti_files': folder_info['scan_count'],
                'voxel_files': total_voxels,
                'ply_files': ply_count,
                'total_size': folder_info['size_display'],
                'total_size_bytes': folder_info['size_bytes'],
                'ct_scan_details': [
                    {
                        'name': scan_name,
                        'voxel_count': scan_info['total_voxels'],
                        'enhancements': scan_info['enhancements']
                    }
                    for scan_name, scan_info in folder_info['scan_voxels'].items()
                ] if folder_info['scan_voxels'] else []
            }
            
            patient_cards.append(card)
            
            # Update totals
            total_nifti_files += folder_info['scan_count']
            total_voxel_files += total_voxels
            total_ply_files += ply_count
        
        # Calculate total data size
        total_data_size_bytes = sum(card.get('total_size_bytes', 0) for card in patient_cards)
        total_data_size_display = format_file_size(total_data_size_bytes)
        
        # Create summary statistics
        summary_stats = {
            'total_patients': len(patient_cards),
            'total_nifti_files': total_nifti_files,
            'total_voxel_files': total_voxel_files,
            'total_ply_files': total_ply_files,
            'total_data_size': total_data_size_display,
            'total_data_size_bytes': total_data_size_bytes,
            'generated_at': str(Path().cwd())  # Simple timestamp placeholder
        }
        
        return {
            'patient_cards': patient_cards,
            'summary_stats': summary_stats
        }
        
    except Exception as e:
        return {
            'error': f"Error analyzing server data: {str(e)}",
            'patient_cards': [],
            'summary_stats': {}
        }


def main():
    """Main function to list patient folders."""
    print("🔍 Analyzing image server data...")
    
    # Load configuration
    image_server_url = load_environment_config()
    print(f"🌐 Image server URL: {image_server_url}")
    
    try:
        # Initialize data manager
        data_manager = DataManager(image_server_url)
        
        # Get patient folders
        patient_folders = get_patient_folders(data_manager)
        
        if not patient_folders:
            print("❌ No patient folders found on image server")
            return
        
        print(f"✅ Found {len(patient_folders)} patient folders:")
        print("-" * 80)
        
        total_scans = 0
        total_voxels = 0
        
        for i, folder_info in enumerate(patient_folders, 1):
            print(f"{i:2d}. {folder_info['name']:<20} {folder_info['scan_count']:>3} scans {folder_info['size_display']:>10}")
            
            # Show voxel counts for each scan
            if folder_info['scan_voxels']:
                for scan_name, scan_info in folder_info['scan_voxels'].items():
                    print(f"    └─ {scan_name:<30} {scan_info['total_voxels']:>3} voxels")
                    total_voxels += scan_info['total_voxels']
                    
                    # Show enhancement details if available
                    if scan_info['enhancements']:
                        for enhancement_name, enhancement_count in scan_info['enhancements'].items():
                            print(f"        ├─ {enhancement_name:<25} {enhancement_count:>3} files")
            else:
                print("    └─ No voxel data found")
            
            total_scans += folder_info['scan_count']
            print()  # Empty line between patients
        
        print("-" * 80)
        total_size = sum(folder['size_bytes'] for folder in patient_folders)
        total_size_display = format_file_size(total_size)
        print(f"Total: {len(patient_folders)} patient folders, {total_scans} scans, {total_voxels} voxels")
        print(f"Total size: {total_size_display}")
        
    except Exception as e:
        print(f"❌ Error connecting to image server: {e}")
        print("Make sure the image server is running and accessible.")

if __name__ == "__main__":
    main()
