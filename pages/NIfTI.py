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
        color_map = st.selectbox("Color Map", ['gray', 'viridis', 'plasma', 'inferno', 'magma'], index=2)
        slice_type = st.selectbox("Slice Type", ["Single View", "Multiplanar", "3D Render"], index=2)
        
        # Show orientation selector only for single view
        orientation = "Axial"  # default
        if slice_type == "Single View":
            orientation = st.selectbox("Orientation", ["Axial", "Coronal", "Sagittal"], index=0)
        
        drag_mode = st.selectbox("Drag Mode", ["Contrast", "Measurement", "Pan"], index=0)
        show_crosshair = st.checkbox("Show 3D Crosshair", True)
        show_colorbar = st.checkbox("Show Colorbar", True)
        show_ruler = st.checkbox("Show Ruler", True)



# Main area for viewer
if selected_file: # Check if selected_file is not None
    file_url = f'{IMAGE_SERVER_URL}/outputs/{selected_source_folder}/{selected_patient}/{selected_file}'

    # Determine the actual sliceType value based on selection
    if slice_type == "Single View":
        orientation_map = {"Axial": 0, "Coronal": 1, "Sagittal": 2}
        actual_slice_type = orientation_map[orientation]
    elif slice_type == "Multiplanar":
        actual_slice_type = 3  # Multiplanar
    elif slice_type == "3D Render":
        actual_slice_type = 4  # 3D render view
    else:
        actual_slice_type = 3  # fallback to multiplanar
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
    console.log('Starting Niivue initialization...');
    console.log('File URL:', '{file_url}');
    console.log('Niivue available:', typeof niivue !== 'undefined');
    
    if (typeof niivue === 'undefined') {{
        console.error('Niivue library not loaded!');
        document.getElementById('niivue-canvas').innerHTML = '<p style="color: red;">Error: Niivue library not loaded. Check if ./assets/niivue.umd.js exists.</p>';
    }} else {{
        try {{
        console.log('Creating Niivue with sliceType:', {actual_slice_type});
        const nv = new niivue.Niivue({{
            show3Dcrosshair: {str(show_crosshair).lower()},
            sliceType: {actual_slice_type},
            dragMode: {drag_mode_map[drag_mode]},
            isColorbar: {str(show_colorbar).lower()},
            isRuler: {str(show_ruler).lower()},
        }});
        console.log('Niivue instance created successfully:', nv);
        console.log('Available methods:', Object.getOwnPropertyNames(nv).filter(name => typeof nv[name] === 'function'));
        
        nv.attachTo('niivue-canvas');
        console.log('Attached to canvas');
        

        
        const volumeList = [
            {{
                url: '{file_url}',
                colormap: '{color_map}',
            }}
        ];
        console.log('Loading volumes:', volumeList);
        
        nv.loadVolumes(volumeList).then(() => {{
            console.log('Volumes loaded successfully');
            
            // Configure 4-panel layout for Multiplanar view after volumes are loaded
            if ({actual_slice_type} === 3) {{
                try {{
                    // Set multiplanar layout to 2x2 grid
                    if (nv.setMultiplanarLayout && nv.MULTIPLANAR_TYPE) {{
                        nv.setMultiplanarLayout(nv.MULTIPLANAR_TYPE.GRID);
                        console.log('Set 4-panel grid layout for Multiplanar view');
                    }} else if (nv.setMultiplanarLayout) {{
                        nv.setMultiplanarLayout('GRID');
                        console.log('Set 4-panel grid layout for Multiplanar view (string)');
                    }}

                    // Ensure 3D render is always shown in multiplanar
                    if (nv.opts && nv.SHOW_RENDER) {{
                        nv.opts.multiplanarShowRender = nv.SHOW_RENDER.ALWAYS;
                        console.log('Set multiplanarShowRender to ALWAYS');
                    }} else if (nv.opts) {{
                        nv.opts.multiplanarShowRender = 'ALWAYS';
                        console.log('Set multiplanarShowRender to ALWAYS (string)');
                    }}
                    // Fallback: force render tile on
                    if (nv.opts) {{
                        nv.opts.multiplanarForceRender = true;
                        console.log('Enabled multiplanarForceRender');
                    }}

                    if (nv.drawScene) nv.drawScene();
                }} catch (layoutError) {{
                    console.warn('Could not set multiplanar layout:', layoutError);
                }}
            }}
        }}).catch((error) => {{
            console.error('Error loading volumes:', error);
        }});
        }} catch (error) {{
            console.error('Error initializing Niivue:', error);
            document.getElementById('niivue-canvas').innerHTML = '<p style="color: red;">Error loading Niivue viewer: ' + error.message + '</p>';
        }}
    }}
</script>
"""
        
        components.html(html_string, height=800, width=1600)
else:
    st.info("Select a patient and a NIfTI file to view.")
