import streamlit as st
import subprocess
import os
import sys
from pathlib import Path
import json
import pandas as pd
from typing import Dict, List, Optional
import time

# Add utils to path for imports
sys.path.append(str(Path(__file__).parent / 'utils'))

def run_command(command: List[str], description: str = "") -> tuple[bool, str, str]:
    """Run a command and return success status, stdout, and stderr."""
    try:
        result = subprocess.run(
            command, 
            capture_output=True, 
            text=True, 
            cwd=Path(__file__).parent,
            timeout=300  # 5 minute timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", f"Command timed out after 5 minutes"
    except Exception as e:
        return False, "", f"Error running command: {str(e)}"


def render_dicom_tools():
    """Render DICOM processing tools."""
    st.subheader("📋 DICOM Processing Tools")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**DICOM Inspector**")
        st.markdown("Inspect and analyze DICOM files")
        if st.button("Launch DICOM Inspector", key="dicom_inspector"):
            st.switch_page("pages/DICOM_Inspector.py")
    
    with col2:
        st.markdown("**DICOM to NIfTI Converter**")
        st.markdown("Convert DICOM files to NIfTI format")
        if st.button("Run DICOM2NIfTI", key="dicom2nifti"):
            with st.spinner("Converting DICOM files..."):
                success, stdout, stderr = run_command(
                    ["python", "utils/dicom2nifti.py"],
                    "DICOM to NIfTI conversion"
                )
                
                if success:
                    st.success("✅ DICOM conversion completed successfully!")
                    if stdout:
                        st.text_area("Output:", stdout, height=200)
                else:
                    st.error("❌ DICOM conversion failed!")
                    if stderr:
                        st.text_area("Error:", stderr, height=200)

def render_nifti_tools():
    """Render NIfTI processing tools."""
    st.subheader("🧠 NIfTI Processing Tools")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**NIfTI Viewer**")
        st.markdown("View NIfTI files with NiiVue")
        if st.button("Launch NiiVue Viewer", key="niivue_viewer"):
            st.switch_page("pages/NiiVue_Viewer.py")
    
    with col2:
        st.markdown("**NIfTI to PLY Converter**")
        st.markdown("Convert NIfTI files to PLY format")
        if st.button("Run NIfTI2PLY", key="nifti2ply"):
            with st.spinner("Converting NIfTI files to PLY..."):
                success, stdout, stderr = run_command(
                    ["python", "utils/nifti2ply.py"],
                    "NIfTI to PLY conversion"
                )
                
                if success:
                    st.success("✅ NIfTI to PLY conversion completed successfully!")
                    if stdout:
                        st.text_area("Output:", stdout, height=200)
                else:
                    st.error("❌ NIfTI to PLY conversion failed!")
                    if stderr:
                        st.text_area("Error:", stderr, height=200)

def render_3d_tools():
    """Render 3D visualization tools."""
    st.subheader("🔺 3D Visualization Tools")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Open3D Viewer**")
        st.markdown("View 3D meshes and point clouds")
        if st.button("Launch Open3D Viewer", key="open3d_viewer"):
            st.switch_page("pages/Open3d_Viewer.py")
    
    with col2:
        st.markdown("**Mesh Operations**")
        st.markdown("Process and manipulate 3D meshes")
        if st.button("Run Mesh Operations", key="mesh_ops"):
            with st.spinner("Running mesh operations..."):
                success, stdout, stderr = run_command(
                    ["python", "utils/mesh_operations.py"],
                    "Mesh operations"
                )
                
                if success:
                    st.success("✅ Mesh operations completed successfully!")
                    if stdout:
                        st.text_area("Output:", stdout, height=200)
                else:
                    st.error("❌ Mesh operations failed!")
                    if stderr:
                        st.text_area("Error:", stderr, height=200)

def render_segmentation_tools():
    """Render segmentation tools."""
    st.subheader("🎯 Segmentation Tools")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Vista3D Segmentation**")
        st.markdown("Run Vista3D segmentation on medical images")
        if st.button("Run Segmentation", key="segmentation"):
            with st.spinner("Running Vista3D segmentation..."):
                success, stdout, stderr = run_command(
                    ["python", "utils/segment.py"],
                    "Vista3D segmentation"
                )
                
                if success:
                    st.success("✅ Segmentation completed successfully!")
                    if stdout:
                        st.text_area("Output:", stdout, height=200)
                else:
                    st.error("❌ Segmentation failed!")
                    if stderr:
                        st.text_area("Error:", stderr, height=200)
    
    with col2:
        st.markdown("**Voxel Management**")
        st.markdown("Manage voxel data and processing")
        if st.button("Run Voxel Management", key="voxel_mgmt"):
            with st.spinner("Running voxel management..."):
                success, stdout, stderr = run_command(
                    ["python", "utils/voxel_manager.py"],
                    "Voxel management"
                )
                
                if success:
                    st.success("✅ Voxel management completed successfully!")
                    if stdout:
                        st.text_area("Output:", stdout, height=200)
                else:
                    st.error("❌ Voxel management failed!")
                    if stderr:
                        st.text_area("Error:", stderr, height=200)


def render_docker_tools():
    """Render Docker management tools."""
    st.subheader("🐳 Docker Management Tools")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Docker Compose Up**")
        st.markdown("Start all services with Docker Compose")
        if st.button("Start All Services", key="docker_up"):
            with st.spinner("Starting Docker services..."):
                success, stdout, stderr = run_command(
                    ["docker-compose", "up", "-d"],
                    "Docker Compose startup"
                )
                
                if success:
                    st.success("✅ Docker services started successfully!")
                    if stdout:
                        st.text_area("Output:", stdout, height=200)
                else:
                    st.error("❌ Failed to start Docker services!")
                    if stderr:
                        st.text_area("Error:", stderr, height=200)
    
    with col2:
        st.markdown("**Docker Compose Down**")
        st.markdown("Stop all Docker services")
        if st.button("Stop All Services", key="docker_down"):
            with st.spinner("Stopping Docker services..."):
                success, stdout, stderr = run_command(
                    ["docker-compose", "down"],
                    "Docker Compose shutdown"
                )
                
                if success:
                    st.success("✅ Docker services stopped successfully!")
                    if stdout:
                        st.text_area("Output:", stdout, height=200)
                else:
                    st.error("❌ Failed to stop Docker services!")
                    if stderr:
                        st.text_area("Error:", stderr, height=200)


def main():
    """Main function to render the Tools page."""
    st.set_page_config(
        page_title="Tools - HPE-NVIDIA Vista 3D",
        page_icon="🛠️",
        layout="wide"
    )
    
    st.title("🛠️ Tools & Utilities")
    st.markdown("Access various tools and utilities for medical image processing and 3D visualization.")
    
    st.markdown("---")
    
    # DICOM Inspector Section
    st.subheader("📋 DICOM Inspector")
    st.markdown("""
    The DICOM Inspector is a tool for examining and analyzing DICOM medical imaging files to
    help you understand the structure and content of your medical imaging data before processing.
    """)
    
    if st.button("🚀 Launch DICOM Inspector", key="launch_dicom_inspector", type="primary"):
        st.session_state.current_page = "dicom"
        st.rerun()

if __name__ == "__main__":
    main()
