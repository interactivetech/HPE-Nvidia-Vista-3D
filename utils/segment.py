import tempfile
import os
import requests
import json
import argparse
from pathlib import Path
from tqdm import tqdm
import nibabel as nib
import gzip
import zipfile
import io
import numpy as np
import traceback
import shutil
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
IMAGE_SERVER_URL = os.getenv('IMAGE_SERVER', 'http://localhost:8888')
VISTA3D_INFERENCE_URL = "http://localhost:8000/v1/vista3d/inference"
PROJECT_ROOT = Path(os.getenv('PROJECT_ROOT', '.'))
NIFTI_INPUT_BASE_DIR = PROJECT_ROOT / "output"
PATIENT_OUTPUT_BASE_DIR = PROJECT_ROOT / "output"

# Load label dictionaries
LABEL_DICT_PATH = PROJECT_ROOT / "conf" / "vista3d_label_colors.json"
with open(LABEL_DICT_PATH, 'r') as f:
    label_colors_list = json.load(f)

    # Convert list to a dictionary for easier lookup by ID
    LABEL_DICT = {item['id']: item for item in label_colors_list}

    # Create a name-to-id map for target_vessels processing
    NAME_TO_ID_MAP = {item['name']: item['id'] for item in label_colors_list}



def get_nifti_files_in_folder(folder_path: Path):
    """Scans a specific folder for NIfTI files and returns their absolute paths."""
    if not folder_path.exists() or not folder_path.is_dir():
        return []
    return [folder_path / f for f in os.listdir(folder_path) if f.endswith(('.nii', '.nii.gz'))]

def create_patient_folder_structure(patient_id: str):
    """Create the new folder structure for a patient."""
    patient_base_dir = PATIENT_OUTPUT_BASE_DIR / patient_id
    nifti_dir = patient_base_dir / "nifti"
    segments_dir = patient_base_dir / "segments"
    voxels_dir = patient_base_dir / "voxels"
    
    # Create all directories
    nifti_dir.mkdir(parents=True, exist_ok=True)
    segments_dir.mkdir(parents=True, exist_ok=True)
    voxels_dir.mkdir(parents=True, exist_ok=True)
    
    return {
        'base': patient_base_dir,
        'nifti': nifti_dir,
        'segments': segments_dir,
        'voxels': voxels_dir
    }

def create_individual_voxel_files(segmentation_img, ct_scan_name: str, voxels_base_dir: Path, target_vessel_ids: list):
    """Create individual voxel files for each label in the segmentation."""
    # Create folder for this CT scan's voxels
    ct_scan_folder_name = ct_scan_name.replace('.nii.gz', '').replace('.nii', '')
    ct_voxels_dir = voxels_base_dir / ct_scan_folder_name
    ct_voxels_dir.mkdir(parents=True, exist_ok=True)
    
    # Get the segmentation data
    data = segmentation_img.get_fdata().astype(np.int16)
    affine = segmentation_img.affine
    header = segmentation_img.header
    
    # Find unique labels in the segmentation (excluding background/0)
    unique_labels = np.unique(data)
    unique_labels = unique_labels[unique_labels != 0]  # Remove background
    
    print(f"    Found {len(unique_labels)} unique labels in segmentation: {unique_labels}")
    
    created_files = []
    
    # Create individual voxel files for each label
    for label_id in unique_labels:
        if label_id in LABEL_DICT:
            label_info = LABEL_DICT[label_id]
            label_name = label_info['name'].lower().replace(' ', '_').replace('-', '_')
            
            # Create binary mask for this label
            label_data = np.zeros_like(data, dtype=np.int16)
            label_data[data == label_id] = label_id
            
            # Only create file if there are voxels for this label
            if np.any(label_data > 0):
                # Create new NIfTI image for this label
                label_img = nib.Nifti1Image(label_data, affine, header)
                
                # Save individual voxel file
                voxel_filename = f"{label_name}.nii.gz"
                voxel_path = ct_voxels_dir / voxel_filename
                nib.save(label_img, voxel_path)
                
                voxel_count = np.sum(label_data > 0)
                print(f"      Created {voxel_filename} with {voxel_count} voxels (label ID: {label_id})")
                created_files.append(voxel_filename)
    
    print(f"    Created {len(created_files)} individual voxel files in {ct_voxels_dir}")
    return created_files

def main():
    parser = argparse.ArgumentParser(description="Vista3D Batch Segmentation Script")
    parser.add_argument("patient_folder", type=str, nargs='?', default=None, help="Name of the patient folder to process.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing segmentation files.")
    args = parser.parse_args()

    # Create output directories if they don't exist
    NIFTI_INPUT_BASE_DIR.mkdir(parents=True, exist_ok=True)
    PATIENT_OUTPUT_BASE_DIR.mkdir(parents=True, exist_ok=True)

    patient_folders_to_process = []
    if args.patient_folder:
        if (NIFTI_INPUT_BASE_DIR / args.patient_folder).is_dir():
            patient_folders_to_process.append(args.patient_folder)
        else:
            print(f"Error: Specified patient folder not found: {NIFTI_INPUT_BASE_DIR / args.patient_folder}")
            return
    else:
        patient_folders_to_process = [f.name for f in NIFTI_INPUT_BASE_DIR.iterdir() if f.is_dir()]

    if not patient_folders_to_process:
        print("No patient folders found to process. Exiting.")
        return

    print("--- Vista3D Batch Segmentation Script ---")

    for patient_folder_name in tqdm(patient_folders_to_process, desc="Processing patients"):
        # The patient folder is now the base for nifti, segments, etc.
        patient_base_path = NIFTI_INPUT_BASE_DIR / patient_folder_name
        patient_nifti_path = patient_base_path / "nifti"
        print(f"\nProcessing patient folder: {patient_base_path}")

        vessels_of_interest_env = os.getenv('VESSELS_OF_INTEREST', '').strip().lower()
        target_vessels = [v.strip() for v in vessels_of_interest_env.split(',') if v.strip()] if vessels_of_interest_env != "all" else list(NAME_TO_ID_MAP.keys())
        
        if not target_vessels:
            print("No VESSELS_OF_INTEREST specified in .env. Skipping patient.")
            continue

        target_vessel_ids = []
        for v in target_vessels:
            if v in NAME_TO_ID_MAP:
                target_vessel_ids.append(NAME_TO_ID_MAP[v])
        
        # Create folder structure (will ensure segments and voxels directories exist)
        print(f"  Ensuring folder structure for patient: {patient_folder_name}")
        patient_dirs = create_patient_folder_structure(patient_folder_name)
        print(f"  Patient directories ensured: {patient_dirs['base']}")

        all_nifti_files = get_nifti_files_in_folder(patient_nifti_path)
        if not all_nifti_files:
            # Also check if the 'nifti' folder itself is missing
            if not patient_nifti_path.exists():
                print(f"No 'nifti' directory found in {patient_base_path}. Skipping patient.")
            else:
                print(f"No NIfTI files found in {patient_nifti_path}. Skipping patient.")
            continue

        for nifti_file_path in tqdm(all_nifti_files, desc="Processing NIfTI files"):
            # The NIfTI file is already in its final destination.
            # The copy step is no longer needed.
            
            # Define segmentation output path in current structure
            segmentation_output_path = patient_dirs['segments'] / nifti_file_path.name

            if not args.force and segmentation_output_path.exists():
                print(f"\n  Skipping {nifti_file_path.name} as segmentation already exists. Use --force to overwrite.")
                continue

            try:
                # Use the original nifti file path for inference
                relative_path_to_nifti = nifti_file_path.relative_to(PROJECT_ROOT)
                
                # When the inference server is running in a container, it needs to access the image server
                # running on the host. 'host.docker.internal' is a special DNS name for that.
                docker_accessible_url = IMAGE_SERVER_URL.replace('localhost', 'host.docker.internal').replace('127.0.0.1', 'host.docker.internal')
                
                vista3d_input_url = f"{docker_accessible_url.rstrip('/')}/{relative_path_to_nifti}"
                payload = {"image": vista3d_input_url, "prompts": {"labels": target_vessels}}
                headers = {"Content-Type": "application/json"}

                print(f"\n  Processing: {nifti_file_path.name}")
                inference_response = requests.post(VISTA3D_INFERENCE_URL, json=payload, headers=headers, verify=False)
                inference_response.raise_for_status()

                with zipfile.ZipFile(io.BytesIO(inference_response.content), 'r') as zip_ref:
                    nifti_filename = zip_ref.namelist()[0]
                    extracted_nifti_content = zip_ref.read(nifti_filename)
                
                # Create a temporary file to load the NIfTI image, as nibabel.load
                # can have issues with in-memory BytesIO objects.
                raw_nifti_img = None
                tmp_path = None
                try:
                    # The '.nii.gz' suffix is important for nibabel to correctly decompress.
                    with tempfile.NamedTemporaryFile(suffix=".nii.gz", delete=False) as tmp:
                        tmp.write(extracted_nifti_content)
                        tmp_path = tmp.name

                    # Load the NIfTI image from the temporary file.
                    img_loaded = nib.load(tmp_path)
                    
                    # Immediately load the data into memory to prevent issues with the temp file.
                    # Get data as float, then explicitly convert to int16
                    float_data = img_loaded.get_fdata(dtype=np.float32)
                    data = np.zeros(float_data.shape, dtype=np.int16)
                    data[:] = float_data[:]
                    data = np.ascontiguousarray(data) # Ensure contiguous
                    print(f"    Shape of data array: {data.shape}")
                    affine = img_loaded.affine
                    
                    # Create a new NIfTI header to ensure 3D dimensions
                    new_header = nib.Nifti1Header()
                    new_header.set_data_shape(data.shape)
                    new_header.set_data_dtype(np.int16) # Set dtype based on the numpy array
                    
                    # Create a new NIfTI image object in memory with the new header.
                    raw_nifti_img = nib.Nifti1Image(data, affine, new_header)

                except Exception as load_error:
                    import traceback
                    print(f"    ❌ Error loading NIfTI file with nibabel: {load_error}")
                    print("    Full traceback for nibabel.load error:")
                    traceback.print_exc()
                    raise  # Re-raise the exception
                finally:
                    # Clean up the temporary file.
                    if tmp_path and os.path.exists(tmp_path):
                        os.remove(tmp_path)

                # After loading, check if the image object was created successfully
                if raw_nifti_img is None:
                    raise Exception("Failed to load NIfTI image from received content.")
                
                print(f"    Data type of raw_nifti_img data: {raw_nifti_img.get_fdata().dtype}")
                print(f"    NIfTI header datatype: {raw_nifti_img.header['datatype']}")
                # Save full segmentation to segments folder
                nib.save(raw_nifti_img, segmentation_output_path)
                print(f"    Successfully saved segmentation: {segmentation_output_path.name}")
                
                # Create individual voxel files
                print(f"    Creating individual voxel files...")
                created_voxels = create_individual_voxel_files(
                    raw_nifti_img, 
                    nifti_file_path.name, 
                    patient_dirs['voxels'], 
                    target_vessel_ids
                )
                print(f"    Created {len(created_voxels)} individual voxel files")

            except requests.exceptions.RequestException as e:
                print(f"\n  Error during inference for {nifti_file_path.name}: {e}")
            except Exception as e:
                print(f"\n  An unexpected error occurred for {nifti_file_path.name}: {e}")

    print("\n--- Segmentation Process Complete ---")

if __name__ == "__main__":
    main()