#!/usr/bin/env python3
"""
PLY Viewer with Open3D: Advanced 3D PLY File Viewer

A comprehensive Streamlit application for viewing and analyzing PLY (Polygon File Format) files
using Open3D for advanced 3D processing and visualization capabilities.

Features:
- Upload and view PLY files with Open3D's advanced rendering
- Interactive 3D visualization with multiple view modes
- Mesh statistics and comprehensive analysis
- Export to multiple formats (PLY, STL, OBJ, OFF, XYZ)
- Point cloud processing and filtering
- Mesh quality analysis and repair tools
- Color and texture support
- Batch processing capabilities
- Integration with medical imaging pipeline
- Organized by patient and CT scan (similar to voxel structure)

Dependencies:
    - streamlit: For the web interface
    - open3d: For advanced 3D processing and visualization
    - plotly: For interactive 3D visualization
    - trimesh: For mesh processing and format conversion
    - numpy: For numerical operations
    - pandas: For data display
    - scipy: For scientific computing

Usage:
    streamlit run ply_viewer_open3d.py
"""

import streamlit as st
import open3d as o3d
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import tempfile
import os
import io
import requests
from typing import Dict, List, Tuple, Optional, Union
import trimesh
from scipy.spatial import cKDTree
import json
from dotenv import load_dotenv
from scipy.spatial.distance import cdist
from scipy.optimize import minimize
import math
from PIL import Image
import base64

# Import our data management modules
from utils.data_manager import DataManager
from utils.print3d_prep import Print3DPreparator, prepare_ply_for_printing, export_mesh_as_stl
from utils.mesh_operations import MeshProcessor, MeshVisualizer, optimize_mesh_for_performance

# PLY selection modes (similar to VOXEL_MODES)
PLY_MODES = ["Single PLY", "Multiple PLY Files"]


# Moved to utils/mesh_operations.py - MeshProcessor.load_ply_file()


# Moved to utils/mesh_operations.py - MeshProcessor.get_mesh_info()


# Moved to utils/mesh_operations.py - MeshVisualizer.create_multi_mesh_plot()


# Moved to utils/mesh_operations.py - MeshVisualizer.create_multi_mesh_plot() (single mesh case)


# Moved to utils/mesh_operations.py - MeshVisualizer.create_point_cloud_plot()


# Moved to utils/mesh_operations.py - MeshProcessor.analyze_mesh_quality()


# Moved to utils/mesh_operations.py - MeshProcessor.repair_mesh()


# Removed - unused function


# Moved to utils/mesh_operations.py - MeshVisualizer.create_statistics_plot()


# Removed unused analysis functions - moved to utils if needed










def render_ply_selection(selected_patient: str, selected_file: str, data_manager: DataManager, IMAGE_SERVER_URL: str):
    """Render the PLY selection interface similar to voxel selection."""
    with st.sidebar.expander("Select PLY Files", expanded=True):
        # PLY selection mode
        ply_mode = st.radio(
            "Choose PLY selection mode:",
            PLY_MODES,
            index=0,
            help="Select how you want to choose which PLY files to display"
        )
        
        selected_ply_files = []
        file_to_load = None
        
        if ply_mode == "Single PLY":
            # Get PLY files from the CT scan's subfolder within ply directory
            if selected_patient and selected_file:
                ct_scan_folder_name = selected_file.replace('.nii.gz', '').replace('.nii', '')
                ply_files = data_manager.get_server_data(f"{selected_patient}/ply/{ct_scan_folder_name}", 'files', ('.ply',))
                
                if ply_files:
                    # Create display names without .ply extensions
                    display_names = [filename.replace('.ply', '') for filename in ply_files]
                    selected_display_name = st.selectbox(
                        "Choose a single PLY file:",
                        ["None"] + display_names,
                        help="Choose a PLY file from the selected CT scan"
                    )
                    
                    if selected_display_name != "None":
                        # Map back to the actual filename
                        selected_index = display_names.index(selected_display_name)
                        selected_ply_file = ply_files[selected_index]
                        output_folder = os.getenv('OUTPUT_FOLDER', 'output')
                        file_to_load = f"{IMAGE_SERVER_URL}/{output_folder}/{selected_patient}/ply/{ct_scan_folder_name}/{selected_ply_file}"
                        selected_ply_files = [selected_ply_file]
                        
                else:
                    st.warning(f"No PLY files found for CT scan: {ct_scan_folder_name}")
                    output_folder = os.getenv('OUTPUT_FOLDER', 'output')
                    ply_url = f"{IMAGE_SERVER_URL}/{output_folder}/{selected_patient}/ply/{ct_scan_folder_name}/"
                    st.caption(f"PLY directory: {ply_url}")
        
        elif ply_mode == "Multiple PLY Files":
            if selected_patient and selected_file:
                ct_scan_folder_name = selected_file.replace('.nii.gz', '').replace('.nii', '')
                ply_files = data_manager.get_server_data(f"{selected_patient}/ply/{ct_scan_folder_name}", 'files', ('.ply',))
                
                if ply_files:
                    # Create display names without .ply extensions
                    display_names = [filename.replace('.ply', '') for filename in ply_files]
                    selected_display_names = st.multiselect(
                        "Choose multiple PLY files to overlay:",
                        display_names,
                        default=[],
                        help="Select specific PLY files to display together"
                    )
                    
                    # Map back to actual filenames
                    selected_ply_files = []
                    for display_name in selected_display_names:
                        selected_index = display_names.index(display_name)
                        selected_ply_files.append(ply_files[selected_index])
                    
                    # Display selection status
                    if selected_ply_files:
                        st.info(f"Will display {len(selected_ply_files)} PLY files from the PLY directory.")
                        if len(selected_ply_files) > 5:
                            st.warning("⚠️ Selecting many PLY files may cause slow loading. Consider selecting fewer files for better performance.")
                    else:
                        st.info("No PLY files selected. Select specific files to display.")
                else:
                    st.warning(f"No PLY files found for CT scan: {ct_scan_folder_name}")
                    output_folder = os.getenv('OUTPUT_FOLDER', 'output')
                    ply_url = f"{IMAGE_SERVER_URL}/{output_folder}/{selected_patient}/ply/{ct_scan_folder_name}/"
                    st.caption(f"PLY directory: {ply_url}")
            else:
                st.info("Please select a patient and CT scan first.")
    
    return ply_mode, selected_ply_files, file_to_load


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="Open3D Viewer",
        page_icon="🔺",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🔺 Open3D Viewer")
    
    # Initialize managers
    load_dotenv()
    IMAGE_SERVER_URL = os.getenv('IMAGE_SERVER', 'http://localhost:8888')
    data_manager = DataManager(IMAGE_SERVER_URL)
    mesh_processor = MeshProcessor()
    mesh_visualizer = MeshVisualizer()
    
    
    # Patient folder selection
    
    # Get patient folders using DataManager (same as NiiVue_Viewer.py)
    patient_folders = data_manager.get_server_data('', 'folders', ('',))
    
    selected_patient = None
    selected_file = None
    
    if patient_folders:
        selected_patient = st.sidebar.selectbox(
            "Select Patient:",
            ["None"] + patient_folders,
            help="Choose a patient folder that contains PLY files"
        )
        
        if selected_patient != "None":
            # Get NIfTI files to determine available CT scans (same as NiiVue_Viewer.py)
            filenames = data_manager.get_server_data(f"{selected_patient}/nifti", 'files', ('.nii.gz', '.nii'))
            
            # Create display names without .nii.gz extensions (same as NiiVue_Viewer.py)
            if filenames:
                display_names = [
                    filename.replace('.nii.gz', '').replace('.nii', '').replace('.dcm', '')
                    for filename in filenames
                ]
                selected_display_name = st.sidebar.selectbox(
                    "Select CT Scan:",
                    ["None"] + display_names,
                    help="Choose a CT scan to view its PLY files"
                )
                
                # Map back to the actual filename
                if selected_display_name != "None":
                    selected_index = display_names.index(selected_display_name)
                    selected_file = filenames[selected_index]
                else:
                    selected_file = None
            else:
                st.sidebar.warning("No NIfTI files found in this patient folder")
                selected_file = None
        else:
            selected_file = None
    else:
        st.sidebar.warning("No patient folders found")
        selected_file = None
    
    # If no file selected yet, show guidance and stop
    if not selected_file:
        st.info("Select a patient and file to begin.")
        return

    # PLY file selection (similar to voxel selection)
    ply_mode, selected_ply_files, file_to_load = render_ply_selection(selected_patient, selected_file, data_manager, IMAGE_SERVER_URL)
    
    
    # Visualization controls
    st.sidebar.header("Visualization Controls")
    view_mode = st.sidebar.selectbox(
        "View Mode",
        ["Solid", "Point Cloud", "Statistics", "Simple"],
        help="Choose how to display the mesh"
    )
    
    
    mesh_color = st.sidebar.color_picker(
        "Mesh Color",
        value="#10CE61",
        help="Color for the solid mesh (if no vertex colors)"
    )
    
    opacity = st.sidebar.slider(
        "Opacity",
        min_value=0.1,
        max_value=1.0,
        value=0.8,
        step=0.1,
        help="Transparency of the mesh"
    )
    
    point_size = st.sidebar.slider(
        "Point Size",
        min_value=1,
        max_value=10,
        value=3,
        help="Size of points in point cloud view"
    )
    
    point_sample_ratio = st.sidebar.slider(
        "Point Sample Ratio",
        min_value=0.01,
        max_value=1.0,
        value=1.0,
        step=0.01,
        help="Ratio of points to display (for performance)"
    )
    
    # Processing options
    st.sidebar.header("Processing Options")
    repair_mesh = st.sidebar.checkbox(
        "Auto-repair mesh",
        value=True,
        help="Automatically repair common mesh issues"
    )
    
    compute_normals = st.sidebar.checkbox(
        "Compute vertex normals",
        value=True,
        help="Compute vertex normals for better rendering"
    )
    
    
    
    show_center_mass = st.sidebar.checkbox(
        "Show Center of Mass",
        value=False,
        help="Display the center of mass point"
    )
    
    show_color_analysis = st.sidebar.checkbox(
        "Show Color Analysis",
        value=False,
        help="Display color distribution and statistics"
    )
    
    # 3D Printing Preparation
    st.sidebar.header("3D Printing Preparation")
    enable_3d_print_prep = st.sidebar.checkbox(
        "Enable 3D Print Preparation",
        value=False,
        help="Prepare meshes for 3D printing (repair, scale, optimize)"
    )
    
    if enable_3d_print_prep:
        target_size_mm = st.sidebar.number_input(
            "Target Size (mm)",
            min_value=10.0,
            max_value=500.0,
            value=100.0,
            step=5.0,
            help="Target maximum dimension in millimeters"
        )
        
        min_wall_thickness = st.sidebar.number_input(
            "Min Wall Thickness (mm)",
            min_value=0.1,
            max_value=5.0,
            value=0.8,
            step=0.1,
            help="Minimum wall thickness for 3D printing"
        )
        
        combine_meshes = st.sidebar.checkbox(
            "Combine Multiple Meshes",
            value=False,
            help="Combine multiple PLY files into a single printable object"
        )
        
        export_stl = st.sidebar.button(
            "🖨️ Export STL for 3D Printing",
            help="Export prepared mesh(es) as STL files ready for 3D printing"
        )
    
    
    # Load mesh(es)
    # Read the upload value from session state since the uploader widget is rendered later
    uploaded_file = st.session_state.get('ply_uploader', None)
    meshes = []  # List of (mesh, name, color) tuples
    metadata = {}
    processed_meshes = []  # Always define to avoid UnboundLocalError
    
    
    if uploaded_file is not None:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ply') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name
        
        mesh, metadata = mesh_processor.load_ply_file(tmp_file_path)
        if mesh is not None and not mesh.is_empty():
            meshes = [(mesh, uploaded_file.name, mesh_color)]
        
        # Clean up temporary file
        os.unlink(tmp_file_path)
        
    elif ply_mode == "Single PLY" and file_to_load is not None:
        # Show loading indicator for single PLY
        # Attempting to load single PLY file
        with st.spinner(f"Loading PLY file: {selected_ply_files[0] if selected_ply_files else 'Single PLY'}"):
            try:
                mesh, metadata = mesh_processor.load_ply_file(file_to_load)
                if mesh is not None and not mesh.is_empty():
                    # Simplify mesh if it's too complex for better performance
                    vertex_count = len(mesh.vertices)
                    triangle_count = len(mesh.triangles)
                    
                    # Optimize mesh for performance
                    mesh = optimize_mesh_for_performance(mesh)
                    
                    meshes = [(mesh, selected_ply_files[0] if selected_ply_files else "Single PLY", mesh_color)]
                else:
                    st.error("Failed to load PLY file or mesh is empty")
            except Exception as e:
                st.error(f"Error loading PLY file: {str(e)}")
                st.info("Please check if the file exists and is a valid PLY file")
    elif ply_mode == "Single PLY" and file_to_load is None:
        st.info("Please select a PLY file to load it.")
    
    elif ply_mode == "Multiple PLY Files" and selected_ply_files:
        # Load multiple PLY files with progress indicator
        ct_scan_folder_name = selected_file.replace('.nii.gz', '').replace('.nii', '') if selected_file else ""
        
        # Define colors for different PLY files
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F']
        
        for i, ply_file in enumerate(selected_ply_files):
            try:
                output_folder = os.getenv('OUTPUT_FOLDER', 'output')
                file_url = f"{IMAGE_SERVER_URL}/{output_folder}/{selected_patient}/ply/{ct_scan_folder_name}/{ply_file}"
                mesh, _ = mesh_processor.load_ply_file(file_url)
                
                if mesh is not None and not mesh.is_empty():
                    # Simplify mesh only for very large meshes
                    vertex_count = len(mesh.vertices)
                    triangle_count = len(mesh.triangles)
                    # Optimize mesh for performance
                    mesh = optimize_mesh_for_performance(mesh)
                    
                    color = colors[i % len(colors)]  # Cycle through colors
                    meshes.append((mesh, ply_file, color))
                else:
                    st.warning(f"Failed to load or empty mesh: {ply_file}")
                    
            except Exception as e:
                st.error(f"Error loading {ply_file}: {str(e)}")
                continue
        
        if not meshes:
            st.error("No PLY files could be loaded")
    
    # Process meshes if loaded
    if meshes:
        # Apply processing options to all meshes
        processed_meshes = []
        print_reports = []
        
        for mesh, name, color in meshes:
            if mesh is not None and not mesh.is_empty():
                if repair_mesh:
                    mesh = mesh_processor.repair_mesh(mesh)
                
                if compute_normals and len(mesh.vertex_normals) == 0:
                    mesh.compute_vertex_normals()
                
                # Apply 3D printing preparation if enabled
                if enable_3d_print_prep:
                    with st.spinner(f"Preparing {name} for 3D printing..."):
                        preparator = Print3DPreparator(target_size_mm, min_wall_thickness)
                        mesh, print_report = preparator.prepare_mesh_for_printing(mesh, name)
                        print_reports.append(print_report)
                
                processed_meshes.append((mesh, name, color))
        
        # Handle mesh combination for 3D printing
        if enable_3d_print_prep and combine_meshes and len(processed_meshes) > 1:
            with st.spinner("Combining meshes for 3D printing..."):
                preparator = Print3DPreparator(target_size_mm, min_wall_thickness)
                mesh_list = [(mesh, name) for mesh, name, _ in processed_meshes]
                combined_meshes, combined_report = preparator.prepare_multiple_meshes(mesh_list, combine_meshes=True)
                
                if combined_meshes:
                    # Use the first color for the combined mesh
                    combined_color = processed_meshes[0][2] if processed_meshes else mesh_color
                    processed_meshes = [(mesh, name, combined_color) for mesh, name in combined_meshes]
                    print_reports.append(combined_report)
        
    
    # File upload section at the bottom
    st.sidebar.header("File Upload")
    
    # File upload
    uploaded_file = st.sidebar.file_uploader(
        "Choose a PLY file",
        type=['ply'],
        help="Upload a PLY file to view and analyze with Open3D",
        key="ply_uploader"
    )
    
    # Show detailed mesh information
    with st.expander("Detailed Mesh Information"):
        if len(processed_meshes) == 1:
            # Single mesh - show detailed info
            mesh, name, color = processed_meshes[0]
            mesh_info = mesh_processor.get_mesh_info(mesh)
            if mesh_info:
                detailed_info = pd.DataFrame([
                    {"Property": "File Size", "Value": f"{metadata.get('file_size', 0) / 1024:.1f} KB"},
                    {"Property": "Vertices", "Value": mesh_info.get("Vertices", "N/A")},
                    {"Property": "Triangles", "Value": mesh_info.get("Triangles", "N/A")},
                    {"Property": "Volume", "Value": mesh_info.get("Volume", "N/A")},
                    {"Property": "Surface Area", "Value": mesh_info.get("Surface Area", "N/A")},
                    {"Property": "Is Watertight", "Value": mesh_info.get("Is Watertight", "N/A")},
                    {"Property": "Is Orientable", "Value": mesh_info.get("Is Orientable", "N/A")},
                    {"Property": "Has Vertex Colors", "Value": mesh_info.get("Has Vertex Colors", "N/A")},
                    {"Property": "Has Vertex Normals", "Value": mesh_info.get("Has Vertex Normals", "N/A")},
                ])
                st.dataframe(detailed_info, use_container_width=True, hide_index=True)
        else:
            # Multiple meshes - show summary table
            summary_data = []
            for mesh, name, color in processed_meshes:
                mesh_info = mesh_processor.get_mesh_info(mesh)
                summary_data.append({
                    "File": name,
                    "Vertices": mesh_info.get("Vertices", "N/A"),
                    "Triangles": mesh_info.get("Triangles", "N/A"),
                    "Volume": mesh_info.get("Volume", "N/A"),
                    "Surface Area": mesh_info.get("Surface Area", "N/A"),
                    "Is Watertight": mesh_info.get("Is Watertight", "N/A"),
                    "Color": color
                })
            
            if summary_data:
                summary_df = pd.DataFrame(summary_data)
                st.dataframe(summary_df, use_container_width=True, hide_index=True)
    
    # 3D Printing Preparation Reports
    if enable_3d_print_prep and print_reports:
        with st.expander("3D Printing Preparation Report", expanded=True):
            for i, report in enumerate(print_reports):
                if isinstance(report, dict) and "mesh_name" in report:
                    st.subheader(f"Mesh: {report['mesh_name']}")
                    
                    # Validation summary
                    validation = report.get("validation", {})
                    if validation:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            score = validation.get("printability_score", 0)
                            if score >= 8:
                                st.success(f"Printability Score: {score}/10")
                            elif score >= 6:
                                st.info(f"Printability Score: {score}/10")
                            else:
                                st.warning(f"Printability Score: {score}/10")
                        
                        with col2:
                            if validation.get("is_watertight", False):
                                st.success("✅ Watertight")
                            else:
                                st.error("❌ Not Watertight")
                        
                        with col3:
                            triangle_count = validation.get("triangle_count", 0)
                            st.info(f"Triangles: {triangle_count:,}")
                    
                    # Scaling info
                    scaling = report.get("scaling", {})
                    if scaling:
                        st.write(f"**Scaled by factor:** {scaling.get('scale_factor', 0):.3f}")
                        dimensions = scaling.get("new_dimensions_mm", {})
                        st.write(f"**Final size:** {dimensions.get('x', 0):.1f} × {dimensions.get('y', 0):.1f} × {dimensions.get('z', 0):.1f} mm")
                    
                    # Warnings and recommendations
                    if validation.get("warnings"):
                        st.warning("**Warnings:**")
                        for warning in validation["warnings"]:
                            st.write(f"• {warning}")
                    
                    if validation.get("recommendations"):
                        st.info("**Recommendations:**")
                        for rec in validation["recommendations"]:
                            st.write(f"• {rec}")
                    
                    st.divider()
    
    # STL Export functionality
    if enable_3d_print_prep and export_stl and processed_meshes:
        st.header("STL Export for 3D Printing")
        
        export_success = []
        export_files = []
        
        with st.spinner("Exporting STL files..."):
            for mesh, name, color in processed_meshes:
                # Create safe filename
                safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                safe_name = safe_name.replace(' ', '_')
                if not safe_name:
                    safe_name = "mesh"
                
                # Create STL filename
                stl_filename = f"{safe_name}_3d_print_ready.stl"
                
                # Export as bytes for download
                try:
                    # Create temporary file
                    with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as tmp_file:
                        tmp_path = tmp_file.name
                    
                    # Export STL
                    success = export_mesh_as_stl(mesh, tmp_path)
                    
                    if success:
                        # Read file for download
                        with open(tmp_path, 'rb') as f:
                            stl_data = f.read()
                        
                        export_files.append((stl_filename, stl_data))
                        export_success.append(f"✅ {name} → {stl_filename}")
                    else:
                        export_success.append(f"❌ Failed to export {name}")
                    
                    # Clean up
                    os.unlink(tmp_path)
                    
                except Exception as e:
                    export_success.append(f"❌ Error exporting {name}: {str(e)}")
        
        # Show export results
        for result in export_success:
            if "✅" in result:
                st.success(result)
            else:
                st.error(result)
        
        # Provide download buttons
        if export_files:
            st.subheader("Download STL Files")
            for filename, stl_data in export_files:
                st.download_button(
                    label=f"📥 Download {filename}",
                    data=stl_data,
                    file_name=filename,
                    mime="application/octet-stream",
                    help=f"Download {filename} ready for 3D printing"
                )
            
            # Show file info
            total_size = sum(len(data) for _, data in export_files)
            st.info(f"Total files: {len(export_files)} | Total size: {total_size/1024:.1f} KB")
        
        st.success("🖨️ STL files are ready for 3D printing! Import them into your slicer software.")
    
    # 3D Visualization
    if processed_meshes:
        # Performance warning for very large meshes
        total_triangles = sum(len(mesh.triangles) for mesh, _, _ in processed_meshes)
        if total_triangles > 200000:
            st.error("Mesh too complex! Maximum 200,000 triangles allowed.")
            st.stop()
        
        with st.spinner("Rendering 3D visualization..."):
            try:
                if view_mode == "Solid":
                    fig = mesh_visualizer.create_multi_mesh_plot(processed_meshes, opacity=opacity)
                    st.plotly_chart(fig, use_container_width=True)
                
                elif view_mode == "Point Cloud":
                    # For point cloud, we'll show the first mesh only for now
                    if processed_meshes:
                        mesh, name, color = processed_meshes[0]
                        fig = mesh_visualizer.create_point_cloud_plot(mesh, color=color, size=point_size, 
                                                           sample_ratio=point_sample_ratio)
                        st.plotly_chart(fig, use_container_width=True)
                        if len(processed_meshes) > 1:
                            st.info(f"Point cloud view showing only the first mesh: {name}")
                
                elif view_mode == "Statistics":
                    # For statistics, we'll show the first mesh only for now
                    if processed_meshes:
                        mesh, name, color = processed_meshes[0]
                        fig = mesh_visualizer.create_statistics_plot(mesh)
                        st.plotly_chart(fig, use_container_width=True)
                        if len(processed_meshes) > 1:
                            st.info(f"Statistics view showing only the first mesh: {name}")
                
                elif view_mode == "Simple":
                    # Simple mode - point cloud visualization
                    if processed_meshes:
                        fig = mesh_visualizer.create_simple_plot(processed_meshes)
                        st.plotly_chart(fig, use_container_width=True)
                
            
            except Exception as e:
                st.error(f"Error rendering 3D visualization: {str(e)}")
                st.info("Try reducing the number of PLY files or simplifying the meshes.")
    else:
        st.info("No PLY files loaded. Please select a PLY file to display.")
        
        
        # Advanced analysis - Center of Mass
        if show_center_mass:
            st.header("Advanced Analysis")
            
            if show_center_mass:
                try:
                    if len(processed_meshes) == 1:
                        # Single mesh
                        mesh, name, color = processed_meshes[0]
                        center = mesh.get_center()
                        st.write(f"Center of Mass: ({center[0]:.3f}, {center[1]:.3f}, {center[2]:.3f})")
                        
                        # Add center point to visualization
                        center_fig = mesh_visualizer.create_multi_mesh_plot(processed_meshes, opacity=opacity)
                        center_fig.add_trace(go.Scatter3d(
                            x=[center[0]],
                            y=[center[1]],
                            z=[center[2]],
                            mode='markers',
                            marker=dict(size=10, color='red'),
                            name='Center of Mass'
                        ))
                        
                        st.plotly_chart(center_fig, use_container_width=True)
                    else:
                        # Multiple meshes - show centers for all
                        centers_data = []
                        center_fig = mesh_visualizer.create_multi_mesh_plot(processed_meshes, opacity=opacity)
                        
                        for i, (mesh, name, color) in enumerate(processed_meshes):
                            center = mesh.get_center()
                            centers_data.append({
                                "File": name,
                                "Center X": f"{center[0]:.3f}",
                                "Center Y": f"{center[1]:.3f}",
                                "Center Z": f"{center[2]:.3f}"
                            })
                            
                            # Add center point to visualization
                            center_fig.add_trace(go.Scatter3d(
                                x=[center[0]],
                                y=[center[1]],
                                z=[center[2]],
                                mode='markers',
                                marker=dict(size=10, color='red'),
                                name=f'{name} Center'
                            ))
                        
                        # Show centers table
                        centers_df = pd.DataFrame(centers_data)
                        st.dataframe(centers_df, use_container_width=True, hide_index=True)
                        
                        st.plotly_chart(center_fig, use_container_width=True)
                except:
                    st.write("Center of Mass: Unable to calculate")
        
        # Color analysis
        if show_color_analysis and processed_meshes:
            st.header("Color Analysis")
            
            # Check if any mesh has vertex colors
            has_colors = any(len(mesh.vertex_colors) > 0 for mesh, _, _ in processed_meshes)
            
            if has_colors:
                try:
                    if len(processed_meshes) == 1:
                        # Single mesh with colors
                        mesh, name, color = processed_meshes[0]
                        if len(mesh.vertex_colors) > 0:
                            colors = np.asarray(mesh.vertex_colors)
                            if len(colors) > 0 and colors.shape[1] >= 3:
                                # Create color histogram
                                fig_hist = go.Figure()
                                
                                color_names = ['Red', 'Green', 'Blue']
                                if colors.shape[1] >= 4:
                                    color_names.append('Alpha')
                                
                                for i, color_name in enumerate(color_names):
                                    if i < colors.shape[1]:
                                        fig_hist.add_trace(go.Histogram(
                                            x=colors[:, i],
                                            name=color_name,
                                            opacity=0.7
                                        ))
                                
                                fig_hist.update_layout(
                                    title="Color Distribution",
                                    xaxis_title="Color Value",
                                    yaxis_title="Frequency",
                                    barmode='overlay'
                                )
                                
                                st.plotly_chart(fig_hist, use_container_width=True)
                                
                                # Color statistics
                                col_stats = {
                                    "Mean Red": f"{np.mean(colors[:, 0]):.3f}",
                                    "Mean Green": f"{np.mean(colors[:, 1]):.3f}",
                                    "Mean Blue": f"{np.mean(colors[:, 2]):.3f}",
                                    "Std Red": f"{np.std(colors[:, 0]):.3f}",
                                    "Std Green": f"{np.std(colors[:, 1]):.3f}",
                                    "Std Blue": f"{np.std(colors[:, 2]):.3f}"
                                }
                                
                                if colors.shape[1] >= 4:
                                    col_stats["Mean Alpha"] = f"{np.mean(colors[:, 3]):.3f}"
                                    col_stats["Std Alpha"] = f"{np.std(colors[:, 3]):.3f}"
                                
                                col_df = pd.DataFrame(list(col_stats.items()), columns=['Color Statistic', 'Value'])
                                st.dataframe(col_df, use_container_width=True)
                            else:
                                st.info("Color data is not in the expected format (RGB values).")
                        else:
                            st.info("This mesh does not have vertex colors.")
                    else:
                        # Multiple meshes - show which ones have colors
                        color_info = []
                        for mesh, name, color in processed_meshes:
                            has_vertex_colors = len(mesh.vertex_colors) > 0
                            color_info.append({
                                "File": name,
                                "Has Vertex Colors": has_vertex_colors,
                                "Assigned Color": color
                            })
                        
                        color_df = pd.DataFrame(color_info)
                        st.dataframe(color_df, use_container_width=True, hide_index=True)
                        
                        if not any(len(mesh.vertex_colors) > 0 for mesh, _, _ in processed_meshes):
                            st.info("None of the selected meshes have vertex colors.")
                except Exception as e:
                    st.error(f"Error analyzing colors: {e}")
            else:
                st.info("None of the selected meshes have vertex colors.")
        
        # (Enhanced Geometric Analysis removed per request)
    
    # If no meshes are available, guide the user
    


if __name__ == "__main__":
    main()
