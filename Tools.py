import streamlit as st
import subprocess
import os
import sys
from pathlib import Path
import json
import pandas as pd
from typing import Dict, List, Optional
import time

# Add utils to path for imports
sys.path.append(str(Path(__file__).parent / 'utils'))

def run_command(command: List[str], description: str = "") -> tuple[bool, str, str]:
    """Run a command and return success status, stdout, and stderr."""
    try:
        result = subprocess.run(
            command, 
            capture_output=True, 
            text=True, 
            cwd=Path(__file__).parent,
            timeout=300  # 5 minute timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", f"Command timed out after 5 minutes"
    except Exception as e:
        return False, "", f"Error running command: {str(e)}"


def get_dicom_patient_folders() -> List[str]:
    """Get list of patient folders from DICOM directory."""
    try:
        # Load environment variables to get DICOM folder path
        from dotenv import load_dotenv
        load_dotenv()
        
        # Check if we're running in a Docker container
        is_docker = os.path.exists('/.dockerenv') or os.environ.get('DOCKER_CONTAINER') == 'true'
        
        if is_docker:
            # In Docker container, use the mounted paths
            dicom_folder = '/app/dicom'
        else:
            # On host machine, use environment variables
            dicom_folder = os.getenv('DICOM_FOLDER')
            if not dicom_folder:
                return []
        
        dicom_path = Path(dicom_folder)
        
        # Check if DICOM directory exists
        if not dicom_path.exists() or not dicom_path.is_dir():
            return []
        
        # Get list of subdirectories (patient folders)
        patient_folders = []
        for entry in os.scandir(dicom_path):
            if entry.is_dir() and entry.name != 'uploads':
                patient_folders.append(entry.name)
        
        return sorted(patient_folders)
        
    except Exception as e:
        st.error(f"Error getting patient folders: {str(e)}")
        return []


def render_dicom_tools():
    """Render DICOM processing tools."""
    st.subheader("📋 DICOM Processing Tools")
    
    col1, col2 = st.columns(2)
    
    with col1:
        pass
    
    with col2:
        st.markdown("**DICOM to NIfTI Converter**")
        st.markdown("Convert DICOM files to NIfTI format")
        if st.button("Run DICOM2NIfTI", key="dicom2nifti"):
            with st.spinner("Converting DICOM files..."):
                success, stdout, stderr = run_command(
                    ["python", "utils/dicom2nifti.py"],
                    "DICOM to NIfTI conversion"
                )
                
                if success:
                    st.success("✅ DICOM conversion completed successfully!")
                    if stdout:
                        st.text_area("Output:", stdout, height=200)
                else:
                    st.error("❌ DICOM conversion failed!")
                    if stderr:
                        st.text_area("Error:", stderr, height=200)


def render_segmentation_tools():
    """Render segmentation tools."""
    st.subheader("🎯 Vista3D Segmentation Tools")
    st.markdown("""
    Run Vista3D AI segmentation on medical images to identify and segment anatomical structures.
    This tool processes NIfTI files and creates detailed segmentation masks with individual voxel files.
    """)
    
    # Segmentation options
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("**Segmentation Options**")
        
        # Patient selection
        patient_folders = get_dicom_patient_folders()
        
        if not patient_folders:
            st.warning("⚠️ No patient folders found in DICOM directory. Please check your DICOM_FOLDER path in .env file.")
            return
        
        selected_patients = st.multiselect(
            "Select Patients",
            options=patient_folders,
            default=patient_folders,  # Select all by default
            help="Select one or more patient folders to process. Leave empty or uncheck all to process no patients.",
            key="segmentation_patients"
        )
        
        # Force overwrite option
        force_overwrite = st.checkbox(
            "Force Overwrite", 
            value=False, 
            help="Overwrite existing segmentation files"
        )
        
        # Vessels of interest
        vessels_of_interest = st.text_input(
            "Vessels of Interest", 
            value="", 
            placeholder="Leave empty for all vessels (default) or specify: aorta, inferior_vena_cava",
            help="Leave empty to process ALL available vessels (default). Or specify a comma-separated list of specific vessels to segment."
        )
        
        # Label set selection
        label_set = st.selectbox(
            "Label Set",
            options=["", "basic", "extended", "custom"],
            help="Select a predefined label set for segmentation"
        )
    
    with col2:
        # Display patient info
        if not selected_patients:
            st.warning("⚠️ **No patients selected**")
            st.markdown("Please select at least one patient to process.")
        elif len(selected_patients) == len(patient_folders):
            st.info(f"📁 **Processing:** All {len(patient_folders)} patients")
        elif len(selected_patients) == 1:
            st.info(f"📁 **Processing:** {selected_patients[0]}")
        else:
            st.info(f"📁 **Processing:** {len(selected_patients)} patients")
        
        # Disable button if no patients selected
        button_disabled = len(selected_patients) == 0
        
        segmentation_clicked = st.button("🎯 Start Vista3D Segmentation", key="start_segmentation", type="primary", disabled=button_disabled)
    
    # Check if segmentation button was clicked
    if segmentation_clicked:
        with st.spinner("Starting Vista3D segmentation..."):
            # Prepare command arguments
            cmd_args = ["python", "utils/segment.py"]
            
            # Add patient selection if specific patients are chosen
            if len(selected_patients) < len(patient_folders):
                # Add selected patients as arguments
                cmd_args.extend(selected_patients)
            
            if force_overwrite:
                cmd_args.append("--force")
            
            # Create progress containers
            progress_container = st.container()
            output_container = st.container()
            
            with progress_container:
                progress_bar = st.progress(0)
                status_text = st.empty()
            
            with output_container:
                output_placeholder = st.empty()
            
            try:
                # Set environment variables if specified
                env = os.environ.copy()
                if vessels_of_interest:
                    env['VESSELS_OF_INTEREST'] = vessels_of_interest
                if label_set:
                    env['LABEL_SET'] = label_set
                
                # Run the segmentation with real-time output
                status_text.text("🎯 Initializing Vista3D segmentation...")
                progress_bar.progress(10)
                
                # Start the subprocess
                process = subprocess.Popen(
                    cmd_args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    cwd=Path(__file__).parent,
                    env=env
                )
                
                # Read output line by line
                output_lines = []
                current_progress = 10
                
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        output_lines.append(output.strip())
                        # Update output display (keep last 20 lines)
                        recent_output = output_lines[-20:]
                        output_placeholder.text_area(
                            "Segmentation Output:", 
                            value="\n".join(recent_output), 
                            height=300,
                            disabled=True
                        )
                        
                        # Update progress based on output keywords
                        if "Processing patients" in output:
                            current_progress = min(30, current_progress + 5)
                        elif "Processing NIfTI files" in output:
                            current_progress = min(60, current_progress + 10)
                        elif "Successfully saved segmentation" in output:
                            current_progress = min(90, current_progress + 15)
                        elif "Segmentation Process Complete" in output:
                            current_progress = 100
                        
                        progress_bar.progress(current_progress)
                        if len(selected_patients) == len(patient_folders):
                            status_text.text(f"🎯 Running Vista3D segmentation for all patients... ({current_progress}%)")
                        elif len(selected_patients) == 1:
                            status_text.text(f"🎯 Running Vista3D segmentation for {selected_patients[0]}... ({current_progress}%)")
                        else:
                            status_text.text(f"🎯 Running Vista3D segmentation for {len(selected_patients)} patients... ({current_progress}%)")
                
                # Wait for process to complete
                return_code = process.wait()
                
                if return_code == 0:
                    progress_bar.progress(100)
                    status_text.text("✅ Segmentation completed successfully!")
                    st.info("Vista3D segmentation completed successfully!")
                    
                    # Show final output
                    final_output = "\n".join(output_lines)
                    st.text_area("Final Output:", final_output, height=400, disabled=True)
                    
                else:
                    progress_bar.progress(0)
                    status_text.text("❌ Segmentation failed!")
                    st.error("❌ Vista3D segmentation failed!")
                    
                    # Show error output
                    error_output = "\n".join(output_lines)
                    st.text_area("Error Output:", error_output, height=400, disabled=True)
                    
            except Exception as e:
                progress_bar.progress(0)
                status_text.text("❌ Segmentation error!")
                st.error(f"❌ Error running segmentation: {str(e)}")
                
                # Show error details
                st.text_area("Error Details:", str(e), height=200, disabled=True)
    




def main():
    """Main function to render the Tools page."""
    # Note: st.set_page_config() is handled by the main app.py
    # Only set page config when running as standalone
    if __name__ == "__main__":
        st.set_page_config(
            page_title="Tools - HPE-NVIDIA Vista 3D",
            page_icon="🛠️",
            layout="wide"
        )
    
    st.title("🛠️ Tools & Utilities")
    st.markdown("Access various tools and utilities for medical image processing and 3D visualization.")
    
    st.markdown("---")
    
    # DICOM to NIfTI Conversion Section
    st.subheader("🔄 DICOM to NIfTI Conversion")
    st.markdown("""
    Convert DICOM medical imaging files to NIfTI format using dcm2niix. This tool processes 
    DICOM files and creates optimized NIfTI files with metadata for medical image analysis.
    """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Patient selection
        patient_folders = get_dicom_patient_folders()
        
        if not patient_folders:
            st.warning("⚠️ No patient folders found in DICOM directory. Please check your DICOM_FOLDER path in .env file.")
            return
        
        selected_patients = st.multiselect(
            "Select Patients",
            options=patient_folders,
            default=patient_folders,  # Select all by default
            help="Select one or more patient folders to process. Leave empty or uncheck all to process no patients."
        )
        
        # Conversion options
        force_overwrite = st.checkbox("Force Overwrite", value=False, help="Overwrite existing NIfTI files")
        min_size_mb = st.number_input("Minimum File Size (MB)", min_value=0.0, value=5.0, step=0.1, 
                                    help="Delete NIfTI files smaller than this size")
    
    with col2:
        # Display patient info
        if not selected_patients:
            st.warning("⚠️ **No patients selected**")
            st.markdown("Please select at least one patient to process.")
        elif len(selected_patients) == len(patient_folders):
            st.info(f"📁 **Processing:** All {len(patient_folders)} patients")
        elif len(selected_patients) == 1:
            st.info(f"📁 **Processing:** {selected_patients[0]}")
        else:
            st.info(f"📁 **Processing:** {len(selected_patients)} patients")
        
        # Disable button if no patients selected
        button_disabled = len(selected_patients) == 0
        
        conversion_clicked = st.button("🔄 Start DICOM to NIfTI Conversion", key="start_dicom2nifti", type="primary", disabled=button_disabled)
    
    # Check if conversion button was clicked
    if conversion_clicked:
        with st.spinner("Starting DICOM to NIfTI conversion..."):
            # Prepare command arguments
            cmd_args = ["python", "utils/dicom2nifti.py"]
            
            if force_overwrite:
                cmd_args.append("--force")
            
            if min_size_mb > 0:
                cmd_args.extend(["--min-size-mb", str(int(min_size_mb))])
            
            # Add patient selection if specific patients are chosen
            if len(selected_patients) < len(patient_folders):
                # Specific patients selected - use --patient argument
                cmd_args.extend(["--patient"] + selected_patients)
            
            # Create progress containers
            progress_container = st.container()
            output_container = st.container()
            
            with progress_container:
                progress_bar = st.progress(0)
                status_text = st.empty()
            
            with output_container:
                output_placeholder = st.empty()
            
            try:
                # Run the conversion with real-time output
                status_text.text("🔄 Initializing conversion...")
                progress_bar.progress(10)
                
                # Start the subprocess
                process = subprocess.Popen(
                    cmd_args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    cwd=Path(__file__).parent
                )
                
                # Read output line by line
                output_lines = []
                current_progress = 10
                
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        output_lines.append(output.strip())
                        # Update output display (keep last 20 lines)
                        recent_output = output_lines[-20:]
                        output_placeholder.text_area(
                            "Conversion Output:", 
                            value="\n".join(recent_output), 
                            height=300,
                            disabled=True
                        )
                        
                        # Update progress based on output keywords
                        if "Processing patients" in output or "Processing specific patient" in output:
                            current_progress = min(50, current_progress + 5)
                        elif "Successfully processed" in output:
                            current_progress = min(90, current_progress + 10)
                        elif "conversion completed" in output:
                            current_progress = 100
                        
                        progress_bar.progress(current_progress)
                        if len(selected_patients) == len(patient_folders):
                            status_text.text(f"🔄 Converting DICOM files for all patients... ({current_progress}%)")
                        elif len(selected_patients) == 1:
                            status_text.text(f"🔄 Converting DICOM files for {selected_patients[0]}... ({current_progress}%)")
                        else:
                            status_text.text(f"🔄 Converting DICOM files for {len(selected_patients)} patients... ({current_progress}%)")
                
                # Wait for process to complete
                return_code = process.wait()
                
                if return_code == 0:
                    progress_bar.progress(100)
                    status_text.text("✅ Conversion completed successfully!")
                    st.info("DICOM to NIfTI conversion completed successfully!")
                    
                    # Show final output
                    final_output = "\n".join(output_lines)
                    st.text_area("Final Output:", final_output, height=400, disabled=True)
                    
                else:
                    progress_bar.progress(0)
                    status_text.text("❌ Conversion failed!")
                    st.error("❌ DICOM to NIfTI conversion failed!")
                    
                    # Show error output
                    error_output = "\n".join(output_lines)
                    st.text_area("Error Output:", error_output, height=400, disabled=True)
                    
            except Exception as e:
                progress_bar.progress(0)
                status_text.text("❌ Conversion error!")
                st.error(f"❌ Error running conversion: {str(e)}")
                
                # Show error details
                st.text_area("Error Details:", str(e), height=200, disabled=True)
    
    st.markdown("---")
    
    # Vista3D Segmentation Section
    render_segmentation_tools()
    
    st.markdown("---")
    
    # NIfTI to PLY Conversion Section
    st.subheader("🔺 NIfTI to PLY Conversion")
    st.markdown("""
    Convert NIfTI medical imaging files to PLY (Polygon File Format) mesh files for 3D visualization.
    This tool processes NIfTI files and creates high-quality 3D meshes using marching cubes algorithm.
    """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Patient selection
        patient_folders = get_dicom_patient_folders()
        
        if not patient_folders:
            st.warning("⚠️ No patient folders found in DICOM directory. Please check your DICOM_FOLDER path in .env file.")
            return
        
        selected_patients_ply = st.multiselect(
            "Select Patients",
            options=patient_folders,
            default=patient_folders,  # Select all by default
            help="Select one or more patient folders to process. Leave empty or uncheck all to process no patients.",
            key="nifti2ply_patients"
        )
        
        # Conversion options
        force_overwrite_ply = st.checkbox("Force Overwrite PLY", value=False, help="Overwrite existing PLY files")
        threshold = st.number_input("Threshold", min_value=0.0, value=0.1, step=0.01, 
                                  help="Threshold value for binary mask (default: 0.1 for high quality)")
        smooth_factor = st.number_input("Smoothing Factor", min_value=0.0, value=1.0, step=0.1,
                                      help="Smoothing factor for mesh quality (default: 1.0)")
        ascii_format = st.checkbox("ASCII Format", value=False, help="Write ASCII PLY format (default: binary)")
        verbose_output = st.checkbox("Verbose Output", value=False, help="Enable detailed output")
    
    with col2:
        # Display patient info
        if not selected_patients_ply:
            st.warning("⚠️ **No patients selected**")
            st.markdown("Please select at least one patient to process.")
        elif len(selected_patients_ply) == len(patient_folders):
            st.info(f"📁 **Processing:** All {len(patient_folders)} patients")
        elif len(selected_patients_ply) == 1:
            st.info(f"📁 **Processing:** {selected_patients_ply[0]}")
        else:
            st.info(f"📁 **Processing:** {len(selected_patients_ply)} patients")
        
        # Disable button if no patients selected
        button_disabled_ply = len(selected_patients_ply) == 0
        
        conversion_ply_clicked = st.button("🔺 Start NIfTI to PLY Conversion", key="start_nifti2ply", type="primary", disabled=button_disabled_ply)
    
    # Check if PLY conversion button was clicked
    if conversion_ply_clicked:
        with st.spinner("Starting NIfTI to PLY conversion..."):
            # Prepare command arguments
            cmd_args = ["python", "utils/nifti2ply.py", "--batch"]
            
            if force_overwrite_ply:
                cmd_args.append("--force")
            
            if threshold != 0.1:
                cmd_args.extend(["--threshold", str(threshold)])
            
            if smooth_factor != 1.0:
                cmd_args.extend(["--smooth", str(smooth_factor)])
            
            if ascii_format:
                cmd_args.append("--ascii")
            
            if verbose_output:
                cmd_args.append("--verbose")
            
            # Add patient selection if specific patients are chosen
            if len(selected_patients_ply) < len(patient_folders):
                # Add selected patients as arguments
                cmd_args.extend(selected_patients_ply)
            
            # Create progress containers
            progress_container = st.container()
            output_container = st.container()
            
            with progress_container:
                progress_bar = st.progress(0)
                status_text = st.empty()
            
            with output_container:
                output_placeholder = st.empty()
            
            try:
                # Run the conversion with real-time output
                status_text.text("🔺 Initializing NIfTI to PLY conversion...")
                progress_bar.progress(10)
                
                # Start the subprocess
                process = subprocess.Popen(
                    cmd_args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    cwd=Path(__file__).parent
                )
                
                # Read output line by line
                output_lines = []
                current_progress = 10
                
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        output_lines.append(output.strip())
                        # Update output display (keep last 20 lines)
                        recent_output = output_lines[-20:]
                        output_placeholder.text_area(
                            "Conversion Output:", 
                            value="\n".join(recent_output), 
                            height=300,
                            disabled=True
                        )
                        
                        # Update progress based on output keywords
                        if "Processing patients" in output or "Processing specific patient" in output:
                            current_progress = min(30, current_progress + 5)
                        elif "Processing subfolder" in output:
                            current_progress = min(60, current_progress + 10)
                        elif "Successfully wrote PLY file" in output:
                            current_progress = min(90, current_progress + 15)
                        elif "Enhanced NIfTI to PLY conversion completed" in output:
                            current_progress = 100
                        
                        progress_bar.progress(current_progress)
                        if len(selected_patients_ply) == len(patient_folders):
                            status_text.text(f"🔺 Converting NIfTI to PLY for all patients... ({current_progress}%)")
                        elif len(selected_patients_ply) == 1:
                            status_text.text(f"🔺 Converting NIfTI to PLY for {selected_patients_ply[0]}... ({current_progress}%)")
                        else:
                            status_text.text(f"🔺 Converting NIfTI to PLY for {len(selected_patients_ply)} patients... ({current_progress}%)")
                
                # Wait for process to complete
                return_code = process.wait()
                
                if return_code == 0:
                    progress_bar.progress(100)
                    status_text.text("✅ PLY conversion completed successfully!")
                    st.info("NIfTI to PLY conversion completed successfully!")
                    
                    # Show final output
                    final_output = "\n".join(output_lines)
                    st.text_area("Final Output:", final_output, height=400, disabled=True)
                    
                else:
                    progress_bar.progress(0)
                    status_text.text("❌ PLY conversion failed!")
                    st.error("❌ NIfTI to PLY conversion failed!")
                    
                    # Show error output
                    error_output = "\n".join(output_lines)
                    st.text_area("Error Output:", error_output, height=400, disabled=True)
                    
            except Exception as e:
                progress_bar.progress(0)
                status_text.text("❌ PLY conversion error!")
                st.error(f"❌ Error running PLY conversion: {str(e)}")
                
                # Show error details
                st.text_area("Error Details:", str(e), height=200, disabled=True)

if __name__ == "__main__":
    main()
