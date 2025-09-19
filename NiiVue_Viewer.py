import streamlit as st
import streamlit.components.v1 as components
import os
import json
from typing import Optional
from dotenv import load_dotenv

# Import our new modules
from utils.config_manager import ConfigManager
from utils.data_manager import DataManager
from utils.voxel_manager import VoxelManager
from utils.viewer_config import ViewerConfig
from utils.template_renderer import TemplateRenderer
from utils.constants import (
    NIFTI_EXTENSIONS, DICOM_EXTENSIONS, IMAGE_EXTENSIONS,
    VOXEL_MODES, MESSAGES, VIEWER_HEIGHT, detect_modality_from_data
)
 
 

# --- Initial Setup ---
load_dotenv()
IMAGE_SERVER_URL = os.getenv('IMAGE_SERVER', 'http://localhost:8888')
EXTERNAL_IMAGE_SERVER_URL = os.getenv('EXTERNAL_IMAGE_SERVER', 'http://localhost:8888')

# Get output folder from environment - must be absolute path
OUTPUT_FOLDER = os.getenv('OUTPUT_FOLDER')
if not OUTPUT_FOLDER:
    raise ValueError("OUTPUT_FOLDER must be set in .env file with absolute path")
if not os.path.isabs(OUTPUT_FOLDER):
    raise ValueError("OUTPUT_FOLDER must be set in .env file with absolute path")

# Initialize our managers
config_manager = ConfigManager()
data_manager = DataManager(IMAGE_SERVER_URL)
external_data_manager = DataManager(EXTERNAL_IMAGE_SERVER_URL)
voxel_manager = VoxelManager(config_manager, external_data_manager)
viewer_config = ViewerConfig()
template_renderer = TemplateRenderer()


# --- Sidebar UI ---
def render_sidebar():
    """Render the sidebar with patient/file selection and viewer settings."""
    with st.sidebar:
        # Patient folders are now directly in the output directory
        patient_folders = data_manager.get_server_data('', 'folders', ('',))
        
        # Debug information - only show if no patient folders found
        if not patient_folders:
            st.warning("No patient folders found. Check if:")
            st.write("1. Image server is running")
            st.write("2. OUTPUT_FOLDER contains patient directories")
            st.write("3. Image server can access the output folder")
            
            # Show debug info only when there's an issue
            with st.expander("Debug Info", expanded=False):
                st.write(f"**Image Server URL:** {IMAGE_SERVER_URL}")
                st.write(f"**External Image Server URL:** {EXTERNAL_IMAGE_SERVER_URL}")
                st.write(f"**Output Folder:** {OUTPUT_FOLDER}")
                st.write(f"**DataManager URL:** {data_manager.image_server_url}")
                st.write(f"**Patient Folders Found:** {len(patient_folders)}")
                
                # Test the actual URL being called
                test_url = f"{data_manager.image_server_url}/output/"
                st.write(f"**Test URL:** {test_url}")
                
                # Try to test the connection directly
                import requests
                try:
                    response = requests.get(test_url, timeout=5)
                    st.write(f"**HTTP Response:** {response.status_code}")
                    if response.status_code == 200:
                        st.write("✅ Server is responding")
                        st.write("**Response preview:**")
                        st.code(response.text[:500] + "..." if len(response.text) > 500 else response.text)
                    else:
                        st.write(f"❌ Server returned HTTP {response.status_code}")
                except Exception as e:
                    st.write(f"❌ Connection error: {e}")
        
        # Add uploaded files as special "patients"
        uploaded_patients = []
        if 'uploaded_files' in st.session_state and st.session_state.uploaded_files:
            for key, file_info in st.session_state.uploaded_files.items():
                uploaded_patients.append(f"📁 {file_info['name']}")
        
        # Combine regular patients and uploaded files
        all_patients = patient_folders + uploaded_patients
        # Add None option at the beginning
        patient_options = [None] + all_patients
        selected_patient = st.selectbox("Select Patient", patient_options, index=0)

        selected_file = None
        is_uploaded_file = False
        
        if selected_patient:
            # Check if this is an uploaded file
            if selected_patient.startswith("📁 "):
                # This is an uploaded file
                uploaded_filename = selected_patient[2:]  # Remove the 📁 prefix
                selected_file = uploaded_filename
                is_uploaded_file = True
                st.info(f"Viewing uploaded file: {uploaded_filename}")
            else:
                # Regular patient folder
                filenames = data_manager.get_server_data(f"{selected_patient}/nifti", 'files', IMAGE_EXTENSIONS)

                # Create display names without .nii.gz extensions
                if filenames:
                    display_names = [
                        filename.replace('.nii.gz', '').replace('.nii', '').replace('.dcm', '')
                        for filename in filenames
                    ]
                    # Add None option at the beginning
                    scan_options = [None] + display_names
                    selected_display_name = st.selectbox("Select Scan", scan_options, index=0)
                    # Map back to the actual filename
                    if selected_display_name:
                        selected_index = display_names.index(selected_display_name)
                        selected_file = filenames[selected_index]

        # Update viewer config with selections
        viewer_config.selected_patient = selected_patient
        viewer_config.selected_file = selected_file

        # Extract data characteristics for modality-specific settings
        min_val, max_val, mean_val = None, None, None
        if selected_patient and selected_file:
            quality_file_path = os.path.join(OUTPUT_FOLDER, selected_patient, "nifti", f"{selected_file}.quality.json")
            if os.path.exists(quality_file_path):
                try:
                    with open(quality_file_path, 'r') as f:
                        quality_data = json.load(f)
                    
                    data_quality = quality_data.get('data_quality', {})
                    min_val = data_quality.get('min_value')
                    max_val = data_quality.get('max_value')
                    mean_val = data_quality.get('mean_value')
                    
                    # Apply optimal window settings immediately when new dataset is selected
                    viewer_config.apply_optimal_window_settings(min_val, max_val, mean_val)
                    
                    # Apply appropriate colormap for the detected modality
                    modality = detect_modality_from_data(min_val, max_val, mean_val)
                    if modality == 'MRI':
                        # Use bone colormap for MRI (works great without cube artifacts)
                        viewer_config._settings['color_map'] = 'bone'
                    
                except Exception:
                    # Fallback to None if parsing fails
                    pass

        # Check if voxels are available for this patient
        has_voxels = bool(selected_patient and voxel_manager.has_voxels_for_patient(selected_patient))
        
        # Render viewer settings with data characteristics
        viewer_config.render_sidebar_settings(min_val, max_val, mean_val, has_voxels)

        # Only show voxel settings if there are voxels available for this patient
        if has_voxels:
            # Voxel selection (after show_overlay is set)
            if viewer_config.settings.get('show_overlay', False):
                render_voxel_selection(selected_patient, selected_file)
                # Voxel image settings (after voxel selection)
                viewer_config.render_voxel_image_settings()

            # Voxel legend
            viewer_config.render_voxel_legend()

        # File upload section at the bottom of sidebar
        render_file_upload()

    return selected_patient, selected_file


def render_voxel_selection(selected_patient: str, selected_file: str):
    """Render the voxel selection interface."""
    with st.expander("Select Voxels", expanded=False):
        # Voxel selection mode
        voxel_mode = st.radio(
            "Choose voxel selection mode:",
            VOXEL_MODES,
            index=0,
            help="Select how you want to choose which voxels to display"
        )

        # Get available voxel information
        available_ids, id_to_name_map, available_voxel_names = voxel_manager.get_available_voxels(
            selected_patient, selected_file, voxel_mode
        )

        # Handle voxel mode selection
        if voxel_mode == "All":
            st.info("Will display the complete base segmentation file.")
            viewer_config.voxel_mode = "all"
            viewer_config.selected_individual_voxels = []

        elif voxel_mode == "Individual Voxels":
            if not available_ids:
                # Show warning if no voxels available
                voxels_url = data_manager.get_voxel_directory_url(selected_patient, selected_file)
                st.warning("No voxels available for this patient/file.")
                st.caption(f"Voxels directory: {voxels_url}")
                st.caption("Individual voxel files should be located in this directory.")
            else:
                # Show voxel selection interface
                selected_voxels = st.multiselect(
                    "Choose individual voxels to overlay:",
                    available_voxel_names,
                    default=[],
                    help="Select specific anatomical structures to display"
                )

                # Display selection status
                if selected_voxels:
                    st.info(f"Will display {len(selected_voxels)} individual voxels from the voxels directory.")
                else:
                    st.info("No individual voxels selected. Select specific structures to display.")

                viewer_config.voxel_mode = "individual_voxels"
                viewer_config.selected_individual_voxels = selected_voxels

        # Update session state
        viewer_config.to_session_state()

    # Display current voxel selection status
    status_message = viewer_config.get_status_message()
    if status_message:
        st.info(status_message)


def render_file_upload():
    """Render the file upload interface at the bottom of the sidebar."""
    st.divider()
    st.subheader("📁 Upload NIfTI File")
    
    # File upload widget
    uploaded_file = st.file_uploader(
        "Choose a .nii.gz file",
        type=['nii.gz', 'nii'],
        help="Upload a NIfTI file to view it in the 3D viewer"
    )
    
    if uploaded_file is not None:
        # Initialize session state for uploaded files if not exists
        if 'uploaded_files' not in st.session_state:
            st.session_state.uploaded_files = {}
        
        # Create a unique key for this upload
        file_key = f"uploaded_{uploaded_file.name}_{uploaded_file.size}"
        
        # Check if this is a new upload
        if file_key not in st.session_state.uploaded_files:
            # Save uploaded file to a location accessible by the image server
            import tempfile
            import shutil
            
            # Create uploads directory in the output folder (accessible by image server)
            uploads_dir = os.path.join(OUTPUT_FOLDER, 'uploads')
            os.makedirs(uploads_dir, exist_ok=True)
            
            # Save file to uploads directory within output folder
            upload_file_path = os.path.join(uploads_dir, uploaded_file.name)
            with open(upload_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Store file info in session state
            st.session_state.uploaded_files[file_key] = {
                'name': uploaded_file.name,
                'path': upload_file_path,
                'size': uploaded_file.size
            }
            
            st.success(f"✅ Uploaded: {uploaded_file.name}")
            st.info("The uploaded file is now available in the patient selection dropdown above.")
        
        # Display uploaded files
        if st.session_state.uploaded_files:
            st.write("**Uploaded Files:**")
            for key, file_info in st.session_state.uploaded_files.items():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"• {file_info['name']}")
                with col2:
                    if st.button("🗑️", key=f"delete_{key}", help="Remove this file"):
                        # Clean up file
                        try:
                            os.remove(file_info['path'])
                        except FileNotFoundError:
                            pass
                        # Remove from session state
                        del st.session_state.uploaded_files[key]
                        st.rerun()
    
    # Cleanup old uploaded files on app start (optional - keep files for persistence)
    # Note: We keep uploaded files in the uploads directory for persistence
    # Users can manually delete them using the delete button


# --- Main Application ---
def render_viewer(selected_patient: str, selected_file: str):
    """Render the main NiiVue viewer."""
    if not selected_file:
        st.info(MESSAGES['select_patient_file'])
        return

    # Prepare volume URLs and overlays
    # Check if this is an uploaded file
    if selected_patient and selected_patient.startswith("📁 "):
        # For uploaded files, use the temporary file path
        uploaded_filename = selected_patient[2:]  # Remove the 📁 prefix
        # Find the file in session state
        uploaded_file_path = None
        if 'uploaded_files' in st.session_state:
            for key, file_info in st.session_state.uploaded_files.items():
                if file_info['name'] == uploaded_filename:
                    uploaded_file_path = file_info['path']
                    break
        
        if uploaded_file_path and os.path.exists(uploaded_file_path):
            # For uploaded files, serve them through the image server
            # The file is in the output/uploads directory, so we can access it via HTTP
            # Use the correct URL path with /output/ prefix
            base_file_url = f"{EXTERNAL_IMAGE_SERVER_URL}/output/uploads/{uploaded_filename}"
        else:
            st.error("Uploaded file not found. Please re-upload the file.")
            return
    else:
        # Regular patient file
        base_file_url = f"{EXTERNAL_IMAGE_SERVER_URL}/output/{selected_patient}/nifti/{selected_file}"

    # Create overlays based on voxel mode (only for regular patient files, not uploaded files)
    overlays = []
    if not (selected_patient and selected_patient.startswith("📁 ")):
        overlays = voxel_manager.create_overlays(
            selected_patient,
            selected_file,
            viewer_config.voxel_mode,
            viewer_config.selected_individual_voxels
        )

    # Build volume list for NiiVue
    volume_list_entries = []
    if viewer_config.settings.get('show_nifti', True):
        volume_list_entries.append({"url": base_file_url})

    # Add overlay volumes
    if viewer_config.settings.get('show_overlay', False) and overlays:
        for overlay in overlays:
            if overlay.get('url'):
                volume_list_entries.append({"url": overlay['url']})

    if not volume_list_entries:
        st.info(MESSAGES['no_nifti_or_voxels'])
        return

    # Prepare JavaScript data
    volume_list_js = json.dumps(volume_list_entries)
    overlay_colors_js = json.dumps(overlays)
    custom_colormap_js = voxel_manager.create_custom_colormap_js()


    # Get viewer settings
    settings = viewer_config.settings
    window_center, window_width = viewer_config.get_window_settings()
    actual_slice_type = viewer_config.get_slice_type_index()

# Removed unused debug checkbox

    # Render the viewer using our template
    html_content = template_renderer.render_viewer(
        volume_list_js=volume_list_js,
        overlay_colors_js=overlay_colors_js,
        custom_colormap_js=custom_colormap_js,
        image_server_url=EXTERNAL_IMAGE_SERVER_URL,
        main_is_nifti=settings.get('show_nifti', True),
        main_vol=settings.get('show_nifti', True),
        color_map_js=json.dumps(settings.get('color_map', 'gray')),
        nifti_gamma=settings.get('nifti_gamma', 1.0),
        nifti_opacity=settings.get('nifti_opacity', 1.0),
        window_center=window_center,
        window_width=window_width,
        overlay_start_index=1 if settings.get('show_nifti', True) else 0,
        actual_slice_type=actual_slice_type,
        segment_opacity=settings.get('segment_opacity', 0.5)
    )

    # Display the viewer
    components.html(html_content, height=VIEWER_HEIGHT, scrolling=False)


# --- Main Application Flow ---
def main():
    """Main application entry point."""
    # Set page title
    st.header("🩻 NiiVue Viewer")
    
    # Render sidebar and get selections
    selected_patient, selected_file = render_sidebar()

    # Render main viewer
    render_viewer(selected_patient, selected_file)


if __name__ == "__main__":
    main()
