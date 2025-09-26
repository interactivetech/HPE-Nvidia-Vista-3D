# Voxel Color Mapping for Vista3D Output

import os
import json
import numpy as np
import nibabel as nib
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


def load_nifti_file(file_path):
    """Load a NIfTI file and return the data."""
    try:
        img = nib.load(file_path)
        return img.get_fdata()
    except Exception as e:
        print(f"Error loading file {file_path}: {e}")
        return None


def load_color_map(json_path):
    """Load color mappings from a JSON file."""
    with open(json_path, 'r') as f:
        color_data = json.load(f)
    # Create a dictionary mapping vessel names to RGB colors (normalized to 0-1)
    color_map = {entry['name'].replace(' ', '_').lower(): tuple(c / 255.0 for c in entry['color']) for entry in color_data}
    return color_map


def load_label_dict(json_path):
    """Load label dictionary from a JSON file for name matching."""
    with open(json_path, 'r') as f:
        label_data = json.load(f)
    # Create a dictionary mapping normalized names to original names
    label_dict = {key.replace(' ', '_').lower(): key for key in label_data.keys()}
    return label_dict


def find_closest_match(vessel_name, label_dict_keys, color_map_keys):
    """Find the closest matching name in the label dictionary and map to color map."""
    vessel_name_lower = vessel_name.lower()
    for key in label_dict_keys:
        if vessel_name_lower == key or vessel_name_lower in key or key in vessel_name_lower:
            original_name = label_dict_keys[key].replace(' ', '_').lower()
            for color_key in color_map_keys:
                if original_name == color_key or original_name in color_key or color_key in original_name:
                    return color_key
    return None


def assign_colors_to_vessels(voxel_dir, output_dir, color_map, label_dict):
    """Assign colors to different vessels based on their filenames using the provided color map.
    
    Args:
        voxel_dir (str): Directory containing voxel NIfTI files.
        output_dir (str): Directory to save color-mapped visualizations or data.
        color_map (dict): Dictionary mapping vessel names to RGB colors.
        label_dict (dict): Dictionary mapping normalized names to original names for matching.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Default fallback color for unmatched structures
    fallback_color = (0.5, 0.5, 0.5)  # Gray

    # Process each NIfTI file in the voxel directory
    for file_name in os.listdir(voxel_dir):
        if file_name.endswith('.nii.gz'):
            input_path = os.path.join(voxel_dir, file_name)
            vessel_name = file_name.replace('.nii.gz', '').replace(' ', '_')

            # Check if vessel has a defined color with exact match
            color = None
            if vessel_name.lower() in color_map:
                color = color_map[vessel_name.lower()]
            else:
                # Try to find a close match using label dictionary
                matched_key = find_closest_match(vessel_name, label_dict, color_map.keys())
                if matched_key:
                    color = color_map[matched_key]
                    print(f"Matched {vessel_name} to {matched_key} with color {color}")
                else:
                    color = fallback_color
                    print(f"No close match found for {vessel_name}, using fallback color {color}")

            data = load_nifti_file(input_path)
            if data is None:
                print(f"Skipping {vessel_name} due to file loading error")
                continue

            # For simplicity, we'll note the color assignment
            # In a real scenario, you might save a color-mapped version or use a 3D rendering tool
            print(f"Assigned color {color} to {vessel_name}")

            # Optionally, create a simple visualization (requires further implementation for 3D)
            # This is a placeholder for actual visualization code
            # You can expand this to use libraries like vtk or 3D Slicer for rendering

# Example function to visualize (placeholder, requires further implementation)
def visualize_voxel_data(data, color, output_path):
    """Placeholder for visualizing voxel data with a specific color."""
    # This is where you would implement 3D visualization with the assigned color
    # For now, we'll just note the intent
    print(f"Visualizing data with color {color}, would save to {output_path}")
    # Actual implementation would depend on the visualization library used

if __name__ == "__main__":
    # Example usage
    patient_folder = "/Users/dave/AI/HPE/HPE-Nvidia-Vista-3D/output/PA00000002"
    voxel_subdir = "2.5MM_ARTERIAL_3"
    voxel_dir = os.path.join(patient_folder, 'voxels', voxel_subdir)
    output_dir = os.path.join(patient_folder, 'visualizations', voxel_subdir)
    color_json_path = "/Users/dave/AI/HPE/HPE-Nvidia-Vista-3D/conf/vista3d_label_colors.json"
    label_json_path = "/Users/dave/AI/HPE/HPE-Nvidia-Vista-3D/conf/vista3d_label_dict.json"

    # Load color map and label dictionary from JSON
    color_map = load_color_map(color_json_path)
    label_dict = load_label_dict(label_json_path)

    assign_colors_to_vessels(voxel_dir, output_dir, color_map=color_map, label_dict=label_dict)
