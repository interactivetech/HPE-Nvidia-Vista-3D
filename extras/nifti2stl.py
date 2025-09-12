#!/usr/bin/env python3
"""
NIfTI to STL Converter

Simple script to convert a NIfTI file directly to STL format using the modular
voxel2mesh.py and mesh2stl.py components.

Usage:
    python nifti2stl.py input.nii.gz [output.stl]
"""

import sys
from voxel2mesh import nifti_to_mesh
from mesh2stl import mesh_file_to_stl


def nifti_to_stl(nifti_path, stl_path=None, threshold=0.5):
    """
    Convert a NIfTI file directly to STL format using modular components.
    
    Args:
        nifti_path (str): Path to the NIfTI file
        stl_path (str): Path for the output STL file (optional)
        threshold (float): Threshold for mesh creation
    
    Returns:
        str: Path to the created STL file
    """
    # Generate output filename if not provided
    if stl_path is None:
        stl_path = nifti_path.replace('.nii.gz', '.stl').replace('.nii', '.stl')
    
    print(f"Converting {nifti_path} to {stl_path}...")
    
    # Step 1: Convert NIfTI to mesh using voxel2mesh.py
    print("Step 1: Converting NIfTI to mesh...")
    mesh_data = nifti_to_mesh(nifti_path, threshold)
    print(f"Created mesh with {len(mesh_data['vertices'])} vertices and {len(mesh_data['triangles'])} triangles")
    
    # Step 2: Save intermediate mesh file
    print("Step 2: Saving intermediate mesh file...")
    temp_mesh_file = nifti_path.replace('.nii.gz', '_temp.ply').replace('.nii', '_temp.ply')
    from voxel2mesh import save_mesh_to_file
    save_mesh_to_file(mesh_data, temp_mesh_file)
    
    # Step 3: Convert mesh file to STL using mesh2stl.py
    print("Step 3: Converting mesh to STL...")
    from mesh2stl import mesh_file_to_stl
    final_stl_path = mesh_file_to_stl(temp_mesh_file, stl_path)
    
    # Step 4: Clean up temporary file
    import os
    try:
        os.remove(temp_mesh_file)
        print(f"Cleaned up temporary file: {temp_mesh_file}")
    except:
        pass
    
    print(f"✅ STL file saved: {final_stl_path}")
    return final_stl_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python nifti2stl.py input.nii.gz [output.stl]")
        print("Example: python nifti2stl.py left_iliac_artery.nii.gz")
        sys.exit(1)
    
    nifti_file = sys.argv[1]
    stl_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        nifti_to_stl(nifti_file, stl_file)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
