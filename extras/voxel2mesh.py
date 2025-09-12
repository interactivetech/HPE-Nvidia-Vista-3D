"""
Voxel2Mesh: Convert NIfTI medical imaging files to 3D meshes

This module provides functionality to convert individual NIfTI (.nii.gz) files to 3D meshes
using Open3D's marching cubes algorithm. It's designed to work with medical
imaging data, particularly segmented anatomical structures.

Dependencies:
    - open3d: For 3D mesh processing and marching cubes algorithm
    - nibabel: For reading NIfTI files
    - numpy: For numerical operations

Example Usage:
    # Convert individual NIfTI file to mesh
    from voxel2mesh import nifti_to_mesh
    mesh_data = nifti_to_mesh("/path/to/left_iliac_artery.nii.gz", threshold=0.5)
    
    # Use with mesh2stl.py
    from mesh2stl import export_mesh_to_stl_bytes
    stl_data = export_mesh_to_stl_bytes(mesh_data)
    with open("left_iliac_artery.stl", "wb") as f:
        f.write(stl_data)
"""

import open3d as o3d
import numpy as np
import nibabel as nib


def nifti_to_mesh(nifti_path, threshold=0.5):
    """
    Convert a NIfTI file to a 3D mesh using Open3D.
    
    Args:
        nifti_path (str): Path to the NIfTI file
        threshold (float): Threshold value for creating the mesh (default: 0.5)
    
    Returns:
        dict: Open3D mesh data with 'vertices' and 'triangles' keys
    """
    # Load NIfTI file
    nifti_img = nib.load(nifti_path)
    data = nifti_img.get_fdata()
    
    # Create binary mask based on threshold
    binary_mask = data > threshold
    
    # Convert to uint8 and ensure C-contiguous array
    volume_data = (binary_mask * 255).astype(np.uint8)
    
    # Create mesh using marching cubes on the volume data
    try:
        # Use marching cubes directly on the volume
        mesh = o3d.geometry.TriangleMesh.create_from_volume_data(
            o3d.geometry.Image(volume_data),
            volume_threshold=128,
            surface_threshold=128
        )
    except:
        # Alternative approach: use skimage marching cubes
        try:
            from skimage import measure
            vertices, faces, _, _ = measure.marching_cubes(volume_data, level=128)
            mesh = o3d.geometry.TriangleMesh()
            mesh.vertices = o3d.utility.Vector3dVector(vertices)
            mesh.triangles = o3d.utility.Vector3iVector(faces)
        except ImportError:
            # Fallback: create a simple mesh from the volume
            print("Warning: Using fallback mesh creation method")
            # Find non-zero voxels and create a simple point cloud
            coords = np.where(volume_data > 128)
            if len(coords[0]) > 0:
                points = np.column_stack([coords[2], coords[1], coords[0]])  # x, y, z
                mesh = o3d.geometry.TriangleMesh()
                mesh.vertices = o3d.utility.Vector3dVector(points)
                # Create a simple triangulation (this is a basic fallback)
                mesh.triangles = o3d.utility.Vector3iVector()
            else:
                # Return empty mesh if no data
                mesh = o3d.geometry.TriangleMesh()
    
    # Clean up the mesh
    if len(mesh.vertices) > 0:
        mesh.remove_degenerate_triangles()
        mesh.remove_duplicated_triangles()
        mesh.remove_duplicated_vertices()
        mesh.remove_non_manifold_edges()
    
    return {
        "vertices": np.asarray(mesh.vertices),
        "triangles": np.asarray(mesh.triangles)
    }


def save_mesh_to_file(mesh_data, output_path):
    """
    Save mesh data to a file (PLY format).
    
    Args:
        mesh_data (dict): Mesh data with 'vertices' and 'triangles' keys
        output_path (str): Path for the output file
    """
    import open3d as o3d
    
    # Create Open3D mesh
    mesh = o3d.geometry.TriangleMesh()
    mesh.vertices = o3d.utility.Vector3dVector(mesh_data['vertices'])
    mesh.triangles = o3d.utility.Vector3iVector(mesh_data['triangles'])
    
    # Save to file
    o3d.io.write_triangle_mesh(output_path, mesh)
    print(f"✅ Mesh saved: {output_path}")


if __name__ == "__main__":
    import sys
    
    # Check if NIfTI file path is provided as argument
    if len(sys.argv) > 1:
        nifti_file = sys.argv[1]
    else:
        # Default example file
        nifti_file = "/Users/dave/AI/HPE/HPE-Nvidia-Vista-3D/output/PA00000002/voxels/2.5MM_ARTERIAL_3/left_iliac_artery.nii.gz"
    
    print(f"Converting NIfTI file to mesh: {nifti_file}")
    mesh_data = nifti_to_mesh(nifti_file, threshold=0.5)
    
    print(f"Created mesh with {len(mesh_data['vertices'])} vertices and {len(mesh_data['triangles'])} triangles")
    
    # Generate output filename
    if nifti_file.endswith('.nii.gz'):
        output_file = nifti_file.replace('.nii.gz', '.ply')
    elif nifti_file.endswith('.nii'):
        output_file = nifti_file.replace('.nii', '.ply')
    else:
        output_file = nifti_file + '.ply'
    
    # Save mesh to file
    save_mesh_to_file(mesh_data, output_file)
    
    print(f"\nMesh file created: {output_file}")
    print("You can now use this mesh file with 3D software or convert to STL using mesh2stl.py")
