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
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
IMAGE_SERVER_URL = os.getenv('IMAGE_SERVER', 'https://localhost:8888')
VISTA3D_INFERENCE_URL = "http://localhost:8000/v1/vista3d/inference"
PROJECT_ROOT = Path(os.getenv('PROJECT_ROOT', '.'))
NIFTI_INPUT_BASE_DIR = PROJECT_ROOT / "outputs" / "nifti"
SEGMENTATION_OUTPUT_BASE_DIR = PROJECT_ROOT / "outputs" / "segments"

# Load label dictionaries
LABEL_DICT_PATH = PROJECT_ROOT / "conf" / "vista3d_label_colors.json"
with open(LABEL_DICT_PATH, 'r') as f:
    label_colors_list = json.load(f)

    # Convert list to a dictionary for easier lookup by ID
    LABEL_DICT = {item['id']: item for item in label_colors_list}

    # Create a name-to-id map for target_vessels processing
    NAME_TO_ID_MAP = {item['name']: item['id'] for item in label_colors_list}

def create_colored_segmentation(label_map_nii):
    """Creates a colored NIfTI image from a label map."""
    data = label_map_nii.get_fdata().astype(np.int16)
    affine = label_map_nii.affine
    header = label_map_nii.header

    colored_data = np.zeros((*data.shape, 3), dtype=np.uint8)
    unique_labels = np.unique(data)

    print(f"  Unique labels in NIfTI data: {unique_labels}")
    print(f"  LABEL_DICT content (first 5 values): {list(LABEL_DICT.values())[:5]}")

    for label_id in unique_labels:
        if label_id == 0:
            continue
        color = [255, 255, 255] # Default to white
        found_color = False
        print(f"  Processing label_id: {label_id} (type: {type(label_id)})")
        
        # Direct lookup using the new LABEL_DICT structure
        if int(label_id) in LABEL_DICT:
            label_info = LABEL_DICT[int(label_id)]
            color = label_info["color"]
            found_color = True
            print(f"    ID: {label_info['id']} - Name: {label_info['name']}, Color: {label_info['color']} (Match: True)")
        else:
            print(f"    ID: {label_id} - Name: N/A, Color: [255, 255, 255] (Match: False)") # No match found
        
        print(f"  Applying color {color} to label ID {label_id} (Found: {found_color})")
        colored_data[data == label_id] = color

    return nib.Nifti1Image(colored_data, affine, header)

def get_nifti_files_in_folder(folder_path: Path):
    """Scans a specific folder for NIfTI files and returns their absolute paths."""
    if not folder_path.exists() or not folder_path.is_dir():
        return []
    return [folder_path / f for f in os.listdir(folder_path) if f.endswith(('.nii', '.nii.gz'))]

def main():
    parser = argparse.ArgumentParser(description="Vista3D Batch Segmentation Script")
    parser.add_argument("patient_folder", type=str, nargs='?', default=None, help="Name of the patient folder to process.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing segmentation files.")
    args = parser.parse_args()

    patient_folders_to_process = []
    if args.patient_folder:
        if (NIFTI_INPUT_BASE_DIR / args.patient_folder).is_dir():
            patient_folders_to_process.append(args.patient_folder)
        else:
            print(f"Error: Specified patient folder not found: {NIFTI_INPUT_BASE_DIR / args.patient_folder}")
            return
    else:
        if NIFTI_INPUT_BASE_DIR.exists():
            patient_folders_to_process = [f.name for f in NIFTI_INPUT_BASE_DIR.iterdir() if f.is_dir()]
        else:
            print(f"Error: NIfTI input base directory not found: {NIFTI_INPUT_BASE_DIR}")
            return

    if not patient_folders_to_process:
        print("No patient folders found to process. Exiting.")
        return

    print("--- Vista3D Batch Segmentation Script ---")

    for patient_folder_name in tqdm(patient_folders_to_process, desc="Processing patients"):
        patient_nifti_path = NIFTI_INPUT_BASE_DIR / patient_folder_name
        print(f"\nProcessing patient folder: {patient_nifti_path}")

        vessels_of_interest_env = os.getenv('VESSELS_OF_INTEREST', '').strip().lower()
        target_vessels = [v.strip() for v in vessels_of_interest_env.split(',') if v.strip()] if vessels_of_interest_env != "all" else list(NAME_TO_ID_MAP.keys())
        
        if not target_vessels:
            print("No VESSELS_OF_INTEREST specified in .env. Skipping patient.")
            continue

        target_vessel_ids = []
        for v in target_vessels:
            if v in NAME_TO_ID_MAP:
                target_vessel_ids.append(NAME_TO_ID_MAP[v])
        
        patient_segmentation_output_path = SEGMENTATION_OUTPUT_BASE_DIR / patient_folder_name
        patient_segmentation_output_path.mkdir(parents=True, exist_ok=True)

        all_nifti_files = get_nifti_files_in_folder(patient_nifti_path)
        if not all_nifti_files:
            print(f"No NIfTI files found in {patient_nifti_path}. Skipping patient.")
            continue

        for nifti_file_path in tqdm(all_nifti_files, desc="Processing NIfTI files"):
            base_name = nifti_file_path.name.replace('.nii.gz', '').replace('.nii', '')
            output_segmentation_path = patient_segmentation_output_path / f"{base_name}_seg.nii.gz"
            colored_output_path = patient_segmentation_output_path / f"{base_name}_colored_seg.nii.gz"

            if not args.force and output_segmentation_path.exists() and colored_output_path.exists():
                print(f"\n  Skipping {nifti_file_path.name} as output files already exist. Use --force to overwrite.")
                continue

            try:
                relative_path_to_nifti = nifti_file_path.relative_to(PROJECT_ROOT)
                vista3d_input_url = f"https://host.docker.internal:8888/{relative_path_to_nifti}"
                payload = {"image": vista3d_input_url, "prompts": {"classes": target_vessel_ids}}
                headers = {"Content-Type": "application/json"}

                print(f"\n  Processing: {nifti_file_path.name}")
                inference_response = requests.post(VISTA3D_INFERENCE_URL, json=payload, headers=headers, verify=False)
                inference_response.raise_for_status()

                with zipfile.ZipFile(io.BytesIO(inference_response.content), 'r') as zip_ref:
                    nifti_filename = zip_ref.namelist()[0]
                    extracted_nifti_content = zip_ref.read(nifti_filename)
                
                with open(output_segmentation_path, 'wb') as f:
                    f.write(extracted_nifti_content)
                
                print(f"    Successfully saved raw segmentation: {output_segmentation_path.name}")

                # Create and save the colored version
                raw_nifti_img = nib.load(output_segmentation_path)
                print("    Creating colored segmentation...")
                colored_nifti_img = create_colored_segmentation(raw_nifti_img)
                
                nib.save(colored_nifti_img, colored_output_path)
                print(f"    Successfully saved colored segmentation: {colored_output_path.name}")

            except requests.exceptions.RequestException as e:
                print(f"\n  Error during inference for {nifti_file_path.name}: {e}")
            except Exception as e:
                print(f"\n  An unexpected error occurred for {nifti_file_path.name}: {e}")

    print("\n--- Segmentation Process Complete ---")

if __name__ == "__main__":
    main()