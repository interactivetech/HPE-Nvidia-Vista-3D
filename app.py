import streamlit as st
from pathlib import Path
import sys
import requests
import os
from urllib.parse import urlparse
import subprocess
import json
import base64
import mimetypes
from typing import List, Dict, Optional

# Add utils to path for imports
sys.path.append(str(Path(__file__).parent / 'utils'))
from assets.navigation import render_navigation
from assets.nvidia_badge import render_nvidia_vista_card as _render_nvidia_vista_card
from assets.hpe_badge import render_hpe_badge as _render_hpe_badge
#from assets.niivue_badge import render_niivue_badge as _render_niivue_badge

def check_image_server_status():
    """Check if the image server is available."""
    # Get server URL from environment variable (matching image_server.py)
    image_server_url = os.getenv("IMAGE_SERVER", "http://localhost:8888")
    
    try:
        # Make a quick HEAD request to check if server is responding
        response = requests.head(image_server_url, timeout=3)
        return True if response.status_code == 200 else False
    except (requests.exceptions.RequestException, requests.exceptions.Timeout):
        return False

def run_server_analysis():
    """Run the server analysis script and return parsed data."""
    try:
        # Run the analysis script
        result = subprocess.run([
            'python', 'utils/analyze_server_data.py', '--quiet'
        ], capture_output=True, text=True, cwd=Path(__file__).parent)
        
        if result.returncode != 0:
            return None, f"Error running analysis: {result.stderr}"
        
        # Parse the output to extract key statistics
        output_lines = result.stdout.split('\n')
        
        # Extract summary statistics
        stats = {}
        for line in output_lines:
            if "Total Patients Found:" in line:
                stats['total_patients'] = line.split(":")[1].strip()
            elif "Total CT Scans:" in line:
                stats['total_ct_scans'] = line.split(":")[1].strip()
            elif "Patients with CT Scans:" in line:
                stats['patients_with_ct'] = line.split(":")[1].strip()
            elif "Patients with Voxel Data:" in line:
                stats['patients_with_voxels'] = line.split(":")[1].strip()
        
        # Extract patient details
        patients = []
        current_patient = None
        
        for line in output_lines:
            if "Patient ID:" in line:
                if current_patient:
                    patients.append(current_patient)
                current_patient = {
                    'id': line.split(":")[1].strip(),
                    'ct_scans': 0,
                    'voxel_files': 0,
                    'scans': []
                }
            elif "CT Scans:" in line and current_patient:
                current_patient['ct_scans'] = int(line.split(":")[1].strip())
            elif "Voxel Files:" in line and current_patient:
                current_patient['voxel_files'] = int(line.split(":")[1].strip())
            elif "✅" in line and current_patient and "(" in line:
                # Parse scan details like "✅ 2.5_mm_STD_-_30%_ASIR_2 (segmentation file, 84 voxels)"
                scan_line = line.strip()
                if "✅" in scan_line:
                    # Extract scan name and voxel count
                    parts = scan_line.split("(")
                    if len(parts) >= 2:
                        scan_name = parts[0].replace("✅", "").strip()
                        voxel_info = parts[1].replace(")", "").strip()
                        voxel_count = 0
                        if "voxels" in voxel_info:
                            try:
                                voxel_count = int(voxel_info.split("voxels")[0].split()[-1])
                            except:
                                pass
                        current_patient['scans'].append({
                            'name': scan_name,
                            'voxel_count': voxel_count
                        })
        
        if current_patient:
            patients.append(current_patient)
        
        return {'stats': stats, 'patients': patients}, None
        
    except Exception as e:
        return None, f"Error: {str(e)}"

def render_nvidia_vista_card():
    """Delegate rendering to assets.nvidia_badge module."""
    _render_nvidia_vista_card()

def render_server_status_sidebar():
    """Render server status message in sidebar."""
    
    if check_image_server_status():
        image_server_url = os.getenv("IMAGE_SERVER", "http://localhost:8888")
        
        st.sidebar.info(f"🖥️ **Image Server**  \n🟢 Online • {image_server_url}")
    else:
        st.sidebar.error(f"🖥️ **Image Server**  \n❌ Offline  \nStart with: `python utils/image_server.py`")

st.set_page_config(
    page_title="NIfTI Vessel Segmentation and Viewer",
    page_icon="🩻",
    layout="wide",
)

# Render navigation and get the navigation instance
nav = render_navigation()

# Main content based on current page
current_page = nav.get_current_page()

if current_page == 'home':
    # Render Nvidia Vista 3D card in sidebar
    render_nvidia_vista_card()
    # Render HPE AI badge in sidebar
    _render_hpe_badge()
    # Render NiiVue badge in sidebar
    #_render_niivue_badge()
    st.title("Vessel Segmentation Viewer")
    st.markdown("Welcome to the NIfTI Vessel Segmentation and Viewer application.")
    st.markdown("Use the sidebar to navigate to different tools and features.")
    
    # Image Data Analysis Section on main page
    if check_image_server_status():
        image_server_url = os.getenv("IMAGE_SERVER", "http://localhost:8888")
        st.info(f"🖥️ Image Server — Online • {image_server_url}")
    else:
        st.error("🖥️ Image Server — Offline. Start with: `python utils/image_server.py`")
    st.markdown("---")
    st.header("🩻 Image Data")
    
    if check_image_server_status():
        with st.spinner("Analyzing server data..."):
            analysis_data, error = run_server_analysis()
        
        if analysis_data and not error:
            stats = analysis_data['stats']
            patients = analysis_data['patients']
            
            # Summary Statistics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    label="Total Patients",
                    value=stats.get('total_patients', '0'),
                    help="Number of patient folders found"
                )
            
            with col2:
                st.metric(
                    label="Total CT Scans",
                    value=stats.get('total_ct_scans', '0'),
                    help="Total number of CT scans across all patients"
                )
            
            with col3:
                # Calculate total voxels from all patients
                total_voxels = sum(patient.get('voxel_files', 0) for patient in patients)
                st.metric(
                    label="Total Voxels",
                    value=total_voxels,
                    help="Total number of voxel files across all patients"
                )
            
            # Patient Details
            st.subheader("👥 Patient Details")
            
            for patient in patients:
                with st.expander(f"Patient {patient['id']} - {patient['ct_scans']} CT Scans"):
                    st.write(f"**CT Scans:** {patient['ct_scans']}")
                    st.write(f"**Voxel Files:** {patient['voxel_files']}")
                    
                    if patient['scans']:
                        st.write("**Scan Details:**")
                        for scan in patient['scans']:
                            st.write(f"• {scan['name']}: {scan['voxel_count']} voxels")
                    else:
                        st.write("No scan details available")
        
        elif error:
            st.error(f"❌ Analysis failed: {error}")
        else:
            st.warning("⚠️ No analysis data available")
    
    else:
        st.warning("⚠️ Image server is offline. Start the server to view data analysis.")
        st.code("python utils/image_server.py", language="bash")
elif current_page == 'niivue':
    # Import and run NiiVue content
    sys.path.append(str(Path(__file__).parent))
    exec(open('NiiVue.py').read())
    

