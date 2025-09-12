"""
Mesh2STL: Convert 3D meshes to STL files

This module provides functionality to convert 3D mesh data to STL (STereoLithography)
files, which are commonly used for 3D printing and CAD applications. It works with
mesh data in the format returned by voxel2mesh.py.

Dependencies:
    - open3d: For 3D mesh processing
    - trimesh: For STL export functionality
    - numpy: For numerical operations

Example Usage:
    # Basic usage with voxel2mesh
    from voxel2mesh import process_voxels_directory
    from mesh2stl import export_meshes_to_stl_files
    
    # Step 1: Convert NIfTI files to meshes
    meshes = process_voxels_directory("/path/to/voxels", threshold=0.5)
    
    # Step 2: Export to individual STL files
    export_meshes_to_stl_files(meshes, "/path/to/output/stl_files")
    
    # Process individual mesh
    from mesh2stl import export_mesh_to_stl_bytes
    stl_data = export_mesh_to_stl_bytes(mesh_data)
    with open("single_mesh.stl", "wb") as f:
        f.write(stl_data)
    
    # Advanced usage with custom mesh data
    custom_meshes = {
        "heart": {"vertices": vertices_array, "triangles": triangles_array},
        "liver": {"vertices": vertices_array, "triangles": triangles_array}
    }
    export_meshes_to_stl_files(custom_meshes, "/output/path")
"""

import open3d as o3d
import trimesh
import numpy as np
from pathlib import Path


def o3d_to_trimesh(data):
    return trimesh.Trimesh(
        vertices=data["vertices"], faces=data["triangles"], process=False
    )


def export_mesh_to_stl_bytes(o3d_mesh):
    tmesh = o3d_to_trimesh(o3d_mesh)
    return tmesh.export(file_type="stl")  # returns bytes


def load_mesh_from_file(mesh_path):
    """
    Load mesh data from a file (PLY, OBJ, etc.).
    
    Args:
        mesh_path (str): Path to the mesh file
    
    Returns:
        dict: Mesh data with 'vertices' and 'triangles' keys
    """
    mesh = o3d.io.read_triangle_mesh(mesh_path)
    
    if len(mesh.vertices) == 0:
        raise ValueError(f"No mesh data found in {mesh_path}")
    
    return {
        "vertices": np.asarray(mesh.vertices),
        "triangles": np.asarray(mesh.triangles)
    }


def mesh_file_to_stl(mesh_path, stl_path=None):
    """
    Convert a mesh file to STL format.
    
    Args:
        mesh_path (str): Path to the input mesh file
        stl_path (str): Path for the output STL file (optional)
    
    Returns:
        str: Path to the created STL file
    """
    # Generate output filename if not provided
    if stl_path is None:
        if mesh_path.endswith('.ply'):
            stl_path = mesh_path.replace('.ply', '.stl')
        elif mesh_path.endswith('.obj'):
            stl_path = mesh_path.replace('.obj', '.stl')
        else:
            stl_path = mesh_path + '.stl'
    
    print(f"Converting {mesh_path} to {stl_path}...")
    
    # Load mesh from file
    mesh_data = load_mesh_from_file(mesh_path)
    print(f"Loaded mesh with {len(mesh_data['vertices'])} vertices and {len(mesh_data['triangles'])} triangles")
    
    # Convert to STL
    stl_data = export_mesh_to_stl_bytes(mesh_data)
    
    # Save STL file
    with open(stl_path, 'wb') as f:
        f.write(stl_data)
    
    print(f"✅ STL file saved: {stl_path}")
    return stl_path


def export_meshes_to_stl_files(combined_meshes, output_dir):
    """
    Export a dictionary of meshes to individual STL files.
    
    Args:
        combined_meshes (dict): Dictionary of mesh data
        output_dir (str): Output directory for STL files
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    for mesh_name, mesh_data in combined_meshes.items():
        stl_data = export_mesh_to_stl_bytes(mesh_data)
        stl_path = output_path / f"{mesh_name}.stl"
        with open(stl_path, 'wb') as f:
            f.write(stl_data)
        print(f"Saved: {stl_path}")


if __name__ == "__main__":
    import sys
    
    # Check if mesh file path is provided as argument
    if len(sys.argv) > 1:
        mesh_file = sys.argv[1]
        stl_file = sys.argv[2] if len(sys.argv) > 2 else None
        
        try:
            mesh_file_to_stl(mesh_file, stl_file)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        # Example usage
        print("Usage: python mesh2stl.py input_mesh.ply [output.stl]")
        print("Example: python mesh2stl.py left_iliac_artery.ply")
        print("\nSupported formats: PLY, OBJ, and other Open3D-supported mesh formats")
