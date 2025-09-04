import os
import argparse
from pathlib import Path
import nibabel as nib
import numpy as np
import open3d as o3d
import json
from tqdm import tqdm
from skimage.measure import marching_cubes

# Point cloud sampling constants
DEFAULT_SAMPLED_POINTS_PER_VERT = 10
MAX_SAMPLED_POINTS = 100000 # Cap the number of points for very large meshes

# Load label dictionary
PROJECT_ROOT = Path(__file__).parent.parent
LABEL_DICT_PATH = PROJECT_ROOT / "conf" / "label_dict.json"
with open(LABEL_DICT_PATH, 'r') as f:
    LABEL_DICT = json.load(f)

LABEL_COLORS_PATH = PROJECT_ROOT / "conf" / "label_colors.json"
with open(LABEL_COLORS_PATH, 'r') as f:
    LABEL_COLORS = json.load(f)

def create_colored_segmentation(nifti_file_path: Path, output_path: Path):
    """Creates and saves a colored NIfTI file from a label map."""
    try:
        img = nib.load(nifti_file_path)
        data = img.get_fdata().astype(np.int16)
        affine = img.affine

        # Create an empty RGB image
        colored_data = np.zeros((*data.shape, 3), dtype=np.uint8)

        # Get unique labels
        unique_labels = np.unique(data)

        for label_id in unique_labels:
            if label_id == 0: # Skip background
                continue
            
            color = LABEL_COLORS.get(str(int(label_id)), [255, 255, 255]) # Default to white if not found
            colored_data[data == label_id] = color

        colored_nii = nib.Nifti1Image(colored_data, affine, img.header)
        nib.save(colored_nii, output_path)
        print(f"      ✅ Colored segmentation saved: {output_path.name}")

    except Exception as e:
        print(f"    ❌ Failed to create colored segmentation for {nifti_file_path.name}: {e}")

def process_nifti_for_point_clouds(nifti_file_path: Path, output_base_dir: Path):
    """
    Converts a segmented NIfTI file into individual point clouds for each segment.
    Saves each point cloud as a .pcd file using Open3D.
    """
    try:
        img = nib.load(nifti_file_path)
        data = img.get_fdata()
        affine = img.affine

        unique_labels = np.unique(data[data > 0])

        if len(unique_labels) == 0:
            print(f"    No segments found in {nifti_file_path.name}. Skipping.")
            return

        print(f"    Found {len(unique_labels)} unique segments in {nifti_file_path.name}.")

        for label_id in tqdm(unique_labels, desc="      Processing segments", leave=False):
            if label_id not in LABEL_DICT.values():
                print(f"      Warning: Segment ID {label_id} is not defined in LABEL_DICT. Skipping.")
                continue
            
            segment_name = next(name for name, lid in LABEL_DICT.items() if lid == label_id)
            segment_mask = (data == label_id)

            if not np.any(segment_mask):
                continue

            verts, faces, normals, values = marching_cubes(segment_mask, level=0.5)

            if len(verts) == 0:
                continue

            verts_homogeneous = np.hstack((verts, np.ones((verts.shape[0], 1))))
            world_coords_verts = (affine @ verts_homogeneous.T).T[:, :3]

            mesh = o3d.geometry.TriangleMesh()
            mesh.vertices = o3d.utility.Vector3dVector(world_coords_verts)
            mesh.triangles = o3d.utility.Vector3iVector(faces)
            mesh.compute_vertex_normals()

            if not mesh.has_vertices() or not mesh.has_triangles():
                continue

            num_sampled_points = min(MAX_SAMPLED_POINTS, int(len(verts) * DEFAULT_SAMPLED_POINTS_PER_VERT))
            if num_sampled_points == 0 and len(verts) > 0:
                num_sampled_points = 100

            pcd = mesh.sample_points_uniformly(number_of_points=num_sampled_points)

            if not pcd.has_points():
                continue
            
            color_float_0_1 = np.array(LABEL_COLORS.get(str(int(label_id)), [0, 0, 0])) / 255.0
            pcd.colors = o3d.utility.Vector3dVector(np.tile(color_float_0_1, (len(pcd.points), 1)))

            output_filename = f"{nifti_file_path.stem}_{segment_name}.pcd"
            output_point_cloud_path = output_base_dir / output_filename
            output_point_cloud_path.parent.mkdir(parents=True, exist_ok=True)

            min_points_threshold = 100
            if len(pcd.points) < min_points_threshold:
                continue
            
            o3d.io.write_point_cloud(str(output_point_cloud_path), pcd, write_ascii=True)
            print(f"      ✅ Point cloud created for {segment_name}: {output_point_cloud_path.name} ({len(pcd.points)} points)")

    except Exception as e:
        print(f"    ❌ Failed to process {nifti_file_path.name} for point clouds: {e}")

def main():
    parser = argparse.ArgumentParser(description="Generate point clouds and colored segmentations from NIfTI files.")
    parser.add_argument("patient_folder", type=str, nargs='?', default=None,
                        help="Name of the patient folder to process. If not provided, all patient folders will be processed.")
    args = parser.parse_args()

    input_base_path = PROJECT_ROOT / "output" / "segments"
    points_output_base_path = PROJECT_ROOT / "output" / "points"

    if not input_base_path.exists():
        print(f"Error: Input base folder not found: {input_base_path}")
        return

    patient_folders_to_process = []
    if args.patient_folder:
        specific_patient_path = input_base_path / args.patient_folder
        if specific_patient_path.is_dir():
            patient_folders_to_process.append(args.patient_folder)
        else:
            print(f"Error: Specified patient folder not found: {specific_patient_path}")
            return
    else:
        patient_folders_to_process = [f.name for f in input_base_path.iterdir() if f.is_dir()]
        
    if not patient_folders_to_process:
        print(f"No patient folders found to process in {input_base_path}. Exiting.")
        return

    print(f"Found {len(patient_folders_to_process)} patient folders to process.")

    for patient_folder_name in tqdm(patient_folders_to_process, desc="Processing patient folders", unit="folder"):
        patient_nifti_path = input_base_path / patient_folder_name
        point_cloud_output_path = points_output_base_path / patient_folder_name
        point_cloud_output_path.mkdir(parents=True, exist_ok=True)

        nifti_files = [patient_nifti_path / f for f in os.listdir(patient_nifti_path) if f.endswith(('.nii', '.nii.gz'))]

        if not nifti_files:
            print(f"No NIfTI files found in {patient_nifti_path}. Skipping.")
            continue

        print(f"  Found {len(nifti_files)} NIfTI files in {patient_folder_name}.")

        for nifti_file_path in tqdm(nifti_files, desc=f"  Processing NIfTI files for {patient_folder_name}", unit="file"):
            # Create point clouds
            process_nifti_for_point_clouds(nifti_file_path, point_cloud_output_path)
            
            # Create colored segmentation
            # Following user-specified naming convention
            base_name = nifti_file_path.name.replace('.nii.gz', '').replace('.nii', '')
            colored_seg_filename = base_name + '_colored_seg.nii.gz'
            colored_seg_output_path = nifti_file_path.parent / colored_seg_filename
            create_colored_segmentation(nifti_file_path, colored_seg_output_path)

    print("\n--- Processing Complete ---")

if __name__ == "__main__":
    main()
