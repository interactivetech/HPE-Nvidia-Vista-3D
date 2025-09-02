import streamlit as st
import streamlit.components.v1 as components
import os
import glob # Need glob for file scanning
from dotenv import load_dotenv # For .env variables
from pathlib import Path # Import Path
import json # Import json

# Load environment variables
load_dotenv()

# Get config from environment
IMAGE_SERVER_URL = os.getenv('IMAGE_SERVER', 'https://localhost:8888')
PROJECT_ROOT = os.getenv('PROJECT_ROOT', '.') # Default to current directory
NIFTI_BASE_DIR = os.path.join(PROJECT_ROOT, 'outputs', 'segments')

# Load label dictionary
LABEL_DICT_PATH = Path(PROJECT_ROOT) / "conf" / "label_dict.json"
with open(LABEL_DICT_PATH, 'r') as f:
    LABEL_DICT = json.load(f)

LABEL_COLORS_PATH = Path(PROJECT_ROOT) / "conf" / "label_colors.json"
with open(LABEL_COLORS_PATH, 'r') as f:
    LABEL_COLORS = json.load(f)

def generate_niivue_colormap(label_dict):
    colormap = [[0, 0, 0, 0, 0]]  # Background/transparent for label 0
    
    # Use colors from LABEL_COLORS
    for label_id_str, rgb_color in LABEL_COLORS.items():
        label_id = int(label_id_str)
        if label_id > 0: # Skip background if it's 0
            r, g, b = rgb_color
            colormap.append([label_id, r, g, b, 255]) # Add opaque alpha
    
    # Sort colormap by label_id to ensure correct order for Niivue
    colormap.sort(key=lambda x: x[0])
    
    return colormap

NIIVUE_COLORMAP = generate_niivue_colormap(LABEL_DICT)

st.set_page_config(layout="wide")

# Sidebar for controls
with st.sidebar:
    st.header("Controls")
    
    source_folder = 'segments'

    # Get patient folders from local filesystem
    patient_folders = []
    if os.path.exists(NIFTI_BASE_DIR):
        patient_folders = [f for f in os.listdir(NIFTI_BASE_DIR) if os.path.isdir(os.path.join(NIFTI_BASE_DIR, f))]
    
    selected_patient = st.selectbox("Select Patient", patient_folders)
    
    selected_file = None # Initialize selected_file
    if selected_patient:
        # Get NIfTI files from local filesystem
        folder_path = os.path.join(NIFTI_BASE_DIR, selected_patient)
        nifti_files = glob.glob(os.path.join(folder_path, '*.nii')) + \
                      glob.glob(os.path.join(folder_path, '*.nii.gz'))
        
        # Extract just the filenames
        nifti_filenames = [os.path.basename(f) for f in nifti_files]
        
        selected_file = st.selectbox("Select NIfTI File", nifti_filenames)
        
        # Viewer Settings (removed as they are now hardcoded in niivue)



# Main area for viewer
if selected_file: # Check if selected_file is not None
    file_url = f'{IMAGE_SERVER_URL}/outputs/{source_folder}/{selected_patient}/{selected_file}'

    slice_type_map = {
        "Axial": 0,
        "Coronal": 1,
        "Sagittal": 2,
        "Render": 3
    }
    drag_mode_map = {
        "Contrast": 1,
        "Measurement": 2,
        "Pan": 3
    }

    with st.spinner('Loading NIfTI file...'):
        html_string = r"""<style>
body, html {{
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
    overflow: hidden;
}}
#niivue-canvas {{
    width: 100%;
    height: 100%;
    display: block;
}}
</style>
<canvas id="niivue-canvas"></canvas>
<script src="{image_server_url}/assets/niivue.umd.js"></script>
<script>
    
    const nv = new niivue.Niivue ({{
        show3Dcrosshair: {show3d_crosshair},
        sliceType: 3,
        dragMode: 1,
        isColorbar: {is_colorbar},
        isRuler: {is_ruler},
    }});
    nv.attachTo('niivue-canvas');
    const volumeUrl = '{file_url}';
    const volumeList = [
        {{
            url: volumeUrl,
            colormap: {colormap},
        }}
    ];
    nv.loadVolumes(volumeList);
</script>
        """.format(
            image_server_url=IMAGE_SERVER_URL,
            show3d_crosshair=str(True).lower(),
            is_colorbar=str(True).lower(),
            is_ruler=str(True).lower(),
            file_url=file_url,
            colormap=json.dumps(NIIVUE_COLORMAP)
        )
        
        components.html(html_string, height=700, width=2000)
else:
    st.info("Select a patient and a NIfTI file to view.")
