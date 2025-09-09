"""
Improved voxel to STL conversion using better methods.
This module provides superior mesh generation compared to basic marching cubes.
"""

import os
import numpy as np
import nibabel as nib
from pathlib import Path
import tempfile
import requests
from typing import Optional, Tuple

try:
    import vtk
    VTK_AVAILABLE = True
except ImportError:
    VTK_AVAILABLE = False
    print("VTK not available. Install with: pip install vtk")

try:
    import trimesh
    import pymeshfix
    TRIMESH_AVAILABLE = True
except ImportError:
    TRIMESH_AVAILABLE = False
    print("Trimesh/PyMeshFix not available. Install with: pip install trimesh pymeshfix")

try:
    import open3d as o3d
    OPEN3D_AVAILABLE = True
except ImportError:
    OPEN3D_AVAILABLE = False
    print("Open3D not available. Install with: pip install open3d")


def convert_nii_to_stl_vtk(nii_path: str, stl_path: str, threshold: float = 0.5, 
                          smoothing_iterations: int = 50, smoothing_factor: float = 0.1) -> bool:
    """
    Convert NIfTI to STL using VTK with proper medical imaging handling.
    
    Args:
        nii_path: Path to input NIfTI file
        stl_path: Path to output STL file
        threshold: Threshold value for marching cubes
        smoothing_iterations: Number of smoothing iterations
        smoothing_factor: Smoothing relaxation factor
    
    Returns:
        True if successful, False otherwise
    """
    if not VTK_AVAILABLE:
        print("VTK not available. Cannot use VTK method.")
        return False
    
    try:
        # Load NIfTI file
        nii_img = nib.load(nii_path)
        data = nii_img.get_fdata()
        affine = nii_img.affine
        voxel_spacing = nii_img.header.get_zooms()[:3]
        
        print(f"  Data shape: {data.shape}")
        print(f"  Voxel spacing: {voxel_spacing}")
        print(f"  Data range: {data.min()} to {data.max()}")
        
        # Create VTK image data
        vtk_image = vtk.vtkImageData()
        vtk_image.SetDimensions(data.shape)
        vtk_image.SetSpacing(voxel_spacing)
        vtk_image.SetOrigin(0, 0, 0)
        
        # Convert numpy array to VTK array
        flat_data = data.flatten(order='F')  # Fortran order for VTK
        vtk_array = vtk.vtkFloatArray()
        vtk_array.SetNumberOfTuples(len(flat_data))
        for i, val in enumerate(flat_data):
            vtk_array.SetValue(i, float(val))
        
        vtk_image.GetPointData().SetScalars(vtk_array)
        
        # Marching cubes with proper thresholding
        marching_cubes = vtk.vtkMarchingCubes()
        marching_cubes.SetInputData(vtk_image)
        marching_cubes.SetValue(0, threshold)
        marching_cubes.Update()
        
        # Check if mesh was generated
        if marching_cubes.GetOutput().GetNumberOfPoints() == 0:
            print(f"  Warning: No mesh generated with threshold {threshold}")
            return False
        
        print(f"  Marching cubes: {marching_cubes.GetOutput().GetNumberOfPoints()} points, "
              f"{marching_cubes.GetOutput().GetNumberOfCells()} cells")
        
        # Apply smoothing
        smoother = vtk.vtkSmoothPolyDataFilter()
        smoother.SetInputConnection(marching_cubes.GetOutputPort())
        smoother.SetNumberOfIterations(smoothing_iterations)
        smoother.SetRelaxationFactor(smoothing_factor)
        smoother.Update()
        
        # Apply affine transformation
        transform = vtk.vtkTransform()
        transform.SetMatrix(affine.flatten())
        
        transform_filter = vtk.vtkTransformPolyDataFilter()
        transform_filter.SetInputConnection(smoother.GetOutputPort())
        transform_filter.SetTransform(transform)
        transform_filter.Update()
        
        # Write STL file
        writer = vtk.vtkSTLWriter()
        writer.SetFileName(stl_path)
        writer.SetInputConnection(transform_filter.GetOutputPort())
        writer.Write()
        
        print(f"  Successfully created STL with VTK: {stl_path}")
        return True
        
    except Exception as e:
        print(f"  VTK conversion failed: {e}")
        return False


def convert_nii_to_stl_open3d(nii_path: str, stl_path: str, 
                             poisson_depth: int = 9) -> bool:
    """
    Convert NIfTI to STL using Open3D with Poisson reconstruction.
    
    Args:
        nii_path: Path to input NIfTI file
        stl_path: Path to output STL file
        poisson_depth: Depth for Poisson reconstruction
    
    Returns:
        True if successful, False otherwise
    """
    if not OPEN3D_AVAILABLE:
        print("Open3D not available. Cannot use Open3D method.")
        return False
    
    try:
        # Load NIfTI file
        nii_img = nib.load(nii_path)
        data = nii_img.get_fdata()
        affine = nii_img.affine
        voxel_spacing = nii_img.header.get_zooms()[:3]
        
        print(f"  Data shape: {data.shape}")
        print(f"  Voxel spacing: {voxel_spacing}")
        
        # Get points from voxel data
        points = np.argwhere(data > 0)
        if len(points) == 0:
            print(f"  Warning: No non-zero voxels found")
            return False
        
        # Convert to world coordinates
        points_world = points * voxel_spacing
        
        # Apply affine transformation
        points_homogeneous = np.column_stack([points_world, np.ones(len(points_world))])
        points_world = (affine @ points_homogeneous.T).T[:, :3]
        
        # Create point cloud
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points_world)
        
        # Estimate normals
        pcd.estimate_normals()
        
        # Create mesh using Poisson reconstruction
        mesh, _ = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pcd, depth=poisson_depth)
        
        # Clean mesh
        mesh.remove_degenerate_triangles()
        mesh.remove_duplicated_triangles()
        mesh.remove_duplicated_vertices()
        mesh.remove_unreferenced_vertices()
        
        # Save mesh
        o3d.io.write_triangle_mesh(stl_path, mesh)
        
        print(f"  Successfully created STL with Open3D: {stl_path}")
        return True
        
    except Exception as e:
        print(f"  Open3D conversion failed: {e}")
        return False


def clean_mesh_with_pymeshfix(stl_path: str, output_path: Optional[str] = None) -> bool:
    """
    Clean and repair mesh using PyMeshFix.
    
    Args:
        stl_path: Path to input STL file
        output_path: Path to output cleaned STL file (if None, overwrites input)
    
    Returns:
        True if successful, False otherwise
    """
    if not TRIMESH_AVAILABLE:
        print("Trimesh/PyMeshFix not available. Cannot clean mesh.")
        return False
    
    try:
        # Load mesh
        mesh = trimesh.load(stl_path)
        
        # Fix mesh using pymeshfix
        fixed_vertices, fixed_faces = pymeshfix.clean_from_arrays(
            mesh.vertices, 
            mesh.faces
        )
        
        # Create new mesh from fixed data
        fixed_mesh = trimesh.Trimesh(vertices=fixed_vertices, faces=fixed_faces)
        
        # Save cleaned mesh
        output_file = output_path or stl_path
        fixed_mesh.export(output_file)
        
        print(f"  Successfully cleaned mesh: {output_file}")
        return True
        
    except Exception as e:
        print(f"  Mesh cleaning failed: {e}")
        return False


def convert_nii_to_stl_improved(nii_path: str, stl_path: str, 
                               method: str = "vtk", 
                               clean_mesh: bool = True,
                               **kwargs) -> bool:
    """
    Convert NIfTI to STL using improved methods.
    
    Args:
        nii_path: Path to input NIfTI file
        stl_path: Path to output STL file
        method: Method to use ("vtk", "open3d", or "auto")
        clean_mesh: Whether to clean the mesh with PyMeshFix
        **kwargs: Additional arguments for the conversion method
    
    Returns:
        True if successful, False otherwise
    """
    print(f"Converting {nii_path} to {stl_path} using {method} method...")
    
    success = False
    
    if method == "vtk" or method == "auto":
        success = convert_nii_to_stl_vtk(nii_path, stl_path, **kwargs)
    
    if not success and (method == "open3d" or method == "auto"):
        success = convert_nii_to_stl_open3d(nii_path, stl_path, **kwargs)
    
    if success and clean_mesh:
        print("  Cleaning mesh with PyMeshFix...")
        clean_mesh_with_pymeshfix(stl_path)
    
    return success


def process_patient_folder_improved(patient_dir: str, method: str = "vtk", 
                                  force: bool = False, **kwargs) -> None:
    """
    Process a patient's folder to convert all .nii.gz files to .stl files using improved methods.
    
    Args:
        patient_dir: Path to patient directory
        method: Method to use for conversion
        force: If True, overwrite existing STL files
        **kwargs: Additional arguments for conversion
    """
    voxels_dir = Path(patient_dir) / "voxels"
    mesh_dir = Path(patient_dir) / "mesh"
    
    if not voxels_dir.exists():
        print(f"Error: 'voxels' directory not found in {patient_dir}")
        return
    
    # Create mesh directory if it doesn't exist
    mesh_dir.mkdir(parents=True, exist_ok=True)
    
    for root, _, files in os.walk(voxels_dir):
        for file in files:
            if file.endswith('.nii.gz'):
                nii_file_path = Path(root) / file
                
                # Create the corresponding mesh directory
                relative_path = nii_file_path.relative_to(voxels_dir)
                stl_file_dir = mesh_dir / relative_path.parent
                stl_file_dir.mkdir(parents=True, exist_ok=True)
                
                # Define the output STL file path
                base_name = relative_path.stem.replace('.nii', '')
                stl_file_path = stl_file_dir / f"{base_name}.stl"
                
                # Skip if file exists and not forcing
                if stl_file_path.exists() and not force:
                    print(f"  Skipping {stl_file_path} (already exists, use --force to overwrite)")
                    continue
                
                # Convert the file
                convert_nii_to_stl_improved(
                    str(nii_file_path), 
                    str(stl_file_path), 
                    method=method,
                    **kwargs
                )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Convert .nii.gz voxel files to .stl mesh files using improved methods.')
    parser.add_argument('patient', nargs='?', help='Patient name to process (e.g., PA00000002). If not provided, processes all patients.')
    parser.add_argument('--output_dir', type=str, default='output', help='Path to the output directory containing patient folders')
    parser.add_argument('--force', action='store_true', help='Overwrite existing STL files')
    parser.add_argument('--method', choices=['vtk', 'open3d', 'auto'], default='vtk', help='Conversion method to use')
    parser.add_argument('--no_clean', action='store_true', help='Disable mesh cleaning with PyMeshFix')
    parser.add_argument('--threshold', type=float, default=0.5, help='Threshold for marching cubes (VTK method)')
    parser.add_argument('--smoothing_iterations', type=int, default=50, help='Number of smoothing iterations (VTK method)')
    parser.add_argument('--smoothing_factor', type=float, default=0.1, help='Smoothing relaxation factor (VTK method)')
    parser.add_argument('--poisson_depth', type=int, default=9, help='Depth for Poisson reconstruction (Open3D method)')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.output_dir):
        print(f"Error: Output directory not found at {args.output_dir}")
        exit(1)
    
    # Set parameters
    kwargs = {
        'threshold': args.threshold,
        'smoothing_iterations': args.smoothing_iterations,
        'smoothing_factor': args.smoothing_factor,
        'poisson_depth': args.poisson_depth,
        'clean_mesh': not args.no_clean
    }
    
    # Determine which patients to process
    if args.patient:
        patient_dir = os.path.join(args.output_dir, args.patient)
        if os.path.isdir(patient_dir):
            process_patient_folder_improved(patient_dir, args.method, args.force, **kwargs)
        else:
            print(f"Error: Patient directory not found: {patient_dir}")
    else:
        # Process all patients
        for item in os.listdir(args.output_dir):
            patient_dir = os.path.join(args.output_dir, item)
            if os.path.isdir(patient_dir):
                print(f"Processing patient: {item}")
                process_patient_folder_improved(patient_dir, args.method, args.force, **kwargs)
