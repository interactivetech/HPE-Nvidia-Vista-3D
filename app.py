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
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import extra_streamlit_components as stx

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Fallback if python-dotenv is not available
    pass

# Add utils to path for imports
sys.path.append(str(Path(__file__).parent / 'utils'))
from utils.navigation import render_navigation
from utils.mermaid import render_workflow_section
from assets.vista3d_badge import render_nvidia_vista_card as _render_nvidia_vista_card
from assets.hpe_badge import render_hpe_badge as _render_hpe_badge
#from assets.niivue_badge import render_niivue_badge as _render_niivue_badge

def check_image_server_status():
    """Check if the image server is available."""
    # Get server URL from environment variable (matching image_server.py)
    image_server_url = os.getenv("IMAGE_SERVER", "http://localhost:8888")
    
    # If running in Docker container, try multiple approaches
    if os.getenv("DOCKER_CONTAINER") == "true":
        # List of URLs to try in order
        urls_to_try = [
            image_server_url,  # Configured URL (likely host.docker.internal:8888)
            "http://localhost:8888",  # localhost fallback
            "http://127.0.0.1:8888",  # IP fallback
            "http://image-server:8888",  # Container name (if image server is in same compose)
        ]
        
        for url in urls_to_try:
            try:
                response = requests.head(url, timeout=2)
                if response.status_code == 200:
                    return True
            except (requests.exceptions.RequestException, requests.exceptions.Timeout):
                continue
        return False
    else:
        # Running outside Docker, use the configured URL
        try:
            response = requests.head(image_server_url, timeout=3)
            return True if response.status_code == 200 else False
        except (requests.exceptions.RequestException, requests.exceptions.Timeout):
            return False

def check_vista3d_server_status():
    """Check if the Vista3D server is available."""
    # Get server URL from environment variable
    vista3d_server_url = os.getenv("VISTA3D_SERVER", "http://localhost:8000")
    
    # If running in Docker container, try multiple approaches
    if os.getenv("DOCKER_CONTAINER") == "true":
        # List of URLs to try in order
        urls_to_try = [
            vista3d_server_url,  # Configured URL (likely host.docker.internal:8000)
            "http://localhost:8000",  # localhost fallback
            "http://127.0.0.1:8000",  # IP fallback
        ]
        
        for base_url in urls_to_try:
            try:
                response = requests.get(f"{base_url}/v1/vista3d/info", timeout=3)
                if response.status_code == 200:
                    return True
                # Log the specific error for debugging
                print(f"Vista3D status check - {base_url}: HTTP {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"Vista3D status check - {base_url}: {type(e).__name__}: {e}")
                continue
        return False
    else:
        # Running outside Docker, use the configured URL
        try:
            response = requests.get(f"{vista3d_server_url}/v1/vista3d/info", timeout=5)
            return True if response.status_code == 200 else False
        except (requests.exceptions.RequestException, requests.exceptions.Timeout):
            return False

def render_nvidia_vista_card():
    """Delegate rendering to assets.vista3d_badge module."""
    _render_nvidia_vista_card()
    

def render_server_status_sidebar():
    """Render server status message in sidebar."""
    
    if check_image_server_status():
        image_server_url = os.getenv("IMAGE_SERVER", "http://localhost:8888")
        
        st.sidebar.info(f"🖥️ **Image Server**  \n🟢 Online • {image_server_url}")
    else:
        st.sidebar.error(f"🖥️ **Image Server**  \n❌ Offline  \nStart with: `python utils/image_server.py`")
    
    # Vista3D Server Status
    vista3d_server_url = os.getenv("VISTA3D_SERVER", "http://localhost:8000")
    if check_vista3d_server_status():
        st.sidebar.info(f"🧠 **Vista3D Server**  \n🟢 Online • {vista3d_server_url}")
    else:
        st.sidebar.error(f"🧠 **Vista3D Server**  \n❌ Offline • {vista3d_server_url}")

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
    
    # Render server status widgets in sidebar
    render_server_status_sidebar()
    
    st.markdown('<h2 style="font-size: 1.5rem; margin-bottom: 1rem;">Vessel Segmentation Viewer</h2>', unsafe_allow_html=True)
    
    # Welcome message and navigation guidance
    st.markdown("""
    ## Welcome to HPE-NVIDIA Vista 3D Medical Imaging Platform
    
    This platform provides comprehensive tools for medical image analysis, visualization, and 3D reconstruction. 
    Use the navigation menu on the left to access different features:
    
    - **📊 Image Data**: Browse and analyze patient medical imaging data
    - **🩻 NiiVue Viewer**: Interactive medical image viewer for NIfTI files
    - **🔺 Open3D Viewer**: 3D mesh and point cloud visualization
    - **🛠️ Tools**: Utilities for medical image processing
    """)
    
    # Server status information
    if check_image_server_status():
        image_server_url = os.getenv("IMAGE_SERVER", "http://localhost:8888")
        st.success(f"✅ Image server is online at {image_server_url}")
    else:
        st.warning("⚠️ Image server is offline. Start the server to access medical imaging features.")
        st.code("python utils/image_server.py", language="bash")
    
    if check_vista3d_server_status():
        vista3d_server_url = os.getenv("VISTA3D_SERVER", "http://localhost:8000")
        st.success(f"✅ Vista3D server is online at {vista3d_server_url}")
    else:
        st.warning("⚠️ Vista3D server is offline. Some advanced features may not be available.")
    
    # Add workflow diagram after Image Data section
    st.markdown("---")
    
    # Display workflow section directly
    render_workflow_section()
    
    # Add definitions section
    st.markdown("---")
    
    with st.expander("👁️ Key Terms", expanded=False):
        st.markdown("### DICOM (Digital Imaging and Communications in Medicine)")
        st.markdown("""
        DICOM refers to both a standard protocol for handling, storing, and transmitting medical imaging information, and its associated file format. Developed by the National Electrical Manufacturers Association (NEMA), DICOM ensures interoperability between medical imaging equipment from different vendors. DICOM files contain not only the image data itself but also comprehensive metadata including patient demographics, study information, acquisition parameters, and technical details about the imaging procedure. This rich metadata structure makes DICOM files self-contained medical records that preserve the complete context of the imaging study, which is essential for clinical diagnosis and treatment planning.
        """)
        
        st.markdown("### NIfTI (Neuroimaging Informatics Technology Initiative)")
        st.markdown("""
        NIfTI refers to an open, NIH-sponsored initiative and its associated file format, primarily used in neuroimaging for storing data from sources like MRI scanners. The NIfTI format provides advantages over older formats by unambiguously storing orientation and coordinate system information, facilitating software interoperability and the analysis of complex brain scans. The NIfTI file can be a single .nii file or a pair of .hdr and .img files, containing both image data and associated metadata. Unlike DICOM's clinical focus, NIfTI is optimized for research and computational analysis, making it the preferred format for neuroimaging studies, brain mapping research, and AI/ML applications in medical imaging.
        """)
        
        st.markdown("### NiiVue Viewer")
        st.markdown("""
        NiiVue is a modern, web-based neuroimaging viewer designed for displaying NIfTI format brain images directly in web browsers. Developed as a JavaScript library, NiiVue provides interactive 3D visualization capabilities for neuroimaging data without requiring specialized desktop software. It supports real-time manipulation of brain scans, including slice viewing, 3D rendering, overlay visualization, and custom colormap applications. NiiVue is particularly valuable in research and clinical settings where quick, accessible visualization of neuroimaging data is needed, offering features like cross-sectional views, volume rendering, and the ability to overlay statistical maps or segmentation results onto anatomical images.
        """)
        
        st.markdown("### Voxels")
        st.markdown("""
        Voxels, short for "volume pixels," are the three-dimensional equivalent of pixels in 2D images, representing the smallest unit of volume in 3D medical imaging data. Each voxel contains specific intensity values that correspond to tissue properties at that spatial location within the body, such as bone density, soft tissue characteristics, or contrast agent concentration. In medical imaging, voxels form the building blocks of 3D anatomical structures, enabling detailed volumetric analysis and precise spatial measurements. The size and resolution of voxels directly impact image quality and diagnostic accuracy, with smaller voxels providing higher resolution but requiring more computational resources and storage space. In the context of Vista3D segmentation, voxels are individually classified and labeled to identify different anatomical structures, organs, or pathological regions within the medical scan.
        """)
        
        st.markdown("### PLY (Polygon File Format)")
        st.markdown("""
        PLY, which stands for "Polygon File Format" or "Stanford Triangle Format," is a computer file format used to store 3D graphics data, particularly 3D mesh models composed of polygons (typically triangles). Developed at Stanford University, PLY files store geometric data such as vertex coordinates, face indices, and associated properties like colors, normals, and texture coordinates. In the context of medical imaging and Vista3D segmentation, PLY files represent the 3D surface meshes generated from segmented anatomical structures, converting voxel-based medical data into smooth, renderable 3D models. These PLY files enable interactive 3D visualization of organs, vessels, and other anatomical structures, making them valuable for surgical planning, medical education, and patient communication. The format's simplicity and widespread support make it ideal for transferring 3D medical models between different visualization and analysis software packages.
        """)
    

elif current_page == 'image_data':
    # Import and run Image Data content
    sys.path.append(str(Path(__file__).parent))
    from Image_Data import main as image_data_main
    image_data_main()

elif current_page == 'niivue':
    # Import and run NiiVue content
    sys.path.append(str(Path(__file__).parent))
    exec(open('NiiVue_Viewer.py').read())

elif current_page == 'ply_viewer':
    # Import and run Open3D Viewer content
    sys.path.append(str(Path(__file__).parent))
    exec(open('Open3d_Viewer.py').read())

elif current_page == 'tools':
    # Import and run Tools content
    sys.path.append(str(Path(__file__).parent))
    exec(open('Tools.py').read())
    

