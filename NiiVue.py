import streamlit as st
import streamlit.components.v1 as components
import os
import re
import requests
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import json
from pathlib import Path

# --- Initial Setup ---
load_dotenv()
IMAGE_SERVER_URL = os.getenv('IMAGE_SERVER', 'http://localhost:8888')

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
    url = f"{IMAGE_SERVER_URL.rstrip('/')}/output/{folder_path.strip('/')}/"
    try:
        response = requests.get(url, timeout=10)
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
    
    st.header("Data Selection")
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
    # Initialize all viewer settings with sensible defaults
    slice_type = "Multiplanar"
    orientation = "Axial"
    color_map = "gray"
    nifti_opacity = 1.0
    nifti_gamma = 1.0
    show_overlay = False
    segment_opacity = 0.5
    segment_gamma = 1.0

    if selected_source != 'segments':
        st.subheader("Slice Type")
        slice_type = st.selectbox("Slice Type", ["3D Render", "Multiplanar", "Single View"], index=1)
        orientation = "Axial"
        if slice_type == "Single View":
            orientation = st.selectbox("Orientation", ["Axial", "Coronal", "Sagittal"], index=0)

        st.subheader("NIfTI Color Map")
        color_map = st.selectbox("Color Map", ['gray', 'viridis', 'plasma', 'inferno', 'magma'], index=0)

        with st.expander("NIfTI Image Settings", expanded=False):
            nifti_opacity = st.slider("NIfTI Opacity", 0.0, 1.0, 1.0, key="nifti_opacity")
            nifti_gamma = st.slider("NIfTI Gamma", 0.1, 3.0, 1.0, step=0.1, key="nifti_gamma")
        
        show_overlay = st.checkbox("Show Segmentation Overlay", value=False)
        if show_overlay:
            with st.expander("Overlay Settings", expanded=False):
                segment_opacity = st.slider("Segment Opacity", 0.0, 1.0, 0.5, key="segment_opacity")
                segment_gamma = st.slider("Segment Gamma", 0.1, 3.0, 1.0, step=0.1, key="segment_gamma")
    else:
        st.subheader("Segment Image")
        slice_type = "3D Render"
        orientation = "Axial"
        nifti_opacity = 1.0
        nifti_gamma = 1.0
        show_overlay = False
        segment_opacity = st.slider("Segment Opacity", 0.0, 1.0, 1.0, key="segment_opacity")
        segment_gamma = st.slider("Segment Gamma", 0.1, 3.0, 1.0, step=0.1, key="segment_gamma")

    with st.expander("Segment Colors", expanded=False):
        try:
            with open('conf/vista3d_label_colors.json', 'r') as f:
                label_dict = json.load(f)
            
            for label_info in label_dict:
                label_name = label_info["name"]
                label_id = label_info["id"]
                color_rgb = label_info["color"]
                color_hex = f"#{color_rgb[0]:02x}{color_rgb[1]:02x}{color_rgb[2]:02x}"
                st.markdown(f'''<div style="display: flex; align-items: center; margin-bottom: 5px;">
                            <div style="width: 20px; height: 20px; background-color: {color_hex}; border: 1px solid #ccc; margin-right: 10px;"></div>
                            <span>{label_name} (ID: {label_id})</span>
                            </div>''', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error loading segment colors: {e}")

# --- Main Viewer Area ---
if selected_file:
    # --- Prepare URLs and Settings for Viewer ---
    base_file_url = f"{IMAGE_SERVER_URL}/output/{selected_source}/{selected_patient}/{selected_file}"
    segment_url = ''
    if show_overlay:
        segment_filename = selected_file
        segment_url = f"{IMAGE_SERVER_URL}/output/segments/{selected_patient}/{segment_filename}"
    
    slice_type_map = {"Axial": 0, "Coronal": 1, "Sagittal": 2, "Multiplanar": 3, "3D Render": 4}
    actual_slice_type = slice_type_map.get(slice_type if slice_type != "Single View" else orientation, 3)

    # --- HTML and Javascript for NiiVue ---
    if selected_source != 'segments':
        main_volume_entry = f"{{ url: \"{base_file_url}\", opacity: {nifti_opacity} }}"
    else:
        main_volume_entry = f"{{ url: \"{base_file_url}\", colormap: \"custom_segmentation\" }}"
    
    volume_list_entries = [main_volume_entry]
    if show_overlay and segment_url:
        overlay_entry = f"{{ url: \"{segment_url}\", opacity: {segment_opacity}, colormap: \"custom_segmentation\" }}"
        volume_list_entries.append(overlay_entry)
    
    volume_list_js = "[" + ", ".join(volume_list_entries) + "]"

    custom_colormap_js = ""
    try:
        with open('conf/vista3d_label_colors.json', 'r') as f:
            label_colors_list = json.load(f)
            r_values, g_values, b_values, a_values, labels = [0]*256, [0]*256, [0]*256, [0]*256, [""]*256
            r_values[0], g_values[0], b_values[0], a_values[0], labels[0] = 0,0,0,0, "Background"
            max_id = 0
            for item in label_colors_list:
                idx, label_name, color = item['id'], item['name'], item['color']
                if 0 <= idx < 256:
                    r_values[idx], g_values[idx], b_values[idx], a_values[idx], labels[idx] = color[0], color[1], color[2], 255, label_name
                if idx > max_id:
                    max_id = idx
            r_values, g_values, b_values, a_values, labels = r_values[:max_id+1], g_values[:max_id+1], b_values[:max_id+1], a_values[:max_id+1], labels[:max_id+1]

            # Correctly format the labels for the JavaScript array
            js_labels = []
            for l in labels:
                escaped_l = l.replace('"', '\"')
                js_labels.append(f'"{escaped_l}"')
            labels_string = ",".join(js_labels)

        custom_colormap_js = f"""
            const customSegmentationColormap = {{
                R: [{ ",".join(map(str, r_values)) }],
                G: [{ ",".join(map(str, g_values)) }],
                B: [{ ",".join(map(str, b_values)) }],
                A: [{ ",".join(map(str, a_values)) }],
                labels: [{labels_string}]
            }}; 
            console.log('Vista3D colormap loaded from vista3d_label_colors.json:', customSegmentationColormap);
            """
    except Exception as e:
        st.error(f"Error loading vista3d_label_colors.json: {e}")

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
    <script src=\"https://cdnjs.cloudflare.com/ajax/libs/pako/2.1.0/pako.min.js\"></script>
    <script>
        if (typeof niivue === 'undefined') {{
            console.error('Niivue library not loaded!');
        }} else {{
            console.log('NiiVue library loaded successfully');
            
            const nv = new niivue.Niivue ({{
                isColorbar: false,
                loadingText: 'loading ...',
                dragAndDropEnabled: false,
                isResizeCanvas: true,
                crosshairWidth: 1,
                crosshairColor: [1, 0, 0, 1]
            }});
            nv.attachTo('niivue-canvas');

            const volumeList = {volume_list_js};
            
            nv.loadVolumes(volumeList).then(() => {{
                console.log('Volumes loaded');
                const mainVol = nv.volumes[0];
                {custom_colormap_js}
                if (typeof customSegmentationColormap !== 'undefined') {{
                    nv.addColormap('custom_segmentation', customSegmentationColormap);
                }}
                if ('{selected_source}' !== 'segments') {{
                    nv.setColormap(mainVol.id, '{color_map}');
                    nv.setGamma({nifti_gamma});
                    mainVol.opacity = {nifti_opacity};
                }} else {{
                    if (typeof customSegmentationColormap !== 'undefined') {{
                        nv.setColormap(mainVol.id, 'custom_segmentation');
                    }}
                    nv.setGamma({segment_gamma});
                    mainVol.opacity = {segment_opacity};
                }}
                if (nv.volumes.length > 1) {{
                    const overlayVol = nv.volumes[1];
                    overlayVol.opacity = {segment_opacity};
                    if (typeof customSegmentationColormap !== 'undefined') {{
                        nv.setColormap(overlayVol.id, 'custom_segmentation');
                    }}
                }}
                
                nv.setSliceType({actual_slice_type});

                if ({actual_slice_type} === 3) {{
                    nv.opts.multiplanarShowRender = true;
                    nv.opts.multiplanarForceRender = true;
                    nv.opts.showCrosshairs = true;
                    setTimeout(() => {{
                        nv.opts.show3Dcrosshair = true;
                        nv.drawScene();
                    }}, 500);
                }} else {{
                    nv.opts.showCrosshairs = false;
                }}
                nv.drawScene();
            }}).catch(console.error);
        }}
    </script>
</body>
</html>"""

    components.html(html_string, height=1000, scrolling=False)
else:
    st.info("Select a data source, patient, and file to begin.")