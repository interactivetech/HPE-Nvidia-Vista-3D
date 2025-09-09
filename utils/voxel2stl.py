
import os
import argparse
import nibabel as nib
import numpy as np
from stl import mesh
from skimage.measure import marching_cubes
from scipy.spatial import cKDTree
from scipy.ndimage import gaussian_filter
from scipy.spatial import ConvexHull

def calculate_mesh_volume(vertices, faces):
    """
    Calculate the volume of a mesh using the divergence theorem.
    This gives the exact volume enclosed by the mesh surface.
    """
    if len(vertices) == 0 or len(faces) == 0:
        return 0.0
    
    volume = 0.0
    for face in faces:
        # Get the three vertices of the triangle
        v0 = vertices[face[0]]
        v1 = vertices[face[1]]
        v2 = vertices[face[2]]
        
        # Calculate the volume contribution of this triangle
        # Using the divergence theorem: V = (1/6) * sum(dot(vi, cross(vj, vk)))
        volume += np.dot(v0, np.cross(v1, v2)) / 6.0
    
    return abs(volume)

def calculate_voxel_volume(voxel_data, voxel_spacing):
    """
    Calculate the volume of voxel data in mm³.
    """
    # Count non-zero voxels
    non_zero_voxels = np.sum(voxel_data > 0)
    
    # Calculate volume of each voxel
    voxel_volume_mm3 = np.prod(voxel_spacing)
    
    # Total volume
    total_volume = non_zero_voxels * voxel_volume_mm3
    
    return total_volume

def volume_preserving_smooth(vertices, faces, target_volume, iterations=3, lambda_factor=0.3):
    """
    Apply volume-preserving Laplacian smoothing.
    Adjusts the smoothing to maintain the original volume.
    """
    if len(vertices) == 0 or len(faces) == 0:
        return vertices
    
    original_volume = calculate_mesh_volume(vertices, faces)
    if original_volume == 0:
        return vertices
    
    smoothed_vertices = vertices.copy()
    
    for iteration in range(iterations):
        # Build adjacency list for each vertex
        vertex_neighbors = {}
        for face in faces:
            for i in range(3):
                vertex_idx = face[i]
                if vertex_idx not in vertex_neighbors:
                    vertex_neighbors[vertex_idx] = set()
                # Add the other two vertices of this face as neighbors
                for j in range(3):
                    if i != j:
                        vertex_neighbors[vertex_idx].add(face[j])
        
        # Apply Laplacian smoothing
        new_vertices = smoothed_vertices.copy()
        for vertex_idx, neighbors in vertex_neighbors.items():
            if len(neighbors) > 0:
                # Calculate average position of neighbors
                neighbor_positions = smoothed_vertices[list(neighbors)]
                neighbor_avg = np.mean(neighbor_positions, axis=0)
                
                # Move vertex towards the average of its neighbors
                new_vertices[vertex_idx] = (
                    smoothed_vertices[vertex_idx] * (1 - lambda_factor) + 
                    neighbor_avg * lambda_factor
                )
        
        smoothed_vertices = new_vertices
        
        # Calculate current volume and adjust if needed
        current_volume = calculate_mesh_volume(smoothed_vertices, faces)
        if current_volume > 0:
            # Scale to preserve volume
            volume_ratio = (target_volume / current_volume) ** (1/3)
            center = np.mean(smoothed_vertices, axis=0)
            smoothed_vertices = center + (smoothed_vertices - center) * volume_ratio
    
    return smoothed_vertices

def smooth_mesh(vertices, faces, iterations=3, lambda_factor=0.5):
    """
    Apply Laplacian smoothing to reduce blocky appearance of marching cubes meshes.
    
    Args:
        vertices: Array of vertex coordinates
        faces: Array of face indices
        iterations: Number of smoothing iterations
        lambda_factor: Smoothing factor (0.0 = no smoothing, 1.0 = maximum smoothing)
    
    Returns:
        Smoothed vertices
    """
    if len(vertices) == 0:
        return vertices
    
    smoothed_vertices = vertices.copy()
    
    for iteration in range(iterations):
        # Build adjacency list for each vertex
        vertex_neighbors = {}
        for face in faces:
            for i in range(3):
                vertex_idx = face[i]
                if vertex_idx not in vertex_neighbors:
                    vertex_neighbors[vertex_idx] = set()
                # Add the other two vertices of this face as neighbors
                for j in range(3):
                    if i != j:
                        vertex_neighbors[vertex_idx].add(face[j])
        
        # Apply Laplacian smoothing
        new_vertices = smoothed_vertices.copy()
        for vertex_idx, neighbors in vertex_neighbors.items():
            if len(neighbors) > 0:
                # Calculate average position of neighbors
                neighbor_positions = smoothed_vertices[list(neighbors)]
                neighbor_avg = np.mean(neighbor_positions, axis=0)
                
                # Move vertex towards the average of its neighbors
                new_vertices[vertex_idx] = (
                    smoothed_vertices[vertex_idx] * (1 - lambda_factor) + 
                    neighbor_avg * lambda_factor
                )
        
        smoothed_vertices = new_vertices
    
    return smoothed_vertices

def convert_nii_to_stl(nii_path, stl_path, force=False, smooth_iterations=3, smooth_factor=0.5):
    """
    Converts a .nii.gz file to a .stl file, preserving voxel spacing and affine transformation.
    
    Args:
        nii_path: Path to input NIfTI file
        stl_path: Path to output STL file
        force: If True, overwrite existing STL files
        smooth_iterations: Number of smoothing iterations (default: 3)
        smooth_factor: Smoothing factor 0.0-1.0 (default: 0.5)
    """
    try:
        # Check if STL file already exists
        if os.path.exists(stl_path) and not force:
            print(f"  Skipping {stl_path} (already exists, use --force to overwrite)")
            return
        
        # Load the NIfTI file
        nii_img = nib.load(nii_path)
        nii_data = nii_img.get_fdata()
        
        # Get voxel spacing and affine transformation
        voxel_spacing = nii_img.header.get_zooms()[:3]  # Get first 3 dimensions
        affine = nii_img.affine
        
        print(f"  Voxel spacing: {voxel_spacing} mm")
        print(f"  Data shape: {nii_data.shape}")
        print(f"  Data type: {nii_data.dtype}")
        print(f"  Data range: {nii_data.min()} to {nii_data.max()}")
        print(f"  Unique values: {np.unique(nii_data)}")

        # Convert label data to binary for marching cubes
        # The voxel files contain label IDs, but marching cubes needs binary data
        binary_data = (nii_data > 0).astype(np.float32)
        print(f"  Binary data - non-zero voxels: {np.sum(binary_data)}")

        # Calculate original voxel volume for validation
        voxel_volume = calculate_voxel_volume(nii_data, voxel_spacing)
        print(f"  Original voxel volume: {voxel_volume:.2f} mm³")

        # Apply Gaussian smoothing to the binary data for smoother meshes
        # This helps reduce the blocky appearance by smoothing the voxel boundaries
        smoothed_data = gaussian_filter(binary_data, sigma=0.5)
        print(f"  Applied Gaussian smoothing to reduce blocky appearance")

        # Generate the mesh using marching cubes
        try:
            verts, faces, _, _ = marching_cubes(smoothed_data, level=0.5)
            print(f"  Marching cubes successful: {len(verts)} vertices, {len(faces)} faces")
        except Exception as mc_error:
            print(f"  Marching cubes failed: {mc_error}")
            print(f"  Trying with different parameters...")
            # Try with different level values
            try:
                verts, faces, _, _ = marching_cubes(smoothed_data, level=0.0)
                print(f"  Marching cubes (level=0.0) successful: {len(verts)} vertices, {len(faces)} faces")
            except Exception as mc_error2:
                print(f"  Marching cubes (level=0.0) also failed: {mc_error2}")
                raise mc_error2
        
        if len(verts) == 0:
            print(f"  Warning: No mesh generated - check if voxel data contains valid structures")
            return
        
        # Apply voxel spacing to convert from voxel coordinates to mm
        # This preserves the actual anatomical dimensions
        verts_scaled = verts.copy()
        for i in range(3):
            verts_scaled[:, i] *= voxel_spacing[i]
        
        # Apply affine transformation to get real-world coordinates
        # Add homogeneous coordinate (1) to each vertex
        verts_homogeneous = np.column_stack([verts_scaled, np.ones(verts_scaled.shape[0])])
        verts_world = (affine @ verts_homogeneous.T).T[:, :3]
        
        print(f"  Mesh vertices: {len(verts_world)}")
        print(f"  Bounding box: {verts_world.min(axis=0)} to {verts_world.max(axis=0)}")

        # Apply volume-preserving Laplacian smoothing to reduce blocky appearance
        if smooth_iterations > 0 and smooth_factor > 0:
            print(f"  Applying volume-preserving smoothing: {smooth_iterations} iterations, factor={smooth_factor}")
            verts_world = volume_preserving_smooth(verts_world, faces, voxel_volume, smooth_iterations, smooth_factor)
            
            # Validate volume preservation
            final_volume = calculate_mesh_volume(verts_world, faces)
            volume_error = abs(final_volume - voxel_volume) / voxel_volume * 100
            print(f"  Volume validation - Voxel: {voxel_volume:.2f} mm³, STL: {final_volume:.2f} mm³, Error: {volume_error:.1f}%")
            
            if volume_error > 5.0:  # More than 5% error
                print(f"  Warning: Volume error > 5% - consider reducing smoothing parameters")
            else:
                print(f"  Volume preservation: Good (error < 5%)")
        else:
            # Still validate volume even without smoothing
            final_volume = calculate_mesh_volume(verts_world, faces)
            volume_error = abs(final_volume - voxel_volume) / voxel_volume * 100
            print(f"  Volume validation - Voxel: {voxel_volume:.2f} mm³, STL: {final_volume:.2f} mm³, Error: {volume_error:.1f}%")

        # Create the mesh object
        stl_mesh = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
        for i, f in enumerate(faces):
            for j in range(3):
                stl_mesh.vectors[i][j] = verts_world[f[j],:]

        # Save the mesh to an STL file
        stl_mesh.save(stl_path)
        print(f"Successfully converted {nii_path} to {stl_path}")

    except Exception as e:
        print(f"Could not convert {nii_path}. Error: {e}")

def process_patient_folder(patient_dir, force=False, smooth_iterations=3, smooth_factor=0.5):
    """
    Processes a patient's folder to convert all .nii.gz files to .stl files.
    
    Args:
        patient_dir: Path to patient directory
        force: If True, overwrite existing STL files
        smooth_iterations: Number of smoothing iterations
        smooth_factor: Smoothing factor 0.0-1.0
    """
    voxels_dir = os.path.join(patient_dir, 'voxels')
    mesh_dir = os.path.join(patient_dir, 'mesh')

    if not os.path.isdir(voxels_dir):
        print(f"Error: 'voxels' directory not found in {patient_dir}")
        return

    for root, _, files in os.walk(voxels_dir):
        for file in files:
            if file.endswith('.nii.gz'):
                nii_file_path = os.path.join(root, file)
                
                # Create the corresponding mesh directory
                relative_path = os.path.relpath(nii_file_path, voxels_dir)
                stl_file_dir = os.path.join(mesh_dir, os.path.dirname(relative_path))
                os.makedirs(stl_file_dir, exist_ok=True)
                
                # Define the output STL file path
                # Remove both .nii and .gz extensions if present
                base_name = os.path.basename(relative_path)
                if base_name.endswith('.nii.gz'):
                    base_name = base_name[:-7]  # Remove .nii.gz
                elif base_name.endswith('.nii'):
                    base_name = base_name[:-4]  # Remove .nii
                stl_file_name = base_name + '.stl'
                stl_file_path = os.path.join(stl_file_dir, stl_file_name)
                
                # Convert the file
                convert_nii_to_stl(nii_file_path, stl_file_path, force, smooth_iterations, smooth_factor)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert .nii.gz voxel files to .stl mesh files for all patients in the output directory.')
    parser.add_argument('--output_dir', type=str, default='output', help='Path to the output directory containing patient folders (default: output)')
    parser.add_argument('--force', action='store_true', help='Overwrite existing STL files (default: skip existing files)')
    parser.add_argument('--smooth_iterations', type=int, default=3, help='Number of Laplacian smoothing iterations (default: 3)')
    parser.add_argument('--smooth_factor', type=float, default=0.5, help='Smoothing factor 0.0-1.0 (default: 0.5)')
    parser.add_argument('--no_smooth', action='store_true', help='Disable mesh smoothing (keep original blocky appearance)')
    args = parser.parse_args()

    if not os.path.isdir(args.output_dir):
        print(f"Error: Output directory not found at {args.output_dir}")
        exit()

    # Set smoothing parameters
    smooth_iterations = 0 if args.no_smooth else args.smooth_iterations
    smooth_factor = 0.0 if args.no_smooth else args.smooth_factor
    
    print(f"Processing patients in {args.output_dir}...")
    if args.force:
        print("Force mode enabled - will overwrite existing STL files")
    else:
        print("Skip mode enabled - will skip existing STL files (use --force to overwrite)")
    
    if smooth_iterations > 0:
        print(f"Smoothing enabled: {smooth_iterations} iterations, factor={smooth_factor}")
    else:
        print("Smoothing disabled - keeping original blocky appearance")
    
    for patient_folder in os.listdir(args.output_dir):
        patient_dir = os.path.join(args.output_dir, patient_folder)
        if os.path.isdir(patient_dir):
            print(f"Processing patient folder: {patient_dir}")
            process_patient_folder(patient_dir, args.force, smooth_iterations, smooth_factor)
