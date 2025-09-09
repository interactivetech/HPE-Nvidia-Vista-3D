
import os
import argparse
import nibabel as nib
import numpy as np
from stl import mesh
from skimage.measure import marching_cubes

def convert_nii_to_stl(nii_path, stl_path):
    """
    Converts a .nii.gz file to a .stl file.
    """
    try:
        # Load the NIfTI file
        nii_img = nib.load(nii_path)
        nii_data = nii_img.get_fdata()

        # Generate the mesh using marching cubes
        verts, faces, _, _ = marching_cubes(nii_data, level=0)

        # Create the mesh object
        stl_mesh = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
        for i, f in enumerate(faces):
            for j in range(3):
                stl_mesh.vectors[i][j] = verts[f[j],:]

        # Save the mesh to an STL file
        stl_mesh.save(stl_path)
        print(f"Successfully converted {nii_path} to {stl_path}")

    except Exception as e:
        print(f"Could not convert {nii_path}. Error: {e}")

def process_patient_folder(patient_dir):
    """
    Processes a patient's folder to convert all .nii.gz files to .stl files.
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
                stl_file_name = os.path.splitext(os.path.basename(relative_path))[0] + '.stl'
                stl_file_path = os.path.join(stl_file_dir, stl_file_name)
                
                # Convert the file
                convert_nii_to_stl(nii_file_path, stl_file_path)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert .nii.gz voxel files to .stl mesh files for all patients in the output directory.')
    parser.add_argument('--output_dir', type=str, default='output', help='Path to the output directory containing patient folders (default: output)')
    args = parser.parse_args()

    if not os.path.isdir(args.output_dir):
        print(f"Error: Output directory not found at {args.output_dir}")
        exit()

    print(f"Processing patients in {args.output_dir}...")
    for patient_folder in os.listdir(args.output_dir):
        patient_dir = os.path.join(args.output_dir, patient_folder)
        if os.path.isdir(patient_dir):
            print(f"Processing patient folder: {patient_dir}")
            process_patient_folder(patient_dir)
