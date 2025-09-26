# MONAI Post-Processing for Vista3D Output

import os
import json
import numpy as np
import nibabel as nib
from monai.transforms import GaussianSmooth
from datetime import datetime


def load_nifti_file(file_path):
    """Load a NIfTI file and return the data and affine."""
    img = nib.load(file_path)
    return img.get_fdata(), img.affine

def save_nifti_file(data, affine, output_path):
    """Save data as a NIfTI file."""
    img = nib.Nifti1Image(data, affine)
    nib.save(img, output_path)

def update_json_metadata(json_path, monai_params):
    """Update JSON metadata to indicate MONAI enhancements have been applied.
    
    Args:
        json_path (str): Path to the JSON metadata file
        monai_params (dict): MONAI processing parameters used
    """
    try:
        # Load existing JSON if it exists
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                metadata = json.load(f)
        else:
            metadata = {}
        
        # Add MONAI enhancement information
        metadata['monai_enhancements'] = {
            'applied': True,
            'timestamp': datetime.now().isoformat(),
            'parameters': monai_params,
            'description': 'MONAI Gaussian smoothing applied for noise reduction and detail preservation'
        }
        
        # Save updated metadata
        with open(json_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Updated JSON metadata: {json_path}")
        
    except Exception as e:
        print(f"Warning: Could not update JSON metadata {json_path}: {e}")

def get_optimal_sigma_values(data_type="general", voxel_spacing=None):
    """Get optimal sigma values for different medical imaging data types.
    
    Args:
        data_type (str): Type of data - "ct", "mri", "segmentation", "general"
        voxel_spacing (list, optional): Voxel spacing in mm [x, y, z]
    
    Returns:
        float: Optimal sigma value for the data type
    """
    # Optimal sigma values based on medical imaging literature
    optimal_sigmas = {
        "ct": 0.4,           # CT scans - preserve fine details
        "mri": 0.5,          # MRI scans - balanced smoothing
        "segmentation": 0.6, # Segmentation masks - cleaner boundaries
        "general": 0.5       # General purpose
    }
    
    sigma = optimal_sigmas.get(data_type.lower(), 0.5)
    
    # Adjust for voxel spacing if provided
    if voxel_spacing is not None:
        # Scale sigma to maintain consistent effective smoothing across resolutions
        # Target: 0.5mm effective smoothing
        avg_spacing = np.mean(voxel_spacing)
        sigma = sigma * (avg_spacing / 1.0)  # Normalize to 1mm spacing
        sigma = np.clip(sigma, 0.1, 1.0)  # Keep within medical imaging range
    
    return sigma

def apply_smoothing(data, sigma=0.5, spacing=None):
    """Apply Gaussian smoothing with optimal medical imaging parameters.
    
    Args:
        data (np.ndarray): Input data to smooth
        sigma (float or list): Smoothing parameter. If spacing provided, 
                              sigma is scaled by voxel spacing for consistent smoothing.
        spacing (list, optional): Voxel spacing in mm [x, y, z]. If provided,
                                 sigma is scaled to maintain consistent smoothing across resolutions.
    
    Returns:
        np.ndarray: Smoothed data
    """
    # Validate sigma parameter for medical imaging
    if isinstance(sigma, (int, float)):
        if not 0.1 <= sigma <= 1.0:
            print(f"Warning: sigma={sigma} outside recommended medical imaging range (0.1-1.0)")
        sigma = float(sigma)
    elif isinstance(sigma, (list, tuple)):
        if not all(0.1 <= s <= 1.0 for s in sigma):
            print(f"Warning: sigma values outside recommended medical imaging range (0.1-1.0)")
    
    # Adaptive sigma based on voxel spacing for consistent smoothing
    if spacing is not None:
        # Scale sigma by voxel spacing to maintain consistent effective smoothing
        # across different image resolutions (target: 0.5mm effective smoothing)
        if isinstance(sigma, (int, float)):
            sigma = [s * 0.5 for s in spacing]  # Scale by spacing
        else:
            # If sigma is already a list, ensure it matches spacing length
            if len(sigma) != len(spacing):
                sigma = [sigma[0] * s * 0.5 for s in spacing]
    
    smoother = GaussianSmooth(sigma=sigma)
    return smoother(data[None, ...])[0].numpy()

def process_patient_folder(patient_folder, sigma=0.5, overwrite=False, target_ct='2.5MM_ARTERIAL_3.nii.gz', 
                          ct_sigma=None, voxel_sigma=None, inplace=True):
    """Process the specified CT scan and its associated voxels in the patient folder.
    
    Args:
        patient_folder (str): Path to the patient folder.
        sigma (float): Default smoothing intensity for all data types (0.1-1.0).
        overwrite (bool): If True, overwrite existing processed files. If False, skip them.
        target_ct (str): Specific CT scan filename to process.
        ct_sigma (float, optional): Specific sigma for CT scans. If None, uses sigma.
        voxel_sigma (float, optional): Specific sigma for voxel/segmentation data. If None, uses sigma.
        inplace (bool): If True, modify files in-place. If False, create new files with _MONAI suffix.
    """
    # Set optimal sigma values for different data types
    ct_sigma = ct_sigma if ct_sigma is not None else sigma
    voxel_sigma = voxel_sigma if voxel_sigma is not None else sigma
    
    # Process the specified CT scan in nifti directory
    nifti_dir = os.path.join(patient_folder, 'nifti')
    if os.path.exists(nifti_dir):
        input_path = os.path.join(nifti_dir, target_ct)
        if os.path.exists(input_path):
            # Determine output path based on inplace setting
            if inplace:
                output_path = input_path  # Overwrite original file
            else:
                base_name = target_ct.replace('.nii.gz', '')
                output_name = f"{base_name}_MONAI.nii.gz"
                output_path = os.path.join(nifti_dir, output_name)

            # Check if output file already exists (only for non-inplace mode)
            if not inplace and os.path.exists(output_path) and not overwrite:
                print(f"Skipping CT scan {target_ct} (already exists)")
            else:
                # Load the data
                data, affine = load_nifti_file(input_path)
                
                # Extract voxel spacing from affine matrix
                spacing = np.sqrt(np.sum(affine[:3, :3] ** 2, axis=0))

                # Apply smoothing with CT-optimized parameters
                processed_data = apply_smoothing(data, sigma=ct_sigma, spacing=spacing)

                # Save the processed data
                save_nifti_file(processed_data, affine, output_path)
                
                if inplace:
                    print(f"Enhanced CT scan {target_ct} in-place with sigma={ct_sigma}")
                else:
                    print(f"Processed CT scan {target_ct} with sigma={ct_sigma} and saved to {output_path}")
                
                # Update JSON metadata if inplace processing
                if inplace:
                    json_path = os.path.join(nifti_dir, target_ct.replace('.nii.gz', '.json'))
                    monai_params = {
                        'ct_sigma': ct_sigma,
                        'voxel_spacing': spacing.tolist(),
                        'processing_mode': 'inplace'
                    }
                    update_json_metadata(json_path, monai_params)
        else:
            print(f"Target CT scan {target_ct} not found in {nifti_dir}")
    else:
        print(f"Nifti directory not found in {patient_folder}")

    # Process voxel files in the corresponding subdirectory
    target_subdir = target_ct.replace('.nii.gz', '')
    voxels_dir = os.path.join(patient_folder, 'voxels')
    subdir_path = os.path.join(voxels_dir, target_subdir)
    if os.path.exists(subdir_path):
        # Process each NIfTI file in the subdirectory
        for file_name in os.listdir(subdir_path):
            if file_name.endswith('.nii.gz'):
                input_path = os.path.join(subdir_path, file_name)
                
                # Determine output path based on inplace setting
                if inplace:
                    output_path = input_path  # Overwrite original file
                else:
                    # Create output directory with _MONAI suffix
                    output_subdir = f"{target_subdir}_MONAI"
                    output_dir = os.path.join(voxels_dir, output_subdir)
                    if not os.path.exists(output_dir):
                        os.makedirs(output_dir)
                    output_path = os.path.join(output_dir, file_name)

                # Check if output file already exists (only for non-inplace mode)
                if not inplace and os.path.exists(output_path) and not overwrite:
                    print(f"Skipping {file_name} from {target_subdir} (already exists)")
                    continue

                # Load the data
                data, affine = load_nifti_file(input_path)

                # For individual voxel files, we need to preserve the label IDs
                # Apply smoothing but then threshold back to discrete values
                if file_name.endswith('.nii.gz'):
                    # Check if this is an individual voxel file (contains discrete label IDs)
                    unique_vals = np.unique(data)
                    if len(unique_vals) <= 2 and np.all(unique_vals == unique_vals.astype(int)):
                        # This is likely an individual voxel file with discrete label IDs
                        # Apply smoothing with voxel-optimized parameters
                        processed_data = apply_smoothing(data, sigma=voxel_sigma)
                        
                        # Adaptive thresholding based on data distribution
                        # Use median of non-zero smoothed values as threshold
                        non_zero_mask = data > 0
                        if np.any(non_zero_mask):
                            threshold = np.median(processed_data[non_zero_mask])
                            # Ensure threshold is reasonable (between 0.1 and 0.9)
                            threshold = np.clip(threshold, 0.1, 0.9)
                        else:
                            threshold = 0.5
                        
                        # Threshold back to discrete values to preserve label IDs
                        processed_data = np.where(processed_data > threshold, data, 0).astype(data.dtype)
                        print(f"Applied adaptive thresholding with threshold={threshold:.3f} for {file_name}")
                    else:
                        # This is a continuous volume, apply normal smoothing
                        processed_data = apply_smoothing(data, sigma=voxel_sigma)
                else:
                    # Apply normal smoothing for non-NIfTI files
                    processed_data = apply_smoothing(data, sigma=voxel_sigma)

                # Save the processed data
                save_nifti_file(processed_data, affine, output_path)
                
                if inplace:
                    print(f"Enhanced {file_name} from {target_subdir} in-place with sigma={voxel_sigma}")
                else:
                    print(f"Processed {file_name} from {target_subdir} and saved to {output_path}")
    else:
        print(f"Voxels subdirectory {target_subdir} not found in {voxels_dir}")

if __name__ == "__main__":
    # Process PA00000002 2.5MM_ARTERIAL_3 scan with in-place MONAI enhancements
    patient_folder = "/Users/dave/AI/HPE/HPE-Nvidia-Vista-3D/output/PA00000002"
    
    # Get optimal sigma values for different data types
    default_sigma = get_optimal_sigma_values("general")
    ct_sigma = get_optimal_sigma_values("ct")
    voxel_sigma = get_optimal_sigma_values("segmentation")
    
    target_ct_name = "2.5MM_ARTERIAL_3.nii.gz"

    print(f"Applying MONAI enhancements in-place to PA00000002:")
    print(f"  CT scan: {target_ct_name}")
    print(f"  Voxel files: {target_ct_name.replace('.nii.gz', '')}/*.nii.gz")
    print(f"  Using optimal parameters:")
    print(f"    CT sigma: {ct_sigma}")
    print(f"    Voxel/segmentation sigma: {voxel_sigma}")
    print(f"  Processing mode: IN-PLACE (no new files created)")

    process_patient_folder(
        patient_folder, 
        sigma=default_sigma, 
        ct_sigma=ct_sigma,
        voxel_sigma=voxel_sigma,
        overwrite=True, 
        target_ct=target_ct_name,
        inplace=True  # Process files in-place
    )
