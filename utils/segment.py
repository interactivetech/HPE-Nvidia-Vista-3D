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
import numpy as np # Added numpy
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
IMAGE_SERVER_URL = os.getenv('IMAGE_SERVER', 'https://localhost:8888')
VISTA3D_INFERENCE_URL = "http://localhost:8000/v1/vista3d/inference"
PROJECT_ROOT = Path(os.getenv('PROJECT_ROOT', '.'))
NIFTI_INPUT_BASE_DIR = PROJECT_ROOT / "outputs" / "nifti"
SEGMENTATION_OUTPUT_BASE_DIR = PROJECT_ROOT / "outputs" / "segments" # Changed to 'segments'


# Load label dictionary
LABEL_DICT_PATH = PROJECT_ROOT / "conf" / "label_dict.json"
with open(LABEL_DICT_PATH, 'r') as f:
    LABEL_DICT = json.load(f)

def download_file(url: str, destination_path: Path):
    """Downloads a file from a URL with a progress bar."""
    print(f"Downloading {url} to {destination_path}...")
    try:
        response = requests.get(url, stream=True, verify=False) # verify=False for self-signed certs
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024 # 1 Kibibyte
        
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(destination_path, 'wb') as f:
            with tqdm(total=total_size, unit='iB', unit_scale=True, desc=destination_path.name) as pbar:
                for chunk in response.iter_content(chunk_size=block_size):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
        print(f"Successfully downloaded {destination_path}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {e}")
        return False

def get_nifti_files_in_folder(folder_path: Path):
    """Scans a specific folder for NIfTI files and returns their absolute paths."""
    nifti_files = []
    if not folder_path.exists() or not folder_path.is_dir():
        print(f"Error: Folder not found or is not a directory: {folder_path}")
        return []

    for file in os.listdir(folder_path):
        if file.endswith(('.nii', '.nii.gz')):
            nifti_files.append(folder_path / file)
    return nifti_files

def main():
    parser = argparse.ArgumentParser(description="Vista3D Batch Segmentation Script")
    parser.add_argument("patient_folder", type=str, nargs='?', default=None, help="Name of the patient folder in outputs/nifti to process. If not provided, all patient folders will be processed.")
    args = parser.parse_args()

    patient_folders_to_process = []
    if args.patient_folder:
        patient_folders_to_process.append(args.patient_folder)
    else:
        # Process all patient folders
        if os.path.exists(NIFTI_INPUT_BASE_DIR):
            patient_folders_to_process = [f for f in os.listdir(NIFTI_INPUT_BASE_DIR) if os.path.isdir(NIFTI_INPUT_BASE_DIR / f)]
        else:
            print(f"Error: NIfTI input base directory not found: {NIFTI_INPUT_BASE_DIR}")
            return

    if not patient_folders_to_process:
        print("No patient folders found to process. Exiting.")
        return

    print("--- Vista3D Batch Segmentation Script ---")
    print(f"Output Segmentation directory: {SEGMENTATION_OUTPUT_BASE_DIR.absolute()}")
    print("------------------------------------------")

    successful_patient_conversions = 0
    failed_patient_conversions = 0

    for patient_folder_name in tqdm(patient_folders_to_process, desc="Processing patients", unit="patient"):
        patient_nifti_path = NIFTI_INPUT_BASE_DIR / patient_folder_name
        print(f"\nProcessing patient folder: {patient_nifti_path.absolute()}")
        print("-" * 50)

    # Determine vessels of interest
        vessels_of_interest_env = os.getenv('VESSELS_OF_INTEREST', '').strip().lower()
        target_vessels = []
        if vessels_of_interest_env == "all":
            target_vessels = list(LABEL_DICT.keys())
            print("Segmenting ALL available labels from conf/label_dict.json.")
        elif vessels_of_interest_env:
            target_vessels = [v.strip() for v in vessels_of_interest_env.split(',') if v.strip()]
            # Validate requested vessels against LABEL_DICT
            invalid_vessels = [v for v in target_vessels if v not in LABEL_DICT]
            if invalid_vessels:
                print(f"Warning: The following vessels are not found in conf/label_dict.json and will be ignored: {invalid_vessels}")
                target_vessels = [v for v in target_vessels if v in LABEL_DICT]
            print(f"Segmenting specified vessels: {', '.join(target_vessels)}")
        else:
            print("No Vessels_OF_INTEREST specified in .env. No segmentation will be performed.")
            # If no vessels are specified, consider this patient as failed for segmentation purposes
            failed_patient_conversions += 1
            continue # Skip to next patient

        if not target_vessels:
            print("No valid vessels to segment. Exiting.")
            failed_patient_conversions += 1
            continue # Skip to next patient

    # Convert vessel names to IDs
        target_vessel_ids = [LABEL_DICT[vessel] for vessel in target_vessels]
        print(f"Requesting segmentation for vessel IDs: {target_vessel_ids}")

        # Create output directory for the patient
        patient_segmentation_output_path = SEGMENTATION_OUTPUT_BASE_DIR / patient_folder_name
        patient_segmentation_output_path.mkdir(parents=True, exist_ok=True)

        all_nifti_files = get_nifti_files_in_folder(patient_nifti_path)
        if not all_nifti_files:
            print(f"No NIfTI files found in {patient_nifti_path}. Exiting.")
            failed_patient_conversions += 1
            continue # Skip to next patient

    print(f"Found {len(all_nifti_files)} NIfTI files to process in {patient_folder_name}.")
    print("\n--- Starting Segmentation ---")

    successful_segmentations_for_patient = 0
    failed_segmentations_for_patient = 0

    for nifti_file_path in tqdm(all_nifti_files, desc="Processing NIfTI files", unit="file"):
        try:
            # Construct output path

            # Construct URL for Vista3D (using host.docker.internal for container access)
            # The image server serves from PROJECT_ROOT, so relative_path is correct for URL
            relative_path_to_nifti = nifti_file_path.relative_to(PROJECT_ROOT)
            vista3d_input_url = f"https://host.docker.internal:8888/{relative_path_to_nifti}"

            payload = {"image": vista3d_input_url}
            if target_vessel_ids:
                payload["prompts"] = {"classes": target_vessel_ids}
            else:
                # This case should ideally not be reached due to earlier checks
                payload["prompts"] = {}
            headers = {"Content-Type": "application/json"}

            print(f"\n  Processing: {nifti_file_path.name}")
            print(f"    Input URL for Vista3D: {vista3d_input_url}")
            print(f"    Requesting segmentation for: {target_vessels} (IDs: {target_vessel_ids})")

            inference_response = requests.post(VISTA3D_INFERENCE_URL, json=payload, headers=headers, verify=False)
            
            inference_response.raise_for_status()
            
            
            
            
            
            # Construct output path with .nii.gz extension
            output_segmentation_path = patient_segmentation_output_path / f"{nifti_file_path.with_suffix('').stem}_seg.nii.gz"

            # Process the ZIP file response
            zip_file_like_object = io.BytesIO(inference_response.content)
            with zipfile.ZipFile(zip_file_like_object, 'r') as zip_ref:
                # Assuming there's only one file in the zip, or the NIfTI is the first one
                nifti_filename = zip_ref.namelist()[0]
                extracted_nifti_content = zip_ref.read(nifti_filename)

            

            # Construct output path with .nii.gz extension
            output_segmentation_path = patient_segmentation_output_path / f"{nifti_file_path.with_suffix('').stem}_seg.nii.gz"

            import tempfile
            tmp_file_path = None # Initialize to None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".nii.gz") as tmp_file:
                    tmp_file.write(extracted_nifti_content)
                    tmp_file_path = Path(tmp_file.name)

                original_nifti_img = nib.load(tmp_file_path)
                segmentation_scan = original_nifti_img.get_fdata()
                affine = original_nifti_img.affine

                # Create a new segmentation map with only the vessels of interest in it.
                # The VISTA-3D output should already contain the correct label IDs.
                # We will filter it to only include the target vessels.
                filtered_segmentation_scan = np.zeros_like(segmentation_scan, dtype=np.uint8) # Ensure uint8 dtype
                
                for vessel_name in target_vessels:
                    original_label_id = LABEL_DICT[vessel_name]
                    # Assign original label ID to voxels matching original_label_id
                    filtered_segmentation_scan[segmentation_scan == original_label_id] = original_label_id

                # Create a new NIfTI image with the filtered data
                # Preserve original affine and header info
                remapped_nifti_img = nib.Nifti1Image(filtered_segmentation_scan, affine, original_nifti_img.header)
                
                # Save the remapped NIfTI image
                if not output_segmentation_path.parent.exists():
                    print(f"    ERROR: Output directory does not exist: {output_segmentation_path.parent}")
                    raise IOError("Output directory not found")

                print(f"    Attempting to save to: {output_segmentation_path}")
                print(f"    NIfTI image shape before saving: {remapped_nifti_img.shape}")
                print(f"    NIfTI image dtype before saving: {remapped_nifti_img.header.get_data_dtype()}")

                try:
                    nib.save(remapped_nifti_img, output_segmentation_path)
                    if os.path.exists(output_segmentation_path):
                        print(f"    Successfully saved: {output_segmentation_path.name}")
                    else:
                        print(f"    ERROR: File not found after saving: {output_segmentation_path.name}")
                        raise IOError("File not found after save operation")
                except Exception as save_e:
                    print(f"    ERROR: Failed to save NIfTI file: {save_e}")
                    raise IOError(f"Failed to save NIfTI file: {save_e}")
                
                print(f"    Saved NIfTI dtype: {remapped_nifti_img.header.get_data_dtype()}")
                print(f"    Saved NIfTI shape: {remapped_nifti_img.shape}")
                print(f"    Inference successful. Remapped and saved to: {output_segmentation_path.name}")

            finally:
                if tmp_file_path and tmp_file_path.exists(): # Only delete if it was created and still exists
                    os.unlink(tmp_file_path)
            
            successful_segmentations_for_patient += 1

        except requests.exceptions.RequestException as e:
            print(f"\n  Error during inference request for {nifti_file_path.name}: {e}")
            print(f"  Status Code: {inference_response.status_code}") # Debugging
            
            print(f"  Please ensure the Vista3D Docker container is running and accessible at {VISTA3D_INFERENCE_URL}")
            failed_segmentations_for_patient += 1
        except json.JSONDecodeError:
            print(f"\n  Error: Could not decode JSON response from inference server for {nifti_file_path.name}.")
            
            failed_segmentations_for_patient += 1
        except Exception as e:
            print(f"\n  An unexpected error occurred for {nifti_file_path.name}: {e}")
            failed_segmentations_for_patient += 1
        
        # Update patient-level counts
        if successful_segmentations_for_patient > 0:
            successful_patient_conversions += 1
        else:
            failed_patient_conversions += 1

    print("\n--- Segmentation Process Complete ---")
    print(f"Successful patient segmentations: {successful_patient_conversions}")
    print(f"Failed patient segmentations: {failed_patient_conversions}")
    print("-------------------------------------")
    print(f"You can now view the segmented files in your Streamlit app by selecting them from the 'outputs/segments/<patient_folder>' folder.")

if __name__ == "__main__":
    main()