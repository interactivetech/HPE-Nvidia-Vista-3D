#!/usr/bin/env python3
"""
Test script for improved mesh generation methods.
This script tests different approaches to convert voxel data to STL meshes.
"""

import os
import sys
import tempfile
import requests
from pathlib import Path

# Add utils to path
sys.path.append(str(Path(__file__).parent / 'utils'))

from improved_voxel2stl import convert_nii_to_stl_improved, convert_nii_to_stl_vtk, convert_nii_to_stl_open3d

def test_mesh_generation():
    """Test mesh generation with different methods."""
    
    # Test data from image server
    patient_id = "PA00000002"
    ct_scan = "2.5MM_ARTERIAL_3"
    voxel_file = "aorta.nii.gz"
    
    voxel_url = f"http://localhost:8888/output/{patient_id}/voxels/{ct_scan}/{voxel_file}"
    
    print(f"Testing mesh generation for: {voxel_file}")
    print(f"Source: {voxel_url}")
    
    # Download voxel file
    try:
        response = requests.get(voxel_url, timeout=10)
        if response.status_code != 200:
            print(f"Failed to download voxel file: {response.status_code}")
            return
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.nii.gz', delete=False) as tmp_file:
            tmp_file.write(response.content)
            tmp_file.flush()
            nii_path = tmp_file.name
        
        print(f"Downloaded voxel file to: {nii_path}")
        
        # Test different methods
        methods = [
            ("VTK", "vtk"),
            ("Open3D", "open3d"),
            ("Auto (VTK first)", "auto")
        ]
        
        for method_name, method_code in methods:
            print(f"\n--- Testing {method_name} ---")
            
            # Create output path
            output_path = f"test_output_{method_code}.stl"
            
            # Convert
            success = convert_nii_to_stl_improved(
                nii_path, 
                output_path, 
                method=method_code,
                clean_mesh=True
            )
            
            if success:
                # Check file size
                file_size = os.path.getsize(output_path)
                print(f"✓ {method_name} succeeded: {output_path} ({file_size} bytes)")
            else:
                print(f"✗ {method_name} failed")
        
        # Clean up
        os.unlink(nii_path)
        
    except Exception as e:
        print(f"Error during testing: {e}")

if __name__ == "__main__":
    test_mesh_generation()
