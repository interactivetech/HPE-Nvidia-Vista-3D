#!/usr/bin/env python3
"""
Fix Vista3D Voxel Colors

This script fixes the label ID mismatch issue in voxel files to ensure
proper color display according to vista3d_label_colors.json.

The issue: Individual voxel files contain original segmentation label IDs
but the color mapping system expects Vista3D label IDs.

This script:
1. Scans all voxel directories in the output folder
2. Validates each voxel file against vista3d_label_colors.json
3. Fixes any mismatched label IDs
4. Generates a comprehensive report
"""

import os
import sys
import json
from pathlib import Path
from utils.vista3d_color_validator import Vista3DColorValidator


def find_all_voxel_directories(output_dir: str) -> list:
    """Find all voxel directories in the output folder."""
    voxel_dirs = []
    output_path = Path(output_dir)
    
    if not output_path.exists():
        print(f"Error: Output directory {output_dir} does not exist")
        return voxel_dirs
    
    # Look for patient directories
    for patient_dir in output_path.iterdir():
        if patient_dir.is_dir():
            voxels_dir = patient_dir / 'voxels'
            if voxels_dir.exists():
                # Look for subdirectories within voxels
                for voxel_subdir in voxels_dir.iterdir():
                    if voxel_subdir.is_dir():
                        voxel_dirs.append(str(voxel_subdir))
    
    return voxel_dirs


def main():
    """Main function to fix all voxel color mappings."""
    print("=" * 80)
    print("VISTA3D VOXEL COLOR FIXER")
    print("=" * 80)
    print()
    
    # Get the output directory
    if len(sys.argv) > 1:
        output_dir = sys.argv[1]
    else:
        output_dir = "/Users/dave/AI/HPE/HPE-Nvidia-Vista-3D/output"
    
    print(f"Scanning output directory: {output_dir}")
    print()
    
    # Find all voxel directories
    voxel_dirs = find_all_voxel_directories(output_dir)
    
    if not voxel_dirs:
        print("No voxel directories found!")
        return
    
    print(f"Found {len(voxel_dirs)} voxel directories:")
    for voxel_dir in voxel_dirs:
        print(f"  - {voxel_dir}")
    print()
    
    # Initialize the validator
    validator = Vista3DColorValidator()
    
    # Process each directory
    total_fixed = 0
    total_files = 0
    results = []
    
    for voxel_dir in voxel_dirs:
        print(f"Processing: {voxel_dir}")
        
        # Validate first
        validation = validator.validate_voxel_directory(voxel_dir)
        total_files += validation['total_files']
        
        if validation['invalid_files'] > 0:
            print(f"  Found {validation['invalid_files']} invalid files, fixing...")
            
            # Fix the files
            fix_results = validator.fix_voxel_directory(voxel_dir)
            total_fixed += fix_results['files_fixed']
            
            results.append({
                'directory': voxel_dir,
                'total_files': validation['total_files'],
                'invalid_files': validation['invalid_files'],
                'files_fixed': fix_results['files_fixed'],
                'fixes': fix_results['fixes']
            })
            
            print(f"  Fixed {fix_results['files_fixed']} files")
        else:
            print(f"  All {validation['total_files']} files are valid")
            results.append({
                'directory': voxel_dir,
                'total_files': validation['total_files'],
                'invalid_files': 0,
                'files_fixed': 0,
                'fixes': []
            })
        print()
    
    # Generate summary report
    print("=" * 80)
    print("SUMMARY REPORT")
    print("=" * 80)
    print(f"Total directories processed: {len(voxel_dirs)}")
    print(f"Total voxel files: {total_files}")
    print(f"Total files fixed: {total_fixed}")
    print()
    
    if total_fixed > 0:
        print("FIXED DIRECTORIES:")
        print("-" * 40)
        for result in results:
            if result['files_fixed'] > 0:
                print(f"Directory: {os.path.basename(result['directory'])}")
                print(f"  Files fixed: {result['files_fixed']}/{result['total_files']}")
                print(f"  Fixes applied:")
                for fix in result['fixes']:
                    print(f"    - {fix}")
                print()
    else:
        print("No files needed fixing - all voxel files already have correct label IDs!")
    
    print("=" * 80)
    print("Voxel color fixing completed!")
    print("Individual voxels should now display in their defined colors from vista3d_label_colors.json")
    print("=" * 80)


if __name__ == "__main__":
    main()
