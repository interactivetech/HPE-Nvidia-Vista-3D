import streamlit as st
import streamlit.components.v1 as components
import os
import re
import requests
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import json

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
                if text == "📁 ../" or text.endswith('../'):
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
    data_sources = ['nifti', 'segments']
    selected_source = st.selectbox("Select Data Source", data_sources)

    patient_folders = get_server_data(selected_source, 'folders', ('',))
    selected_patient = st.selectbox("Select Patient", patient_folders)

    selected_file = None
    if selected_patient:
        file_ext = ('.nii', '.nii.gz', '.dcm')
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

    slice_type = st.selectbox("Slice Type", ["3D Render", "Multiplanar", "Single View"], index=1)
    orientation = "Axial"
    if slice_type == "Single View":
        orientation = st.selectbox("Orientation", ["Axial", "Coronal", "Sagittal"], index=0)

    # Only show colormap selector when not viewing segments directly
    if selected_source != 'segments':
        color_map = st.selectbox("Color Map", ['gray', 'viridis', 'plasma', 'inferno', 'magma'], index=0)
    else:
        color_map = 'gray'  # Default value, won't be used

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
    volume_list_entry_parts = [f"url: \"{base_file_url}\""]
    # Only apply colormap when not viewing segments directly
    if selected_source != 'segments':
        volume_list_entry_parts.append(f"colormap: \"{color_map}\"")
    else:
        # For segments, specify that this is RGB data
        volume_list_entry_parts.append("colormap: \"rgb\"")
    volume_list_entry = "{ " + ", ".join(volume_list_entry_parts) + " }"

    # --- Prepare Custom Colormap for Segments ---
    custom_colormap_js = ""
    if show_overlay or selected_source == 'segments':
        try:
            with open('conf/vista3d_label_colors.json', 'r') as f:
                label_colors_list = json.load(f)

            r_values = [0] * 256 # Assuming max ID is less than 256, adjust if needed
            g_values = [0] * 256
            b_values = [0] * 256
            a_values = [0] * 256 # Default to transparent
            labels = [""] * 256

            # Set background (ID 0) to transparent black
            r_values[0] = 0
            g_values[0] = 0
            b_values[0] = 0
            a_values[0] = 0
            labels[0] = "Background"

            max_id = 0
            for item in label_colors_list: # Iterate over the list
                idx = item['id']
                label_name = item['name'] # Get name
                color = item['color']
                if 0 <= idx < 256: # Ensure index is within bounds
                    r_values[idx] = color[0]
                    g_values[idx] = color[1]
                    b_values[idx] = color[2]
                    a_values[idx] = 255 # Make segments opaque
                    labels[idx] = label_name
                if idx > max_id:
                    max_id = idx
            
            # Trim arrays to max_id + 1
            r_values = r_values[:max_id + 1]
            g_values = g_values[:max_id + 1]
            b_values = b_values[:max_id + 1]
            a_values = a_values[:max_id + 1]
            labels = labels[:max_id + 1]

            custom_colormap_js = f"""
                const customSegmentationColormap = {{
                    R: [{ ",".join(map(str, r_values)) }],
                    G: [{ ",".join(map(str, g_values)) }],
                    B: [{ ",".join(map(str, b_values)) }],
                    A: [{ ",".join(map(str, a_values)) }],
                    labels: [{ ",".join(f'"{l}"' for l in labels) }]
                }}; 
                console.log('Custom colormap loaded:', customSegmentationColormap);
                """
        except Exception as e:
            st.error(f"Error loading label_dict.json: {e}")
            custom_colormap_js = "" # Ensure it's empty if error

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
            const nv = new niivue.Niivue ({{
                sliceType: {actual_slice_type},
                isColorbar: true
            }});
            nv.attachTo('niivue-canvas');

            const volumeList = [{volume_list_entry}];
            nv.loadVolumes(volumeList).then(() => {{
                {custom_colormap_js}
                console.log('Selected source:', '{selected_source}');
                console.log('Volume list:', volumeList);
                if (typeof customSegmentationColormap !== 'undefined' && '{selected_source}' !== 'segments') {{
                    // For overlays only, set as label colormap
                    console.log('Setting label colormap for overlay');
                    nv.setColormapLabel(customSegmentationColormap);
                }} else if ('{selected_source}' === 'segments') {{
                    console.log('Segments loaded - no colormap manipulation needed');
                }} else {{
                    console.log('Custom colormap not defined');
                }}
                if ('{segment_url}') {{
                    nv.loadDrawingFromUrl('{segment_url}');
                }}
                if ({actual_slice_type} === 3) {{ // 3 is Multiplanar
                    nv.setSliceType(nv.sliceType.MULTIPLANAR); // Ensure correct slice type
                    nv.opts.multiplanarShowRender = 'ALWAYS';
                    nv.drawScene();
                }}
            }}).catch(console.error);
        }}
    </script>
</body>
</html>"
"""

    components.html(html_string, height=1000, scrolling=False)
else:
    st.info("Select a data source, patient, and file to begin.")
