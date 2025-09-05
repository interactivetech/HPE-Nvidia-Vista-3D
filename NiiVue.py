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
    
    data_sources = ['nifti', 'segments']
    data_source_display = {'nifti': 'NIfTI', 'segments': 'Segments'}
    display_options = [data_source_display[source] for source in data_sources]
    selected_display = st.selectbox("Select Data Source", display_options)
    # Map back to the actual source name
    selected_source = data_sources[display_options.index(selected_display)]

    patient_folders = get_server_data(selected_source, 'folders', ('',))
    selected_patient = st.selectbox("Select Patient", patient_folders)

    selected_file = None
    if selected_patient:
        file_ext = ('.nii', '.nii.gz', '.dcm')
        filenames = get_server_data(f"{selected_source}/{selected_patient}", 'files', file_ext)
        
        # Create display names without .nii.gz extensions
        if filenames:
            display_names = [filename.replace('.nii.gz', '').replace('.nii', '').replace('.dcm', '') for filename in filenames]
            selected_display_name = st.selectbox("Select File", display_names)
            # Map back to the actual filename
            if selected_display_name:
                selected_index = display_names.index(selected_display_name)
                selected_file = filenames[selected_index]
        
        # Show voxels popdown for segments data source
        if selected_source == 'segments' and selected_file:
            voxels_folders = get_server_data(f"{selected_source}/{selected_patient}", 'folders', ('',))
            if 'voxels' in voxels_folders:
                voxels_files = get_server_data(f"{selected_source}/{selected_patient}/voxels", 'files', file_ext)
                if voxels_files:
                    # Filter voxels that are associated with the selected file
                    # Assuming voxels are named similarly or contain the base name of the selected file
                    selected_file_base = selected_file.replace('.nii.gz', '').replace('.nii', '').replace('.dcm', '')
                    associated_voxels = [vf for vf in voxels_files if selected_file_base in vf]
                    
                    if associated_voxels:
                        with st.expander("Voxels", expanded=False):
                            # Add Clear All button
                            if st.button("Clear All", key="clear_all_voxels"):
                                # Clear all voxel checkboxes by resetting their session state
                                for voxel_file in associated_voxels:
                                    clean_name = voxel_file.replace('2.5MM_ARTERIAL_3_', '').replace('.nii.gz', '').replace('.nii', '').replace('.dcm', '')
                                    if f"voxel_{clean_name}" in st.session_state:
                                        st.session_state[f"voxel_{clean_name}"] = False
                            
                            for voxel_file in associated_voxels:
                                # Extract the clean voxel name by removing specific prefix and extensions
                                clean_name = voxel_file.replace('2.5MM_ARTERIAL_3_', '').replace('.nii.gz', '').replace('.nii', '').replace('.dcm', '')
                                st.checkbox(clean_name, value=False, key=f"voxel_{clean_name}")

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
        # For segments data source, ALWAYS use 3D Render only - no other view options
        slice_type = "3D Render"
        orientation = "Axial"
        nifti_opacity = 1.0
        nifti_gamma = 1.0
        show_overlay = False
        
        # Display info that only 3D render is available for segments
        
        with st.expander("Image Settings", expanded=False):
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
    # Check if any voxels are selected when in segments mode
    selected_voxel_files = []
    if selected_source == 'segments':
        # Collect all selected voxels
        for voxel_file in get_server_data(f"{selected_source}/{selected_patient}/voxels", 'files', ('.nii', '.nii.gz', '.dcm')):
            clean_name = voxel_file.replace('2.5MM_ARTERIAL_3_', '').replace('.nii.gz', '').replace('.nii', '').replace('.dcm', '')
            if f"voxel_{clean_name}" in st.session_state and st.session_state[f"voxel_{clean_name}"]:
                selected_voxel_files.append(voxel_file)
    
    # --- Prepare URLs and Settings for Viewer ---
    if selected_voxel_files:
        # Display the first selected voxel as the main volume
        base_file_url = f"{IMAGE_SERVER_URL}/output/{selected_source}/{selected_patient}/voxels/{selected_voxel_files[0]}"
    else:
        base_file_url = f"{IMAGE_SERVER_URL}/output/{selected_source}/{selected_patient}/{selected_file}"
    segment_url = ''
    if show_overlay:
        segment_filename = selected_file
        segment_url = f"{IMAGE_SERVER_URL}/output/segments/{selected_patient}/{segment_filename}"
    
    slice_type_map = {"Axial": 0, "Coronal": 1, "Sagittal": 2, "Multiplanar": 3, "3D Render": 4}
    # For segments, always use pure 3D render (4), not multiplanar (3)
    if selected_source == 'segments':
        actual_slice_type = 4  # Pure 3D render
    else:
        actual_slice_type = slice_type_map.get(slice_type if slice_type != "Single View" else orientation, 3)

    # --- HTML and Javascript for NiiVue ---
    if selected_source != 'segments':
        main_volume_entry = f"{{ url: \"{base_file_url}\", opacity: {nifti_opacity} }}"
    else:
        main_volume_entry = f"{{ url: \"{base_file_url}\", colormap: \"custom_segmentation\" }}"
    
    volume_list_entries = [main_volume_entry]
    
    # Add additional selected voxels as overlays (if more than one is selected)
    if selected_voxel_files and len(selected_voxel_files) > 1:
        for additional_voxel in selected_voxel_files[1:]:  # Skip the first one as it's already the main volume
            additional_voxel_url = f"{IMAGE_SERVER_URL}/output/{selected_source}/{selected_patient}/voxels/{additional_voxel}"
            additional_entry = f"{{ url: \"{additional_voxel_url}\", opacity: {segment_opacity}, colormap: \"custom_segmentation\" }}"
            volume_list_entries.append(additional_entry)
    
    if show_overlay and segment_url and not selected_voxel_files:  # Only show overlay if no voxels are selected
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
        #niivue-canvas {{ width: 100%; height: 100%; display: block; pointer-events: auto; }}
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
                dragAndDropEnabled: true,
                isResizeCanvas: true,
                crosshairWidth: 1,
                crosshairColor: [1, 0, 0, 1],
                sliceType: {actual_slice_type},
                multiplanarShowRender: {str(actual_slice_type == 3).lower()},
                multiplanarForceRender: {str(actual_slice_type == 3).lower()},
                showCrosshairs: {str(actual_slice_type not in [3, 4]).lower()}
            }});
            nv.attachTo('niivue-canvas');

            const volumeList = {volume_list_js};
            
            nv.loadVolumes(volumeList).then(() => {{
                console.log('Volumes loaded');
                const mainVol = nv.volumes[0];
                {custom_colormap_js}
                if (typeof customSegmentationColormap !== 'undefined') {{
                    nv.addColormap('custom_segmentation', customSegmentationColormap);
                    console.log('Custom segmentation colormap added');
                }}
                if ('{selected_source}' !== 'segments') {{
                    nv.setColormap(mainVol.id, '{color_map}');
                    nv.setGamma({nifti_gamma});
                    mainVol.opacity = {nifti_opacity};
                }} else {{
                    if (typeof customSegmentationColormap !== 'undefined') {{
                        nv.setColormap(mainVol.id, 'custom_segmentation');
                        console.log('Applied custom_segmentation colormap to main volume:', mainVol.id);
                        console.log('Main volume min/max values:', mainVol.cal_min, mainVol.cal_max);
                        // Force update the colormap
                        mainVol.colormapLabel = 'custom_segmentation';
                    }}
                    // Gamma not applied in pure 3D label render to avoid interaction issues
                    mainVol.opacity = {segment_opacity};
                }}
                // Apply colormap to all additional volumes (overlays)
                if (nv.volumes.length > 1) {{
                    for (let i = 1; i < nv.volumes.length; i++) {{
                        const overlayVol = nv.volumes[i];
                        overlayVol.opacity = {segment_opacity};
                        if (typeof customSegmentationColormap !== 'undefined') {{
                            nv.setColormap(overlayVol.id, 'custom_segmentation');
                            console.log('Applied custom_segmentation colormap to overlay volume:', overlayVol.id);
                            console.log('Overlay volume', i, 'min/max values:', overlayVol.cal_min, overlayVol.cal_max);
                            // Force update the colormap
                            overlayVol.colormapLabel = 'custom_segmentation';
                        }}
                    }}
                }}
                
                // Ensure correct view mode after volumes load
                if ({actual_slice_type} === 3) {{
                    // Multiplanar view with 4 panes (includes 3D render tile)
                    nv.opts.multiplanarShowRender = true;
                    nv.opts.multiplanarForceRender = true;
                    nv.opts.show3Dcrosshair = true;
                    nv.setSliceType(3);
                    console.log('Set to multiplanar view (3)');
                }} else if ({actual_slice_type} === 4) {{
                    // Pure 3D render only for segments
                    nv.opts.multiplanarShowRender = false;
                    nv.opts.multiplanarForceRender = false;
                    nv.opts.showCrosshairs = false;
                    nv.opts.show3Dcrosshair = false;
                    nv.setSliceType(4);
                    console.log('Set to pure 3D render (4) for segments');
                }}
                
                // Force a final redraw to ensure colormap is applied
                setTimeout(() => {{
                    nv.drawScene();
                    console.log('Final scene redraw completed');
                    
                    // Final check for segments: ensure pure 3D render
                    if ('{selected_source}' === 'segments') {{
                        console.log('Final segments enforcement - ensuring 3D render only');
                        nv.drawScene();
                    }}
                }}, 100);
                
                nv.drawScene();
            }}).catch(console.error);
        }}
    </script>
</body>
</html>"""

    components.html(html_string, height=1000, scrolling=False)
else:
    st.info("Select a data source, patient, and file to begin.")