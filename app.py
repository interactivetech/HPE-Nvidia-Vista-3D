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

# Add utils to path for imports
sys.path.append(str(Path(__file__).parent / 'utils'))
from utils.navigation import render_navigation
from utils.mermaid import render_workflow_section
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
                # Extract just the number, ignoring any additional info
                ct_text = line.split(":")[1].strip()
                stats['total_ct_scans'] = ct_text.split()[0] if ct_text.split() else "0"
            elif "Patients with CT Scans:" in line:
                stats['patients_with_ct'] = line.split(":")[1].strip()
            elif "Patients with Voxel Data:" in line:
                stats['patients_with_voxels'] = line.split(":")[1].strip()
            elif "Patients with Mesh Data:" in line:
                stats['patients_with_meshes'] = line.split(":")[1].strip()
            elif "TOTAL DATA SIZE:" in line:
                stats['total_data_size'] = line.split(":")[1].strip()
        
        # Extract patient details
        patients = []
        current_patient = None
        
        for line in output_lines:
            if "Patient ID:" in line:
                if current_patient:
                    patients.append(current_patient)
                
                # Parse patient ID and data size from format: "Patient ID: PA00000002 - 123.4 MB"
                line_parts = line.split(":")
                if len(line_parts) >= 2:
                    patient_info = line_parts[1].strip()
                    if " - " in patient_info:
                        patient_id, data_size = patient_info.split(" - ", 1)
                        patient_id = patient_id.strip()
                        data_size = data_size.strip()
                    else:
                        patient_id = patient_info
                        data_size = "Unknown"
                else:
                    patient_id = "Unknown"
                    data_size = "Unknown"
                
                current_patient = {
                    'id': patient_id,
                    'data_size': data_size,
                    'ct_scans': 0,
                    'voxel_files': 0,
                    'mesh_files': 0,
                    'scans': []
                }
            elif "CT Scans:" in line and current_patient:
                # Extract just the number, ignoring size info like "2 (1.2 GB)"
                ct_text = line.split(":")[1].strip()
                try:
                    # Try to extract just the number part
                    ct_number = ct_text.split()[0]  # Get first part before space
                    current_patient['ct_scans'] = int(ct_number)
                except (ValueError, IndexError):
                    current_patient['ct_scans'] = 0
            elif "Voxel Files:" in line and current_patient:
                # Extract just the number, ignoring size info like "15 (800.5 MB)"
                voxel_text = line.split(":")[1].strip()
                try:
                    # Try to extract just the number part
                    voxel_number = voxel_text.split()[0]  # Get first part before space
                    current_patient['voxel_files'] = int(voxel_number)
                except (ValueError, IndexError):
                    current_patient['voxel_files'] = 0
            elif "Mesh Files:" in line and current_patient:
                # Extract just the number, ignoring size info like "8 (45.2 MB)"
                mesh_text = line.split(":")[1].strip()
                try:
                    # Try to extract just the number part
                    mesh_number = mesh_text.split()[0]  # Get first part before space
                    current_patient['mesh_files'] = int(mesh_number)
                except (ValueError, IndexError):
                    current_patient['mesh_files'] = 0
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

def prepare_chart_data(patients_data: List[Dict]) -> pd.DataFrame:
    """Prepare patient data for the stacked bar chart."""
    chart_data = []
    
    for patient in patients_data:
        patient_id = patient.get('id', 'Unknown')
        ct_scans = patient.get('ct_scans', 0)
        voxel_files = patient.get('voxel_files', 0)
        mesh_files = patient.get('mesh_files', 0)
        
        # Calculate segments - this is the number of individual voxel files per patient
        # In the current data structure, segments are represented by voxel files
        segments = voxel_files
        
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
            'Segments': segments,
            'Voxels': voxel_files,  # Using voxel_files as the voxel count
            'Meshes': mesh_files,
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
            value_vars=['CT Scans', 'Segments', 'Voxels', 'Meshes'],
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
            title='Patient File Counts - CT Scans, Segments, Voxels, and Meshes',
            labels={'Count': 'Number of Files', 'Patient': 'Patient ID'},
            color_discrete_map={
                'CT Scans': '#1f77b4',
                'Segments': '#ff7f0e', 
                'Voxels': '#2ca02c',
                'Meshes': '#d62728'
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
            value_vars=['CT Scans', 'Segments', 'Voxels', 'Meshes'],
            var_name='Data Type', 
            value_name='Count'
        )
        
        # Add scan names for hover tooltips
        chart_df_with_scans = chart_df.merge(df[['Patient', 'Scan Names']], on='Patient', how='left')
        chart_df_with_scans['Scan Names Text'] = chart_df_with_scans['Scan Names'].apply(
            lambda x: '<br>'.join(x) if x else 'No scan data'
        )
        
        for data_type in ['CT Scans', 'Segments', 'Voxels', 'Meshes']:
            data_subset = chart_df_with_scans[chart_df_with_scans['Data Type'] == data_type]
            fig.add_trace(
                go.Bar(
                    x=data_subset['Patient'], 
                    y=data_subset['Count'],
                    name=data_type,
                    marker_color={
                        'CT Scans': '#1f77b4',
                        'Segments': '#ff7f0e', 
                        'Voxels': '#2ca02c',
                        'Meshes': '#d62728'
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
        # Get scan names for this patient
        scan_names = []
        if patient.get('scans'):
            scan_names = [scan.get('name', 'Unknown') for scan in patient['scans']]
        
        # Format scan names for display
        if scan_names:
            scan_names_text = ', '.join(scan_names)
        else:
            scan_names_text = f"{patient['ct_scans']} scans"
        
        table_data.append({
            'Patient ID': patient['id'],
            'CT Scans': scan_names_text,
            'Voxel Files': patient['voxel_files'],
            'Mesh Files': patient['mesh_files'],
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
            "Mesh Files": st.column_config.NumberColumn("Mesh Files", width="small"),
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
            col1, col2, col3, col4, col5 = st.columns(5)
            
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
            
            with col4:
                # Calculate total meshes from all patients
                total_meshes = sum(patient.get('mesh_files', 0) for patient in patients)
                st.metric(
                    label="Total Meshes",
                    value=total_meshes,
                    help="Total number of mesh files across all patients"
                )
            
            with col5:
                st.metric(
                    label="Total Data Size",
                    value=stats.get('total_data_size', 'Unknown'),
                    help="Total size of all patient data"
                )
            
            # Patient Details Visualization
            render_patient_details_visualization(patients)
            
        
        elif error:
            st.error(f"❌ Analysis failed: {error}")
        else:
            st.warning("⚠️ No analysis data available")
    
    else:
        st.warning("⚠️ Image server is offline. Start the server to view data analysis.")
        st.code("python utils/image_server.py", language="bash")
    
    # Add workflow diagram after Image Data section
    st.markdown("---")
    render_workflow_section()
    

elif current_page == 'niivue':
    # Import and run NiiVue content
    sys.path.append(str(Path(__file__).parent))
    exec(open('NiiVue.py').read())
    

