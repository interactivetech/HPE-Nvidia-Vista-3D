import streamlit as st
import streamlit.components.v1 as components
import os
import glob # Need glob for file scanning
import requests # For HTTP requests to image server
import urllib3
from urllib.parse import urljoin
import re
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from dotenv import load_dotenv # For .env variables

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables
load_dotenv()

# Get config from environment
IMAGE_SERVER_URL = os.getenv('IMAGE_SERVER', 'https://localhost:8888')
PROJECT_ROOT = os.getenv('PROJECT_ROOT', '.') # Default to current directory
st.set_page_config(layout="wide")

def parse_directory_listing(html_content: str) -> List[Dict[str, str]]:
    """Parse HTML directory listing to extract file and folder information."""
    items = []
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all list items in the directory listing
        list_items = soup.find_all('li')
        
        for item in list_items:
            link = item.find('a')
            if link and link.get('href'):
                href = link.get('href')
                text = link.get_text().strip()
                
                # Skip parent directory links
                if text == "📁 ../" or href.endswith('../'):
                    continue
                
                # Determine if it's a directory or file
                is_directory = text.startswith('📁') or href.endswith('/')
                
                # Extract name (remove emoji and trailing slash)
                name = re.sub(r'^📁\s*|📄\s*', '', text)
                if name.endswith('/'):
                    name = name[:-1]
                
                # Extract size info if present
                size_info = ""
                size_span = item.find('span', style=re.compile(r'color.*#666'))
                if size_span:
                    size_info = size_span.get_text().strip()
                
                items.append({
                    'name': name,
                    'href': href,
                    'is_directory': is_directory,
                    'size': size_info,
                    'full_text': text
                })
    
    except Exception as e:
        st.error(f"Error parsing directory listing: {e}")
    
    return items

def get_folder_contents(base_url: str, folder_path: str, verify_ssl: bool = False) -> Optional[List[Dict[str, str]]]:
    """Get contents of a folder from the image server."""
    
    # Construct the full URL
    folder_url = urljoin(base_url.rstrip('/') + '/', f"outputs/{folder_path}/")
    
    try:
        # Make request with SSL verification disabled for self-signed certs
        response = requests.get(folder_url, verify=verify_ssl, timeout=10)
        
        if response.status_code == 200:
            items = parse_directory_listing(response.text)
            return items
        elif response.status_code == 404:
            st.warning(f"Folder not found: {folder_path}")
            return None
        else:
            st.error(f"HTTP {response.status_code}: {response.reason}")
            return None
            
    except requests.exceptions.SSLError as e:
        st.error(f"SSL Error: {e}")
        return None
    except requests.exceptions.ConnectionError as e:
        st.error(f"Connection Error: {e}. Make sure the image server is running.")
        return None
    except requests.exceptions.Timeout:
        st.error(f"Request timed out")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return None

def get_patient_folders_from_server(base_url, data_source):
    """Fetch patient folders from the image server for the given data source."""
    items = get_folder_contents(base_url, data_source, verify_ssl=False)
    
    if items is None:
        return []
    
    # Extract only directories (patient folders)
    patient_folders = []
    for item in items:
        if item['is_directory']:
            patient_folders.append(item['name'])
    
    return sorted(patient_folders)

def get_files_from_server(base_url, data_source, patient_folder):
    """Fetch files from the image server for the given patient folder."""
    items = get_folder_contents(base_url, f"{data_source}/{patient_folder}", verify_ssl=False)
    
    if items is None:
        return []
    
    # Extract only files with medical imaging extensions
    medical_files = []
    for item in items:
        if not item['is_directory']:
            filename = item['name']
            # Check for medical imaging file extensions
            if filename.lower().endswith(('.nii', '.nii.gz', '.dcm')):
                medical_files.append(filename)
    
    return sorted(medical_files)

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
