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
from navigation import render_navigation

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
    """Render a modern NVIDIA VISTA-3D badge that links to NVIDIA Build."""
    st.sidebar.markdown("---")

    vista_url = "https://build.nvidia.com/nvidia/vista-3d"

    # Prepare inline images as base64 so the card renders reliably inside HTML
    try:
        hero_candidates = [
            Path(__file__).parent / 'assets' / 'vista-3d.jpg',
            Path(__file__).parent / 'assets' / 'vista-3d.png',
            Path(__file__).parent / 'assets' / 'vista-3d.webp',
            Path(__file__).parent / 'assets' / 'CT-Image-Planes-768x768.jpeg',
        ]
        hero_path = next((p for p in hero_candidates if p.exists()), None)
        hero_b64 = ''
        hero_mime = 'image/jpeg'
        if hero_path and hero_path.exists():
            guessed_mime, _ = mimetypes.guess_type(str(hero_path))
            hero_mime = guessed_mime or 'image/jpeg'
            hero_b64 = base64.b64encode(hero_path.read_bytes()).decode('utf-8')
    except Exception:
        hero_b64 = ''
        hero_mime = 'image/jpeg'

    try:
        nvidia_logo_path = Path(__file__).parent / 'assets' / 'nvidia.png'
        nvidia_logo_b64 = base64.b64encode(nvidia_logo_path.read_bytes()).decode('utf-8') if nvidia_logo_path.exists() else ''
    except Exception:
        nvidia_logo_b64 = ''

    card_css = f"""
    <style>
      .nv-card {{
        position: relative;
        display: block;
        border-radius: 14px;
        overflow: hidden;
        border: 1px solid rgba(118,185,0,0.35);
        background: radial-gradient(120% 120% at 0% 0%, #0f130f 0%, #0b0d0a 45%, #131613 100%);
        box-shadow: 0 6px 18px rgba(0,0,0,0.35), inset 0 0 0 1px rgba(118,185,0,0.08);
        transition: transform .15s ease, box-shadow .2s ease, border-color .2s ease;
        text-decoration: none;
      }}
      .nv-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 10px 24px rgba(0,0,0,0.45), inset 0 0 0 1px rgba(118,185,0,0.12);
        border-color: rgba(118,185,0,0.6);
      }}
      /* Ensure no underlines appear on any text inside the card */
      .nv-card, .nv-card:hover, .nv-card * {{ text-decoration: none !important; }}
      .nv-hero {{
        height: 112px;
        background: linear-gradient(180deg, rgba(0,0,0,0.0), rgba(0,0,0,0.35)), url('data:{hero_mime};base64,{hero_b64}') center/cover no-repeat;
        filter: saturate(1.05) contrast(1.05);
      }}
      .nv-body {{
        padding: 12px 12px 14px 12px;
      }}
      .nv-title {{
        display: flex; align-items: center; gap: 8px;
        color: #e9f5dd; font-weight: 700; letter-spacing: .2px;
      }}
      .nv-title .nv-wordmark {{
        color: #76b900; font-size: 13px; font-weight: 800; letter-spacing: .8px;
        display: inline-block; text-transform: uppercase; line-height: 1;
      }}
      .nv-kicker {{ color: #a6d36b; font-size: 11px; font-weight: 600; opacity: .9; }}
      .nv-name {{ color: #ffffff; font-size: 15px; }}
      .nv-desc {{ color: #d7dfcf; font-size: 12px; line-height: 1.35; margin-top: 6px; opacity: .95; }}
      .nv-tags {{ display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }}
      .nv-tag {{
        font-size: 10.5px; font-weight: 600; letter-spacing: .2px;
        padding: 3px 8px; border-radius: 999px; border: 1px solid rgba(118,185,0,.35);
        color: #b9e07d; background: rgba(118,185,0,.12);
      }}
      .nv-cta {{
        margin-top: 10px; display: inline-block; width: 100%; text-align: center;
        color: #0b0d0a; background: #76b900; border-radius: 10px; padding: 7px 10px;
        font-weight: 700; font-size: 12px; letter-spacing: .2px; border: none;
      }}
      .nv-cta:hover {{ filter: brightness(1.05); }}
    </style>
    """

    logo_img = "<span class='nv-wordmark'>NVIDIA</span>"

    card_html = f"""
    <a class="nv-card" href="{vista_url}" target="_blank" rel="noopener noreferrer">
      <div class="nv-hero"></div>
      <div class="nv-body">
        <div class="nv-kicker">FOUNDATION MODEL</div>
        <div class="nv-title">{logo_img}<span class="nv-name">VISTA‑3D</span></div>
        <div class="nv-desc">Specialized interactive model for 3D medical image segmentation.</div>
        <div class="nv-tags">
          <span class="nv-tag">interactive annotation</span>
          <span class="nv-tag">3D segmentation</span>
          <span class="nv-tag">medical imaging</span>
        </div>
        <div class="nv-cta">Open on NVIDIA Build ↗</div>
      </div>
    </a>
    """

    with st.sidebar.container():
        st.markdown(card_css + card_html, unsafe_allow_html=True)

def render_server_status_sidebar():
    """Render server status message in sidebar."""
    st.sidebar.markdown("---")
    
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
    # Render server status in sidebar (only on home page)
    render_server_status_sidebar()
    
    # Render Nvidia Vista 3D card in sidebar
    render_nvidia_vista_card()
    st.title("Vessel Segmentation Viewer")
    st.markdown("Welcome to the NIfTI Vessel Segmentation and Viewer application.")
    st.markdown("Use the sidebar to navigate to different tools and features.")
    
    # Image Data Analysis Section on main page
    st.markdown("---")
    st.header("🧬 Image Data")
    
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
elif current_page == 'cache':
    # Import and run cache content
    sys.path.append(str(Path(__file__).parent))
    exec(open('cache.py').read())

