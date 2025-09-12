#!/usr/bin/env python3
"""
Example Usage: Voxel2Mesh + Mesh2STL Pipeline

This script demonstrates how to use the voxel2mesh.py and mesh2stl.py modules
together to convert NIfTI medical imaging files to STL files for 3D printing.

Usage:
    python extras/example_usage.py
"""

from voxel2mesh import process_voxels_directory, nifti_to_mesh
from mesh2stl import export_meshes_to_stl_files, export_mesh_to_stl_bytes
import os
from pathlib import Path


def example_basic_pipeline():
    """Example 1: Basic pipeline - convert all voxels to STL files"""
    print("=== Example 1: Basic Pipeline ===")
    
    # Define paths
    voxels_dir = "/Users/dave/AI/HPE/HPE-Nvidia-Vista-3D/output/PA00000002/voxels"
    output_dir = "/Users/dave/AI/HPE/HPE-Nvidia-Vista-3D/output/PA00000002/stl_files"
    
    # Step 1: Convert NIfTI files to meshes
    print("Converting NIfTI files to meshes...")
    meshes = process_voxels_directory(voxels_dir, threshold=0.5)
    
    print(f"Created {len(meshes)} meshes:")
    for name in list(meshes.keys())[:5]:  # Show first 5
        print(f"  - {name}")
    if len(meshes) > 5:
        print(f"  ... and {len(meshes) - 5} more")
    
    # Step 2: Export to individual STL files
    print(f"\nExporting meshes to STL files in {output_dir}...")
    export_meshes_to_stl_files(meshes, output_dir)
    
    print(f"STL files saved to: {output_dir}")
    return meshes


def example_individual_file():
    """Example 2: Process individual NIfTI file"""
    print("\n=== Example 2: Individual File Processing ===")
    
    # Find a specific NIfTI file
    voxels_dir = Path("/Users/dave/AI/HPE/HPE-Nvidia-Vista-3D/output/PA00000002/voxels")
    nifti_files = list(voxels_dir.glob("**/*.nii.gz"))
    
    if nifti_files:
        nifti_file = nifti_files[0]  # Use first file found
        print(f"Processing individual file: {nifti_file.name}")
        
        # Convert single file to mesh
        mesh_data = nifti_to_mesh(str(nifti_file), threshold=0.5)
        
        # Convert to STL bytes
        stl_data = export_mesh_to_stl_bytes(mesh_data)
        
        # Save individual STL file
        output_file = f"/tmp/{nifti_file.stem}.stl"
        with open(output_file, 'wb') as f:
            f.write(stl_data)
        
        print(f"Individual STL file saved to: {output_file}")
    else:
        print("No NIfTI files found for individual processing")


def example_custom_meshes():
    """Example 3: Work with custom mesh data"""
    print("\n=== Example 3: Custom Mesh Data ===")
    
    # This would be your custom mesh data (example with dummy data)
    print("Note: This example shows how you would work with custom mesh data")
    print("In practice, you would have actual vertex and triangle arrays")
    
    # Example structure (not executed with dummy data)
    custom_meshes = {
        "custom_organ_1": {
            "vertices": "your_vertices_array_here",
            "triangles": "your_triangles_array_here"
        },
        "custom_organ_2": {
            "vertices": "your_vertices_array_here", 
            "triangles": "your_triangles_array_here"
        }
    }
    
    print("Custom mesh structure:")
    for name, data in custom_meshes.items():
        print(f"  - {name}: {list(data.keys())}")
    
    print("\nTo use custom meshes:")
    print("  export_meshes_to_stl_files(custom_meshes, '/output/path')")


def example_different_thresholds():
    """Example 4: Process with different thresholds"""
    print("\n=== Example 4: Different Thresholds ===")
    
    voxels_dir = "/Users/dave/AI/HPE/HPE-Nvidia-Vista-3D/output/PA00000002/voxels"
    
    # Process with different thresholds
    thresholds = [0.3, 0.5, 0.7]
    
    for threshold in thresholds:
        print(f"\nProcessing with threshold {threshold}...")
        meshes = process_voxels_directory(voxels_dir, threshold=threshold)
        
        # Count non-empty meshes
        non_empty = sum(1 for mesh in meshes.values() 
                       if len(mesh["vertices"]) > 0)
        
        print(f"  Created {len(meshes)} meshes, {non_empty} non-empty")
        
        # Save with threshold in filename
        output_dir = f"/Users/dave/AI/HPE/HPE-Nvidia-Vista-3D/output/PA00000002/stl_files_threshold_{threshold}"
        export_meshes_to_stl_files(meshes, output_dir)


def main():
    """Run all examples"""
    print("Voxel2Mesh + Mesh2STL Example Usage")
    print("=" * 50)
    
    try:
        # Run examples
        meshes = example_basic_pipeline()
        example_individual_file()
        example_custom_meshes()
        example_different_thresholds()
        
        print("\n" + "=" * 50)
        print("All examples completed successfully!")
        print(f"Total meshes processed: {len(meshes) if 'meshes' in locals() else 'N/A'}")
        
    except Exception as e:
        print(f"Error running examples: {e}")
        print("Make sure the voxels directory exists and contains NIfTI files")


if __name__ == "__main__":
    main()
