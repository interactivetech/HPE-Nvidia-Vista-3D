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
from assets.vista3d_badge import render_nvidia_vista_card as _render_nvidia_vista_card
from assets.hpe_badge import render_hpe_badge as _render_hpe_badge
#from assets.niivue_badge import render_niivue_badge as _render_niivue_badge

def check_image_server_status():
    """Check if the image server is available."""
    # Get server URL from environment variable (matching image_server.py)
    image_server_url = os.getenv("IMAGE_SERVER", "http://localhost:8888")
    
    # If running in Docker container, try multiple approaches
    if os.getenv("DOCKER_CONTAINER") == "true":
        # List of URLs to try in order of preference for health checks
        urls_to_try = [
            "http://image-server:8888",  # Container name (primary for Docker Compose)
            image_server_url,  # Configured URL
            "http://localhost:8888",  # localhost fallback
            "http://127.0.0.1:8888",  # IP fallback
        ]
        
        for url in urls_to_try:
            try:
                response = requests.head(url, timeout=2)
                if response.status_code == 200:
                    # Keep the external URL for browser access, don't change IMAGE_SERVER
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
        # List of URLs to try in order of preference
        urls_to_try = [
            vista3d_server_url,  # Configured URL (likely host.docker.internal:8000)
            "http://vista3d-server:8000",  # Container name (if Vista3D is in same compose)
            "http://localhost:8000",  # localhost fallback
            "http://127.0.0.1:8000",  # IP fallback
        ]
        
        for base_url in urls_to_try:
            try:
                response = requests.get(f"{base_url}/v1/vista3d/info", timeout=3)
                if response.status_code == 200:
                    # Keep the configured URL for browser access, don't change VISTA3D_SERVER
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
        
        st.sidebar.info(f"🖥️ **Image Server**  \n✅ Online • {image_server_url}")
    else:
        st.sidebar.error(f"🖥️ **Image Server**  \n❌ Offline  \nStart with: `python utils/image_server.py`")
    
    # Vista3D Server Status
    vista3d_server_url = os.getenv("VISTA3D_SERVER", "http://localhost:8000")
    if check_vista3d_server_status():
        st.sidebar.info(f"🫁 **Vista3D Server**  \n✅ Online • {vista3d_server_url}")
    else:
        st.sidebar.error(f"🫁 **Vista3D Server**  \n❌ Offline • {vista3d_server_url}")

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
    
    # Add spacing between HPE badge and server status widgets
    st.sidebar.markdown("")
    
    # Render server status widgets in sidebar
    render_server_status_sidebar()
    
    
    # Welcome message and navigation guidance
    st.markdown("""
    ## HPE-NVIDIA Medical Imaging Segmentation

    This platform provides automated vessel segmentation using NVIDIA's Vista3D model on HPE infrastructure, transforming DICOM medical imaging data into actionable clinical insights through AI-powered segmentation and 3D visualization.
    
    **🔄 Workflow Process**:  
    1. **📁 Add DICOM Folders**: Upload patient DICOM imaging data through the Image Data section
    2. **🔄 Convert to NIfTI**: Automatically convert DICOM files to NIfTI format for processing
    3. **🫁 AI Segmentation**: Run Vista3D model to perform automated vessel and organ segmentation
    4. **👁️ 3D Visualization**: View and analyze results using the interactive NiiVue viewer
    
    > **📋 Vista3D Capabilities & Limitations**:  
    > Vista3D supports both **CT and MRI DICOM files** (converted to NIfTI format) and excels at whole-body organ and lesion segmentation across 127+ anatomical structures. However, it has specific limitations: while it can process brain imaging data, it may not be optimal for detailed brain structure segmentation tasks that typically require specialized brain-focused models.
    
    Use the navigation menu on the left to access different features:
    
    - **📥 Image Data**: Browse and analyze patient medical imaging data
    - **🩻 NiiVue Viewer**: Interactive medical image viewer for NIfTI files
    - **🫁 OBJ Viewer**: Interactive 3D mesh viewer for anatomical structures
    - **🛠️ Tools**: Utilities for medical image processing
    """)
    

elif current_page == 'image_data':
    # Import and run Image Data content
    sys.path.append(str(Path(__file__).parent))
    from Image_Data import main as image_data_main
    image_data_main()

elif current_page == 'niivue':
    # Import and run NiiVue content
    sys.path.append(str(Path(__file__).parent))
    from NiiVue_Viewer import main as niivue_viewer_main
    niivue_viewer_main()

elif current_page == 'obj_viewer':
    # Import and run OBJ Viewer content
    sys.path.append(str(Path(__file__).parent))
    from OBJ_Viewer import main as obj_viewer_main
    obj_viewer_main()

elif current_page == 'tools':
    # Import and run Tools content
    sys.path.append(str(Path(__file__).parent))
    from Tools import main as tools_main
    tools_main()
    

