#!/usr/bin/env python3
"""
Voxel Smoothing Script for Vista-3D Pipeline
Applies Gaussian smoothing to segmented voxel files to reduce blockiness
and improve anatomical accuracy of Vista3D segmentations.
"""

import os
import argparse
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm
import nibabel as nib
import traceback

# Try importing nilearn
try:
    from nilearn import image as nimage
except ImportError:
    print("❌ Error: nilearn is not installed. Please install it with: pip install nilearn")
    exit(1)

# Import the shared constants
import sys
sys.path.append(str(Path(__file__).parent))
from constants import MIN_FILE_SIZE_MB


# Smoothing presets (kernel sizes for morphological operations)
SMOOTHING_PRESETS = {
    'light': 3,      # Small kernel - gentle smoothing
    'medium': 5,     # Medium kernel - moderate smoothing  
    'heavy': 7,      # Large kernel - strong smoothing
    'extra_heavy': 9, # Very large kernel - very strong smoothing
    'ultra_heavy': 11 # Extra large kernel - maximum smoothing
}


def load_environment():
    """Load environment variables from .env file"""
    load_dotenv()
    
    # Check if we're running in a Docker container
    is_docker = os.path.exists('/.dockerenv') or os.environ.get('DOCKER_CONTAINER') == 'true'
    
    if is_docker:
        # In Docker container, use the mounted paths
        output_folder = '/app/output'
    else:
        # On host machine, use environment variables
        output_folder = os.getenv('OUTPUT_FOLDER')
        
        if not output_folder:
            raise ValueError("OUTPUT_FOLDER not found in .env file")
        
        # OUTPUT_FOLDER should be a full path
        if not os.path.isabs(output_folder):
            raise ValueError("OUTPUT_FOLDER must be set in .env file with full absolute path")
    
    return Path(output_folder)


def get_voxel_files(patient_id: str, scan_name: str, output_folder: Path):
    """
    Find all voxel NIfTI files for a specific patient and scan.
    Returns list of file paths.
    """
    voxels_dir = output_folder / patient_id / "voxels" / scan_name
    
    if not voxels_dir.exists() or not voxels_dir.is_dir():
        return []
    
    voxel_files = []
    for f in os.listdir(voxels_dir):
        if f.endswith('.nii.gz'):
            file_path = voxels_dir / f
            voxel_files.append(file_path)
    
    return sorted(voxel_files)


def smooth_voxel_file(file_path: Path, kernel_size: int, method: str = "morphological"):
    """
    Apply smoothing to a voxel file and overwrite it.
    
    Args:
        file_path: Path to the voxel NIfTI file
        kernel_size: Kernel size for morphological operations (integer)
        method: Smoothing method - "gaussian" or "morphological" (default: morphological)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Load the NIfTI file
        img = nib.load(str(file_path))
        data = img.get_fdata()
        
        if method == "morphological":
            # Enhanced binary morphological smoothing for segmentation voxels
            from scipy import ndimage
            import numpy as np
            
            # Extract the label ID (non-zero value)
            unique_vals = np.unique(data)
            non_zero_vals = unique_vals[unique_vals > 0]
            
            if len(non_zero_vals) == 0:
                # No data to smooth
                smoothed_img = img
            else:
                # Use the most common non-zero value as the label ID
                label_id = non_zero_vals[0] if len(non_zero_vals) == 1 else int(np.median(non_zero_vals))
                
                # Create binary mask
                binary_mask = (data > 0).astype(np.float32)
                
                # Step 1: Morphological opening to remove small protrusions
                structure = np.ones((kernel_size, kernel_size, kernel_size))
                opened = ndimage.binary_opening(binary_mask, structure=structure)
                
                # Step 2: Morphological closing to fill small holes
                closed = ndimage.binary_closing(opened, structure=structure)
                
                # Step 3: Apply Gaussian filter to smooth the boundary
                # Use sigma proportional to kernel size for consistent smoothing
                sigma = kernel_size / 3.0
                gaussian_smoothed = ndimage.gaussian_filter(closed.astype(np.float32), sigma=sigma)
                
                # Step 4: Threshold to get clean binary mask
                smoothed_mask = (gaussian_smoothed > 0.5).astype(np.uint8)
                
                # Step 5: Convert back to label ID format
                smoothed_data = smoothed_mask.astype(np.int16) * label_id
                
                # Create new image
                smoothed_img = nib.Nifti1Image(smoothed_data, img.affine, img.header)
        else:
            # Gaussian smoothing (fallback for continuous data)
            # Convert kernel size to approximate FWHM for Gaussian smoothing
            fwhm = kernel_size * 2.0  # Rough approximation
            smoothed_img = nimage.smooth_img(img, fwhm=fwhm)
        
        # Save back to the same file (overwrite)
        nib.save(smoothed_img, str(file_path))
        
        return True
    except Exception as e:
        print(f"❌ Error smoothing {file_path.name}: {str(e)}")
        traceback.print_exc()
        return False


def get_available_scans(patient_id: str, output_folder: Path):
    """Get list of available scan names for a patient."""
    voxels_dir = output_folder / patient_id / "voxels"
    
    if not voxels_dir.exists() or not voxels_dir.is_dir():
        return []
    
    scans = []
    for entry in os.scandir(voxels_dir):
        if entry.is_dir():
            scans.append(entry.name)
    
    return sorted(scans)


def process_patients(patient_ids: list, selected_scans: list, smoothing_level: str, output_folder: Path):
    """
    Main processing loop for smoothing voxel files.
    
    Args:
        patient_ids: List of patient IDs to process
        selected_scans: List of scan names to process (empty means all)
        smoothing_level: Smoothing preset level ('light', 'medium', 'heavy')
        output_folder: Path to output folder
    """
    # Get kernel size from preset
    kernel_size = SMOOTHING_PRESETS.get(smoothing_level, SMOOTHING_PRESETS['medium'])
    
    print("=" * 80)
    print("Voxel Smoothing Tool")
    print("=" * 80)
    print(f"Smoothing level: {smoothing_level} (Kernel size: {kernel_size})")
    print(f"Processing {len(patient_ids)} patient(s)")
    print("=" * 80)
    
    total_files = 0
    successful_files = 0
    failed_files = 0
    
    # Process each patient
    for patient_id in patient_ids:
        print(f"\n📁 Processing patient: {patient_id}")
        
        # Get available scans for this patient
        available_scans = get_available_scans(patient_id, output_folder)
        
        if not available_scans:
            print(f"  ⚠️  No voxel folders found for patient {patient_id}")
            continue
        
        # Determine which scans to process
        if selected_scans:
            # Filter to only selected scans that are available
            scans_to_process = [s for s in selected_scans if s in available_scans]
        else:
            # Process all available scans
            scans_to_process = available_scans
        
        if not scans_to_process:
            print(f"  ⚠️  No matching scans found for patient {patient_id}")
            continue
        
        print(f"  Processing {len(scans_to_process)} scan(s): {', '.join(scans_to_process)}")
        
        # Process each scan
        for scan_name in scans_to_process:
            print(f"\n  🔬 Scan: {scan_name}")
            
            # Get all voxel files for this scan
            voxel_files = get_voxel_files(patient_id, scan_name, output_folder)
            
            if not voxel_files:
                print(f"    ⚠️  No voxel files found")
                continue
            
            print(f"    Found {len(voxel_files)} voxel file(s)")
            
            # Process each voxel file with progress bar
            for voxel_file in tqdm(voxel_files, desc=f"    Smoothing", unit="file"):
                total_files += 1
                if smooth_voxel_file(voxel_file, kernel_size):
                    successful_files += 1
                else:
                    failed_files += 1
    
    # Print summary
    print("\n" + "=" * 80)
    print("Smoothing Process Complete")
    print("=" * 80)
    print(f"Total files processed: {total_files}")
    print(f"✅ Successful: {successful_files}")
    if failed_files > 0:
        print(f"❌ Failed: {failed_files}")
    print("=" * 80)
    
    return successful_files, failed_files


def main():
    """Main function for command-line execution."""
    parser = argparse.ArgumentParser(
        description="Apply binary morphological smoothing to Vista3D voxel segmentations"
    )
    parser.add_argument(
        'patients',
        nargs='*',
        help='Patient IDs to process (leave empty to process all)'
    )
    parser.add_argument(
        '--smoothing',
        choices=['light', 'medium', 'heavy', 'extra_heavy', 'ultra_heavy'],
        default='medium',
        help='Smoothing level preset - kernel size for morphological operations (default: medium)'
    )
    
    args = parser.parse_args()
    
    try:
        # Load environment
        output_folder = load_environment()
        
        # Get selected scans from environment variable
        selected_scans_str = os.getenv('SELECTED_SCANS', '')
        selected_scans = [s.strip() for s in selected_scans_str.split(',') if s.strip()] if selected_scans_str else []
        
        # Determine which patients to process
        if args.patients:
            patient_ids = args.patients
        else:
            # Process all patients with voxel folders
            patient_ids = []
            for entry in os.scandir(output_folder):
                if entry.is_dir():
                    voxels_dir = output_folder / entry.name / "voxels"
                    if voxels_dir.exists() and voxels_dir.is_dir():
                        patient_ids.append(entry.name)
            
            if not patient_ids:
                print("❌ No patients with voxel folders found")
                return
        
        # Process patients
        successful, failed = process_patients(patient_ids, selected_scans, args.smoothing, output_folder)
        
        # Exit with appropriate code
        if failed > 0:
            exit(1)
        else:
            exit(0)
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()

