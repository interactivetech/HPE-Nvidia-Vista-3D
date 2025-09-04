import nibabel as nib
import numpy as np
import os

file_path = "outputs/segments/PA00000002/01_2.5MM_ARTERIAL_seg_int16.nii.gz"

if not os.path.exists(file_path):
    print(f"Error: File not found at {file_path}")
else:
    try:
        img = nib.load(file_path)
        data = img.get_fdata()
        header = img.header

        print(f"File: {file_path}")
        print(f"  Data Shape: {data.shape}")
        print(f"  Data Dtype: {data.dtype}")
        print(f"  Raw NIfTI Header Object: {header}")
        print(f"  NIfTI Header 'dim' field: {header['dim']}")
        print(f"  NIfTI Header 'datatype' field: {header['datatype']}")
        print(f"  NIfTI Header 'pixdim' field: {header['pixdim']}")
        print(f"  NIfTI Header 'sform_code' field: {header['sform_code']}")
        print(f"  NIfTI Header 'qform_code' field: {header['qform_code']}")
        print(f"  NIfTI Header 'srow_x' field: {header['srow_x']}")
        print(f"  NIfTI Header 'srow_y' field: {header['srow_y']}")
        print(f"  NIfTI Header 'srow_z' field: {header['srow_z']}")

        # Check unique values in data to confirm it's a label map
        unique_values = np.unique(data)
        print(f"  Unique Data Values (first 10): {unique_values[:10]}")
        print(f"  Number of Unique Data Values: {len(unique_values)}")

    except Exception as e:
        print(f"Error loading or inspecting NIfTI file: {e}")
