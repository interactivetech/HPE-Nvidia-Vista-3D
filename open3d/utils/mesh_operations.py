#!/usr/bin/env python3
"""
Mesh Operations Utilities

This module handles all mesh loading, processing, analysis, and visualization operations
for the Open3D Viewer, separating complex logic from the GUI components.

Functions:
- Mesh loading and validation
- Mesh repair and optimization
- 3D visualization creation
- Mesh analysis and statistics
- File format exports
"""

# Try to import Open3D with fallback handling
try:
    import open3d as o3d
    OPEN3D_AVAILABLE = True
except ImportError:
    o3d = None
    OPEN3D_AVAILABLE = False

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import tempfile
import os
import requests
from typing import Dict, List, Tuple, Optional, Union
import json
from scipy.spatial import cKDTree


class MeshProcessor:
    """Handles all mesh processing operations."""
    
    def __init__(self, timeout: int = 15):
        self.timeout = timeout
    
    def load_ply_file(self, file_path: str) -> Tuple[Optional[o3d.geometry.TriangleMesh], Dict]:
        """
        Load a PLY file using Open3D and return mesh with metadata.
        
        Args:
            file_path (str): Path to the PLY file (local path or HTTP URL)
            
        Returns:
            Tuple[Optional[o3d.geometry.TriangleMesh], Dict]: Mesh object and metadata
        """
        try:
            # Check if it's an HTTP URL
            if file_path.startswith('http'):
                # Download the file to a temporary location with timeout
                response = requests.get(file_path, timeout=self.timeout)
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
            
            # Validate mesh
            if mesh is None:
                return None, {"error": "Open3D returned None for the mesh"}
            
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
            
        except requests.exceptions.Timeout:
            return None, {"error": f"Timeout loading PLY file: {file_path}"}
        except requests.exceptions.RequestException as e:
            return None, {"error": f"Network error loading PLY file: {e}"}
        except FileNotFoundError:
            return None, {"error": f"File not found: {file_path}"}
        except Exception as e:
            return None, {"error": f"Error loading PLY file with Open3D: {e}"}
    
    def get_mesh_info(self, mesh: o3d.geometry.TriangleMesh) -> Dict:
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
    
    def repair_mesh(self, mesh: o3d.geometry.TriangleMesh) -> o3d.geometry.TriangleMesh:
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
            # Return original mesh if repair fails
            return mesh
    
    def analyze_mesh_quality(self, mesh: o3d.geometry.TriangleMesh) -> Dict:
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


class MeshVisualizer:
    """Handles all mesh visualization operations."""
    
    def create_multi_mesh_plot(self, meshes: List[Tuple[o3d.geometry.TriangleMesh, str, str]], 
                              opacity: float = 0.8, show_wireframe: bool = False) -> go.Figure:
        """
        Create a 3D plotly visualization of multiple Open3D meshes.
        
        Args:
            meshes (List[Tuple[o3d.geometry.TriangleMesh, str, str]]): List of (mesh, name, color) tuples
            opacity (float): Opacity of the meshes (0-1)
            show_wireframe (bool): Whether to show wireframe overlay
            
        Returns:
            go.Figure: Plotly figure object
        """
        if not meshes:
            return go.Figure()
        
        fig = go.Figure()
        
        # Limit the number of meshes for performance
        max_meshes = 10
        if len(meshes) > max_meshes:
            meshes = meshes[:max_meshes]
        
        for mesh, name, color in meshes:
            if mesh is None or mesh.is_empty():
                continue
                
            vertices = np.asarray(mesh.vertices)
            triangles = np.asarray(mesh.triangles)
            
            # Skip wireframe for performance if too many triangles
            if show_wireframe and len(triangles) > 20000:
                show_wireframe = False
            
            # Check for vertex colors
            has_vertex_colors = len(mesh.vertex_colors) > 0
            
            if has_vertex_colors:
                vertex_colors = np.asarray(mesh.vertex_colors)
                # Calculate average color for the mesh
                avg_color = np.mean(vertex_colors, axis=0)
                colors = f"rgb({int(avg_color[0]*255)},{int(avg_color[1]*255)},{int(avg_color[2]*255)})"
            else:
                colors = color
            
            # Create the mesh plot with quality optimizations
            fig.add_trace(go.Mesh3d(
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
                name=name,
                showlegend=True,
                flatshading=False,
                visible=True,
                hoverinfo='skip'
            ))
            
            # Add wireframe if requested and not too complex
            if show_wireframe and len(triangles) <= 20000:
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
                    name=f'{name} Wireframe',
                    showlegend=True
                ))
        
        # Update layout with performance optimizations
        fig.update_layout(
            scene=dict(
                aspectmode="data",
                xaxis=dict(showgrid=False, showticklabels=False, showbackground=False),
                yaxis=dict(showgrid=False, showticklabels=False, showbackground=False),
                zaxis=dict(showgrid=False, showticklabels=False, showbackground=False),
                camera=dict(eye=dict(x=1.5, y=1.5, z=1.5)),
                bgcolor='rgba(0,0,0,0)',
                dragmode='turntable'
            ),
            width=1200,
            height=800,
            showlegend=True,
            legend=dict(x=0, y=1),
            margin=dict(l=0, r=0, t=0, b=0),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig
    
    def create_point_cloud_plot(self, mesh: o3d.geometry.TriangleMesh, color: str = "blue", 
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
    
    def create_statistics_plot(self, mesh: o3d.geometry.TriangleMesh) -> go.Figure:
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
    
    def create_simple_plot(self, meshes: List[Tuple[o3d.geometry.TriangleMesh, str, str]]) -> go.Figure:
        """
        Create a simple point cloud visualization for multiple meshes.
        
        Args:
            meshes (List[Tuple[o3d.geometry.TriangleMesh, str, str]]): List of (mesh, name, color) tuples
            
        Returns:
            go.Figure: Plotly figure object
        """
        fig = go.Figure()
        
        for mesh, name, color in meshes:
            vertices = np.asarray(mesh.vertices)
            # Sample vertices for performance but keep more for better quality
            if len(vertices) > 20000:
                indices = np.random.choice(len(vertices), 20000, replace=False)
                vertices = vertices[indices]
            
            fig.add_trace(go.Scatter3d(
                x=vertices[:, 0],
                y=vertices[:, 1], 
                z=vertices[:, 2],
                mode='markers',
                marker=dict(size=2, color=color),
                name=name
            ))
        
        fig.update_layout(
            title="Simple Point Cloud View",
            scene=dict(
                aspectmode="data",
                xaxis=dict(showgrid=False, showticklabels=False),
                yaxis=dict(showgrid=False, showticklabels=False),
                zaxis=dict(showgrid=False, showticklabels=False)
            ),
            width=800,
            height=600
        )
        
        return fig


def optimize_mesh_for_performance(mesh: o3d.geometry.TriangleMesh, max_vertices: int = 50000, 
                                 max_triangles: int = 100000) -> o3d.geometry.TriangleMesh:
    """
    Optimize mesh for better performance by simplifying if necessary.
    
    Args:
        mesh: Input mesh
        max_vertices: Maximum number of vertices
        max_triangles: Maximum number of triangles
        
    Returns:
        Optimized mesh
    """
    if mesh is None or mesh.is_empty():
        return mesh
    
    vertex_count = len(mesh.vertices)
    triangle_count = len(mesh.triangles)
    
    # Apply mesh simplification only for very large meshes
    if vertex_count > max_vertices or triangle_count > max_triangles:
        try:
            target_triangles = min(20000, triangle_count // 2)  # Reduce to 50% or max 20000
            mesh = mesh.simplify_quadric_decimation(target_number_of_triangles=target_triangles)
        except Exception:
            pass  # Continue with original mesh if simplification fails
    
    return mesh
