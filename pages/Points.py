import streamlit as st
import os
import glob
from pathlib import Path
import open3d as o3d
import plotly.graph_objects as go
import numpy as np

st.set_page_config(layout="wide")

PROJECT_ROOT = Path(__file__).parent.parent
POINTS_BASE_DIR = PROJECT_ROOT / "outputs" / "points"

st.header("Point Cloud Viewer")

# Sidebar for controls
with st.sidebar:
    st.header("Controls")
    
    patient_folders = []
    if os.path.exists(POINTS_BASE_DIR):
        patient_folders = [f for f in os.listdir(POINTS_BASE_DIR) if os.path.isdir(POINTS_BASE_DIR / f)]
    
    selected_patient = st.selectbox("Select Patient", patient_folders)
    
    selected_file = None
    if selected_patient:
        folder_path = POINTS_BASE_DIR / selected_patient
        pcd_files = glob.glob(str(folder_path / "*.pcd"))
        
        pcd_filenames = [os.path.basename(f) for f in pcd_files]
        
        selected_file = st.selectbox("Select PCD File", pcd_filenames)

# Main area for viewer
if selected_file:
    file_path = POINTS_BASE_DIR / selected_patient / selected_file
    
    try:
        pcd = o3d.io.read_point_cloud(str(file_path))
        points = np.asarray(pcd.points)
        
        if pcd.has_colors():
            colors = np.asarray(pcd.colors)
        else:
            # Assign a default color if no colors are present in the PCD
            colors = np.array([[0.5, 0.5, 0.5]] * len(points)) # Grey

        fig = go.Figure(data=[go.Scatter3d(
            x=points[:,0], 
            y=points[:,1], 
            z=points[:,2],
            mode='markers',
            marker=dict(
                size=2,
                color=colors,
                opacity=0.8
            )
        )])

        fig.update_layout(margin=dict(l=0, r=0, b=0, t=0))
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error loading or displaying point cloud: {e}")
else:
    st.info("Select a patient and a PCD file to view.")
