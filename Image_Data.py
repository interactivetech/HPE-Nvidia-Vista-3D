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
import plotly.express as px
import plotly.graph_objects as go
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
    """Render patient data as simple sections."""
    if not patient_cards:
        st.warning("No patient data available")
        return
    
    # Display patient data as sections
    for i, card in enumerate(patient_cards):
        if card['status'] == 'error':
            # Error section
            st.error(f"**{card['patient_id']}** - Error: {card['error_message']}")
        else:
            # Patient section
            st.markdown(f"### {card['patient_id']}")
            
            # Patient info in columns
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("🩻 CT Scans", card['ct_scans'])
            
            with col2:
                st.metric("🧠 Voxel Files", card['voxel_files'])
            
            with col3:
                st.metric("🔺 PLY Files", card['ply_files'])
            
            with col4:
                st.metric("💾 Total Size", card['total_size'])
            
            # Show NIfTI file previews
            if card.get('ct_scans', 0) > 0:
                st.markdown("**🩻 CT Scan Previews:**")
                nifti_files = get_nifti_files_for_patient(card['patient_id'])
                if nifti_files:
                    # Show first few NIfTI files as previews
                    display_files = nifti_files[:3]  # Show max 3 files
                    for i, nifti_url in enumerate(display_files):
                        nifti_name = nifti_url.split('/')[-1].replace('.nii.gz', '')
                        create_nifti_preview(nifti_url, nifti_name, f"{card['patient_id']}_{i}")
                        if i < len(display_files) - 1:
                            st.markdown("---")
            
            # Show mini STL viewer if mesh files are available
            if card.get('mesh_files', 0) > 0:
                # Get STL file URLs for this patient
                stl_files = get_stl_files_for_patient(card['patient_id'])
                if stl_files:
                    # Show first STL file as mini viewer
                    st.markdown("**🔺 3D Model Preview:**")
                    create_mini_stl_viewer_in_card(stl_files[0], card['patient_id'])
            
            # Add separator between patients
            if i < len(patient_cards) - 1:
                st.markdown("---")

def prepare_chart_data(patients_data: List[Dict]) -> pd.DataFrame:
    """Prepare patient data for the stacked bar chart."""
    chart_data = []
    
    for patient in patients_data:
        patient_id = patient.get('id', 'Unknown')
        ct_scans = patient.get('ct_scans', 0)
        voxel_files = patient.get('voxel_files', 0)
        ply_files = patient.get('ply_files', 0)
        
        # Calculate scans - this is the number of individual voxel files per patient
        # In the current data structure, scans are represented by voxel files
        scans = voxel_files
        
        # Extract size information from data_size string (e.g., "123.4 MB")
        data_size_str = patient.get('data_size', 'Unknown')
        size_mb = 0
        if data_size_str != 'Unknown' and 'MB' in data_size_str:
            try:
                size_mb = float(data_size_str.replace('MB', '').strip())
            except:
                size_mb = 0
        elif data_size_str != 'Unknown' and 'GB' in data_size_str:
            try:
                size_gb = float(data_size_str.replace('GB', '').strip())
                size_mb = size_gb * 1024  # Convert GB to MB
            except:
                size_mb = 0
        
        # Prepare scan names for hover tooltip
        scan_names = []
        if patient.get('scans'):
            scan_names = [scan.get('name', 'Unknown') for scan in patient['scans']]
        
        chart_data.append({
            'Patient': patient_id,
            'CT Scans': ct_scans,
            'Scans': scans,
            'Voxels': voxel_files,  # Using voxel_files as the voxel count
            'PLY Files': ply_files,
            'Size (MB)': size_mb,
            'Scan Names': scan_names
        })
    
    return pd.DataFrame(chart_data)

def render_patient_data_chart(patients_data: List[Dict]):
    """Render a comprehensive chart showing patient data with file counts and folder sizes."""
    if not patients_data:
        st.warning("No patient data available for chart")
        return
    
    # Prepare data for the chart
    df = prepare_chart_data(patients_data)
    
    # Create tabs for different chart views
    tab1, tab2, tab3 = st.tabs(["📊 File Counts", "💾 Folder Sizes", "📈 Combined View"])
    
    with tab1:
        # File counts stacked bar chart
        chart_df = pd.melt(
            df, 
            id_vars=['Patient'], 
            value_vars=['CT Scans', 'Scans', 'Voxels', 'PLY Files'],
            var_name='Data Type', 
            value_name='Count'
        )
        
        # Add scan names to the chart data for hover tooltips
        chart_df_with_scans = chart_df.merge(df[['Patient', 'Scan Names']], on='Patient', how='left')
        chart_df_with_scans['Scan Names Text'] = chart_df_with_scans['Scan Names'].apply(
            lambda x: '<br>'.join(x) if x else 'No scan data'
        )
        
        fig = px.bar(
            chart_df_with_scans, 
            x='Patient', 
            y='Count', 
            color='Data Type',
            title='Patient File Counts - CT Scans, Scans, Voxels, and PLY Files',
            labels={'Count': 'Number of Files', 'Patient': 'Patient ID'},
            color_discrete_map={
                'CT Scans': '#1f77b4',
                'Scans': '#ff7f0e', 
                'Voxels': '#2ca02c',
                'PLY Files': '#d62728'
            },
            hover_data={'Scan Names Text': True}
        )
        
        fig.update_layout(
            xaxis_tickangle=-45,
            height=500,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        # Folder sizes bar chart
        fig = px.bar(
            df, 
            x='Patient', 
            y='Size (MB)',
            title='Patient Folder Sizes',
            labels={'Size (MB)': 'Folder Size (MB)', 'Patient': 'Patient ID'},
            color='Size (MB)',
            color_continuous_scale='Viridis'
        )
        
        fig.update_layout(
            xaxis_tickangle=-45,
            height=500,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        # Combined view with dual y-axis
        from plotly.subplots import make_subplots
        
        # Create subplot with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Add file counts as stacked bars
        chart_df = pd.melt(
            df, 
            id_vars=['Patient'], 
            value_vars=['CT Scans', 'Scans', 'Voxels', 'PLY Files'],
            var_name='Data Type', 
            value_name='Count'
        )
        
        # Add scan names for hover tooltips
        chart_df_with_scans = chart_df.merge(df[['Patient', 'Scan Names']], on='Patient', how='left')
        chart_df_with_scans['Scan Names Text'] = chart_df_with_scans['Scan Names'].apply(
            lambda x: '<br>'.join(x) if x else 'No scan data'
        )
        
        for data_type in ['CT Scans', 'Scans', 'Voxels', 'PLY Files']:
            data_subset = chart_df_with_scans[chart_df_with_scans['Data Type'] == data_type]
            fig.add_trace(
                go.Bar(
                    x=data_subset['Patient'], 
                    y=data_subset['Count'],
                    name=data_type,
                    marker_color={
                        'CT Scans': '#1f77b4',
                        'Scans': '#ff7f0e', 
                        'Voxels': '#2ca02c',
                        'PLY Files': '#d62728'
                    }[data_type],
                    customdata=data_subset['Scan Names Text'],
                    hovertemplate=f'<b>{data_type}</b><br>' +
                                 'Patient: %{x}<br>' +
                                 'Count: %{y}<br>' +
                                 'Scan Names:<br>%{customdata}<br>' +
                                 '<extra></extra>'
                ),
                secondary_y=False
            )
        
        # Add folder sizes as line chart
        df['Scan Names Text'] = df['Scan Names'].apply(
            lambda x: '<br>'.join(x) if x else 'No scan data'
        )
        fig.add_trace(
            go.Scatter(
                x=df['Patient'], 
                y=df['Size (MB)'],
                name='Folder Size (MB)',
                mode='lines+markers',
                line=dict(color='red', width=3),
                marker=dict(size=8),
                customdata=df['Scan Names Text'],
                hovertemplate='<b>Folder Size</b><br>' +
                             'Patient: %{x}<br>' +
                             'Size: %{y} MB<br>' +
                             'Scan Names:<br>%{customdata}<br>' +
                             '<extra></extra>'
            ),
            secondary_y=True
        )
        
        # Update layout
        fig.update_layout(
            title_text="Patient Data Overview - File Counts & Folder Sizes",
            xaxis_tickangle=-45,
            height=600,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        # Set y-axes titles
        fig.update_yaxes(title_text="Number of Files", secondary_y=False)
        fig.update_yaxes(title_text="Folder Size (MB)", secondary_y=True)
        
        st.plotly_chart(fig, use_container_width=True)

def render_patient_details_visualization(patients_data: List[Dict]):
    """Render comprehensive patient details visualization."""
    if not patients_data:
        st.warning("No patient data available")
        return
    
    # Prepare data for visualization
    df = prepare_chart_data(patients_data)
    
    # Interactive Data Table
    
    # Prepare table data
    table_data = []
    for patient in patients_data:
        # Get actual NIfTI file names from the analysis data
        # The scan names are stored in the 'scans' array with the actual file names
        scan_names = []
        if patient.get('scans'):
            # Extract the actual file names from the scans array
            # These are the base names without .nii.gz extension
            scan_names = [scan.get('name', 'Unknown') for scan in patient['scans']]
        
        # Format scan names for display - show actual NIfTI file names
        if scan_names:
            # Join the scan names with commas for display
            scan_names_text = ', '.join(scan_names)
        else:
            # Fallback to count if no scan names available
            scan_names_text = f"{patient['ct_scans']} scans"
        
        table_data.append({
            'Patient ID': patient['id'],
            'CT Scans': scan_names_text,
            'Voxel Files': patient['voxel_files'],
            'PLY Files': patient.get('ply_files', 0),
            'Data Size': patient.get('data_size', 'Unknown')
        })
    
    table_df = pd.DataFrame(table_data)
    st.dataframe(
        table_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Patient ID": st.column_config.TextColumn("Patient ID", width="medium"),
            "CT Scans": st.column_config.TextColumn("CT Scans", width="large"),
            "Voxel Files": st.column_config.NumberColumn("Voxel Files", width="small"),
            "PLY Files": st.column_config.NumberColumn("PLY Files", width="small"),
            "Data Size": st.column_config.TextColumn("Data Size", width="medium")
        }
    )

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
        with st.spinner("Analyzing server data..."):
            cards_data, error = run_server_analysis()
        
        if cards_data and not error:
            stats = cards_data['summary_stats']
            patient_cards = cards_data['patient_cards']
            
            # Summary Statistics
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric(
                    label="Total Patients",
                    value=stats.get('total_patients', 0),
                    help="Number of patient folders found"
                )
            
            with col2:
                st.metric(
                    label="Total CT Scans",
                    value=stats.get('total_ct_scans', 0),
                    help="Total number of CT scans across all patients"
                )
            
            with col3:
                st.metric(
                    label="Patients with Voxels",
                    value=stats.get('patients_with_voxels', 0),
                    help="Number of patients with voxel data"
                )
            
            with col4:
                st.metric(
                    label="Patients with PLY",
                    value=stats.get('patients_with_ply', 0),
                    help="Number of patients with PLY data"
                )
            
            with col5:
                st.metric(
                    label="Total Data Size",
                    value=stats.get('total_data_size', 'Unknown'),
                    help="Total size of all patient data"
                )
            
            # Patient Cards Display
            st.markdown("---")
            render_patient_cards(patient_cards)
            
            # Optional: Keep the old visualization as an expandable section
            with st.expander("📊 Detailed Analysis & Charts", expanded=False):
                # Convert cards data to old format for compatibility with existing charts
                patients_for_charts = []
                for card in patient_cards:
                    if card['status'] == 'success':
                        patients_for_charts.append({
                            'id': card['patient_id'],
                            'ct_scans': card['ct_scans'],
                            'voxel_files': card['voxel_files'],
                            'ply_files': card['ply_files'],
                            'data_size': card['total_size'],
                            'scans': [{'name': scan['name'], 'voxel_count': scan['voxel_count']} for scan in card['ct_scan_details']]
                        })
                
                if patients_for_charts:
                    render_patient_data_chart(patients_for_charts)
                    render_patient_details_visualization(patients_for_charts)
        
        elif error:
            st.error(f"❌ Analysis failed: {error}")
        else:
            st.warning("⚠️ No analysis data available")
    
    else:
        st.warning("⚠️ Image server is offline. Start the server to view data analysis.")
        st.code("python utils/image_server.py", language="bash")

if __name__ == "__main__":
    main()
