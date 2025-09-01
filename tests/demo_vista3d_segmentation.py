import os
import requests
import json
from pathlib import Path
from tqdm import tqdm
import nibabel as nib

# Configuration
VISTA3D_INFERENCE_URL = "http://localhost:8000/v1/vista3d/inference"
SAMPLE_NIFTI_URL = "https://raw.githubusercontent.com/rordenlab/MRIcroGL/master/Resources/standard/mni152.nii.gz"
OUTPUT_DIR = Path("outputs/segmentation")
TEMP_DIR = Path("outputs/temp")

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

def main():
    # Create output directories
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    print("--- Vista3D Segmentation Demo ---")
    print(f"Output will be saved to: {OUTPUT_DIR.absolute()}")
    print("----------------------------------")

    # 1. Download sample NIfTI file
    sample_nifti_local_path = TEMP_DIR / "mni152.nii.gz"
    if not sample_nifti_local_path.exists():
        if not download_file(SAMPLE_NIFTI_URL, sample_nifti_local_path):
            print("Failed to download sample NIfTI. Exiting.")
            return
    else:
        print(f"Using existing sample NIfTI: {sample_nifti_local_path}")

    # 2. Make inference request to Vista3D
    print("\n--- Making Inference Request ---")
    print(f"Sending {sample_nifti_local_path.name} to {VISTA3D_INFERENCE_URL}")
    
    # Define sample_nifti_server_url here, before it's used
    image_server_base_url = os.getenv('IMAGE_SERVER', 'https://host.docker.internal:8888')
    sample_nifti_server_url = f"{image_server_base_url}/outputs/temp/{sample_nifti_local_path.name}"
    print(f"Payload image URL: {sample_nifti_server_url}") # ADD THIS LINE

    payload = {"image": sample_nifti_server_url}
    headers = {"Content-Type": "application/json"}

    try:
        inference_response = requests.post(VISTA3D_INFERENCE_URL, json=payload, headers=headers, verify=False)
        inference_response.raise_for_status()
        result = inference_response.json()
        
        segmented_nifti_url = result.get("result")
        if not segmented_nifti_url:
            print("Error: 'result' URL not found in inference response.")
            print(f"Response: {result}")
            return
        
        print(f"Inference successful. Segmented NIfTI URL: {segmented_nifti_url}")

        # 3. Download segmented NIfTI file
        segmented_nifti_local_path = OUTPUT_DIR / Path(segmented_nifti_url).name
        if not download_file(segmented_nifti_url, segmented_nifti_local_path):
            print("Failed to download segmented NIfTI. Exiting.")
            return
        
        print("\n--- Segmentation Complete ---")
        print(f"Segmented NIfTI saved to: {segmented_nifti_local_path.absolute()}")
        
        print("\nTo view this segmentation:")
        print("1. Ensure your Streamlit app is running (`streamlit run app.py`).")
        print("2. Select the 'outputs' patient folder (or the folder containing your segmentation).")
        print("3. Select the segmented NIfTI file (e.g., 'mni152_seg.nii.gz') from the dropdown.")
        print("4. The segmentation will be displayed in the viewer.")
        print("Note: You might need to adjust viewer settings (e.g., colormap) to see the segmentation clearly.")

    except requests.exceptions.RequestException as e:
        print(f"Error during inference request: {e}")
        print(f"Please ensure the Vista3D Docker container is running and accessible at {VISTA3D_INFERENCE_URL}")
        print("You can start it using the `utils/vista3d.py` script.")
    except json.JSONDecodeError:
        print("Error: Could not decode JSON response from inference server.")
        print(f"Response content: {inference_response.text}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
