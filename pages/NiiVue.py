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
    url = f"{IMAGE_SERVER_URL.rstrip('/')}/output/{folder_path.strip('/')}/"
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

    # Only show slice type selector when not viewing segments directly
    if selected_source != 'segments':
        st.subheader("Slice Type")
        slice_type = st.selectbox("Slice Type", ["3D Render", "Multiplanar", "Single View"], index=1)
        orientation = "Axial"
        if slice_type == "Single View":
            orientation = st.selectbox("Orientation", ["Axial", "Coronal", "Sagittal"], index=0)

    # Only show colormap selector when not viewing segments directly
    if selected_source != 'segments':
        st.subheader("NIfTI Color Map")
        color_map = st.selectbox("Color Map", ['gray', 'viridis', 'plasma', 'inferno', 'magma'], index=0)

    # NIfTI Image Controls
    if selected_source != 'segments':
        st.subheader("NIfTI Image")
        nifti_opacity = st.slider("NIfTI Opacity", 0.0, 1.0, 1.0, key="nifti_opacity")
        nifti_gamma = st.slider("NIfTI Gamma", 0.1, 3.0, 1.0, step=0.1, key="nifti_gamma")
        
        # Overlay Controls
        show_overlay = False
        segment_opacity = 0.5
        segment_gamma = 1.0
        if selected_source == 'nifti' and selected_file:
            show_overlay = st.checkbox("Show Segmentation Overlay", value=False)
            if show_overlay:
                st.subheader("Segment Overlay")
                segment_opacity = st.slider("Segment Opacity", 0.0, 1.0, 0.5, key="segment_opacity")
                segment_gamma = st.slider("Segment Gamma", 0.1, 3.0, 1.0, step=0.1, key="segment_gamma")
    else:
        # For segments data source, only segment controls are relevant
        st.subheader("Segment Image")
        nifti_opacity = 1.0  # Not used
        nifti_gamma = 1.0    # Not used
        show_overlay = False
        segment_opacity = st.slider("Segment Opacity", 0.0, 1.0, 1.0, key="segment_opacity")
        segment_gamma = st.slider("Segment Gamma", 0.1, 3.0, 1.0, step=0.1, key="segment_gamma")

    # Set default values for segments data source
    if selected_source == 'segments':
        slice_type = "3D Render"
        orientation = "Axial" # This won't be used, but good to set a default
        
        # Show Segment Colors widget for segments data source
        with st.expander("Segment Colors", expanded=False):
            try:
                with open('conf/vista3d_label_colors.json', 'r') as f:
                    label_dict = json.load(f)
                
                for label_info in label_dict:
                    label_name = label_info["name"]
                    label_id = label_info["id"]
                    color_rgb = label_info["color"]
                    color_hex = f"#{color_rgb[0]:02x}{color_rgb[1]:02x}{color_rgb[2]:02x}"
                    st.markdown(f"<div style=\"display: flex; align-items: center; margin-bottom: 5px;\">"
                                f"<div style=\"width: 20px; height: 20px; background-color: {color_hex}; border: 1px solid #ccc; margin-right: 10px;\"></div>"
                                f"<span>{label_name} (ID: {label_id})</span>"
                                f"</div>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error loading segment colors: {e}")
    else:
        # Slice type and orientation are now handled above
        pass
        
        # Show Segment Colors widget at bottom for nifti data source (useful for overlays)
        with st.expander("Segment Colors", expanded=False):
            try:
                with open('conf/vista3d_label_colors.json', 'r') as f:
                    label_dict = json.load(f)
                
                for label_info in label_dict:
                    label_name = label_info["name"]
                    label_id = label_info["id"]
                    color_rgb = label_info["color"]
                    color_hex = f"#{color_rgb[0]:02x}{color_rgb[1]:02x}{color_rgb[2]:02x}"
                    st.markdown(f"<div style=\"display: flex; align-items: center; margin-bottom: 5px;\">" 
                                f"<div style=\"width: 20px; height: 20px; background-color: {color_hex}; border: 1px solid #ccc; margin-right: 10px;\"></div>" 
                                f"<span>{label_name} (ID: {label_id})</span>" 
                                f"</div>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error loading segment colors: {e}")

# --- Main Viewer Area ---
if selected_file:
    # --- Prepare URLs and Settings for Viewer ---
    base_file_url = f"{IMAGE_SERVER_URL}/output/{selected_source}/{selected_patient}/{selected_file}"
    segment_url = ''
    if show_overlay:
        # The segmentation files have the same filename as the original NIfTI files
        segment_filename = selected_file
        segment_url = f"{IMAGE_SERVER_URL}/output/segments/{selected_patient}/{segment_filename}"

    slice_type_map = {"Axial": 0, "Coronal": 1, "Sagittal": 2, "Multiplanar": 3, "3D Render": 4}
    actual_slice_type = slice_type_map.get(slice_type if slice_type != "Single View" else orientation, 3)

    # --- HTML and Javascript for NiiVue ---
    # Prepare main volume with proper configuration
    if selected_source != 'segments':
        # For NIfTI files, use basic configuration and apply colormap after loading
        main_volume_entry = f"{{ url: \"{base_file_url}\", opacity: {nifti_opacity} }}"
    else:
        # For segments, use custom Vista3D colormap
        main_volume_entry = f"{{ url: \"{base_file_url}\", colormap: \"custom_segmentation\" }}"
    
    # Prepare volume list including overlay if needed
    volume_list_entries = [main_volume_entry]
    if show_overlay and segment_url:
        overlay_entry = f"{{ url: \"{segment_url}\", opacity: {segment_opacity}, colormap: \"custom_segmentation\" }}"
        volume_list_entries.append(overlay_entry)
    
    volume_list_js = "[" + ", ".join(volume_list_entries) + "]"

    # --- Prepare Custom Colormap for Segments ---
    # ALWAYS load Vista3D colormap since segments should always use it
    custom_colormap_js = ""
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
            console.log('Vista3D colormap loaded from vista3d_label_colors.json:', customSegmentationColormap);
            """
    except Exception as e:
        st.error(f"Error loading vista3d_label_colors.json: {e}")
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
    <script src=\"https://cdnjs.cloudflare.com/ajax/libs/pako/2.1.0/pako.min.js\"></script>
    <script>
        if (typeof niivue === 'undefined') {{
            console.error('Niivue library not loaded!');
        }} else {{
            console.log('NiiVue library loaded successfully');
            
            console.log('🔧 Creating NiiVue instance...');
            const nv = new niivue.Niivue ({{
                sliceType: {actual_slice_type},
                isColorbar: false,
                loadingText: 'loading ...',
                dragAndDropEnabled: false,
                isResizeCanvas: true
            }});
            console.log('🔧 NiiVue instance created:', nv);
            
            console.log('🔧 Attaching to canvas...');
            nv.attachTo('niivue-canvas');
            console.log('🔧 Canvas attached, canvas element:', document.getElementById('niivue-canvas'));

            const volumeList = {volume_list_js};
            
            console.log('🚀 Starting to load volumes:', volumeList);
            console.log('📁 File URL:', volumeList[0].url);
            console.log('🎨 Volume colormap:', volumeList[0].colormap);
            
            // Define a function to handle successful volume loading
            function handleVolumeLoaded() {{
                console.log('📊 Volumes loaded:', nv.volumes.length);
                if (nv.volumes.length === 0) {{
                    console.error('❌ No volumes loaded');
                    return;
                }}
                
                const mainVol = nv.volumes[0];
                console.log('📊 Main volume details:', {{
                    id: mainVol.id,
                    dims: mainVol.dims,
                    colormap: mainVol.colormap,
                    opacity: mainVol.opacity,
                    dataRange: {{min: mainVol.global_min, max: mainVol.global_max}}
                }});
                
                // Apply colormap and settings
                {custom_colormap_js}
                
                // Register Vista3D colormap for segments
                if (typeof customSegmentationColormap !== 'undefined') {{
                    try {{
                        console.log('🎨 Registering Vista3D colormap');
                        nv.addColormap('custom_segmentation', customSegmentationColormap);
                        console.log('✅ Vista3D colormap registered successfully');
                    }} catch (colormapError) {{
                        console.error('❌ Failed to register Vista3D colormap:', colormapError);
                    }}
                }}
                
                // Configure main volume based on data source
                if ('{selected_source}' !== 'segments') {{
                    // NIfTI file configuration
                    console.log('🔧 Configuring NIfTI volume...');
                    
                    // Set proper colormap for NIfTI
                    console.log('🎨 Setting NIfTI colormap to {color_map}');
                    nv.setColormap(mainVol.id, '{color_map}');
                    
                    // Set gamma for better contrast
                    console.log('🎛️ Setting NIfTI gamma to {nifti_gamma}');
                    nv.setGamma({nifti_gamma});
                    
                    // Set opacity
                    mainVol.opacity = {nifti_opacity};
                    
                    // Configure intensity range for better detail
                    console.log('🔧 Configuring intensity range...');
                    nv.setClipPlane(0, 0, 0, 0, 0, 0);
                    nv.setClipPlane(1, 0, 0, 0, 0, 0);
                    
                }} else {{
                    // Segments file configuration
                    console.log('🔧 Configuring segments volume...');
                    
                    if (typeof customSegmentationColormap !== 'undefined') {{
                        nv.setColormap(mainVol.id, 'custom_segmentation');
                    }}
                    
                    nv.setGamma({segment_gamma});
                    mainVol.opacity = {segment_opacity};
                }}
                
                // Configure overlay volumes if present
                if (nv.volumes.length > 1) {{
                    console.log('🎨 Configuring overlay volumes...');
                    for (let i = 1; i < nv.volumes.length; i++) {{
                        const overlayVol = nv.volumes[i];
                        overlayVol.opacity = {segment_opacity};
                        
                        if (typeof customSegmentationColormap !== 'undefined') {{
                            nv.setColormap(overlayVol.id, 'custom_segmentation');
                        }}
                    }}
                }}
                
                // Set slice type
                if ({actual_slice_type} === 3) {{
                    console.log('🖼️ Setting slice type to Multiplanar');
                    nv.setSliceType(nv.sliceType.MULTIPLANAR);
                    nv.opts.multiplanarShowRender = 'ALWAYS';
                }}
                
                // Force initial render
                console.log('🔄 Rendering initial view...');
                nv.drawScene();
                
                // Additional render for stability
                setTimeout(() => {{
                    console.log('🔄 Final render pass...');
                    nv.drawScene();
                    console.log('✅ Rendering complete');
                }}, 100);
            }}
            
            // Load volumes with a simple approach
            console.log('📋 Loading volumes with simplified approach');
            
            nv.loadVolumes(volumeList)
                .then(() => {{
                    console.log('✅ SUCCESS! Volumes loaded');
                    console.log('📊 Volumes loaded:', nv.volumes.length);
                    if (nv.volumes.length > 0) {{
                        const vol = nv.volumes[0];
                        console.log('📊 Volume details:', {{
                            id: vol.id,
                            dims: vol.dims,
                            colormap: vol.colormap,
                            opacity: vol.opacity,
                            dataRange: {{min: vol.global_min, max: vol.global_max}},
                            isLoaded: vol.isLoaded
                        }});
                        
                        // Additional debugging for NIfTI files
                        if ('{selected_source}' !== 'segments') {{
                            console.log('🔍 NIfTI specific debugging:');
                            console.log('🔍 Volume data type:', vol.dataType);
                            console.log('🔍 Volume header:', vol.header);
                            console.log('🔍 Volume matrix:', vol.matRAS);
                        }}
                        
                        handleVolumeLoaded();
                    }} else {{
                        console.error('❌ No volumes loaded despite success');
                    }}
                }})
                .catch(error => {{
                    console.error('❌ Failed to load volumes:', error);
                    console.error('❌ Error details:', error.message);
                    console.error('❌ Error stack:', error.stack);
                    
                    // Try alternative loading approach
                    console.log('🔄 Trying alternative loading approach...');
                    nv.loadVolumes(volumeList, true) // Force reload
                        .then(() => {{
                            console.log('✅ Alternative loading successful');
                            handleVolumeLoaded();
                        }})
                        .catch(altError => {{
                            console.error('❌ Alternative loading also failed:', altError);
                        }});
                }});
        }}
    </script>
</body>
</html>"
"""

    components.html(html_string, height=1000, scrolling=False)
else:
    st.info("Select a data source, patient, and file to begin.")

