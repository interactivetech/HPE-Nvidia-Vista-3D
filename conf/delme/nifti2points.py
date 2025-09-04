import os
import nibabel as nib
import numpy as np
import json
import argparse

# Constants
INPUT_DIR = "/home/hpadmin/Nvidia-Vista3d-segmenation/output/segments"
OUTPUT_DIR = "/home/hpadmin/Nvidia-Vista3d-segmenation/output/points"
LABEL_COLORS_PATH = "/home/hpadmin/Nvidia-Vista3d-segmenation/conf/label_colors.json"
LABEL_DICT_PATH = "/home/hpadmin/Nvidia-Vista3d-segmenation/conf/label_dict.json"
MIN_POINTS = 200

def load_json_file(filepath):
    """Loads a JSON file and returns its content."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: JSON file not found at {filepath}")
        return {}
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {filepath}")
        return {}

def write_ply_file(output_path, points, colors):
    """
    Writes a PLY file from given points and colors.
    Points are (N, 3) numpy array, colors are (N, 3) numpy array (RGB).
    """
    num_points = points.shape[0]
    dtype = [('x', 'f4'), ('y', 'f4'), ('z', 'f4'), ('red', 'u1'), ('green', 'u1'), ('blue', 'u1')]
    point_data = np.zeros(num_points, dtype=dtype)
    point_data['x'] = points[:, 0]
    point_data['y'] = points[:, 1]
    point_data['z'] = points[:, 2]
    point_data['red'] = colors[:, 0]
    point_data['green'] = colors[:, 1]
    point_data['blue'] = colors[:, 2]

    header = f"""ply
format ascii 1.0
element vertex {num_points}
property float x
property float y
property float z
property uchar red
property uchar green
property uchar blue
end_header
"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(header)
        np.savetxt(f, point_data, fmt='%f %f %f %d %d %d')
    print(f"  Saved segment to {output_path}")

def process_nifti_file(nifti_path, relative_path, label_colors, label_dict):
    """
    Processes a single NIfTI file, extracts labeled segments, and saves them as PLY point clouds.
    """
    try:
        img = nib.load(nifti_path)
        data = img.get_fdata()
        affine = img.affine

        # Get unique labels, excluding background (0)
        labels = np.unique(data)
        labels = labels[labels != 0]

        if len(labels) == 0:
            print(f"  No labeled segments found in {relative_path}.")
            return

        for label in labels:
            # Extract voxel coordinates for the current label
            voxel_coords = np.argwhere(data == label)
            num_points = voxel_coords.shape[0]

            if num_points < MIN_POINTS:
                print(f"  Skipping label {int(label)} in {relative_path}: {num_points} points (less than {MIN_POINTS}).")
                continue

            print(f"  Processing label {int(label)} ({num_points} points) in {relative_path}...")

            # Convert voxel coordinates to real-world coordinates
            voxel_coords_homogeneous = np.hstack((voxel_coords, np.ones((num_points, 1))))
            real_world_coords = np.dot(voxel_coords_homogeneous, affine.T)[:, :3]

            # Get color for the label
            color_key = str(int(label))
            rgb_color = label_colors.get(color_key, [255, 255, 255]) # Default to white if color not found
            colors_array = np.tile(np.array(rgb_color, dtype=np.uint8), (num_points, 1))

            # Get segment name
            segment_name = label_dict.get(color_key, f"segment_{int(label)}")

            # Construct output path
            output_relative_dir = os.path.dirname(relative_path)
            output_filename = f"{os.path.splitext(os.path.basename(nifti_path))[0]}_{segment_name}.ply"
            output_full_dir = os.path.join(OUTPUT_DIR, output_relative_dir)
            output_ply_path = os.path.join(output_full_dir, output_filename)

            write_ply_file(output_ply_path, real_world_coords, colors_array)

    except Exception as e:
        print(f"Error processing {nifti_path}: {e}")

import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert NIfTI segmentations to PLY point clouds.")
    parser.add_argument("patient", nargs="?", type=str, help="Optional: Process only a specific patient folder (e.g., PA00000002). If omitted, all patient folders will be processed.")
    args = parser.parse_args()

    print("Starting NIfTI to Point Cloud conversion...")

    # Load label data
    label_colors = load_json_file(LABEL_COLORS_PATH)
    label_dict_raw = load_json_file(LABEL_DICT_PATH)
    # Reverse label_dict for easy lookup by label ID (keys are strings from JSON)
    label_dict = {str(v): k.replace(" ", "_") for k, v in label_dict_raw.items()} # Replace spaces for filenames

    base_input_dir = INPUT_DIR
    if args.patient:
        target_input_dir = os.path.join(INPUT_DIR, args.patient)
        if not os.path.exists(target_input_dir):
            print(f"Error: Patient directory not found: {target_input_dir}")
            exit(1)
        base_input_dir = target_input_dir
        print(f"Processing only patient folder: {args.patient}")

    if not os.path.exists(base_input_dir):
        print(f"Input directory not found: {base_input_dir}")
    else:
        # Traverse input directory
        for root, _, files in os.walk(base_input_dir):
            for file in files:
                if file.endswith((".nii", ".nii.gz")):
                    nifti_file_path = os.path.join(root, file)
                    # Adjust relative_path calculation if a specific patient folder is being processed
                    if args.patient:
                        relative_path = os.path.relpath(nifti_file_path, INPUT_DIR)
                    else:
                        relative_path = os.path.relpath(nifti_file_path, INPUT_DIR)
                    print(f"Processing NIfTI file: {relative_path}")
                    process_nifti_file(nifti_file_path, relative_path, label_colors, label_dict)
    print("Conversion complete.")