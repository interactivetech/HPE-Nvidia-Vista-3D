import os
import argparse
from pathlib import Path
import nibabel as nib
import numpy as np
import open3d as o3d
import json
from tqdm import tqdm

# Load label dictionary
PROJECT_ROOT = Path(__file__).parent.parent
LABEL_DICT_PATH = PROJECT_ROOT / "conf" / "label_dict.json"
with open(LABEL_DICT_PATH, 'r') as f:
    LABEL_DICT = json.load(f)

LABEL_COLORS_PATH = PROJECT_ROOT / "conf" / "label_colors.json"
with open(LABEL_COLORS_PATH, 'r') as f:
    LABEL_COLORS = json.load(f)

def process_nifti_for_point_clouds(nifti_file_path: Path, output_base_dir: Path):
    """
    Converts a segmented NIfTI file into individual point clouds for each segment.
    Saves each point cloud as a .pcd file using Open3D.
    """
    try:
        img = nib.load(nifti_file_path)
        data = img.get_fdata()
        affine = img.affine

        # Get unique segment labels (excluding background 0)
        unique_labels = np.unique(data[data > 0])

        if len(unique_labels) == 0:
            print(f"    No segments found in {nifti_file_path.name}. Skipping.")
            return

        print(f"    Found {len(unique_labels)} unique segments in {nifti_file_path.name}.")

        for label_id in tqdm(unique_labels, desc="      Processing segments", leave=False):
            segment_name = next((name for name, lid in LABEL_DICT.items() if lid == label_id), f"unknown_segment_{int(label_id)}")
            
            # Extract voxels for the current segment
            segment_voxel_indices = np.argwhere(data == label_id)

            if len(segment_voxel_indices) == 0:
                print(f"      Warning: No voxels found for segment ID {label_id} ({segment_name}). Skipping.")
                continue

            # Convert voxel coordinates to real-world coordinates
            # np.argwhere returns (z, y, x) indices, so reorder to (x, y, z)
            voxel_coords_homogeneous = np.hstack((segment_voxel_indices[:, ::-1], np.ones((segment_voxel_indices.shape[0], 1))))
            world_coords = (affine @ voxel_coords_homogeneous.T).T[:, :3]

            # Create Open3D point cloud
            pcd = o3d.geometry.PointCloud()
            pcd.points = o3d.utility.Vector3dVector(world_coords)
            
            # Get color for the current segment
            color = np.array(LABEL_COLORS.get(str(label_id), [0, 0, 0])) / 255.0 # Default to black if not found
            pcd.colors = o3d.utility.Vector3dVector(np.tile(color, (len(world_coords), 1)))

            # Define output path for the segment's point cloud
            # Use original NIfTI file stem + segment name
            output_filename = f"{nifti_file_path.stem}_{segment_name}.pcd"
            output_point_cloud_path = output_base_dir / output_filename
            output_point_cloud_path.parent.mkdir(parents=True, exist_ok=True)

            # Save the point cloud
            o3d.io.write_point_cloud(str(output_point_cloud_path), pcd)

            print(f"      ✅ Point cloud created for {segment_name}: {output_point_cloud_path.name} ({len(world_coords)} points)")

    except Exception as e:
        print(f"    ❌ Failed to process {nifti_file_path.name}: {e}")

def main():
    PROJECT_ROOT = Path(__file__).parent.parent # Assuming project root is two levels up
    input_base_path = PROJECT_ROOT / "outputs" / "segments"
    output_base_path = PROJECT_ROOT / "outputs" / "points"

    if not input_base_path.exists():
        print(f"Error: Input base folder not found: {input_base_path}")
        return

    patient_folders = [f for f in os.listdir(input_base_path) if os.path.isdir(input_base_path / f)]

    if not patient_folders:
        print(f"No patient folders found in {input_base_path}. Exiting.")
        return

    print(f"Found {len(patient_folders)} patient folders to process in {input_base_path}.")
    print(f"Point clouds will be saved to: {output_base_path}")

    for patient_folder_name in tqdm(patient_folders, desc="Processing patient folders", unit="folder"):
        patient_nifti_path = input_base_path / patient_folder_name
        point_cloud_output_path = output_base_path / patient_folder_name
        point_cloud_output_path.mkdir(parents=True, exist_ok=True)

        nifti_files = []
        for file in os.listdir(patient_nifti_path):
            if file.endswith(('.nii', '.nii.gz')):
                nifti_files.append(patient_nifti_path / file)

        if not nifti_files:
            print(f"No NIfTI files found in {patient_nifti_path}. Skipping.")
            continue # Skip to next patient folder

        print(f"  Found {len(nifti_files)} NIfTI files in {patient_folder_name}.")

        for nifti_file_path in tqdm(nifti_files, desc=f"  Processing NIfTI files for {patient_folder_name}", unit="file"):
            process_nifti_for_point_clouds(nifti_file_path, point_cloud_output_path)

    print("\n--- Point Cloud Generation Complete ---")

if __name__ == "__main__":
    main()
