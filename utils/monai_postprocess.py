# MONAI Post-Processing for Vista3D Output

import os
import numpy as np
import nibabel as nib
from monai.transforms import GaussianSmooth


def load_nifti_file(file_path):
    """Load a NIfTI file and return the data and affine."""
    img = nib.load(file_path)
    return img.get_fdata(), img.affine

def save_nifti_file(data, affine, output_path):
    """Save data as a NIfTI file."""
    img = nib.Nifti1Image(data, affine)
    nib.save(img, output_path)

def apply_smoothing(data, sigma=1.0):
    """Apply Gaussian smoothing to the data."""
    smoother = GaussianSmooth(sigma=sigma)
    return smoother(data[None, ...])[0].numpy()

def process_patient_folder(patient_folder, sigma=1.0, overwrite=False, target_ct='2.5MM_ARTERIAL_3.nii.gz'):
    """Process the specified CT scan and its associated voxels in the patient folder.
    
    Args:
        patient_folder (str): Path to the patient folder.
        sigma (float): Smoothing intensity.
        overwrite (bool): If True, overwrite existing processed files. If False, skip them.
        target_ct (str): Specific CT scan filename to process.
    """
    # Process the specified CT scan in nifti directory
    nifti_dir = os.path.join(patient_folder, 'nifti')
    if os.path.exists(nifti_dir):
        input_path = os.path.join(nifti_dir, target_ct)
        if os.path.exists(input_path):
            base_name = target_ct.replace('.nii.gz', '')
            output_name = f"{base_name}_MONAI.nii.gz"
            output_path = os.path.join(nifti_dir, output_name)

            # Check if output file already exists
            if os.path.exists(output_path) and not overwrite:
                print(f"Skipping CT scan {target_ct} (already exists)")
            else:
                # Load the data
                data, affine = load_nifti_file(input_path)

                # Apply smoothing
                processed_data = apply_smoothing(data, sigma=sigma)

                # Save the processed data
                save_nifti_file(processed_data, affine, output_path)
                print(f"Processed CT scan {target_ct} and saved to {output_path}")
        else:
            print(f"Target CT scan {target_ct} not found in {nifti_dir}")
    else:
        print(f"Nifti directory not found in {patient_folder}")

    # Process voxel files in the corresponding subdirectory
    target_subdir = target_ct.replace('.nii.gz', '')
    voxels_dir = os.path.join(patient_folder, 'voxels')
    subdir_path = os.path.join(voxels_dir, target_subdir)
    if os.path.exists(subdir_path):
        # Create output directory with _MONAI suffix
        output_subdir = f"{target_subdir}_MONAI"
        output_dir = os.path.join(voxels_dir, output_subdir)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Process each NIfTI file in the subdirectory
        for file_name in os.listdir(subdir_path):
            if file_name.endswith('.nii.gz'):
                input_path = os.path.join(subdir_path, file_name)
                output_path = os.path.join(output_dir, file_name)

                # Check if output file already exists
                if os.path.exists(output_path) and not overwrite:
                    print(f"Skipping {file_name} from {target_subdir} (already exists)")
                    continue

                # Load the data
                data, affine = load_nifti_file(input_path)

                # Apply smoothing
                processed_data = apply_smoothing(data, sigma=sigma)

                # Save the processed data
                save_nifti_file(processed_data, affine, output_path)
                print(f"Processed {file_name} from {target_subdir} and saved to {output_path}")
    else:
        print(f"Voxels subdirectory {target_subdir} not found in {voxels_dir}")

if __name__ == "__main__":
    # Example usage
    patient_folder = "/Users/dave/AI/HPE/HPE-Nvidia-Vista-3D/output/PA00000002"
    sigma_value = 1.0  # Adjust smoothing intensity
    target_ct_name = "2.5MM_ARTERIAL_3"

    process_patient_folder(patient_folder, sigma=sigma_value, overwrite=True, target_ct=target_ct_name)
