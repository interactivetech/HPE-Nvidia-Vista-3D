import os
import requests
import json
import argparse
from pathlib import Path
from tqdm import tqdm
import nibabel as nib
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
LABEL_DICT_PATH = PROJECT_ROOT / "vista3d" / "label_dict.json"
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
    parser.add_argument("patient_folder", type=str, help="Name of the patient folder in outputs/nifti to process.")
    args = parser.parse_args()

    patient_folder_name = args.patient_folder
    patient_nifti_path = NIFTI_INPUT_BASE_DIR / patient_folder_name

    print("--- Vista3D Batch Segmentation Script ---")
    print(f"Processing patient folder: {patient_nifti_path.absolute()}")
    print(f"Output Segmentation directory: {SEGMENTATION_OUTPUT_BASE_DIR.absolute()}")
    print("------------------------------------------")

    # Determine vessels of interest
    vessels_of_interest_env = os.getenv('VESSELS_OF_INTEREST', '').strip().lower()
    target_vessels = []
    if vessels_of_interest_env == "all":
        target_vessels = list(LABEL_DICT.keys())
        print("Segmenting ALL available labels from label_dict.json.")
    elif vessels_of_interest_env:
        target_vessels = [v.strip() for v in vessels_of_interest_env.split(',') if v.strip()]
        # Validate requested vessels against LABEL_DICT
        invalid_vessels = [v for v in target_vessels if v not in LABEL_DICT]
        if invalid_vessels:
            print(f"Warning: The following vessels are not found in label_dict.json and will be ignored: {invalid_vessels}")
            target_vessels = [v for v in target_vessels if v in LABEL_DICT]
        print(f"Segmenting specified vessels: {', '.join(target_vessels)}")
    else:
        print("No Vessels_OF_INTEREST specified in .env. No segmentation will be performed.")
        return

    if not target_vessels:
        print("No valid vessels to segment. Exiting.")
        return

    # Convert vessel names to IDs
    target_vessel_ids = [LABEL_DICT[vessel] for vessel in target_vessels]
    print(f"Requesting segmentation for vessel IDs: {target_vessel_ids}")

    # Create output directory for the patient
    patient_segmentation_output_path = SEGMENTATION_OUTPUT_BASE_DIR / patient_folder_name
    patient_segmentation_output_path.mkdir(parents=True, exist_ok=True)

    all_nifti_files = get_nifti_files_in_folder(patient_nifti_path)
    if not all_nifti_files:
        print(f"No NIfTI files found in {patient_nifti_path}. Exiting.")
        return

    print(f"Found {len(all_nifti_files)} NIfTI files to process in {patient_folder_name}.")
    print("\n--- Starting Segmentation ---")

    successful_segmentations = 0
    failed_segmentations = 0

    for nifti_file_path in tqdm(all_nifti_files, desc="Processing NIfTI files", unit="file"):
        try:
            # Construct output path
            output_segmentation_path = patient_segmentation_output_path / f"{nifti_file_path.stem}_seg.nii.gz"

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
            print(f"    DEBUG: Raw inference response text: {inference_response.text}") # Added for debugging
            inference_response.raise_for_status()
            
            # Directly save the binary content of the response as the NIfTI file
            with open(output_segmentation_path, 'wb') as f:
                f.write(inference_response.content)
            
            print(f"    Inference successful. Segmented file saved to: {output_segmentation_path.name}")
            
            print(f"    Segmented file saved to: {output_segmentation_path.name}")
            successful_segmentations += 1

        except requests.exceptions.RequestException as e:
            print(f"\n  Error during inference request for {nifti_file_path.name}: {e}")
            print(f"  Status Code: {inference_response.status_code}") # Debugging
            print(f"  Response Text: {inference_response.text}") # Debugging
            print(f"  Please ensure the Vista3D Docker container is running and accessible at {VISTA3D_INFERENCE_URL}")
            failed_segmentations += 1
        except json.JSONDecodeError:
            print(f"\n  Error: Could not decode JSON response from inference server for {nifti_file_path.name}.")
            print(f"  Response content: {inference_response.text}")
            failed_segmentations += 1
        except Exception as e:
            print(f"\n  An unexpected error occurred for {nifti_file_path.name}: {e}")
            failed_segmentations += 1

    print("\n--- Segmentation Process Complete ---")
    print(f"Successful segmentations: {successful_segmentations}")
    print(f"Failed segmentations: {failed_segmentations}")
    print("-------------------------------------")
    print(f"You can now view the segmented files in your Streamlit app by selecting them from the 'outputs/segments/{patient_folder_name}' folder.")

if __name__ == "__main__":
    main()