
import nibabel as nib
import os

nifti_dir = "/home/hpadmin/NV/output/segments/PA00000002"
nifti_files = [f for f in os.listdir(nifti_dir) if f.endswith(".nii.gz")]

print(f"Checking NIfTI files in {nifti_dir}:")
for nifti_file in nifti_files:
    file_path = os.path.join(nifti_dir, nifti_file)
    try:
        img = nib.load(file_path)
        # Attempt to access some data to trigger potential errors
        _ = img.get_fdata()
        print(f"  {nifti_file}: OK (not corrupt)")
    except Exception as e:
        print(f"  {nifti_file}: CORRUPT (Error: {e})")
