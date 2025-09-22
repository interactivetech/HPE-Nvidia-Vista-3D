#!/usr/bin/env python3
"""
Image Data Page - Dedicated page for viewing and managing medical imaging data.
This page provides a focused interface for browsing patient data, CT scans, and related files.
"""

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
import extra_streamlit_components as stx
import numpy as np
import tempfile
from bs4 import BeautifulSoup
import plotly.graph_objects as go

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Fallback if python-dotenv is not available
    pass

# Add utils to path for imports
sys.path.append(str(Path(__file__).parent / 'utils'))
from assets.vista3d_badge import render_nvidia_vista_card as _render_nvidia_vista_card
from assets.hpe_badge import render_hpe_badge as _render_hpe_badge

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

def render_nvidia_vista_card():
    """Delegate rendering to assets.vista3d_badge module."""
    _render_nvidia_vista_card()


def main():
    """Main function for the Image Data page."""
    # Note: This function is called from app.py, so navigation is already rendered
    # We don't need to call render_navigation() or set_page_config() here
    
    # Render Nvidia Vista 3D card in sidebar
    render_nvidia_vista_card()
    # Render HPE AI badge in sidebar
    _render_hpe_badge()
    
    # Render server status widgets in sidebar
    render_server_status_sidebar()
    
    # Main content
    st.title("📥 Image Data")
    
    with st.spinner("Analyzing server data..."):
        try:
            # Import and run the analysis
            from utils.analyze_server_data import get_patient_cards_data, load_environment_config, get_patient_folders, format_file_size
            
            # Load configuration
            output_folder = load_environment_config()
            
            # Get patient folders
            patient_folders = get_patient_folders(output_folder)
            
            if not patient_folders:
                st.warning("❌ No patient folders found in output directory")
                return
            
            # Display the analysis results in a clean format
            st.info(f"📁 Output folder: {output_folder}")
            
            # Create a summary section
            total_size = sum(folder['size_bytes'] for folder in patient_folders)
            total_scans = sum(folder['scan_count'] for folder in patient_folders)
            total_voxels = sum(sum(folder['scan_voxels'].values()) for folder in patient_folders if folder['scan_voxels'])
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Patient Folders", len(patient_folders))
            with col2:
                st.metric("Total Scans", total_scans)
            with col3:
                st.metric("Total Voxels", total_voxels)
            with col4:
                st.metric("Total Size", format_file_size(total_size))
            
            st.markdown("---")
            
            # Display detailed patient information
            for i, folder_info in enumerate(patient_folders, 1):
                with st.expander(f"{i:2d}. {folder_info['name']} - {folder_info['scan_count']} scans - {folder_info['size_display']}", expanded=False):
                    st.write(f"**Folder Name:** {folder_info['name']}")
                    st.write(f"**Size:** {folder_info['size_display']}")
                    st.write(f"**NIfTI Scans:** {folder_info['scan_count']}")
                    
                    if folder_info['scan_voxels']:
                        st.write("**Voxel Data by Scan:**")
                        for scan_name, voxel_count in folder_info['scan_voxels'].items():
                            st.write(f"  └─ {scan_name}: {voxel_count} voxels")
                    else:
                        st.write("**Voxel Data:** No voxel data found")
            
            
        except Exception as e:
            st.error(f"❌ Error analyzing server data: {str(e)}")
            st.code("python utils/analyze_server_data.py", language="bash")

if __name__ == "__main__":
    main()
