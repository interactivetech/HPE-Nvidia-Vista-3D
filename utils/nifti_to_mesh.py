import os
import json
import nibabel as nib
import numpy as np
import pyvista as pv

# Constants
LABEL_COLORS_PATH = "/home/hpadmin/Nvidia-Vista3d-segmenation/conf/label_colors.json"
MIN_VOXELS_FOR_MESH = 100 # Minimum number of non-zero voxels required to create a mesh

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

def create_segment_mesh_file(
    nifti_segment_path: str,
    output_mesh_path: str,
    label_color: list = None,
    smooth_shading: bool = True
):
    """
    Extracts a 3D surface mesh from a NIfTI file containing a single segment
    and saves it as a mesh file (e.g., VTK, OBJ, STL).

    Args:
        nifti_segment_path (str): Path to the input NIfTI file containing a single segment.
        output_mesh_path (str): Path to save the output mesh file (e.g., .vtk, .obj, .stl).
        label_color (list, optional): RGB color [R, G, B] for the mesh. If provided, it will be
                                      stored as point data if the format supports it.
        smooth_shading (bool, optional): Whether to apply smooth shading during mesh extraction.
    """
    print(f"Extracting mesh from {os.path.basename(nifti_segment_path)} and saving to {os.path.basename(output_mesh_path)}...")

    if not os.path.exists(nifti_segment_path):
        print(f"Error: NIfTI segment file not found at {nifti_segment_path}")
        return

    try:
        # Load the NIfTI segment file
        img = nib.load(nifti_segment_path)
        data = img.get_fdata()
        affine = img.affine
        zooms = img.header.get_zooms()[:3] # Get voxel spacing

        # Create a binary mask for the non-zero voxels (the segment)
        mask = (data > 0).astype(np.uint8)

        print(f"    DEBUG: Mask shape: {mask.shape}, Sum of mask (non-zero voxels): {np.sum(mask)}")

        # Check if the mask is empty or too small
        if not np.any(mask) or np.sum(mask) < MIN_VOXELS_FOR_MESH:
            print(f"Warning: Not enough voxels found in {os.path.basename(nifti_segment_path)} ({np.sum(mask)} < {MIN_VOXELS_FOR_MESH}). Skipping mesh creation.")
            return

        # Ensure the mask is C-contiguous for PyVista
        mask_contiguous = np.ascontiguousarray(mask)

        # Transpose the mask to (Z, Y, X) order if necessary for PyVista's marching cubes
        # NIfTI data from nibabel.get_fdata() is typically (X, Y, Z) or (row, col, slice)
        # PyVista's ImageData expects (X, Y, Z) for its internal representation.
        # However, for marching cubes, sometimes (Z, Y, X) is expected or a specific order.
        # Let's try transposing to (Z, Y, X) as a common fix for such issues.
        # This assumes the original data is (X, Y, Z) from nibabel.
        # If it's already (Z,Y,X), this will transpose it back.
        # A more robust solution would check img.header.get_qform() or sform_code
        # For now, let's try a simple transpose.
        mask_transposed = mask_contiguous.transpose(2, 1, 0) # (Z, Y, X)

        pv_image = pv.wrap(mask_transposed)
        pv_image.spacing = zooms
        pv_image.origin = affine[:3, 3]
        print(f"    DEBUG: PyVista ImageData bounds: {pv_image.bounds}")

        # Extract the surface mesh using marching cubes (threshold then extract_surface)
        # This is often more robust for binary masks
        mesh = pv_image.threshold(0.5).extract_surface()

        # Check if mesh extraction resulted in an empty mesh
        if mesh.n_points == 0:
            print(f"Warning: Mesh extraction resulted in an empty mesh. Skipping saving.")
            return

        # Apply smoothing if requested
        if smooth_shading:
            mesh = mesh.smooth(n_iter=50, relaxation_factor=0.01) # Adjust iterations and relaxation as needed

        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_mesh_path), exist_ok=True)

        # Save the mesh
        # PyVista automatically determines format from extension
        if label_color:
            # Convert RGB to 0-1 float for PyVista if storing as point data
            # Or, if saving to VTK, it can handle uint8 directly for cell/point data
            # For simplicity, let's just save the mesh. Color can be applied in viewer.
            # If specific format like OBJ with MTL is needed, it's more complex.
            pass # Color is for viewer, not directly saved in generic mesh unless specific format

        mesh.save(output_mesh_path)

        print(f"Successfully extracted and saved 3D mesh to {output_mesh_path}")

    except Exception as e:
        print(f"Error creating mesh from {nifti_segment_path}: {e}")

if __name__ == "__main__":
    # Example Usage
    # You would typically call this function from another script (e.g., utils/segment.py)
    
    # Define a dummy NIfTI segment file for testing
    dummy_nifti_segment_path = "./dummy_single_segment.nii.gz"
    if not os.path.exists(dummy_nifti_segment_path):
        print("Creating a dummy single segment NIfTI file for demonstration...")
        dummy_data = np.zeros((64, 64, 64), dtype=np.uint8)
        # Create a sphere for a single segment (e.g., label 1)
        x, y, z = np.ogrid[-32:32, -32:32, -32:32]
        r = np.sqrt(x**2 + y**2 + z**2)
        dummy_data[r < 15] = 1 # This NIfTI now represents a single segment
        dummy_affine = np.eye(4)
        dummy_img = nib.Nifti1Image(dummy_data, dummy_affine)
        nib.save(dummy_img, dummy_nifti_segment_path)
        print("Dummy single segment NIfTI created.")

    # Define output mesh path
    output_mesh_dir = "./test_meshes"
    os.makedirs(output_mesh_dir, exist_ok=True)
    output_mesh_file = os.path.join(output_mesh_dir, "dummy_segment_mesh.vtk")

    # Call the function
    create_segment_mesh_file(dummy_nifti_segment_path, output_mesh_file)

    # Clean up dummy file (optional)
    # if os.path.exists(dummy_nifti_segment_path):
    #     os.remove(dummy_nifti_segment_path)
    # if os.path.exists(output_mesh_file):
    #     os.remove(output_mesh_file)