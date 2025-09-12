#!/usr/bin/env python3
"""
PLY Viewer: Interactive 3D PLY File Viewer

A Streamlit application for viewing and analyzing PLY (Polygon File Format) files
with interactive 3D visualization, mesh statistics, and export capabilities.

Features:
- Upload and view PLY files
- Interactive 3D visualization with rotation, zoom, and pan
- Mesh statistics and properties display
- Export to different formats
- Batch processing of multiple PLY files
- Color and texture support for PLY files

Dependencies:
    - streamlit: For the web interface
    - plotly: For 3D visualization
    - trimesh: For PLY file processing
    - numpy: For numerical operations
    - pandas: For data display
    - open3d: For advanced mesh processing

Usage:
    streamlit run ply_viewer.py
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
import open3d as o3d


def load_ply_file(file_path: str) -> trimesh.Trimesh:
    """
    Load a PLY file and return a trimesh object.
    
    Args:
        file_path (str): Path to the PLY file
        
    Returns:
        trimesh.Trimesh: Loaded mesh object
    """
    try:
        mesh = trimesh.load(file_path)
        return mesh
    except Exception as e:
        st.error(f"Error loading PLY file: {e}")
        return None


def get_ply_mesh_info(mesh: trimesh.Trimesh) -> Dict:
    """
    Extract comprehensive information about a PLY mesh.
    
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
    
    # PLY-specific properties
    has_colors = hasattr(mesh.visual, 'vertex_colors') and len(mesh.visual.vertex_colors) > 0
    has_normals = hasattr(mesh, 'vertex_normals') and len(mesh.vertex_normals) > 0
    has_textures = hasattr(mesh.visual, 'material') and mesh.visual.material is not None
    
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
        "Has Colors": has_colors,
        "Has Normals": has_normals,
        "Has Textures": has_textures,
        "Euler Characteristic": mesh.euler_number if hasattr(mesh, 'euler_number') else "N/A"
    }
    
    # Calculate additional metrics
    if len(mesh.vertices) > 0:
        info["Mean Vertex Distance"] = f"{np.mean(np.linalg.norm(mesh.vertices, axis=1)):.6f}"
        info["Max Vertex Distance"] = f"{np.max(np.linalg.norm(mesh.vertices, axis=1)):.6f}"
        
        # Calculate mesh density
        if area > 0:
            info["Vertex Density"] = f"{len(mesh.vertices) / area:.2f} vertices/unit²"
        
        # Calculate face density
        if area > 0:
            info["Face Density"] = f"{len(mesh.faces) / area:.2f} faces/unit²"
    
    return info


def create_ply_3d_plot(mesh: trimesh.Trimesh, color: str = "lightblue", opacity: float = 0.8, 
                      use_vertex_colors: bool = True) -> go.Figure:
    """
    Create a 3D plotly visualization of the PLY mesh.
    
    Args:
        mesh (trimesh.Trimesh): Mesh object to visualize
        color (str): Default color for the mesh
        opacity (float): Opacity of the mesh (0-1)
        use_vertex_colors (bool): Whether to use vertex colors if available
        
    Returns:
        go.Figure: Plotly figure object
    """
    if mesh is None or len(mesh.vertices) == 0:
        return go.Figure()
    
    # Check if mesh has vertex colors
    has_vertex_colors = (hasattr(mesh.visual, 'vertex_colors') and 
                        len(mesh.visual.vertex_colors) > 0 and 
                        use_vertex_colors)
    
    if has_vertex_colors:
        # For Mesh3d, we can't use per-vertex colors directly
        # Instead, we'll use a single color or create a colorscale
        vertex_colors = mesh.visual.vertex_colors
        if len(vertex_colors) == len(mesh.vertices) and vertex_colors.shape[1] >= 3:
            # Calculate average color for the mesh
            avg_color = np.mean(vertex_colors[:, :3], axis=0)
            colors = f"rgb({int(avg_color[0])},{int(avg_color[1])},{int(avg_color[2])})"
        else:
            colors = color
    else:
        colors = color
    
    # Create the mesh plot
    fig = go.Figure(data=[
        go.Mesh3d(
            x=mesh.vertices[:, 0],
            y=mesh.vertices[:, 1],
            z=mesh.vertices[:, 2],
            i=mesh.faces[:, 0],
            j=mesh.faces[:, 1],
            k=mesh.faces[:, 2],
            color=colors,
            opacity=opacity,
            lighting=dict(ambient=0.3, diffuse=0.8, specular=0.2),
            lightposition=dict(x=100, y=100, z=100)
        )
    ])
    
    # Update layout
    title = "3D PLY Mesh Visualization"
    if has_vertex_colors and use_vertex_colors:
        title += " (Average Color)"
    
    fig.update_layout(
        title=title,
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


def create_ply_wireframe_plot(mesh: trimesh.Trimesh, color: str = "red") -> go.Figure:
    """
    Create a wireframe visualization of the PLY mesh.
    
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
        title="PLY Wireframe View",
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


def create_colored_mesh_plot(mesh: trimesh.Trimesh, opacity: float = 0.8) -> go.Figure:
    """
    Create a colored mesh visualization using Scatter3d for proper vertex color support.
    
    Args:
        mesh (trimesh.Trimesh): Mesh object to visualize
        opacity (float): Opacity of the mesh (0-1)
        
    Returns:
        go.Figure: Plotly figure object
    """
    if mesh is None or len(mesh.vertices) == 0:
        return go.Figure()
    
    # Check if mesh has vertex colors
    has_vertex_colors = (hasattr(mesh.visual, 'vertex_colors') and 
                        len(mesh.visual.vertex_colors) > 0)
    
    if not has_vertex_colors:
        # Fall back to regular mesh plot
        return create_ply_3d_plot(mesh, opacity=opacity)
    
    vertex_colors = mesh.visual.vertex_colors
    if len(vertex_colors) != len(mesh.vertices) or vertex_colors.shape[1] < 3:
        # Fall back to regular mesh plot
        return create_ply_3d_plot(mesh, opacity=opacity)
    
    # Create colored scatter plot for each face
    fig = go.Figure()
    
    # Sample faces to avoid too many points
    max_faces = 5000  # Limit for performance
    if len(mesh.faces) > max_faces:
        face_indices = np.random.choice(len(mesh.faces), max_faces, replace=False)
        faces = mesh.faces[face_indices]
    else:
        faces = mesh.faces
    
    for face in faces:
        # Get vertices and colors for this face
        face_vertices = mesh.vertices[face]
        face_colors = vertex_colors[face]
        
        # Convert colors to RGB strings
        rgb_colors = [f"rgb({int(c[0])},{int(c[1])},{int(c[2])})" for c in face_colors]
        
        # Add triangle as scatter plot
        fig.add_trace(go.Scatter3d(
            x=face_vertices[:, 0],
            y=face_vertices[:, 1],
            z=face_vertices[:, 2],
            mode='markers+lines',
            marker=dict(
                size=2,
                color=rgb_colors,
                opacity=opacity
            ),
            line=dict(
                color=rgb_colors[0],  # Use first vertex color for lines
                width=1
            ),
            showlegend=False,
            hoverinfo='skip'
        ))
    
    fig.update_layout(
        title="PLY Colored Mesh (Vertex Colors)",
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


def create_point_cloud_plot(mesh: trimesh.Trimesh, color: str = "blue", size: int = 3) -> go.Figure:
    """
    Create a point cloud visualization of the PLY mesh vertices.
    
    Args:
        mesh (trimesh.Trimesh): Mesh object to visualize
        color (str): Color for the points
        size (int): Size of the points
        
    Returns:
        go.Figure: Plotly figure object
    """
    if mesh is None or len(mesh.vertices) == 0:
        return go.Figure()
    
    # Check if mesh has vertex colors
    has_vertex_colors = (hasattr(mesh.visual, 'vertex_colors') and 
                        len(mesh.visual.vertex_colors) > 0)
    
    if has_vertex_colors:
        vertex_colors = mesh.visual.vertex_colors
        if len(vertex_colors) == len(mesh.vertices):
            # Handle both RGB and RGBA colors
            if vertex_colors.shape[1] >= 3:
                # Convert RGB values to hex strings for Plotly
                rgb_colors = vertex_colors[:, :3]
                colors = [f"rgb({int(c[0])},{int(c[1])},{int(c[2])})" for c in rgb_colors]
            else:
                colors = color
        else:
            colors = color
    else:
        colors = color
    
    fig = go.Figure(data=[
        go.Scatter3d(
            x=mesh.vertices[:, 0],
            y=mesh.vertices[:, 1],
            z=mesh.vertices[:, 2],
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
        title="PLY Point Cloud View",
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


def export_ply_mesh_data(mesh: trimesh.Trimesh, format: str = "ply") -> bytes:
    """
    Export PLY mesh data in the specified format.
    
    Args:
        mesh (trimesh.Trimesh): Mesh object to export
        format (str): Export format (ply, stl, obj, off)
        
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


def analyze_ply_quality(mesh: trimesh.Trimesh) -> Dict:
    """
    Analyze the quality of a PLY mesh.
    
    Args:
        mesh (trimesh.Trimesh): Mesh object to analyze
        
    Returns:
        Dict: Quality metrics and analysis
    """
    if mesh is None:
        return {}
    
    quality = {}
    
    try:
        # Check for degenerate faces
        face_areas = mesh.area_faces
        degenerate_faces = np.sum(face_areas < 1e-10)
        quality["Degenerate Faces"] = f"{degenerate_faces} ({degenerate_faces/len(mesh.faces)*100:.2f}%)"
        
        # Check for duplicate vertices
        unique_vertices = np.unique(mesh.vertices.view(np.void), axis=0)
        duplicate_vertices = len(mesh.vertices) - len(unique_vertices)
        quality["Duplicate Vertices"] = f"{duplicate_vertices} ({duplicate_vertices/len(mesh.vertices)*100:.2f}%)"
        
        # Check for non-manifold edges
        if hasattr(mesh, 'edges_unique'):
            edge_face_count = mesh.edges_unique_in_bounds
            non_manifold_edges = np.sum(edge_face_count > 2)
            quality["Non-manifold Edges"] = f"{non_manifold_edges}"
        
        # Check mesh consistency
        quality["Is Watertight"] = mesh.is_watertight
        quality["Is Convex"] = mesh.is_convex
        
        # Calculate aspect ratio of faces
        if len(face_areas) > 0:
            face_areas = face_areas[face_areas > 1e-10]  # Remove degenerate faces
            if len(face_areas) > 0:
                aspect_ratio = np.max(face_areas) / np.min(face_areas)
                quality["Face Area Ratio"] = f"{aspect_ratio:.2f}"
        
    except Exception as e:
        quality["Analysis Error"] = str(e)
    
    return quality


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="PLY Viewer",
        page_icon="🔺",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🔺 PLY File Viewer")
    st.markdown("Interactive 3D visualization and analysis of PLY (Polygon File Format) files")
    
    # Sidebar for file upload and controls
    st.sidebar.header("File Upload")
    
    # File upload
    uploaded_file = st.sidebar.file_uploader(
        "Choose a PLY file",
        type=['ply'],
        help="Upload a PLY file to view and analyze"
    )
    
    # Load from existing files
    st.sidebar.header("Load Existing Files")
    existing_files = []
    
    # Check for PLY files in common directories
    search_dirs = [
        "/Users/dave/AI/HPE/HPE-Nvidia-Vista-3D/output.mesh",
        "/Users/dave/AI/HPE/HPE-Nvidia-Vista-3D/output",
        "/Users/dave/AI/HPE/HPE-Nvidia-Vista-3D/extras"
    ]
    
    for search_dir in search_dirs:
        if os.path.exists(search_dir):
            for file_path in Path(search_dir).rglob("*.ply"):
                existing_files.append(str(file_path))
    
    if existing_files:
        selected_file = st.sidebar.selectbox(
            "Select existing PLY file:",
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
        ["Solid", "Wireframe", "Point Cloud", "Colored Mesh", "All"],
        help="Choose how to display the mesh"
    )
    
    mesh_color = st.sidebar.color_picker(
        "Mesh Color",
        value="#87CEEB",
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
    
    use_vertex_colors = st.sidebar.checkbox(
        "Use Vertex Colors",
        value=True,
        help="Use vertex colors if available in the PLY file"
    )
    
    point_size = st.sidebar.slider(
        "Point Size",
        min_value=1,
        max_value=10,
        value=3,
        help="Size of points in point cloud view"
    )
    
    # Load mesh
    mesh = None
    if uploaded_file is not None:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ply') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name
        
        mesh = load_ply_file(tmp_file_path)
        
        # Clean up temporary file
        os.unlink(tmp_file_path)
        
    elif file_to_load is not None:
        mesh = load_ply_file(file_to_load)
    
    # Main content area
    if mesh is not None:
        # Display mesh information
        st.header("Mesh Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            mesh_info = get_ply_mesh_info(mesh)
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
        
        # Quality Analysis
        st.header("Mesh Quality Analysis")
        quality_info = analyze_ply_quality(mesh)
        if quality_info:
            quality_df = pd.DataFrame(list(quality_info.items()), columns=['Quality Metric', 'Value'])
            st.dataframe(quality_df, use_container_width=True)
        
        # 3D Visualization
        st.header("3D Visualization")
        
        if view_mode in ["Solid", "All"]:
            fig_solid = create_ply_3d_plot(mesh, color=mesh_color, opacity=opacity, 
                                         use_vertex_colors=use_vertex_colors)
            st.plotly_chart(fig_solid, use_container_width=True)
        
        if view_mode in ["Wireframe", "All"]:
            fig_wireframe = create_ply_wireframe_plot(mesh)
            st.plotly_chart(fig_wireframe, use_container_width=True)
        
        if view_mode in ["Point Cloud", "All"]:
            fig_points = create_point_cloud_plot(mesh, color=mesh_color, size=point_size)
            st.plotly_chart(fig_points, use_container_width=True)
        
        if view_mode in ["Colored Mesh", "All"]:
            fig_colored = create_colored_mesh_plot(mesh, opacity=opacity)
            st.plotly_chart(fig_colored, use_container_width=True)
        
        # Export options
        st.header("Export Options")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("Export as PLY"):
                ply_data = export_ply_mesh_data(mesh, "ply")
                if ply_data:
                    st.download_button(
                        label="Download PLY",
                        data=ply_data,
                        file_name="mesh.ply",
                        mime="application/octet-stream"
                    )
        
        with col2:
            if st.button("Export as STL"):
                stl_data = export_ply_mesh_data(mesh, "stl")
                if stl_data:
                    st.download_button(
                        label="Download STL",
                        data=stl_data,
                        file_name="mesh.stl",
                        mime="application/octet-stream"
                    )
        
        with col3:
            if st.button("Export as OBJ"):
                obj_data = export_ply_mesh_data(mesh, "obj")
                if obj_data:
                    st.download_button(
                        label="Download OBJ",
                        data=obj_data,
                        file_name="mesh.obj",
                        mime="application/octet-stream"
                    )
        
        with col4:
            if st.button("Export as OFF"):
                off_data = export_ply_mesh_data(mesh, "off")
                if off_data:
                    st.download_button(
                        label="Download OFF",
                        data=off_data,
                        file_name="mesh.off",
                        mime="application/octet-stream"
                    )
        
        # Advanced analysis
        st.header("Advanced Analysis")
        
        if st.checkbox("Show Bounding Box"):
            try:
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
            except Exception as e:
                st.error(f"Error displaying bounding box: {e}")
        
        if st.checkbox("Show Center of Mass"):
            try:
                center = mesh.center_mass
                st.write(f"Center of Mass: ({center[0]:.3f}, {center[1]:.3f}, {center[2]:.3f})")
                
                # Add center point to visualization
                center_fig = create_ply_3d_plot(mesh, color=mesh_color, opacity=opacity, 
                                              use_vertex_colors=use_vertex_colors)
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
        if hasattr(mesh.visual, 'vertex_colors') and len(mesh.visual.vertex_colors) > 0:
            st.header("Color Analysis")
            
            try:
                colors = mesh.visual.vertex_colors
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
                        "Mean Red": f"{np.mean(colors[:, 0]):.2f}",
                        "Mean Green": f"{np.mean(colors[:, 1]):.2f}",
                        "Mean Blue": f"{np.mean(colors[:, 2]):.2f}",
                        "Std Red": f"{np.std(colors[:, 0]):.2f}",
                        "Std Green": f"{np.std(colors[:, 1]):.2f}",
                        "Std Blue": f"{np.std(colors[:, 2]):.2f}"
                    }
                    
                    if colors.shape[1] >= 4:
                        col_stats["Mean Alpha"] = f"{np.mean(colors[:, 3]):.2f}"
                        col_stats["Std Alpha"] = f"{np.std(colors[:, 3]):.2f}"
                    
                    col_df = pd.DataFrame(list(col_stats.items()), columns=['Color Statistic', 'Value'])
                    st.dataframe(col_df, use_container_width=True)
                else:
                    st.info("Color data is not in the expected format (RGB values).")
            except Exception as e:
                st.error(f"Error analyzing colors: {e}")
    
    else:
        st.info("👆 Please upload a PLY file or select an existing one from the sidebar to get started.")
        
        # Show example files if available
        if existing_files:
            st.subheader("Available PLY Files")
            for file_path in existing_files[:5]:  # Show first 5 files
                st.write(f"• {file_path}")
            if len(existing_files) > 5:
                st.write(f"... and {len(existing_files) - 5} more files")


if __name__ == "__main__":
    main()
