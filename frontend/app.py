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
        st.sidebar.info(f"🧠 **Vista3D Server**  \n✅ Online • {vista3d_server_url}")
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
    
    # Add spacing between HPE badge and server status widgets
    st.sidebar.markdown("")
    
    # Render server status widgets in sidebar
    render_server_status_sidebar()
    
    
    # Welcome message and navigation guidance
    st.markdown("""
    ## HPE-NVIDIA Medical Imaging Segmentation

    This platform provides automated vessel segmentation using NVIDIA's Vista3D model on HPE infrastructure, transforming DICOM medical imaging data into actionable clinical insights through AI-powered segmentation and 3D visualization.
    
    Use the navigation menu on the left to access different features:
    
    - **📥 Image Data**: Browse and analyze patient medical imaging data
    - **🩻 NiiVue Viewer**: Interactive medical image viewer for NIfTI files
    - **🔺 Open3D Viewer**: 3D mesh and point cloud visualization
    - **🛠️ Tools**: Utilities for medical image processing
    """)
    
    
    # Add workflow diagram after Image Data section
    st.markdown("---")
    
    # Display workflow section directly
    render_workflow_section()
    
    # Add definitions section
    st.markdown("---")
    

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

elif current_page == 'ply_viewer':
    # Open3D Viewer is now a separate service
    st.title("🔺 Open3D Viewer")
    st.info("The Open3D Viewer has been moved to a separate service for better performance and isolation.")
    
    # Get the Open3D service URL from environment
    open3d_service_url = os.getenv("OPEN3D_SERVICE_URL", "http://localhost:8502")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"""
        **Open3D Viewer Service**
        
        The Open3D Viewer is now running as a separate service with dedicated resources for 3D processing.
        
        **Features:**
        - Advanced 3D mesh visualization with Open3D
        - Point cloud processing and analysis
        - 3D printing preparation tools
        - Mesh repair and optimization
        - Multiple format export (PLY, STL, OBJ, etc.)
        """)
    
    with col2:
        st.markdown("**Quick Access**")
        if st.button("🚀 Open Open3D Viewer", type="primary", use_container_width=True):
            st.markdown(f'<meta http-equiv="refresh" content="0; url={open3d_service_url}">', unsafe_allow_html=True)
            st.success(f"Redirecting to Open3D service at {open3d_service_url}")
        
        st.markdown(f"**Service URL:** `{open3d_service_url}`")
        
        # Check if service is running
        try:
            import requests
            response = requests.get(f"{open3d_service_url}/_stcore/health", timeout=5)
            if response.status_code == 200:
                st.success("✅ Open3D service is running")
            else:
                st.warning("⚠️ Open3D service may not be ready")
        except:
            st.error("❌ Open3D service is not accessible")
            st.info("Start the Open3D service with: `cd open3d && docker-compose up`")
    
    st.divider()
    
    # Instructions for running the service
    with st.expander("🔧 How to run the Open3D service", expanded=False):
        st.markdown("""
        **Option 1: Using Docker Compose (Recommended)**
        ```bash
        cd open3d
        docker-compose up
        ```
        
        **Option 2: Using Docker directly**
        ```bash
        cd open3d
        docker build -t vista3d-open3d .
        docker run -p 8502:8502 vista3d-open3d
        ```
        
        **Option 3: Local development**
        ```bash
        cd open3d
        uv sync
        uv run streamlit run Open3d_Viewer.py --server.port=8502
        ```
        """)

elif current_page == 'tools':
    # Import and run Tools content
    sys.path.append(str(Path(__file__).parent))
    from Tools import main as tools_main
    tools_main()
    

