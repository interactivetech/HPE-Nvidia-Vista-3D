import streamlit as st
import streamlit.components.v1 as components
import os
import glob # Need glob for file scanning
from dotenv import load_dotenv # For .env variables

# Load environment variables
load_dotenv()

# Get config from environment
IMAGE_SERVER_URL = os.getenv('IMAGE_SERVER', 'https://localhost:8888')
PROJECT_ROOT = os.getenv('PROJECT_ROOT', '.') # Default to current directory
NIFTI_BASE_DIR = os.path.join(PROJECT_ROOT, 'outputs', 'segments')

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
        
        st.header("Viewer Settings")
        color_map = st.selectbox("Color Map", ['gray', 'viridis', 'plasma', 'inferno', 'magma'])
        show_crosshair = st.checkbox("Show 3D Crosshair", True)
        slice_type = st.selectbox("Slice Type", ["Axial", "Coronal", "Sagittal", "Render"], index=3)
        drag_mode = st.selectbox("Drag Mode", ["Contrast", "Measurement", "Pan"], index=0)
        show_colorbar = st.checkbox("Show Colorbar", True)
        show_ruler = st.checkbox("Show Ruler", True)



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
        html_string = f"""<style>
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
<canvas id=\"niivue-canvas\"></canvas>
<script src=\"{IMAGE_SERVER_URL}/assets/niivue.umd.js\"></script>
<script>
    const nv = new niivue.Niivue ({{ 
        show3Dcrosshair: {str(show_crosshair).lower()},
        sliceType: {slice_type_map[slice_type]},
        dragMode: {drag_mode_map[drag_mode]},
        isColorbar: {str(show_colorbar).lower()},
        isRuler: {str(show_ruler).lower()},
    }});
    nv.attachTo('niivue-canvas');
    const volumeList = [
        {{
            url: '{file_url}',
            colormap: '{color_map}',
        }}
    ];
    nv.loadVolumes(volumeList);
</script>
"""
        
        components.html(html_string, height=700, width=2000)
else:
    st.info("Select a patient and a NIfTI file to view.")
