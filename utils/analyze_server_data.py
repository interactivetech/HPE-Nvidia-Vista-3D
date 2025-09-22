#!/usr/bin/env python3
"""
Simple script to read the output folder from .env and print patient folder names.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

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
    
    # Get OUTPUT_FOLDER from environment variable
    output_folder = os.getenv("OUTPUT_FOLDER", "output")
    return output_folder

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

def get_folder_size(folder_path: Path) -> int:
    """Calculate total size of a folder recursively."""
    total_size = 0
    try:
        for item in folder_path.rglob('*'):
            if item.is_file():
                total_size += item.stat().st_size
    except (OSError, PermissionError):
        # Skip files/folders we can't access
        pass
    return total_size

def count_nifti_scans(patient_folder_path: Path) -> int:
    """Count the number of NIfTI scan files in a patient's nifti folder."""
    nifti_folder = patient_folder_path / "nifti"
    
    if not nifti_folder.exists() or not nifti_folder.is_dir():
        return 0
    
    # Count .nii.gz files in the nifti folder
    nifti_count = 0
    try:
        for item in nifti_folder.iterdir():
            if item.is_file() and item.name.endswith('.nii.gz'):
                nifti_count += 1
    except (OSError, PermissionError):
        # Skip if we can't access the folder
        pass
    
    return nifti_count

def get_scan_voxel_counts(patient_folder_path: Path) -> dict:
    """Get voxel counts for each scan in the patient's voxels folder."""
    voxels_folder = patient_folder_path / "voxels"
    scan_voxels = {}
    
    if not voxels_folder.exists() or not voxels_folder.is_dir():
        return scan_voxels
    
    try:
        # Look for subfolders in the voxels directory
        for item in voxels_folder.iterdir():
            if item.is_dir():
                # Count .nii.gz files in this scan's subfolder
                voxel_count = 0
                for voxel_file in item.iterdir():
                    if voxel_file.is_file() and voxel_file.name.endswith('.nii.gz'):
                        voxel_count += 1
                
                if voxel_count > 0:
                    scan_voxels[item.name] = voxel_count
    except (OSError, PermissionError):
        # Skip if we can't access the folder
        pass
    
    return scan_voxels

def get_patient_folders(output_folder: str) -> list:
    """Get list of patient folders with their sizes and scan counts from the output directory."""
    output_path = Path(output_folder)
    
    if not output_path.exists():
        print(f"❌ Output folder does not exist: {output_path}")
        return []
    
    if not output_path.is_dir():
        print(f"❌ Output path is not a directory: {output_path}")
        return []
    
    # Get all directories in the output folder with their sizes and scan counts
    patient_folders = []
    for item in output_path.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            folder_size = get_folder_size(item)
            scan_count = count_nifti_scans(item)
            scan_voxels = get_scan_voxel_counts(item)
            patient_folders.append({
                'name': item.name,
                'size_bytes': folder_size,
                'size_display': format_file_size(folder_size),
                'scan_count': scan_count,
                'scan_voxels': scan_voxels
            })
    
    # Sort by folder name
    return sorted(patient_folders, key=lambda x: x['name'])

def get_patient_cards_data():
    """
    Get patient data formatted for the Image Data page cards.
    
    Returns:
        dict: Dictionary containing patient cards data and summary statistics
    """
    try:
        # Load configuration
        output_folder = load_environment_config()
        
        # Get patient folders
        patient_folders = get_patient_folders(output_folder)
        
        if not patient_folders:
            return {
                'error': 'No patient folders found in output directory',
                'patient_cards': [],
                'summary_stats': {}
            }
        
        # Convert patient folders to card format
        patient_cards = []
        total_nifti_files = 0
        total_voxel_files = 0
        total_ply_files = 0
        total_size_bytes = 0
        
        for folder_info in patient_folders:
            # Count PLY files (mesh files)
            ply_count = count_ply_files(Path(output_folder) / folder_info['name'])
            
            # Count total voxel files across all scans
            total_voxels = sum(folder_info['scan_voxels'].values()) if folder_info['scan_voxels'] else 0
            
            # Create patient card
            card = {
                'patient_id': folder_info['name'],
                'status': 'success',
                'nifti_files': folder_info['scan_count'],
                'voxel_files': total_voxels,
                'ply_files': ply_count,
                'total_size': folder_info['size_display'],
                'ct_scan_details': [
                    {
                        'name': scan_name,
                        'voxel_count': voxel_count
                    }
                    for scan_name, voxel_count in folder_info['scan_voxels'].items()
                ] if folder_info['scan_voxels'] else []
            }
            
            patient_cards.append(card)
            
            # Update totals
            total_nifti_files += folder_info['scan_count']
            total_voxel_files += total_voxels
            total_ply_files += ply_count
            total_size_bytes += folder_info['size_bytes']
        
        # Create summary statistics
        summary_stats = {
            'total_patients': len(patient_cards),
            'total_nifti_files': total_nifti_files,
            'total_voxel_files': total_voxel_files,
            'total_ply_files': total_ply_files,
            'total_data_size': format_file_size(total_size_bytes),
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

def count_ply_files(patient_folder_path: Path) -> int:
    """Count the number of PLY files in a patient's mesh folder."""
    mesh_folder = patient_folder_path / "mesh"
    
    if not mesh_folder.exists() or not mesh_folder.is_dir():
        return 0
    
    # Count .ply files in the mesh folder
    ply_count = 0
    try:
        for item in mesh_folder.iterdir():
            if item.is_file() and item.name.endswith('.ply'):
                ply_count += 1
    except (OSError, PermissionError):
        # Skip if we can't access the folder
        pass
    
    return ply_count

def main():
    """Main function to list patient folders."""
    print("🔍 Analyzing output folder...")
    
    # Load configuration
    output_folder = load_environment_config()
    print(f"📁 Output folder: {output_folder}")
    
    # Get patient folders
    patient_folders = get_patient_folders(output_folder)
    
    if not patient_folders:
        print("❌ No patient folders found in output directory")
        return
    
    print(f"✅ Found {len(patient_folders)} patient folders:")
    print("-" * 80)
    
    total_size = 0
    total_scans = 0
    total_voxels = 0
    
    for i, folder_info in enumerate(patient_folders, 1):
        print(f"{i:2d}. {folder_info['name']:<20} {folder_info['scan_count']:>3} scans {folder_info['size_display']:>10}")
        
        # Show voxel counts for each scan
        if folder_info['scan_voxels']:
            for scan_name, voxel_count in folder_info['scan_voxels'].items():
                print(f"    └─ {scan_name:<30} {voxel_count:>3} voxels")
                total_voxels += voxel_count
        else:
            print("    └─ No voxel data found")
        
        total_size += folder_info['size_bytes']
        total_scans += folder_info['scan_count']
        print()  # Empty line between patients
    
    print("-" * 80)
    print(f"Total: {len(patient_folders)} patient folders, {total_scans} scans, {total_voxels} voxels")
    print(f"Total size: {format_file_size(total_size)}")

if __name__ == "__main__":
    main()
