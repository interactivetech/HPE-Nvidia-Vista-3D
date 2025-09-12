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

# Import our data management modules
from utils.data_manager import DataManager


def load_ply_file_open3d(file_path: str) -> Tuple[o3d.geometry.TriangleMesh, Dict]:
    """
    Load a PLY file using Open3D and return mesh with metadata.
    Supports both local file paths and HTTP URLs.
    
    Args:
        file_path (str): Path to the PLY file (local path or HTTP URL)
        
    Returns:
        Tuple[o3d.geometry.TriangleMesh, Dict]: Mesh object and metadata
    """
    try:
        # Check if it's an HTTP URL
        if file_path.startswith('http'):
            # Download the file to a temporary location
            response = requests.get(file_path, timeout=30)
            response.raise_for_status()
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.ply') as tmp_file:
                tmp_file.write(response.content)
                local_file_path = tmp_file.name
            
            # Load mesh using Open3D from local file
            mesh = o3d.io.read_triangle_mesh(local_file_path)
            
            # Get file size from response
            file_size = len(response.content)
            
            # Clean up temporary file
            os.unlink(local_file_path)
        else:
            # Local file path
            mesh = o3d.io.read_triangle_mesh(file_path)
            file_size = os.path.getsize(file_path)
        
        # Get metadata
        metadata = {
            "file_path": file_path,
            "file_size": file_size,
            "has_vertices": len(mesh.vertices) > 0,
            "has_faces": len(mesh.triangles) > 0,
            "has_vertex_colors": len(mesh.vertex_colors) > 0,
            "has_vertex_normals": len(mesh.vertex_normals) > 0,
            "is_empty": mesh.is_empty(),
            "is_watertight": mesh.is_watertight(),
            "is_orientable": mesh.is_orientable(),
            "is_self_intersecting": mesh.is_self_intersecting()
        }
        
        return mesh, metadata
        
    except Exception as e:
        st.error(f"Error loading PLY file with Open3D: {e}")
        return None, {}


def get_open3d_mesh_info(mesh: o3d.geometry.TriangleMesh) -> Dict:
    """
    Extract comprehensive information about an Open3D mesh.
    
    Args:
        mesh (o3d.geometry.TriangleMesh): Open3D mesh object
        
    Returns:
        Dict: Dictionary containing mesh statistics and properties
    """
    if mesh is None or mesh.is_empty():
        return {}
    
    # Basic properties
    vertices = np.asarray(mesh.vertices)
    triangles = np.asarray(mesh.triangles)
    
    # Calculate geometric properties
    try:
        volume = mesh.get_volume()
    except:
        volume = 0.0
    
    try:
        surface_area = mesh.get_surface_area()
    except:
        surface_area = 0.0
    
    # Bounding box
    bbox = mesh.get_axis_aligned_bounding_box()
    bbox_min = bbox.min_bound
    bbox_max = bbox.max_bound
    bbox_size = bbox_max - bbox_min
    
    # Center of mass
    try:
        center_mass = mesh.get_center()
    except:
        center_mass = np.mean(vertices, axis=0) if len(vertices) > 0 else np.array([0, 0, 0])
    
    # Color information
    has_vertex_colors = len(mesh.vertex_colors) > 0
    has_vertex_normals = len(mesh.vertex_normals) > 0
    
    # Calculate additional metrics
    info = {
        "Vertices": len(vertices),
        "Triangles": len(triangles),
        "Volume": f"{volume:.6f}",
        "Surface Area": f"{surface_area:.6f}",
        "Bounding Box Min": f"({bbox_min[0]:.3f}, {bbox_min[1]:.3f}, {bbox_min[2]:.3f})",
        "Bounding Box Max": f"({bbox_max[0]:.3f}, {bbox_max[1]:.3f}, {bbox_max[2]:.3f})",
        "Bounding Box Size": f"({bbox_size[0]:.3f}, {bbox_size[1]:.3f}, {bbox_size[2]:.3f})",
        "Center of Mass": f"({center_mass[0]:.3f}, {center_mass[1]:.3f}, {center_mass[2]:.3f})",
        "Is Watertight": mesh.is_watertight(),
        "Is Orientable": mesh.is_orientable(),
        "Is Self-Intersecting": mesh.is_self_intersecting(),
        "Has Vertex Colors": has_vertex_colors,
        "Has Vertex Normals": has_vertex_normals,
        "Is Empty": mesh.is_empty()
    }
    
    # Calculate mesh quality metrics
    if len(vertices) > 0:
        # Vertex statistics
        vertex_distances = np.linalg.norm(vertices, axis=1)
        info["Mean Vertex Distance"] = f"{np.mean(vertex_distances):.6f}"
        info["Max Vertex Distance"] = f"{np.max(vertex_distances):.6f}"
        info["Min Vertex Distance"] = f"{np.min(vertex_distances):.6f}"
        
        # Mesh density
        if surface_area > 0:
            info["Vertex Density"] = f"{len(vertices) / surface_area:.2f} vertices/unit²"
            info["Triangle Density"] = f"{len(triangles) / surface_area:.2f} triangles/unit²"
        
        # Edge length statistics
        if len(triangles) > 0:
            edges = []
            for triangle in triangles:
                edges.extend([
                    np.linalg.norm(vertices[triangle[1]] - vertices[triangle[0]]),
                    np.linalg.norm(vertices[triangle[2]] - vertices[triangle[1]]),
                    np.linalg.norm(vertices[triangle[0]] - vertices[triangle[2]])
                ])
            
            if edges:
                info["Mean Edge Length"] = f"{np.mean(edges):.6f}"
                info["Max Edge Length"] = f"{np.max(edges):.6f}"
                info["Min Edge Length"] = f"{np.min(edges):.6f}"
    
    return info


def create_open3d_3d_plot(mesh: o3d.geometry.TriangleMesh, color: str = "lightblue", 
                         opacity: float = 0.8, show_wireframe: bool = False) -> go.Figure:
    """
    Create a 3D plotly visualization of the Open3D mesh.
    
    Args:
        mesh (o3d.geometry.TriangleMesh): Open3D mesh object
        color (str): Default color for the mesh
        opacity (float): Opacity of the mesh (0-1)
        show_wireframe (bool): Whether to show wireframe overlay
        
    Returns:
        go.Figure: Plotly figure object
    """
    if mesh is None or mesh.is_empty():
        return go.Figure()
    
    vertices = np.asarray(mesh.vertices)
    triangles = np.asarray(mesh.triangles)
    
    # Check for vertex colors
    has_vertex_colors = len(mesh.vertex_colors) > 0
    
    if has_vertex_colors:
        vertex_colors = np.asarray(mesh.vertex_colors)
        # Calculate average color for the mesh
        avg_color = np.mean(vertex_colors, axis=0)
        colors = f"rgb({int(avg_color[0]*255)},{int(avg_color[1]*255)},{int(avg_color[2]*255)})"
    else:
        colors = color
    
    # Create the mesh plot
    fig = go.Figure(data=[
        go.Mesh3d(
            x=vertices[:, 0],
            y=vertices[:, 1],
            z=vertices[:, 2],
            i=triangles[:, 0],
            j=triangles[:, 1],
            k=triangles[:, 2],
            color=colors,
            opacity=opacity,
            lighting=dict(ambient=0.3, diffuse=0.8, specular=0.2),
            lightposition=dict(x=100, y=100, z=100),
            name="Mesh"
        )
    ])
    
    # Add wireframe if requested
    if show_wireframe:
        # Create wireframe by plotting edges
        edges = set()
        for triangle in triangles:
            edges.add((triangle[0], triangle[1]))
            edges.add((triangle[1], triangle[2]))
            edges.add((triangle[2], triangle[0]))
        
        edge_x, edge_y, edge_z = [], [], []
        for edge in edges:
            x0, y0, z0 = vertices[edge[0]]
            x1, y1, z1 = vertices[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            edge_z.extend([z0, z1, None])
        
        fig.add_trace(go.Scatter3d(
            x=edge_x,
            y=edge_y,
            z=edge_z,
            mode='lines',
            line=dict(color='red', width=1),
            name='Wireframe',
            showlegend=True
        ))
    
    # Update layout
    fig.update_layout(
        scene=dict(
            aspectmode="data",
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, showticklabels=False),
            zaxis=dict(showgrid=False, showticklabels=False),
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.5)
            )
        ),
        width=1200,
        height=800
    )
    
    return fig


def create_point_cloud_plot_open3d(mesh: o3d.geometry.TriangleMesh, color: str = "blue", 
                                  size: int = 3, sample_ratio: float = 1.0) -> go.Figure:
    """
    Create a point cloud visualization of the Open3D mesh vertices.
    
    Args:
        mesh (o3d.geometry.TriangleMesh): Open3D mesh object
        color (str): Color for the points
        size (int): Size of the points
        sample_ratio (float): Ratio of points to sample (0-1)
        
    Returns:
        go.Figure: Plotly figure object
    """
    if mesh is None or mesh.is_empty():
        return go.Figure()
    
    vertices = np.asarray(mesh.vertices)
    
    # Sample vertices if requested
    if sample_ratio < 1.0:
        n_samples = int(len(vertices) * sample_ratio)
        indices = np.random.choice(len(vertices), n_samples, replace=False)
        vertices = vertices[indices]
    
    # Check for vertex colors
    has_vertex_colors = len(mesh.vertex_colors) > 0
    
    if has_vertex_colors:
        vertex_colors = np.asarray(mesh.vertex_colors)
        if sample_ratio < 1.0:
            vertex_colors = vertex_colors[indices]
        
        # Convert colors to RGB strings
        colors = [f"rgb({int(c[0]*255)},{int(c[1]*255)},{int(c[2]*255)})" 
                 for c in vertex_colors]
    else:
        colors = color
    
    fig = go.Figure(data=[
        go.Scatter3d(
            x=vertices[:, 0],
            y=vertices[:, 1],
            z=vertices[:, 2],
            mode='markers',
            marker=dict(
                size=size,
                color=colors,
                opacity=0.8
            ),
            name='Point Cloud'
        )
    ])
    
    fig.update_layout(
        title="PLY Point Cloud View (Open3D)",
        scene=dict(
            aspectmode="data",
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, showticklabels=False),
            zaxis=dict(showgrid=False, showticklabels=False)
        ),
        width=1200,
        height=800
    )
    
    return fig


def analyze_mesh_quality_open3d(mesh: o3d.geometry.TriangleMesh) -> Dict:
    """
    Analyze the quality of an Open3D mesh.
    
    Args:
        mesh (o3d.geometry.TriangleMesh): Open3D mesh object
        
    Returns:
        Dict: Quality metrics and analysis
    """
    if mesh is None or mesh.is_empty():
        return {}
    
    quality = {}
    
    try:
        vertices = np.asarray(mesh.vertices)
        triangles = np.asarray(mesh.triangles)
        
        # Basic quality checks
        quality["Is Watertight"] = mesh.is_watertight()
        quality["Is Orientable"] = mesh.is_orientable()
        quality["Is Self-Intersecting"] = mesh.is_self_intersecting()
        quality["Is Empty"] = mesh.is_empty()
        
        # Calculate face areas
        if len(triangles) > 0:
            face_areas = []
            for triangle in triangles:
                v0, v1, v2 = vertices[triangle]
                # Calculate triangle area using cross product
                area = 0.5 * np.linalg.norm(np.cross(v1 - v0, v2 - v0))
                face_areas.append(area)
            
            face_areas = np.array(face_areas)
            quality["Mean Face Area"] = f"{np.mean(face_areas):.6f}"
            quality["Max Face Area"] = f"{np.max(face_areas):.6f}"
            quality["Min Face Area"] = f"{np.min(face_areas):.6f}"
            
            # Check for degenerate faces
            degenerate_faces = np.sum(face_areas < 1e-10)
            quality["Degenerate Faces"] = f"{degenerate_faces} ({degenerate_faces/len(triangles)*100:.2f}%)"
            
            # Face area ratio
            if np.min(face_areas) > 0:
                quality["Face Area Ratio"] = f"{np.max(face_areas) / np.min(face_areas):.2f}"
        
        # Check for duplicate vertices
        if len(vertices) > 0:
            unique_vertices = np.unique(vertices.view(np.void), axis=0)
            duplicate_vertices = len(vertices) - len(unique_vertices)
            quality["Duplicate Vertices"] = f"{duplicate_vertices} ({duplicate_vertices/len(vertices)*100:.2f}%)"
        
        # Calculate edge length statistics
        if len(triangles) > 0:
            edges = []
            for triangle in triangles:
                edges.extend([
                    np.linalg.norm(vertices[triangle[1]] - vertices[triangle[0]]),
                    np.linalg.norm(vertices[triangle[2]] - vertices[triangle[1]]),
                    np.linalg.norm(vertices[triangle[0]] - vertices[triangle[2]])
                ])
            
            if edges:
                edges = np.array(edges)
                quality["Mean Edge Length"] = f"{np.mean(edges):.6f}"
                quality["Max Edge Length"] = f"{np.max(edges):.6f}"
                quality["Min Edge Length"] = f"{np.min(edges):.6f}"
                quality["Edge Length Ratio"] = f"{np.max(edges) / np.min(edges):.2f}"
        
    except Exception as e:
        quality["Analysis Error"] = str(e)
    
    return quality


def repair_mesh_open3d(mesh: o3d.geometry.TriangleMesh) -> o3d.geometry.TriangleMesh:
    """
    Repair common mesh issues using Open3D.
    
    Args:
        mesh (o3d.geometry.TriangleMesh): Input mesh
        
    Returns:
        o3d.geometry.TriangleMesh: Repaired mesh
    """
    if mesh is None or mesh.is_empty():
        return mesh
    
    try:
        # Remove degenerate triangles
        mesh.remove_degenerate_triangles()
        
        # Remove duplicate triangles
        mesh.remove_duplicated_triangles()
        
        # Remove duplicate vertices
        mesh.remove_duplicated_vertices()
        
        # Remove non-manifold edges
        mesh.remove_non_manifold_edges()
        
        # Compute vertex normals
        mesh.compute_vertex_normals()
        
        return mesh
        
    except Exception as e:
        st.error(f"Error repairing mesh: {e}")
        return mesh


def export_mesh_open3d(mesh: o3d.geometry.TriangleMesh, format: str = "ply") -> bytes:
    """
    Export Open3D mesh data in the specified format.
    
    Args:
        mesh (o3d.geometry.TriangleMesh): Mesh object to export
        format (str): Export format (ply, stl, obj, off, xyz)
        
    Returns:
        bytes: Exported mesh data
    """
    if mesh is None or mesh.is_empty():
        return b""
    
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix=f'.{format}', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        # Export using Open3D
        success = o3d.io.write_triangle_mesh(tmp_path, mesh)
        
        if success:
            with open(tmp_path, 'rb') as f:
                data = f.read()
            os.unlink(tmp_path)
            return data
        else:
            os.unlink(tmp_path)
            return b""
            
    except Exception as e:
        st.error(f"Error exporting mesh: {e}")
        return b""


def create_mesh_statistics_plot(mesh: o3d.geometry.TriangleMesh) -> go.Figure:
    """
    Create statistical plots for mesh analysis.
    
    Args:
        mesh (o3d.geometry.TriangleMesh): Open3D mesh object
        
    Returns:
        go.Figure: Plotly figure with statistics
    """
    if mesh is None or mesh.is_empty():
        return go.Figure()
    
    vertices = np.asarray(mesh.vertices)
    triangles = np.asarray(mesh.triangles)
    
    # Calculate face areas
    face_areas = []
    for triangle in triangles:
        v0, v1, v2 = vertices[triangle]
        area = 0.5 * np.linalg.norm(np.cross(v1 - v0, v2 - v0))
        face_areas.append(area)
    
    face_areas = np.array(face_areas)
    
    # Create subplots
    from plotly.subplots import make_subplots
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Face Area Distribution', 'Vertex Distance Distribution', 
                       'Edge Length Distribution', 'Mesh Quality Metrics'),
        specs=[[{"type": "histogram"}, {"type": "histogram"}],
               [{"type": "histogram"}, {"type": "bar"}]]
    )
    
    # Face area histogram
    fig.add_trace(
        go.Histogram(x=face_areas, name='Face Areas', nbinsx=50),
        row=1, col=1
    )
    
    # Vertex distance histogram
    vertex_distances = np.linalg.norm(vertices, axis=1)
    fig.add_trace(
        go.Histogram(x=vertex_distances, name='Vertex Distances', nbinsx=50),
        row=1, col=2
    )
    
    # Edge length histogram
    edges = []
    for triangle in triangles:
        edges.extend([
            np.linalg.norm(vertices[triangle[1]] - vertices[triangle[0]]),
            np.linalg.norm(vertices[triangle[2]] - vertices[triangle[1]]),
            np.linalg.norm(vertices[triangle[0]] - vertices[triangle[2]])
        ])
    
    if edges:
        fig.add_trace(
            go.Histogram(x=edges, name='Edge Lengths', nbinsx=50),
            row=2, col=1
        )
    
    # Quality metrics bar chart
    quality_metrics = {
        'Watertight': 1 if mesh.is_watertight() else 0,
        'Orientable': 1 if mesh.is_orientable() else 0,
        'Self-Intersecting': 1 if mesh.is_self_intersecting() else 0,
        'Empty': 1 if mesh.is_empty() else 0
    }
    
    fig.add_trace(
        go.Bar(x=list(quality_metrics.keys()), y=list(quality_metrics.values()), 
               name='Quality Metrics'),
        row=2, col=2
    )
    
    fig.update_layout(
        title="Mesh Statistics and Quality Analysis",
        height=800,
        showlegend=False
    )
    
    return fig


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="Open3D Viewer",
        page_icon="🔺",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🔺 Open3D Viewer")
    
    # Initialize data manager
    load_dotenv()
    IMAGE_SERVER_URL = os.getenv('IMAGE_SERVER', 'http://localhost:8888')
    data_manager = DataManager(IMAGE_SERVER_URL)
    
    # Patient folder selection
    st.sidebar.header("Patient Data")
    
    # Get patient folders using DataManager (same as NiiVue_Viewer.py)
    patient_folders = data_manager.get_server_data('', 'folders', ('',))
    
    selected_patient = None
    selected_file = None
    file_to_load = None
    
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
                    
                    # Get PLY files from the CT scan's subfolder within ply directory
                    ct_scan_folder_name = selected_file.replace('.nii.gz', '').replace('.nii', '')
                    ply_files = data_manager.get_server_data(f"{selected_patient}/ply/{ct_scan_folder_name}", 'files', ('.ply',))
                    
                    if ply_files:
                        selected_ply_file = st.sidebar.selectbox(
                            "Select PLY File:",
                            ["None"] + ply_files,
                            help="Choose a PLY file from the selected CT scan"
                        )
                        
                        if selected_ply_file != "None":
                            # Construct URL the same way as voxels in NiiVue viewer
                            file_to_load = f"{IMAGE_SERVER_URL}/output/{selected_patient}/ply/{ct_scan_folder_name}/{selected_ply_file}"
                        else:
                            file_to_load = None
                    else:
                        st.sidebar.warning(f"No PLY files found for CT scan: {selected_display_name}")
                        # Show URL the same way as NiiVue viewer
                        ply_url = f"{IMAGE_SERVER_URL}/output/{selected_patient}/ply/{ct_scan_folder_name}/"
                        st.sidebar.caption(f"PLY directory: {ply_url}")
                        file_to_load = None
                else:
                    file_to_load = None
            else:
                st.sidebar.warning("No NIfTI files found in this patient folder")
                file_to_load = None
        else:
            file_to_load = None
    else:
        st.sidebar.warning("No patient folders found")
        file_to_load = None
    
    # Visualization controls
    st.sidebar.header("Visualization Controls")
    view_mode = st.sidebar.selectbox(
        "View Mode",
        ["Solid", "Wireframe", "Point Cloud", "Solid + Wireframe", "Statistics"],
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
    
    # File upload section at the bottom
    st.sidebar.header("File Upload")
    
    # File upload
    uploaded_file = st.sidebar.file_uploader(
        "Choose a PLY file",
        type=['ply'],
        help="Upload a PLY file to view and analyze with Open3D"
    )
    
    # Load mesh
    mesh = None
    metadata = {}
    
    if uploaded_file is not None:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ply') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name
        
        mesh, metadata = load_ply_file_open3d(tmp_file_path)
        
        # Clean up temporary file
        os.unlink(tmp_file_path)
        
    elif file_to_load is not None:
        mesh, metadata = load_ply_file_open3d(file_to_load)
    
    # Process mesh if loaded
    if mesh is not None and not mesh.is_empty():
        # Get mesh information
        mesh_info = get_open3d_mesh_info(mesh)
        
        # Apply processing options
        if repair_mesh:
            mesh = repair_mesh_open3d(mesh)
            st.info("🔧 Mesh repair applied")
        
        if compute_normals and len(mesh.vertex_normals) == 0:
            mesh.compute_vertex_normals()
            st.info("📐 Vertex normals computed")
        
        # Show detailed mesh information
        with st.expander("Detailed Mesh Information"):
            if mesh_info:
                # Create a more detailed view
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
        
        # 3D Visualization
        if view_mode == "Solid":
            fig = create_open3d_3d_plot(mesh, color=mesh_color, opacity=opacity)
            st.plotly_chart(fig, use_container_width=True)
        
        elif view_mode == "Wireframe":
            fig = create_open3d_3d_plot(mesh, color=mesh_color, opacity=opacity, show_wireframe=True)
            st.plotly_chart(fig, use_container_width=True)
        
        elif view_mode == "Point Cloud":
            fig = create_point_cloud_plot_open3d(mesh, color=mesh_color, size=point_size, 
                                               sample_ratio=point_sample_ratio)
            st.plotly_chart(fig, use_container_width=True)
        
        elif view_mode == "Solid + Wireframe":
            fig = create_open3d_3d_plot(mesh, color=mesh_color, opacity=opacity, show_wireframe=True)
            st.plotly_chart(fig, use_container_width=True)
        
        elif view_mode == "Statistics":
            fig = create_mesh_statistics_plot(mesh)
            st.plotly_chart(fig, use_container_width=True)
        
        
        # Advanced analysis - Center of Mass
        if show_center_mass:
            st.header("Advanced Analysis")
            
            if show_center_mass:
                try:
                    center = mesh.get_center()
                    st.write(f"Center of Mass: ({center[0]:.3f}, {center[1]:.3f}, {center[2]:.3f})")
                    
                    # Add center point to visualization
                    center_fig = create_open3d_3d_plot(mesh, color=mesh_color, opacity=opacity)
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
        
        # Color analysis
        if show_color_analysis and len(mesh.vertex_colors) > 0:
            st.header("Color Analysis")
            
            try:
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
            except Exception as e:
                st.error(f"Error analyzing colors: {e}")
    
    else:
        st.info("👆 Please select a patient, CT scan, and PLY file from the sidebar, or upload a PLY file to get started.")


if __name__ == "__main__":
    main()
