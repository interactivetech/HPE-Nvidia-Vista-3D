
import os
import argparse
import nibabel as nib
import numpy as np
from stl import mesh
from skimage.measure import marching_cubes

def convert_nii_to_stl(nii_path, stl_path, force=False):
    """
    Converts a .nii.gz file to a .stl file, preserving voxel spacing and affine transformation.
    
    Args:
        nii_path: Path to input NIfTI file
        stl_path: Path to output STL file
        force: If True, overwrite existing STL files
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

        # Generate the mesh using marching cubes
        try:
            verts, faces, _, _ = marching_cubes(binary_data, level=0.5)
            print(f"  Marching cubes successful: {len(verts)} vertices, {len(faces)} faces")
        except Exception as mc_error:
            print(f"  Marching cubes failed: {mc_error}")
            print(f"  Trying with different parameters...")
            # Try with different level values
            try:
                verts, faces, _, _ = marching_cubes(binary_data, level=0.0)
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

def process_patient_folder(patient_dir, force=False):
    """
    Processes a patient's folder to convert all .nii.gz files to .stl files.
    
    Args:
        patient_dir: Path to patient directory
        force: If True, overwrite existing STL files
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
                convert_nii_to_stl(nii_file_path, stl_file_path, force)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert .nii.gz voxel files to .stl mesh files for all patients in the output directory.')
    parser.add_argument('--output_dir', type=str, default='output', help='Path to the output directory containing patient folders (default: output)')
    parser.add_argument('--force', action='store_true', help='Overwrite existing STL files (default: skip existing files)')
    args = parser.parse_args()

    if not os.path.isdir(args.output_dir):
        print(f"Error: Output directory not found at {args.output_dir}")
        exit()

    print(f"Processing patients in {args.output_dir}...")
    if args.force:
        print("Force mode enabled - will overwrite existing STL files")
    else:
        print("Skip mode enabled - will skip existing STL files (use --force to overwrite)")
    
    for patient_folder in os.listdir(args.output_dir):
        patient_dir = os.path.join(args.output_dir, patient_folder)
        if os.path.isdir(patient_dir):
            print(f"Processing patient folder: {patient_dir}")
            process_patient_folder(patient_dir, args.force)
