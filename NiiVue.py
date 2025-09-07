import streamlit as st
import streamlit.components.v1 as components
import os
import re
import requests
from typing import List, Dict, Optional, Tuple, Set
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import json
 
 

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

def fetch_available_voxel_labels(patient_id: str, filename: str) -> Tuple[Set[int], Dict[int, str]]:
    """Query image server for available voxel files for this patient/CT scan.
    Returns (available_label_ids, id_to_name_map). On error returns (empty set, {})."""
    if not patient_id or not filename:
        return set(), {}
    try:
        # Convert filename to folder name for voxels directory
        ct_scan_folder_name = filename.replace('.nii.gz', '').replace('.nii', '')
        
        # Check the voxels directory for this CT scan
        voxels_folder_url = f"{IMAGE_SERVER_URL.rstrip('/')}/output/{patient_id}/voxels/{ct_scan_folder_name}/"
        
        # Debug: Print the URL being checked
        print(f"DEBUG: Checking voxels URL: {voxels_folder_url}")
        
        resp = requests.get(voxels_folder_url, timeout=10)
        print(f"DEBUG: Response status: {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"DEBUG: Failed to access voxels directory. Status: {resp.status_code}")
            return set(), {}
        
        # Parse directory listing to find individual voxel files
        soup = BeautifulSoup(resp.text, 'html.parser')
        voxel_files = []
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and href.endswith('.nii.gz') and not href.startswith('..'):
                voxel_files.append(href)
        
        print(f"DEBUG: Found {len(voxel_files)} voxel files: {voxel_files}")
        
        # Load label dictionaries to map filenames back to label IDs
        try:
            with open('conf/vista3d_label_colors.json', 'r') as f:
                label_colors_list = json.load(f)
            
            # Create filename to ID mapping
            filename_to_id = {}
            id_to_name = {}
            expected_filenames = []
            for item in label_colors_list:
                label_id = item['id']
                label_name = item['name']
                # Convert name to expected filename format
                expected_filename = label_name.lower().replace(' ', '_').replace('-', '_') + '.nii.gz'
                filename_to_id[expected_filename] = label_id
                id_to_name[label_id] = label_name
                expected_filenames.append(expected_filename)
            
            print(f"DEBUG: Expected filenames (first 10): {expected_filenames[:10]}")
            print(f"DEBUG: Total expected filenames: {len(expected_filenames)}")
            
            # Find which label IDs are available based on existing voxel files
            available_ids = set()
            matched_files = []
            for voxel_file in voxel_files:
                # Extract just the filename from the full path
                filename_only = voxel_file.split('/')[-1]
                if filename_only in filename_to_id:
                    available_ids.add(filename_to_id[filename_only])
                    matched_files.append(filename_only)
            
            print(f"DEBUG: Matched {len(matched_files)} files to label IDs: {matched_files}")
            print(f"DEBUG: Available label IDs: {available_ids}")
            
            return available_ids, id_to_name
            
        except Exception:
            # Fallback: assume all files represent some label
            return set(), {}
            
    except Exception:
        return set(), {}


# --- Sidebar UI ---
with st.sidebar:
    # Patient folders are now directly in the output directory
    patient_folders = get_server_data('', 'folders', ('',))
    selected_patient = st.selectbox("Select Patient", patient_folders)

    selected_file = None
    if selected_patient:
        file_ext = ('.nii', '.nii.gz', '.dcm')
        filenames = get_server_data(f"{selected_patient}/nifti", 'files', file_ext)
        
        # Create display names without .nii.gz extensions
        if filenames:
            display_names = [filename.replace('.nii.gz', '').replace('.nii', '').replace('.dcm', '') for filename in filenames]
            selected_display_name = st.selectbox("Select File", display_names)
            # Map back to the actual filename
            if selected_display_name:
                selected_index = display_names.index(selected_display_name)
                selected_file = filenames[selected_index]
        
        

    # --- Viewer Settings ---
    # Initialize all viewer settings with sensible defaults
    slice_type = "Multiplanar"
    orientation = "Axial"
    color_map = "gray"
    nifti_opacity = 1.0
    nifti_gamma = 1.0
    show_nifti = True
    show_overlay = False
    segment_opacity = 1.0
    segment_gamma = 1.0

    st.markdown("Select Slice")
    slice_type = st.selectbox("", ["3D Render", "Multiplanar", "Single View"], index=0, label_visibility="collapsed")
    orientation = "Axial"
    if slice_type == "Single View":
        orientation = st.selectbox("Orientation", ["Axial", "Coronal", "Sagittal"], index=0)

    show_nifti = st.checkbox("Show NIfTI", value=True)

    with st.expander("NIfTI Image Settings", expanded=False):
        color_map = st.selectbox("Color Map", ['gray', 'viridis', 'plasma', 'inferno', 'magma'], index=0)
        nifti_opacity = st.slider("NIfTI Opacity", 0.0, 1.0, 1.0, key="nifti_opacity")
        nifti_gamma = st.slider("NIfTI Gamma", 0.1, 3.0, 1.0, step=0.1, key="nifti_gamma")
        
        # CT Window/Level settings
        st.markdown("**CT Window/Level Settings**")
        window_center = st.slider("Window Center (Level)", -2500, 2500, 0, key="window_center")
        window_width = st.slider("Window Width", 50, 5000, 1000, key="window_width")
        
        # Preset windowing options
        window_preset = st.selectbox("Window Preset", 
                                   ["Custom", "Standard (W:1000, L:0)", "Soft Tissue (W:400, L:40)", 
                                    "Bone (W:1500, L:300)", "Lung (W:1500, L:-600)", "Air/Background (W:500, L:-1000)"], 
                                   key="window_preset")
        
        if window_preset != "Custom":
            if "Standard" in window_preset:
                window_center, window_width = 0, 1000
            elif "Soft Tissue" in window_preset:
                window_center, window_width = 40, 400
            elif "Bone" in window_preset:
                window_center, window_width = 300, 1500
            elif "Lung" in window_preset:
                window_center, window_width = -600, 1500
            elif "Air/Background" in window_preset:
                window_center, window_width = -1000, 500
    
    show_overlay = st.checkbox("Show Voxels", value=False)
    
    # --- Voxel Selection ---
    with st.expander("Select Voxels", expanded=False):
        # Voxel selection mode
        voxel_mode = st.radio(
            "Choose voxel selection mode:",
            ["All", "Label Sets", "Individual Voxels"],
            index=0,
            help="Select how you want to choose which voxels to display"
        )
        
        # Determine current patient/file to query available voxel labels
        current_patient = selected_patient or ""
        current_filename = selected_file or ""
        available_label_ids, id_to_name_map = fetch_available_voxel_labels(current_patient, current_filename)
        # If none available, surface a clear notice with the voxels directory URL
        ct_scan_folder_name = current_filename.replace('.nii.gz', '').replace('.nii', '') if current_filename else ''
        voxels_directory_url = f"{IMAGE_SERVER_URL.rstrip('/')}/output/{current_patient}/voxels/{ct_scan_folder_name}/"
        if voxel_mode in ["Label Sets", "Individual Voxels"] and current_patient and current_filename and not available_label_ids:
            st.warning("No voxels available for this patient/file.")
            st.caption(f"Voxels directory: {voxels_directory_url}")
            st.caption("Individual voxel files should be located in this directory.")

        if voxel_mode == "All":
            st.info("Will display the complete base segmentation file.")
            st.session_state.voxel_mode = "all"
            st.session_state.selected_label_sets = []
            st.session_state.selected_individual_voxels = []
            
        elif voxel_mode == "Label Sets":
            try:
                with open('conf/vista3d_label_sets.json', 'r') as f:
                    label_sets = json.load(f)
                
                # Create a multiselect for label sets
                available_sets = list(label_sets.keys())
                selected_sets = st.multiselect(
                    "Choose anatomical sets to overlay:",
                    available_sets,
                    default=[],
                    help="Select one or more anatomical sets to display as overlays"
                )
                
                # Display selected sets with descriptions
                if selected_sets:
                    st.markdown("**Selected Sets:**")
                    total_labels = 0
                    for set_name in selected_sets:
                        set_info = label_sets[set_name]
                        # Filter set labels by availability
                        set_label_names = set_info['labels']
                        # Map names -> ids using conf/vista3d_label_dict.json
                        with open('conf/vista3d_label_dict.json', 'r') as f2:
                            name_to_id_dict = json.load(f2)
                        available_names = []
                        for ln in set_label_names:
                            lid = name_to_id_dict.get(ln)
                            if isinstance(lid, int) and lid in available_label_ids:
                                available_names.append(ln)
                        label_count = len(available_names)
                        total_labels += label_count
                        st.markdown(f"• **{set_name.replace('_', ' ').title()}**: {set_info['description']}")
                        st.markdown(f"  *{label_count} available labels*")
                        
                        # Show which specific labels are available for this set
                        if available_names:
                            st.markdown(f"  Available: {', '.join(available_names[:5])}")
                            if len(available_names) > 5:
                                st.markdown(f"  *... and {len(available_names) - 5} more*")
                        else:
                            st.markdown(f"  *No labels available for this set*")
                    
                    st.markdown(f"**Total available labels: {total_labels}**")
                    st.info("Each selected anatomical structure will be displayed as a separate overlay from the voxels directory.")
                else:
                    st.info("No label sets selected. Select sets to display individual voxels.")
                
                st.session_state.voxel_mode = "label_sets"
                st.session_state.selected_label_sets = selected_sets
                st.session_state.selected_individual_voxels = []
                
            except Exception as e:
                st.error(f"Error loading label sets: {e}")
                st.session_state.voxel_mode = "all"
                st.session_state.selected_label_sets = []
                st.session_state.selected_individual_voxels = []
                
        elif voxel_mode == "Individual Voxels":
            try:
                with open('conf/vista3d_label_dict.json', 'r') as f:
                    label_dict = json.load(f)
                
                # Create a multiselect for individual voxels (only available)
                available_voxels = [name for name, lid in label_dict.items() if isinstance(lid, int) and lid in available_label_ids]
                selected_voxels = st.multiselect(
                    "Choose individual voxels to overlay:",
                    available_voxels,
                    default=[],
                    help="Select specific anatomical structures to display as overlays"
                )
                
                # Display selected voxels count only
                if selected_voxels:
                    st.info(f"Will display {len(selected_voxels)} individual voxels from the voxels directory.")
                else:
                    st.info("No individual voxels selected. Select specific structures to display.")
                
                st.session_state.voxel_mode = "individual_voxels"
                st.session_state.selected_label_sets = []
                st.session_state.selected_individual_voxels = selected_voxels
                
            except Exception as e:
                st.error(f"Error loading individual voxels: {e}")
                st.session_state.voxel_mode = "all"
                st.session_state.selected_label_sets = []
                st.session_state.selected_individual_voxels = []
    
    with st.expander("Voxel Image Settings", expanded=False):
        segment_opacity = st.slider("Voxel Opacity", 0.0, 1.0, 0.5, key="segment_opacity")
        segment_gamma = st.slider("Voxel Gamma", 0.1, 3.0, 1.0, step=0.1, key="segment_gamma")
    
    # Display current voxel selection status
    if not show_overlay:
        st.info("Enable 'Show Voxels' to display overlays.")

    with st.expander("Voxel Legend", expanded=False):
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
    base_file_url = f"{IMAGE_SERVER_URL}/output/{selected_patient}/nifti/{selected_file}"
    segment_url = ''
    selected_label_ids = []
    
    
    # Store individual label overlays
    individual_label_overlays = []
    
    if show_overlay:
        segment_filename = selected_file
        # Prefer server-resolved voxels filename if available
        resolved_voxels_filename = st.session_state.get('resolved_voxels_filename', segment_filename)
        # Query server for available voxel label IDs for this patient/file
        available_label_ids_for_file, _ = fetch_available_voxel_labels(selected_patient, segment_filename)
        
        # Get voxel mode from session state
        voxel_mode = getattr(st.session_state, 'voxel_mode', 'all')
        
        if voxel_mode == "all":
            # Show base segmentation file with dynamic colormap
            individual_label_overlays = [{
                'label_id': 'all',
                'label_name': 'All Segmentation',
                'url': f"{IMAGE_SERVER_URL}/output/{selected_patient}/segments/{segment_filename}",
                'is_all_segmentation': True  # Flag to indicate this needs special handling
            }]
            
        elif voxel_mode == "label_sets":
            # Show individual voxels from selected label sets
            if hasattr(st.session_state, 'selected_label_sets') and st.session_state.selected_label_sets:
                try:
                    with open('conf/vista3d_label_sets.json', 'r') as f:
                        label_sets = json.load(f)
                    with open('conf/vista3d_label_dict.json', 'r') as f:
                        label_dict = json.load(f)
                    with open('conf/vista3d_label_colors.json', 'r') as f:
                        label_colors_list = json.load(f)
                    
                    # Collect individual labels from selected sets
                    # Convert CT scan name to folder name (remove .nii.gz extension)
                    ct_scan_folder_name = segment_filename.replace('.nii.gz', '').replace('.nii', '')
                    
                    for set_name in st.session_state.selected_label_sets:
                        if set_name in label_sets:
                            for label_name in label_sets[set_name]['labels']:
                                if label_name in label_dict:
                                    label_id = label_dict[label_name]
                                    # Only include overlays for labels that exist in voxels file
                                    if label_id in available_label_ids_for_file:
                                        selected_label_ids.append(label_id)
                                        # Convert label name to filename format
                                        voxel_filename = label_name.lower().replace(' ', '_').replace('-', '_') + '.nii.gz'
                                        # Get color for this label
                                        label_color = None
                                        for item in label_colors_list:
                                            if item['id'] == label_id:
                                                label_color = item['color']
                                                break
                                        
                                        individual_label_overlays.append({
                                            'label_id': label_id,
                                            'label_name': label_name,
                                            'url': f"{IMAGE_SERVER_URL}/output/{selected_patient}/voxels/{ct_scan_folder_name}/{voxel_filename}",
                                            'color': label_color
                                        })
                    
                    # Remove duplicates and sort
                    selected_label_ids = sorted(list(set(selected_label_ids)))
                    
                except Exception as e:
                    st.error(f"Error processing selected label sets: {e}")
                    selected_label_ids = []
                    individual_label_overlays = []
            else:
                # No label sets selected, show base segmentation
                individual_label_overlays = [{
                    'label_id': 'all',
                    'label_name': 'All Segmentation',
                    'url': f"{IMAGE_SERVER_URL}/output/{selected_patient}/segments/{segment_filename}"
                }]
                
        elif voxel_mode == "individual_voxels":
            # Show individual voxels from selected individual voxels
            if hasattr(st.session_state, 'selected_individual_voxels') and st.session_state.selected_individual_voxels:
                try:
                    with open('conf/vista3d_label_dict.json', 'r') as f:
                        label_dict = json.load(f)
                    with open('conf/vista3d_label_colors.json', 'r') as f:
                        label_colors_list = json.load(f)
                    
                    # Create individual overlays for selected voxels
                    # Convert CT scan name to folder name (remove .nii.gz extension)
                    ct_scan_folder_name = segment_filename.replace('.nii.gz', '').replace('.nii', '')
                    
                    for voxel_name in st.session_state.selected_individual_voxels:
                        if voxel_name in label_dict:
                            label_id = label_dict[voxel_name]
                            if label_id in available_label_ids_for_file:
                                selected_label_ids.append(label_id)
                                # Convert voxel name to filename format
                                voxel_filename = voxel_name.lower().replace(' ', '_').replace('-', '_') + '.nii.gz'
                                
                                # Get color for this label
                                label_color = None
                                for item in label_colors_list:
                                    if item['id'] == label_id:
                                        label_color = item['color']
                                        break
                                
                                individual_label_overlays.append({
                                    'label_id': label_id,
                                    'label_name': voxel_name,
                                    'url': f"{IMAGE_SERVER_URL}/output/{selected_patient}/voxels/{ct_scan_folder_name}/{voxel_filename}",
                                    'color': label_color
                                })
                    
                    # Remove duplicates and sort
                    selected_label_ids = sorted(list(set(selected_label_ids)))
                    
                except Exception as e:
                    st.error(f"Error processing selected individual voxels: {e}")
                    selected_label_ids = []
                    individual_label_overlays = []
            else:
                # No individual voxels selected, show base segmentation
                individual_label_overlays = [{
                    'label_id': 'all',
                    'label_name': 'All Segmentation',
                    'url': f"{IMAGE_SERVER_URL}/output/{selected_patient}/segments/{segment_filename}"
                }]
    else:
        # Show Voxels is disabled, no overlays
        individual_label_overlays = []
    
    slice_type_map = {"Axial": 0, "Coronal": 1, "Sagittal": 2, "Multiplanar": 3, "3D Render": 4}
    actual_slice_type = slice_type_map.get(slice_type if slice_type != "Single View" else orientation, 3)

    # --- HTML and Javascript for NiiVue ---
    volume_list_entries = []
    if show_nifti:
        # Niivue expects objects with a `url` property
        main_volume_entry = {"url": base_file_url}
        volume_list_entries.append(main_volume_entry)
    
    # Add individual label overlays
    if show_overlay and individual_label_overlays:
        for overlay in individual_label_overlays:
            # Validate overlay data before creating entry
            if overlay.get('url') and overlay.get('label_name'):
                # Only provide url; set opacity/colormap after load
                overlay_entry = {"url": overlay['url']}
                volume_list_entries.append(overlay_entry)
            else:
                st.warning(f"Skipping invalid overlay: {overlay}")
    
    if not volume_list_entries:
        st.info("Nothing to display. Enable 'Show NIfTI' or 'Show Voxels' with selected label sets.")
    
    # Convert to proper JavaScript JSON (array of strings)
    volume_list_js = json.dumps(volume_list_entries)
    main_is_nifti = show_nifti
    overlay_start_index = 1 if main_is_nifti else 0
    color_map_js = json.dumps(color_map)
    
    # Prepare individual overlay color information for JavaScript
    overlay_colors_js = json.dumps(individual_label_overlays)
    
    # For "all segmentation" mode, we use the same colormap as individual voxels
    # No need to analyze the segmentation file since we use the standard colormap
    

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
                dragAndDropEnabled: false,
                isResizeCanvas: true,
                crosshairWidth: 1,
                crosshairColor: [1, 0, 0, 1]
            }});
            nv.attachTo('niivue-canvas');

            const volumeList = {volume_list_js};
            const overlayColors = {overlay_colors_js};
            console.log('Prepared volumeList:', volumeList);
            console.log('Overlay colors:', overlayColors);
            if (!Array.isArray(volumeList) || volumeList.some(v => !v || typeof v.url !== 'string')) {{
                console.error('Invalid volumeList shape. Expected [{{ url: string }}, ...]. Got:', volumeList);
            }}
            
            {custom_colormap_js}
            if (typeof customSegmentationColormap !== 'undefined') {{
                nv.addColormap('custom_segmentation', customSegmentationColormap);
                console.log('Custom segmentation colormap added');
            }}
            
            // For "all segmentation" mode, use the same colormap as individual voxels
            // This ensures consistent colors between individual voxels and all segmentation mode
            
            nv.loadVolumes(volumeList).then(() => {{
                console.log('Volumes loaded successfully');
                const hasVolumes = nv.volumes.length > 0;
                const mainVol = hasVolumes ? nv.volumes[0] : null;

                if ({str(main_is_nifti).lower()} && mainVol) {{
                    nv.setColormap(mainVol.id, {color_map_js});
                    nv.setGamma({nifti_gamma});
                    mainVol.opacity = {nifti_opacity};
                    
                    // Apply CT windowing settings
                    const windowCenter = {window_center};
                    const windowWidth = {window_width};
                    const windowMin = windowCenter - windowWidth / 2;
                    const windowMax = windowCenter + windowWidth / 2;
                    
                    // Set the volume's display range for proper CT windowing
                    mainVol.cal_min = windowMin;
                    mainVol.cal_max = windowMax;
                    
                    console.log('Applied CT windowing - Center:', windowCenter, 'Width:', windowWidth, 'Range:', windowMin, 'to', windowMax);
                }}

                // Apply individual colors to overlays
                if (nv.volumes.length > {overlay_start_index}) {{
                    for (let i = {overlay_start_index}; i < nv.volumes.length; i++) {{
                        const overlayVol = nv.volumes[i];
                        // Set opacity to 50% for Single View mode, otherwise use slider value
                        const isSingleView = {actual_slice_type} !== 3 && {actual_slice_type} !== 4;
                        overlayVol.opacity = isSingleView ? 0.5 : {segment_opacity};
                        
                        // Get the corresponding overlay color info
                        const overlayIndex = i - {overlay_start_index};
                        
                        // Check if this is the "all segmentation" mode
                        if (overlayIndex < overlayColors.length && overlayColors[overlayIndex].is_all_segmentation) {{
                            // Use the same colormap as individual voxels for consistency
                            if (typeof customSegmentationColormap !== 'undefined') {{
                                nv.setColormap(overlayVol.id, 'custom_segmentation');
                                console.log('Applied custom_segmentation colormap to all segmentation overlay');
                            }}
                        }} else if (overlayIndex < overlayColors.length && overlayColors[overlayIndex].color) {{
                            const color = overlayColors[overlayIndex].color;
                            const labelName = overlayColors[overlayIndex].label_name;
                            
                            // Create a custom colormap for this specific overlay
                            const customColormap = {{
                                R: [0, color[0]],
                                G: [0, color[1]], 
                                B: [0, color[2]],
                                A: [0, 255],
                                labels: ['Background', labelName]
                            }};
                            
                            const colormapName = `custom_${{overlayIndex}}`;
                            nv.addColormap(colormapName, customColormap);
                            nv.setColormap(overlayVol.id, colormapName);
                            console.log(`Applied custom color to overlay ${{overlayIndex}}: ${{labelName}}`, color);
                        }} else {{
                            // Fallback to generic segmentation colormap
                            if (typeof customSegmentationColormap !== 'undefined') {{
                                nv.setColormap(overlayVol.id, 'custom_segmentation');
                                console.log('Applied custom_segmentation colormap to overlay volume:', overlayVol.id, 'Name:', overlayVol.name || 'Unnamed');
                            }}
                        }}
                    }}
                }}

                // Honor requested slice type
                nv.setSliceType({actual_slice_type});
                if ({actual_slice_type} === 3) {{
                    // Multiplanar view with 4 panes
                    nv.opts.multiplanarShowRender = true;
                    nv.opts.multiplanarForceRender = true;
                    nv.opts.showCrosshairs = true;
                    setTimeout(() => {{
                        nv.opts.show3Dcrosshair = true;
                        nv.drawScene();
                    }}, 500);
                }} else if ({actual_slice_type} === 4) {{
                    // 3D Render mode - disable any container/boundary settings
                    nv.opts.multiplanarShowRender = false;
                    nv.opts.multiplanarForceRender = false;
                    nv.opts.showCrosshairs = false;
                    nv.opts.show3Dcrosshair = false;
                    nv.opts.isOrientCube = false;
                    nv.opts.isRuler = false;
                    nv.opts.isRadiologicalConvention = false;
                    nv.opts.isOrientCube = false;
                    nv.opts.isRuler = false;
                    // Disable any 3D container or boundary rendering
                    nv.opts.isOrientCube = false;
                    nv.opts.isRuler = false;
                }} else {{
                    // Ensure multiplanar flags are disabled when not in multiplanar mode
                    nv.opts.multiplanarShowRender = false;
                    nv.opts.multiplanarForceRender = false;
                    nv.opts.showCrosshairs = false;
                    nv.opts.show3Dcrosshair = false;
                }}
                nv.drawScene();

                // Final redraw to ensure colormap is applied
                setTimeout(() => {{
                    nv.drawScene();
                }}, 100);

            }}).catch((error) => {{
                console.error('Error loading volumes:', error);
                console.error('Volume list that failed:', volumeList);
                console.error('Error details:', {{
                    message: error.message,
                    stack: error.stack,
                    name: error.name
                }});
                
                // Try to provide more helpful error information
                if (error.message && error.message.includes('fetch')) {{
                    console.error('Network error - check if image server is running and file exists');
                }} else if (error.message && error.message.includes('parse')) {{
                    console.error('File parsing error - check if file is valid NIfTI format');
                }} else {{
                    console.error('Unknown error during volume loading');
                }}
            }});
        }}
    </script>
</body>
</html>"""

    components.html(html_string, height=1000, scrolling=False)
else:
    st.info("Select a patient and file to begin.")