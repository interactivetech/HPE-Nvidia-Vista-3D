#!/usr/bin/env python3
"""
STL Viewer: Interactive 3D STL File Viewer

A Streamlit application for viewing and analyzing STL (STereoLithography) files
with interactive 3D visualization, mesh statistics, and export capabilities.

Features:
- Upload and view STL files
- Interactive 3D visualization with rotation, zoom, and pan
- Mesh statistics and properties display
- Export to different formats
- Batch processing of multiple STL files

Dependencies:
    - streamlit: For the web interface
    - plotly: For 3D visualization
    - trimesh: For STL file processing
    - numpy: For numerical operations
    - pandas: For data display

Usage:
    streamlit run stl_viewer.py
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import trimesh
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import os
from typing import Dict, List, Tuple, Optional
import io


def load_stl_file(file_path: str) -> trimesh.Trimesh:
    """
    Load an STL file and return a trimesh object.
    
    Args:
        file_path (str): Path to the STL file
        
    Returns:
        trimesh.Trimesh: Loaded mesh object
    """
    try:
        mesh = trimesh.load(file_path)
        return mesh
    except Exception as e:
        st.error(f"Error loading STL file: {e}")
        return None


def get_mesh_info(mesh: trimesh.Trimesh) -> Dict:
    """
    Extract comprehensive information about a mesh.
    
    Args:
        mesh (trimesh.Trimesh): Mesh object
        
    Returns:
        Dict: Dictionary containing mesh statistics and properties
    """
    if mesh is None:
        return {}
    
    # Get basic mesh properties with error handling
    try:
        volume = mesh.volume
    except:
        volume = 0.0
    
    try:
        area = mesh.area
    except:
        area = 0.0
    
    try:
        is_watertight = mesh.is_watertight
    except:
        is_watertight = "Unknown"
    
    try:
        is_convex = mesh.is_convex
    except:
        is_convex = "Unknown"
    
    try:
        is_empty = mesh.is_empty
    except:
        is_empty = "Unknown"
    
    try:
        center_mass = mesh.center_mass
    except:
        center_mass = "Unknown"
    
    try:
        bounds = mesh.bounds
        bounding_box = f"{bounds[0]} to {bounds[1]}"
    except:
        bounding_box = "Unknown"
    
    info = {
        "Vertices": len(mesh.vertices),
        "Faces": len(mesh.faces),
        "Volume": f"{volume:.6f}",
        "Surface Area": f"{area:.6f}",
        "Bounding Box": bounding_box,
        "Center of Mass": f"{center_mass}",
        "Is Watertight": is_watertight,
        "Is Convex": is_convex,
        "Is Empty": is_empty,
        "Euler Characteristic": mesh.euler_number if hasattr(mesh, 'euler_number') else "N/A"
    }
    
    # Calculate additional metrics
    if len(mesh.vertices) > 0:
        info["Mean Vertex Distance"] = f"{np.mean(np.linalg.norm(mesh.vertices, axis=1)):.6f}"
        info["Max Vertex Distance"] = f"{np.max(np.linalg.norm(mesh.vertices, axis=1)):.6f}"
    
    return info


def create_3d_plot(mesh: trimesh.Trimesh, color: str = "lightblue", opacity: float = 0.8) -> go.Figure:
    """
    Create a 3D plotly visualization of the mesh.
    
    Args:
        mesh (trimesh.Trimesh): Mesh object to visualize
        color (str): Color for the mesh
        opacity (float): Opacity of the mesh (0-1)
        
    Returns:
        go.Figure: Plotly figure object
    """
    if mesh is None or len(mesh.vertices) == 0:
        return go.Figure()
    
    # Create the mesh plot
    fig = go.Figure(data=[
        go.Mesh3d(
            x=mesh.vertices[:, 0],
            y=mesh.vertices[:, 1],
            z=mesh.vertices[:, 2],
            i=mesh.faces[:, 0],
            j=mesh.faces[:, 1],
            k=mesh.faces[:, 2],
            color=color,
            opacity=opacity,
            lighting=dict(ambient=0.3, diffuse=0.8, specular=0.2),
            lightposition=dict(x=100, y=100, z=100)
        )
    ])
    
    # Update layout
    fig.update_layout(
        title="3D STL Mesh Visualization",
        scene=dict(
            xaxis_title="X",
            yaxis_title="Y",
            zaxis_title="Z",
            aspectmode="data",
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.5)
            )
        ),
        width=800,
        height=600
    )
    
    return fig


def create_wireframe_plot(mesh: trimesh.Trimesh, color: str = "red") -> go.Figure:
    """
    Create a wireframe visualization of the mesh.
    
    Args:
        mesh (trimesh.Trimesh): Mesh object to visualize
        color (str): Color for the wireframe
        
    Returns:
        go.Figure: Plotly figure object
    """
    if mesh is None or len(mesh.vertices) == 0:
        return go.Figure()
    
    # Create wireframe by plotting edges
    edges = mesh.edges_unique
    edge_x = []
    edge_y = []
    edge_z = []
    
    for edge in edges:
        x0, y0, z0 = mesh.vertices[edge[0]]
        x1, y1, z1 = mesh.vertices[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        edge_z.extend([z0, z1, None])
    
    fig = go.Figure(data=[
        go.Scatter3d(
            x=edge_x,
            y=edge_y,
            z=edge_z,
            mode='lines',
            line=dict(color=color, width=2),
            name='Wireframe'
        )
    ])
    
    fig.update_layout(
        title="STL Wireframe View",
        scene=dict(
            xaxis_title="X",
            yaxis_title="Y",
            zaxis_title="Z",
            aspectmode="data"
        ),
        width=800,
        height=600
    )
    
    return fig


def export_mesh_data(mesh: trimesh.Trimesh, format: str = "stl") -> bytes:
    """
    Export mesh data in the specified format.
    
    Args:
        mesh (trimesh.Trimesh): Mesh object to export
        format (str): Export format (stl, ply, obj)
        
    Returns:
        bytes: Exported mesh data
    """
    if mesh is None:
        return b""
    
    try:
        return mesh.export(file_type=format)
    except Exception as e:
        st.error(f"Error exporting mesh: {e}")
        return b""


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="STL Viewer",
        page_icon="🔺",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🔺 STL File Viewer")
    st.markdown("Interactive 3D visualization and analysis of STL files")
    
    # Sidebar for file upload and controls
    st.sidebar.header("File Upload")
    
    # File upload
    uploaded_file = st.sidebar.file_uploader(
        "Choose an STL file",
        type=['stl'],
        help="Upload an STL file to view and analyze"
    )
    
    # Load from existing files
    st.sidebar.header("Load Existing Files")
    existing_files = []
    
    # Check for STL files in common directories
    search_dirs = [
        "/Users/dave/AI/HPE/HPE-Nvidia-Vista-3D/output.mesh",
        "/Users/dave/AI/HPE/HPE-Nvidia-Vista-3D/output",
        "/Users/dave/AI/HPE/HPE-Nvidia-Vista-3D/extras"
    ]
    
    for search_dir in search_dirs:
        if os.path.exists(search_dir):
            for file_path in Path(search_dir).rglob("*.stl"):
                existing_files.append(str(file_path))
    
    if existing_files:
        selected_file = st.sidebar.selectbox(
            "Select existing STL file:",
            ["None"] + existing_files
        )
        
        if selected_file != "None":
            file_to_load = selected_file
        else:
            file_to_load = None
    else:
        file_to_load = None
    
    # Visualization controls
    st.sidebar.header("Visualization Controls")
    view_mode = st.sidebar.selectbox(
        "View Mode",
        ["Solid", "Wireframe", "Both"],
        help="Choose how to display the mesh"
    )
    
    mesh_color = st.sidebar.color_picker(
        "Mesh Color",
        value="#87CEEB",
        help="Color for the solid mesh"
    )
    
    opacity = st.sidebar.slider(
        "Opacity",
        min_value=0.1,
        max_value=1.0,
        value=0.8,
        step=0.1,
        help="Transparency of the mesh"
    )
    
    # Load mesh
    mesh = None
    if uploaded_file is not None:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.stl') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name
        
        mesh = load_stl_file(tmp_file_path)
        
        # Clean up temporary file
        os.unlink(tmp_file_path)
        
    elif file_to_load is not None:
        mesh = load_stl_file(file_to_load)
    
    # Main content area
    if mesh is not None:
        # Display mesh information
        st.header("Mesh Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            mesh_info = get_mesh_info(mesh)
            info_df = pd.DataFrame(list(mesh_info.items()), columns=['Property', 'Value'])
            st.dataframe(info_df, use_container_width=True)
        
        with col2:
            # Quick stats
            st.metric("Vertices", f"{len(mesh.vertices):,}")
            st.metric("Faces", f"{len(mesh.faces):,}")
            
            # Get volume and area with error handling
            try:
                volume = mesh.volume
            except:
                volume = 0.0
            
            try:
                area = mesh.area
            except:
                area = 0.0
            
            st.metric("Volume", f"{volume:.6f}")
            st.metric("Surface Area", f"{area:.6f}")
        
        # 3D Visualization
        st.header("3D Visualization")
        
        if view_mode in ["Solid", "Both"]:
            fig_solid = create_3d_plot(mesh, color=mesh_color, opacity=opacity)
            st.plotly_chart(fig_solid, use_container_width=True)
        
        if view_mode in ["Wireframe", "Both"]:
            fig_wireframe = create_wireframe_plot(mesh)
            st.plotly_chart(fig_wireframe, use_container_width=True)
        
        # Export options
        st.header("Export Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Export as STL"):
                stl_data = export_mesh_data(mesh, "stl")
                if stl_data:
                    st.download_button(
                        label="Download STL",
                        data=stl_data,
                        file_name="mesh.stl",
                        mime="application/octet-stream"
                    )
        
        with col2:
            if st.button("Export as PLY"):
                ply_data = export_mesh_data(mesh, "ply")
                if ply_data:
                    st.download_button(
                        label="Download PLY",
                        data=ply_data,
                        file_name="mesh.ply",
                        mime="application/octet-stream"
                    )
        
        with col3:
            if st.button("Export as OBJ"):
                obj_data = export_mesh_data(mesh, "obj")
                if obj_data:
                    st.download_button(
                        label="Download OBJ",
                        data=obj_data,
                        file_name="mesh.obj",
                        mime="application/octet-stream"
                    )
        
        # Advanced analysis
        st.header("Advanced Analysis")
        
        if st.checkbox("Show Bounding Box"):
            bbox = mesh.bounding_box
            bbox_vertices = bbox.vertices
            bbox_faces = bbox.faces
            
            bbox_fig = go.Figure(data=[
                go.Mesh3d(
                    x=bbox_vertices[:, 0],
                    y=bbox_vertices[:, 1],
                    z=bbox_vertices[:, 2],
                    i=bbox_faces[:, 0],
                    j=bbox_faces[:, 1],
                    k=bbox_faces[:, 2],
                    color="red",
                    opacity=0.3,
                    name="Bounding Box"
                ),
                go.Mesh3d(
                    x=mesh.vertices[:, 0],
                    y=mesh.vertices[:, 1],
                    z=mesh.vertices[:, 2],
                    i=mesh.faces[:, 0],
                    j=mesh.faces[:, 1],
                    k=mesh.faces[:, 2],
                    color=mesh_color,
                    opacity=opacity,
                    name="Mesh"
                )
            ])
            
            bbox_fig.update_layout(
                title="Mesh with Bounding Box",
                scene=dict(
                    xaxis_title="X",
                    yaxis_title="Y",
                    zaxis_title="Z",
                    aspectmode="data"
                ),
                width=800,
                height=600
            )
            
            st.plotly_chart(bbox_fig, use_container_width=True)
        
        if st.checkbox("Show Center of Mass"):
            try:
                center = mesh.center_mass
                st.write(f"Center of Mass: ({center[0]:.3f}, {center[1]:.3f}, {center[2]:.3f})")
                
                # Add center point to visualization
                center_fig = create_3d_plot(mesh, color=mesh_color, opacity=opacity)
                center_fig.add_trace(go.Scatter3d(
                    x=[center[0]],
                    y=[center[1]],
                    z=[center[2]],
                    mode='markers',
                    marker=dict(size=10, color='red'),
                    name='Center of Mass'
                ))
                
                st.plotly_chart(center_fig, use_container_width=True)
            except:
                st.write("Center of Mass: Unable to calculate")
    
    else:
        st.info("👆 Please upload an STL file or select an existing one from the sidebar to get started.")
        
        # Show example files if available
        if existing_files:
            st.subheader("Available STL Files")
            for file_path in existing_files[:5]:  # Show first 5 files
                st.write(f"• {file_path}")
            if len(existing_files) > 5:
                st.write(f"... and {len(existing_files) - 5} more files")


if __name__ == "__main__":
    main()
