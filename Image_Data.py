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

def run_server_analysis():
    """Run the server analysis script and return patient cards data."""
    try:
        # Import the analysis function directly
        from utils.analyze_server_data import get_patient_cards_data
        
        # Get patient cards data
        cards_data = get_patient_cards_data()
        
        if 'error' in cards_data:
            return None, cards_data['error']
        
        return cards_data, None
        
    except Exception as e:
        return None, f"Error: {str(e)}"

def render_patient_cards(patient_cards: List[Dict]):
    """Render patient data as simple sections (legacy function - now redirects to clean view)."""
    # This function is kept for backward compatibility but now redirects to the clean view
    if not patient_cards:
        st.warning("No patient data available")
        return
    
    # For backward compatibility, just show a simple list
    for card in patient_cards:
        if card['status'] == 'error':
            st.error(f"**{card['patient_id']}** - Error: {card['error_message']}")
        else:
            with st.expander(f"Patient: {card['patient_id']} ({card['nifti_files']} NIfTI files)", expanded=False):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("NIfTI Files", card['nifti_files'])
                with col2:
                    st.metric("Voxel Files", card['voxel_files'])
                with col3:
                    st.metric("PLY Files", card.get('ply_files', 0))
                with col4:
                    st.metric("Total Size", card['total_size'])


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

def get_nifti_files_for_patient(patient_id: str) -> List[str]:
    """
    Get NIfTI file URLs for a specific patient.
    
    Args:
        patient_id (str): Patient ID (e.g., PA00000002)
        
    Returns:
        List[str]: List of NIfTI file URLs
    """
    try:
        image_server_url = os.getenv("IMAGE_SERVER", "http://localhost:8888")
        
        # Try current structure first: output/{patient_id}/nifti/
        nifti_contents = get_folder_contents(image_server_url, f"{patient_id}/nifti")
        nifti_files = []
        
        if nifti_contents:
            for item in nifti_contents:
                if not item['is_directory'] and (item['name'].endswith('.nii.gz') or item['name'].endswith('.nii')):
                    nifti_url = f"{image_server_url}/{patient_id}/nifti/{item['name']}"
                    nifti_files.append(nifti_url)
        else:
            # Try old structure: output/scans/{patient_id}/nifti/
            nifti_contents = get_folder_contents(image_server_url, f"scans/{patient_id}/nifti")
            if nifti_contents:
                for item in nifti_contents:
                    if not item['is_directory'] and (item['name'].endswith('.nii.gz') or item['name'].endswith('.nii')):
                        nifti_url = f"{image_server_url}/scans/{patient_id}/nifti/{item['name']}"
                        nifti_files.append(nifti_url)
        
        return nifti_files
        
    except Exception as e:
        st.error(f"Error getting NIfTI files for {patient_id}: {e}")
        return []

def create_nifti_preview(nifti_url: str, nifti_name: str, unique_key: str) -> None:
    """
    Create a preview showing the corresponding STL file for NIfTI files.
    
    Args:
        nifti_url (str): URL to NIfTI file
        nifti_name (str): Display name for the NIfTI file
        unique_key (str): Unique key for Streamlit components
    """
    try:
        # Extract patient ID from the unique key
        patient_id = unique_key.split('_')[0]
        
        # Get corresponding STL files for this patient
        stl_files = get_stl_files_for_patient(patient_id)
        
        if stl_files:
            # Find STL file that matches the NIfTI name
            matching_stl = None
            for stl_url in stl_files:
                stl_name = stl_url.split('/')[-1].replace('.stl', '')
                # Check if STL name contains NIfTI name or vice versa
                if nifti_name.lower() in stl_name.lower() or stl_name.lower() in nifti_name.lower():
                    matching_stl = stl_url
                    break
            
            # If no exact match, use the first STL file
            if not matching_stl and stl_files:
                matching_stl = stl_files[0]
            
            if matching_stl:
                # Display the STL file instead of placeholder
                st.markdown(f"**🔺 3D Model for {nifti_name}:**")
                create_mini_stl_viewer_in_card(matching_stl, f"{unique_key}_stl")
            else:
                # Fallback to placeholder if no STL found
                st.markdown(f"""
                <div style="
                    border: 2px solid #4CAF50;
                    border-radius: 8px;
                    padding: 15px;
                    margin: 10px 0;
                    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                    color: white;
                    text-align: center;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.3);
                ">
                    <div style="font-size: 24px; margin-bottom: 10px;">🧠</div>
                    <div style="font-weight: bold; font-size: 14px; margin-bottom: 5px;">{nifti_name}</div>
                    <div style="font-size: 12px; opacity: 0.8;">NIfTI Medical Image</div>
                    <div style="font-size: 10px; opacity: 0.6; margin-top: 5px;">No corresponding STL file found</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            # No STL files available
            st.markdown(f"""
            <div style="
                border: 2px solid #4CAF50;
                border-radius: 8px;
                padding: 15px;
                margin: 10px 0;
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                color: white;
                text-align: center;
                box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            ">
                <div style="font-size: 24px; margin-bottom: 10px;">🧠</div>
                <div style="font-weight: bold; font-size: 14px; margin-bottom: 5px;">{nifti_name}</div>
                <div style="font-size: 12px; opacity: 0.8;">NIfTI Medical Image</div>
                <div style="font-size: 10px; opacity: 0.6; margin-top: 5px;">No STL files available</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Add a button to view in NiiVue
        if st.button(f"🩻 View {nifti_name}", key=f"view_nifti_{unique_key}"):
            st.info(f"Opening {nifti_name} in NiiVue viewer...")
            # In a real implementation, this would redirect to the NiiVue viewer
            # For now, just show the URL
            st.code(f"URL: {nifti_url}")
            
    except Exception as e:
        st.error(f"Error creating NIfTI preview: {e}")

def get_stl_files_for_patient(patient_id: str) -> List[str]:
    """
    Get STL file URLs for a specific patient.
    
    Args:
        patient_id (str): Patient ID (e.g., PA00000002)
        
    Returns:
        List[str]: List of STL file URLs
    """
    try:
        image_server_url = os.getenv("IMAGE_SERVER", "http://localhost:8888")
        
        # Try current structure first: output/{patient_id}/mesh/
        mesh_contents = get_folder_contents(image_server_url, f"{patient_id}/mesh")
        stl_files = []
        
        if mesh_contents:
            for item in mesh_contents:
                if not item['is_directory'] and item['name'].endswith('.stl'):
                    stl_url = f"{image_server_url}/{patient_id}/mesh/{item['name']}"
                    stl_files.append(stl_url)
        else:
            # Try old structure: output/scans/{patient_id}/mesh/
            mesh_contents = get_folder_contents(image_server_url, f"scans/{patient_id}/mesh")
            if mesh_contents:
                for item in mesh_contents:
                    if not item['is_directory'] and item['name'].endswith('.stl'):
                        stl_url = f"{image_server_url}/scans/{patient_id}/mesh/{item['name']}"
                        stl_files.append(stl_url)
        
        return stl_files
        
    except Exception as e:
        st.error(f"Error getting STL files for {patient_id}: {e}")
        return []

def get_folder_contents(server_url: str, folder_path: str) -> List[Dict]:
    """
    Get folder contents from the image server.
    
    Args:
        server_url (str): Base URL of the image server
        folder_path (str): Folder path to list
        
    Returns:
        List[Dict]: List of folder contents or empty list if error
    """
    try:
        url = f"{server_url}/{folder_path}" if folder_path else server_url
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Parse HTML directory listing
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        contents = []
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and href != '../' and href != '/':
                name = href.rstrip('/')
                is_directory = href.endswith('/')
                contents.append({
                    'name': name,
                    'is_directory': is_directory,
                    'url': f"{url}/{name}" if not is_directory else None
                })
        
        return contents
        
    except Exception as e:
        return []

def load_stl_file(stl_url: str) -> Optional[Dict]:
    """
    Load STL file from URL and return mesh data for visualization.
    
    Args:
        stl_url (str): URL to STL file
        
    Returns:
        Dict: Mesh data with vertices, faces, and normals or None if failed
    """
    try:
        response = requests.get(stl_url, timeout=10)
        response.raise_for_status()
        
        # Parse STL file (binary format)
        stl_data = response.content
        
        # Simple STL parser for binary format
        if len(stl_data) < 84:  # Minimum STL file size
            return None
            
        # Skip header (80 bytes) and get triangle count
        triangle_count = int.from_bytes(stl_data[80:84], byteorder='little')
        
        if triangle_count == 0:
            return None
            
        vertices = []
        faces = []
        
        # Parse triangles (50 bytes each: 12 bytes normal + 36 bytes vertices + 2 bytes attributes)
        for i in range(triangle_count):
            offset = 84 + i * 50
            
            if offset + 50 > len(stl_data):
                break
                
            # Skip normal (12 bytes)
            # Read vertices (36 bytes = 3 vertices * 3 coordinates * 4 bytes)
            v1 = np.frombuffer(stl_data[offset+12:offset+24], dtype=np.float32)
            v2 = np.frombuffer(stl_data[offset+24:offset+36], dtype=np.float32)
            v3 = np.frombuffer(stl_data[offset+36:offset+48], dtype=np.float32)
            
            # Add vertices to list
            start_idx = len(vertices)
            vertices.extend([v1, v2, v3])
            
            # Add face (triangle)
            faces.append([start_idx, start_idx + 1, start_idx + 2])
        
        if not vertices or not faces:
            return None
            
        return {
            'vertices': np.array(vertices),
            'faces': np.array(faces),
            'triangle_count': triangle_count
        }
        
    except Exception as e:
        st.error(f"Error loading STL file: {e}")
        return None

def create_mini_stl_viewer_in_card(stl_url: str, patient_id: str) -> None:
    """
    Create a mini STL viewer directly embedded in patient card.
    
    Args:
        stl_url (str): URL to STL file
        patient_id (str): Patient ID for unique keys
    """
    try:
        stl_name = stl_url.split('/')[-1]
        
        with st.spinner(f"Loading {stl_name}..."):
            mesh_data = load_stl_file(stl_url)
            
        if mesh_data:
            # Create a smaller 3D plot for the card
            fig = go.Figure()
            
            # Add the mesh data
            fig.add_trace(go.Mesh3d(
                x=mesh_data['vertices'][:, 0],
                y=mesh_data['vertices'][:, 1],
                z=mesh_data['vertices'][:, 2],
                i=mesh_data['faces'][:, 0],
                j=mesh_data['faces'][:, 1],
                k=mesh_data['faces'][:, 2],
                colorscale='Viridis',
                intensity=mesh_data['vertices'][:, 2],
                showscale=False,
                lighting=dict(ambient=0.4, diffuse=0.8, specular=0.3),
                lightposition=dict(x=100, y=100, z=100),
                opacity=0.9
            ))
            
            # Create rotation frames for auto-rotation
            frames = []
            for angle in range(0, 360, 20):  # 18 frames for smooth rotation
                rad = np.radians(angle)
                frames.append(go.Frame(
                    data=[go.Mesh3d(
                        x=mesh_data['vertices'][:, 0],
                        y=mesh_data['vertices'][:, 1],
                        z=mesh_data['vertices'][:, 2],
                        i=mesh_data['faces'][:, 0],
                        j=mesh_data['faces'][:, 1],
                        k=mesh_data['faces'][:, 2],
                        colorscale='Viridis',
                        intensity=mesh_data['vertices'][:, 2],
                        showscale=False,
                        lighting=dict(ambient=0.4, diffuse=0.8, specular=0.3),
                        lightposition=dict(x=100, y=100, z=100),
                        opacity=0.9
                    )],
                    layout=go.Layout(
                        scene=dict(
                            camera=dict(
                                eye=dict(
                                    x=1.8 * np.cos(rad),
                                    y=1.8 * np.sin(rad),
                                    z=1.2
                                )
                            )
                        )
                    )
                ))
            
            fig.frames = frames
            
            # Layout configuration for card display
            fig.update_layout(
                title=f"🔺 {stl_name}",
                scene=dict(
                    xaxis=dict(showbackground=False, showticklabels=False, title="", showgrid=False),
                    yaxis=dict(showbackground=False, showticklabels=False, title="", showgrid=False),
                    zaxis=dict(showbackground=False, showticklabels=False, title="", showgrid=False),
                    aspectmode='data',
                    camera=dict(
                        eye=dict(x=1.8, y=0, z=1.2)
                    ),
                    bgcolor='rgba(0,0,0,0)'
                ),
                margin=dict(l=0, r=0, t=20, b=0),
                height=200,  # Smaller height for card
                showlegend=False,
                updatemenus=[{
                    'type': 'buttons',
                    'showactive': False,
                    'buttons': [
                        {
                            'label': '▶️',
                            'method': 'animate',
                            'args': [None, {
                                'frame': {'duration': 200, 'redraw': True},
                                'fromcurrent': True,
                                'transition': {'duration': 0}
                            }]
                        },
                        {
                            'label': '⏸️',
                            'method': 'animate',
                            'args': [[None], {
                                'frame': {'duration': 0, 'redraw': False},
                                'mode': 'immediate',
                                'transition': {'duration': 0}
                            }]
                        }
                    ],
                    'x': 0.1,
                    'xanchor': 'left',
                    'y': 0,
                    'yanchor': 'top'
                }]
            )
            
            # Display the mini viewer
            st.plotly_chart(fig, use_container_width=True, key=f"mini_stl_{patient_id}")
            
        else:
            st.error(f"Failed to load {stl_name}")
            
    except Exception as e:
        st.error(f"Error loading STL: {e}")

def create_mini_stl_viewer(stl_files: List[str], patient_id: str) -> None:
    """
    Create a mini auto-rotating STL viewer for patient cards.
    
    Args:
        stl_files (List[str]): List of STL file URLs
        patient_id (str): Patient ID for unique keys
    """
    if not stl_files:
        return
        
    # Limit to first 2 STL files for performance and space
    display_files = stl_files[:2]
    
    with st.expander(f"🔺 STL Viewer ({len(stl_files)} files)", expanded=False):
        if len(stl_files) > 2:
            st.info(f"Showing first 2 of {len(stl_files)} STL files")
            
        for i, stl_url in enumerate(display_files):
            stl_name = stl_url.split('/')[-1]
            
            with st.spinner(f"Loading {stl_name}..."):
                mesh_data = load_stl_file(stl_url)
                
            if mesh_data:
                # Create 3D plot with auto-rotation using frames
                fig = go.Figure()
                
                # Add the mesh data
                fig.add_trace(go.Mesh3d(
                    x=mesh_data['vertices'][:, 0],
                    y=mesh_data['vertices'][:, 1],
                    z=mesh_data['vertices'][:, 2],
                    i=mesh_data['faces'][:, 0],
                    j=mesh_data['faces'][:, 1],
                    k=mesh_data['faces'][:, 2],
                    colorscale='Viridis',
                    intensity=mesh_data['vertices'][:, 2],
                    showscale=False,
                    lighting=dict(ambient=0.4, diffuse=0.8, specular=0.3),
                    lightposition=dict(x=100, y=100, z=100),
                    opacity=0.9
                ))
                
                # Create rotation frames (simpler approach)
                frames = []
                for angle in range(0, 360, 15):  # 24 frames for smooth rotation
                    rad = np.radians(angle)
                    frames.append(go.Frame(
                        data=[go.Mesh3d(
                            x=mesh_data['vertices'][:, 0],
                            y=mesh_data['vertices'][:, 1],
                            z=mesh_data['vertices'][:, 2],
                            i=mesh_data['faces'][:, 0],
                            j=mesh_data['faces'][:, 1],
                            k=mesh_data['faces'][:, 2],
                            colorscale='Viridis',
                            intensity=mesh_data['vertices'][:, 2],
                            showscale=False,
                            lighting=dict(ambient=0.4, diffuse=0.8, specular=0.3),
                            lightposition=dict(x=100, y=100, z=100),
                            opacity=0.9
                        )],
                        layout=go.Layout(
                            scene=dict(
                                camera=dict(
                                    eye=dict(
                                        x=2.0 * np.cos(rad),
                                        y=2.0 * np.sin(rad),
                                        z=1.5
                                    )
                                )
                            )
                        )
                    ))
                
                fig.frames = frames
                
                # Layout configuration
                fig.update_layout(
                    title=f"{stl_name} ({mesh_data['triangle_count']} triangles)",
                    scene=dict(
                        xaxis=dict(showbackground=False, showticklabels=False, title="", showgrid=False),
                        yaxis=dict(showbackground=False, showticklabels=False, title="", showgrid=False),
                        zaxis=dict(showbackground=False, showticklabels=False, title="", showgrid=False),
                        aspectmode='data',
                        camera=dict(
                            eye=dict(x=2.0, y=0, z=1.5)
                        ),
                        bgcolor='rgba(0,0,0,0)'
                    ),
                    margin=dict(l=0, r=0, t=30, b=0),
                    height=250,
                    showlegend=False,
                    updatemenus=[{
                        'type': 'buttons',
                        'showactive': False,
                        'buttons': [
                            {
                                'label': '▶️',
                                'method': 'animate',
                                'args': [None, {
                                    'frame': {'duration': 150, 'redraw': True},
                                    'fromcurrent': True,
                                    'transition': {'duration': 0}
                                }]
                            },
                            {
                                'label': '⏸️',
                                'method': 'animate',
                                'args': [[None], {
                                    'frame': {'duration': 0, 'redraw': False},
                                    'mode': 'immediate',
                                    'transition': {'duration': 0}
                                }]
                            }
                        ],
                        'x': 0.1,
                        'xanchor': 'left',
                        'y': 0,
                        'yanchor': 'top'
                    }]
                )
                
                st.plotly_chart(fig, use_container_width=True, key=f"stl_viewer_{patient_id}_{i}")
                
                # Download button
                try:
                    response = requests.get(stl_url, timeout=5)
                    if response.status_code == 200:
                        st.download_button(
                            label=f"📥 Download {stl_name}",
                            data=response.content,
                            file_name=stl_name,
                            mime="application/octet-stream",
                            key=f"download_{patient_id}_{i}"
                        )
                except:
                    pass
            else:
                st.error(f"Failed to load {stl_name}")
                
            if i < len(display_files) - 1:
                st.markdown("---")

def render_clean_data_view(patient_cards: List[Dict], stats: Dict):
    """Render a clean, organized view of the patient data."""
    
    # Header with key metrics
    st.markdown("### 📊 Data Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Patients", stats.get('total_patients', 0))
    with col2:
        st.metric("NIfTI Files", stats.get('total_nifti_files', 0))
    with col3:
        st.metric("Total Size", stats.get('total_data_size', '0 B'))
    with col4:
        st.metric("Last Updated", stats.get('generated_at', 'Unknown')[:10])
    
    st.markdown("---")
    
    # Patient data in a clean table format
    if patient_cards:
        st.markdown("### 👥 Patient Data")
        
        # Create a clean data table
        table_data = []
        for card in patient_cards:
            if card['status'] == 'success':
                # Get scan names for display
                scan_names = []
                if card.get('ct_scan_details'):
                    scan_names = [scan['name'] for scan in card['ct_scan_details']]
                
                table_data.append({
                    'Patient ID': card['patient_id'],
                    'NIfTI Files': f"{card['nifti_files']} files",
                    'Voxel Files': card['voxel_files'],
                    'PLY Files': card.get('ply_files', 0),
                    'Total Size': card['total_size'],
                    'File Names': ', '.join(scan_names[:3]) + ('...' if len(scan_names) > 3 else '')
                })
            else:
                table_data.append({
                    'Patient ID': card['patient_id'],
                    'NIfTI Files': 'Error',
                    'Voxel Files': 'Error',
                    'PLY Files': 'Error',
                    'Total Size': 'Error',
                    'File Names': card.get('error_message', 'Unknown error')
                })
        
        # Display as a clean table
        df = pd.DataFrame(table_data)
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Patient ID": st.column_config.TextColumn("Patient ID", width="medium"),
                "NIfTI Files": st.column_config.TextColumn("NIfTI Files", width="small"),
                "Voxel Files": st.column_config.NumberColumn("Voxel Files", width="small"),
                "PLY Files": st.column_config.NumberColumn("PLY Files", width="small"),
                "Total Size": st.column_config.TextColumn("Total Size", width="medium"),
                "File Names": st.column_config.TextColumn("File Names", width="large")
            }
        )
        
        # Detailed view for selected patient
        st.markdown("### 🔍 Patient Details")
        patient_options = [f"{card['patient_id']} ({card['nifti_files']} NIfTI files)" for card in patient_cards if card['status'] == 'success']
        
        if patient_options:
            selected_patient = st.selectbox(
                "Select a patient to view details:",
                options=patient_options,
                index=0
            )
            
            # Find the selected patient data
            selected_patient_id = selected_patient.split(' (')[0]
            selected_card = next((card for card in patient_cards if card['patient_id'] == selected_patient_id), None)
            
            if selected_card and selected_card['status'] == 'success':
                render_patient_detail_view(selected_card)
        else:
            st.info("No patient data available for detailed view")

def render_patient_detail_view(card: Dict):
    """Render detailed view for a selected patient."""
    
    # Patient header
    st.markdown(f"#### Patient: {card['patient_id']}")
    
    # Key metrics for this patient
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("NIfTI Files", card['nifti_files'])
    with col2:
        st.metric("Voxel Files", card['voxel_files'])
    with col3:
        st.metric("PLY Files", card.get('ply_files', 0))
    with col4:
        st.metric("Total Size", card['total_size'])
    
    # File details
    if card.get('file_details'):
        st.markdown("##### File Details")
        for i, file_info in enumerate(card['file_details']):
            with st.expander(f"{file_info['type']} {i+1}: {file_info['name']}", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Size:** {file_info['size_display']}")
                with col2:
                    st.write(f"**Type:** {file_info['type']}")
                
                # Show subfolder information for voxel and PLY files
                if file_info.get('subfolder'):
                    st.write(f"**Subfolder:** {file_info['subfolder']}")
                
                # Show file type status
                status_cols = st.columns(3)
                with status_cols[0]:
                    if file_info['type'] == 'NIfTI':
                        st.success("✅ NIfTI File")
                    elif file_info['type'] == 'Voxel':
                        st.info("🧠 Voxel File")
                    elif file_info['type'] == 'PLY':
                        st.success("🔺 PLY File")

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
    st.markdown('<h1 style="font-size: 2.5rem; margin-bottom: 1rem;">🩻 Image Data</h1>', unsafe_allow_html=True)
    st.markdown("Browse and analyze medical imaging data from your patients.")
    
    if check_image_server_status():
        with st.spinner("Loading data..."):
            cards_data, error = run_server_analysis()
        
        if cards_data and not error:
            stats = cards_data['summary_stats']
            patient_cards = cards_data['patient_cards']
            
            # Render clean data view
            render_clean_data_view(patient_cards, stats)
        
        elif error:
            st.error(f"❌ Failed to load data: {error}")
        else:
            st.warning("⚠️ No data available")
    
    else:
        st.warning("⚠️ Image server is offline. Start the server to view data.")
        st.code("python utils/image_server.py", language="bash")

if __name__ == "__main__":
    main()
