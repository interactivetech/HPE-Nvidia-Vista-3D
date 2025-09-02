import streamlit as st
import streamlit.components.v1 as components
import os
import glob # Need glob for file scanning
import requests # For HTTP requests to image server
from dotenv import load_dotenv # For .env variables

# Load environment variables
load_dotenv()

# Get config from environment
IMAGE_SERVER_URL = os.getenv('IMAGE_SERVER', 'https://localhost:8888')
PROJECT_ROOT = os.getenv('PROJECT_ROOT', '.') # Default to current directory
st.set_page_config(layout="wide")

def get_patient_folders_from_server(base_url, data_source):
    """Fetch patient folders from the image server for the given data source."""
    try:
        # Request the directory listing from the image server
        url = f"{base_url}/outputs/{data_source}/"
        response = requests.get(url, verify=False, timeout=10)
        
        if response.status_code == 200:
            # Parse HTML response to extract folder names
            # This is a simple approach - assumes server returns directory listing
            import re
            html_content = response.text
            
            # Look for directory links in the HTML
            # Pattern matches typical directory listing formats
            folder_pattern = r'<a href="([^"]+)/"[^>]*>([^<]+)/?</a>'
            matches = re.findall(folder_pattern, html_content)
            
            # Filter out parent directory links and extract folder names
            folders = []
            for href, display_name in matches:
                if href not in ['.', '..', '../'] and not href.startswith('/'):
                    folder_name = href.rstrip('/')
                    if folder_name:  # Skip empty names
                        folders.append(folder_name)
            
            return sorted(list(set(folders)))  # Remove duplicates and sort
        else:
            st.error(f"Failed to fetch patient folders from server: {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to image server: {e}")
        return []
    except Exception as e:
        st.error(f"Error parsing server response: {e}")
        return []

def get_files_from_server(base_url, data_source, patient_folder):
    """Fetch files from the image server for the given patient folder."""
    try:
        # Request the directory listing for the patient folder
        url = f"{base_url}/outputs/{data_source}/{patient_folder}/"
        response = requests.get(url, verify=False, timeout=10)
        
        if response.status_code == 200:
            import re
            html_content = response.text
            
            # Look for file links in the HTML
            # Pattern matches files with medical imaging extensions
            file_pattern = r'<a href="([^"]+\.(nii|nii\.gz|dcm))"[^>]*>([^<]+)</a>'
            matches = re.findall(file_pattern, html_content, re.IGNORECASE)
            
            # Extract filenames
            files = []
            for href, ext, display_name in matches:
                if not href.startswith('/') and href not in ['.', '..']:
                    files.append(href)
            
            return sorted(list(set(files)))  # Remove duplicates and sort
        else:
            st.error(f"Failed to fetch files from server: {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to image server: {e}")
        return []
    except Exception as e:
        st.error(f"Error parsing server response: {e}")
        return []

# Sidebar for controls
with st.sidebar:
    st.header("Controls")
    
    # Data Source Selection
    data_sources = ['nifti', 'segments']
    selected_source_folder = st.selectbox("Select Data Source", data_sources)

    # Get patient folders from image server
    with st.spinner('Loading patient folders...'):
        patient_folders = get_patient_folders_from_server(IMAGE_SERVER_URL, selected_source_folder)

    
    selected_patient = st.selectbox("Select Patient", patient_folders)
    
    selected_file = None # Initialize selected_file
    if selected_patient:
        # Get files from image server
        with st.spinner('Loading files...'):
            nifti_filenames = get_files_from_server(IMAGE_SERVER_URL, selected_source_folder, selected_patient)
        
        if nifti_filenames:
            selected_file = st.selectbox("Select File", nifti_filenames)
        else:
            st.warning(f"No medical imaging files found for patient {selected_patient}")
        
        st.header("Viewer Settings")
        color_map = st.selectbox("Color Map", ['gray', 'viridis', 'plasma', 'inferno', 'magma'])
        show_crosshair = st.checkbox("Show 3D Crosshair", True)
        slice_type = st.selectbox("Slice Type", ["Axial", "Coronal", "Sagittal", "Render"], index=3)
        drag_mode = st.selectbox("Drag Mode", ["Contrast", "Measurement", "Pan"], index=0)
        show_colorbar = st.checkbox("Show Colorbar", True)
        show_ruler = st.checkbox("Show Ruler", True)



# Main area for viewer
if selected_file: # Check if selected_file is not None
    file_url = f'{IMAGE_SERVER_URL}/outputs/{selected_source_folder}/{selected_patient}/{selected_file}'

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
