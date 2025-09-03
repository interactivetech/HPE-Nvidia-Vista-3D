import streamlit as st
import streamlit.components.v1 as components
import os
import re
import requests
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# --- Initial Setup ---
st.set_page_config(layout="wide")
load_dotenv()
IMAGE_SERVER_URL = os.getenv('IMAGE_SERVER', 'https://localhost:8888')

# --- Helper Functions ---
def parse_directory_listing(html_content: str) -> List[Dict[str, str]]:
    """Parses the HTML from the image server to get a list of files and folders."""
    items = []
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        for item in soup.find_all('li'):
            link = item.find('a')
            if link and link.get('href'):
                text = link.get_text().strip()
                if text == "📁 .." or text.endswith('../'):
                    continue
                is_directory = text.startswith('📁') or text.endswith('/')
                name = re.sub(r'^📁\s*|📄\s*', '', text).strip('/')
                items.append({'name': name, 'is_directory': is_directory})
    except Exception as e:
        st.error(f"Error parsing directory listing: {e}")
    return items

def get_folder_contents(folder_path: str) -> Optional[List[Dict[str, str]]]:
    """Fetches and parses the contents of a specific folder from the image server."""
    url = f"{IMAGE_SERVER_URL.rstrip('/')}/outputs/{folder_path.strip('/')}/"
    try:
        response = requests.get(url, verify=False, timeout=10) # verify=False for self-signed certs
        if response.status_code == 200:
            return parse_directory_listing(response.text)
        elif response.status_code != 404:
            st.error(f"Image server returned HTTP {response.status_code}")
    except requests.exceptions.RequestException as e:
        st.error(f"Could not connect to image server: {e}")
    return None

def get_server_data(path: str, type: str, file_extensions: tuple):
    """Gets folders or files from the server based on the path and type."""
    items = get_folder_contents(path)
    if items is None:
        return []
    if type == 'folders':
        return sorted([item['name'] for item in items if item['is_directory']])
    elif type == 'files':
        return sorted([item['name'] for item in items if not item['is_directory'] and item['name'].lower().endswith(file_extensions)])
    return []

# --- Sidebar UI ---
with st.sidebar:
    st.header("Controls")
    data_sources = ['nifti', 'segments', 'overlay', 'mesh']
    selected_source = st.selectbox("Select Data Source", data_sources)

    patient_folders = get_server_data(selected_source, 'folders', ('',))
    selected_patient = st.selectbox("Select Patient", patient_folders)

    selected_file = None
    if selected_patient:
        file_ext = ('.nii', '.nii.gz', '.dcm') if selected_source != 'mesh' else ('.vtk', '.obj', '.stl', '.gltf', '.glb')
        filenames = get_server_data(f"{selected_source}/{selected_patient}", 'files', file_ext)
        selected_file = st.selectbox("Select File", filenames)

    # --- Viewer Settings ---
    st.header("Viewer Settings")
    show_overlay = False
    overlay_opacity = 0.5
    if selected_source == 'nifti' and selected_file:
        show_overlay = st.checkbox("Show Segmentation Overlay", value=True)
        if show_overlay:
            overlay_opacity = st.slider("Overlay Opacity", 0.0, 1.0, 0.5)

    if selected_source != 'mesh':
        slice_type = st.selectbox("Slice Type", ["3D Render", "Multiplanar", "Single View"], index=1)
        orientation = "Axial"
        if slice_type == "Single View":
            orientation = st.selectbox("Orientation", ["Axial", "Coronal", "Sagittal"], index=0)
        color_map = st.selectbox("Color Map", ['gray', 'viridis', 'plasma', 'inferno', 'magma'], index=0)
    else:
        slice_type, orientation, color_map = '3D Render', 'Axial', 'gray'

# --- Main Viewer Area ---
if selected_file:
    # --- Prepare URLs and Settings for Viewer ---
    base_file_url = f"{IMAGE_SERVER_URL}/outputs/{selected_source}/{selected_patient}/{selected_file}"
    segment_url = ''
    if show_overlay:
        base_name = selected_file.replace('.nii.gz', '').replace('.nii', '')
        segment_filename = f"{base_name}_colored_seg.nii.gz"
        segment_url = f"{IMAGE_SERVER_URL}/outputs/segments/{selected_patient}/{segment_filename}"

    slice_type_map = {"Axial": 0, "Coronal": 1, "Sagittal": 2, "Multiplanar": 3, "3D Render": 4}
    actual_slice_type = slice_type_map.get(slice_type if slice_type != "Single View" else orientation, 3)

    # --- HTML and Javascript for NiiVue ---
    html_string = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body, html {{ margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; }}
        #niivue-canvas {{ width: 100%; height: 100%; display: block; }}
    </style>
</head>
<body>
    <canvas id=\"niivue-canvas\"></canvas>
    <script src=\"{IMAGE_SERVER_URL}/assets/niivue.umd.js\"></script>
    <script>
        if (typeof niivue === 'undefined') {{
            console.error('Niivue library not loaded!');
        }} else {{
            const nv = new niivue.Niivue({{
                sliceType: {actual_slice_type},
                isColorbar: true
            }});
            nv.attachTo('niivue-canvas');

            const volumeList = [{{ url: \"{base_file_url}\", colormap: \"{color_map}\" }}];
            if ('{segment_url}') {{
                volumeList.push({{
                    url: '{segment_url}',
                    colormap: 'jet',
                    opacity: {overlay_opacity}
                }});
            }}

            nv.loadVolumes(volumeList).then(() => {{ 
                if ({actual_slice_type} === 3) {{ // 3 is Multiplanar
                    nv.setSliceType(nv.sliceType.MULTIPLANAR); // Ensure correct slice type
                    nv.opts.multiplanarShowRender = 'ALWAYS';
                    nv.drawScene();
                }}
            }}).catch(console.error);
        }}
    </script>
</body>
</html>"""

    components.html(html_string, height=1000, scrolling=False)
else:
    st.info("Select a data source, patient, and file to begin.")
