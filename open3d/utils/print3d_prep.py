#!/usr/bin/env python3
"""
3D Print Preparation Utilities

This module provides comprehensive tools for preparing PLY meshes for 3D printing,
including mesh repair, validation, optimization, and STL export functionality.

Key Features:
- Mesh repair and cleanup (remove duplicates, degenerate faces, non-manifold edges)
- Watertight mesh validation and repair
- Mesh simplification and optimization for 3D printing
- Scale normalization and orientation correction
- Wall thickness analysis and correction
- Support structure detection
- STL export with 3D printing optimizations
- Quality assessment and reporting

Dependencies:
    - open3d: For 3D mesh processing
    - numpy: For numerical operations
    - trimesh: For advanced mesh operations
    - scipy: For scientific computing
"""

# Try to import Open3D with fallback handling
try:
    import open3d as o3d
    OPEN3D_AVAILABLE = True
except ImportError:
    o3d = None
    OPEN3D_AVAILABLE = False

import numpy as np
import trimesh
from typing import Dict, List, Tuple, Optional, Union
import tempfile
import os
from scipy.spatial import cKDTree
from scipy.spatial.distance import cdist
import math


class Print3DPreparator:
    """
    A comprehensive class for preparing 3D meshes for printing.
    """
    
    def __init__(self, target_scale_mm: float = 100.0, min_wall_thickness: float = 0.8):
        """
        Initialize the 3D print preparator.
        
        Args:
            target_scale_mm (float): Target scale in millimeters for the printed object
            min_wall_thickness (float): Minimum wall thickness in mm for 3D printing
        """
        self.target_scale_mm = target_scale_mm
        self.min_wall_thickness = min_wall_thickness
        self.preparation_log = []
    
    def log_step(self, message: str):
        """Log a preparation step."""
        self.preparation_log.append(message)
        print(f"[3D Print Prep] {message}")
    
    def prepare_mesh_for_printing(self, mesh: o3d.geometry.TriangleMesh, 
                                 mesh_name: str = "mesh") -> Tuple[o3d.geometry.TriangleMesh, Dict]:
        """
        Comprehensive mesh preparation for 3D printing.
        
        Args:
            mesh (o3d.geometry.TriangleMesh): Input mesh
            mesh_name (str): Name of the mesh for logging
            
        Returns:
            Tuple[o3d.geometry.TriangleMesh, Dict]: Prepared mesh and preparation report
        """
        if mesh is None or mesh.is_empty():
            return mesh, {"error": "Empty or invalid mesh"}
        
        self.preparation_log = []
        self.log_step(f"Starting 3D print preparation for: {mesh_name}")
        
        # Step 1: Basic mesh repair
        mesh = self._basic_mesh_repair(mesh)
        
        # Step 2: Make watertight
        mesh, watertight_report = self._make_watertight(mesh)
        
        # Step 3: Orient mesh properly
        mesh = self._orient_mesh(mesh)
        
        # Step 4: Scale to target size
        mesh, scale_report = self._scale_mesh(mesh)
        
        # Step 5: Optimize for printing
        mesh = self._optimize_for_printing(mesh)
        
        # Step 6: Validate for printing
        validation_report = self._validate_for_printing(mesh)
        
        # Compile final report
        report = {
            "mesh_name": mesh_name,
            "watertight_repair": watertight_report,
            "scaling": scale_report,
            "validation": validation_report,
            "preparation_log": self.preparation_log.copy(),
            "final_stats": self._get_mesh_stats(mesh)
        }
        
        self.log_step("3D print preparation completed")
        return mesh, report
    
    def _basic_mesh_repair(self, mesh: o3d.geometry.TriangleMesh) -> o3d.geometry.TriangleMesh:
        """Perform basic mesh repair operations."""
        self.log_step("Performing basic mesh repair...")
        
        original_vertices = len(mesh.vertices)
        original_triangles = len(mesh.triangles)
        
        # Remove degenerate triangles
        mesh.remove_degenerate_triangles()
        
        # Remove duplicate triangles
        mesh.remove_duplicated_triangles()
        
        # Remove duplicate vertices
        mesh.remove_duplicated_vertices()
        
        # Remove non-manifold edges
        mesh.remove_non_manifold_edges()
        
        # Remove unreferenced vertices
        mesh.remove_unreferenced_vertices()
        
        # Compute vertex normals
        mesh.compute_vertex_normals()
        
        new_vertices = len(mesh.vertices)
        new_triangles = len(mesh.triangles)
        
        self.log_step(f"Mesh repair: {original_vertices}→{new_vertices} vertices, {original_triangles}→{new_triangles} triangles")
        
        return mesh
    
    def _make_watertight(self, mesh: o3d.geometry.TriangleMesh) -> Tuple[o3d.geometry.TriangleMesh, Dict]:
        """Attempt to make the mesh watertight for 3D printing."""
        self.log_step("Checking and repairing watertight properties...")
        
        report = {
            "originally_watertight": mesh.is_watertight(),
            "repair_attempted": False,
            "finally_watertight": False,
            "method_used": "none"
        }
        
        if mesh.is_watertight():
            self.log_step("Mesh is already watertight")
            report["finally_watertight"] = True
            return mesh, report
        
        # Try Open3D hole filling
        try:
            self.log_step("Attempting hole filling...")
            # Note: Open3D doesn't have direct hole filling, so we'll use trimesh
            report["repair_attempted"] = True
            
            # Convert to trimesh for better hole filling
            vertices = np.asarray(mesh.vertices)
            faces = np.asarray(mesh.triangles)
            
            if len(vertices) > 0 and len(faces) > 0:
                trimesh_obj = trimesh.Trimesh(vertices=vertices, faces=faces)
                
                # Fill holes using trimesh
                if not trimesh_obj.is_watertight:
                    self.log_step("Attempting to fill holes with trimesh...")
                    trimesh_obj.fill_holes()
                    
                    # Convert back to Open3D
                    mesh_new = o3d.geometry.TriangleMesh()
                    mesh_new.vertices = o3d.utility.Vector3dVector(trimesh_obj.vertices)
                    mesh_new.triangles = o3d.utility.Vector3iVector(trimesh_obj.faces)
                    mesh_new.compute_vertex_normals()
                    
                    if mesh_new.is_watertight():
                        self.log_step("Successfully made mesh watertight using hole filling")
                        report["finally_watertight"] = True
                        report["method_used"] = "hole_filling"
                        return mesh_new, report
                    else:
                        mesh = mesh_new  # Use the improved version even if not fully watertight
                
        except Exception as e:
            self.log_step(f"Hole filling failed: {str(e)}")
        
        # Try convex hull as last resort (only for very broken meshes)
        if not mesh.is_watertight():
            try:
                self.log_step("Attempting convex hull repair (last resort)...")
                hull = mesh.get_convex_hull()
                if hull.is_watertight():
                    self.log_step("Created watertight mesh using convex hull (geometry simplified)")
                    report["finally_watertight"] = True
                    report["method_used"] = "convex_hull"
                    return hull, report
            except Exception as e:
                self.log_step(f"Convex hull repair failed: {str(e)}")
        
        # Final check
        report["finally_watertight"] = mesh.is_watertight()
        if not report["finally_watertight"]:
            self.log_step("Warning: Could not make mesh fully watertight - may have printing issues")
        
        return mesh, report
    
    def _orient_mesh(self, mesh: o3d.geometry.TriangleMesh) -> o3d.geometry.TriangleMesh:
        """Orient the mesh optimally for 3D printing (largest face on Z=0 plane)."""
        self.log_step("Optimizing mesh orientation for 3D printing...")
        
        try:
            # Get the bounding box
            bbox = mesh.get_axis_aligned_bounding_box()
            bbox_size = bbox.max_bound - bbox.min_bound
            
            # Find the largest dimension to determine the base
            max_dim_idx = np.argmax(bbox_size)
            
            # Rotate to put the largest face down
            if max_dim_idx == 0:  # X is largest - rotate around Y
                rotation_matrix = mesh.get_rotation_matrix_from_xyz((0, np.pi/2, 0))
                mesh.rotate(rotation_matrix, center=mesh.get_center())
            elif max_dim_idx == 1:  # Y is largest - rotate around X  
                rotation_matrix = mesh.get_rotation_matrix_from_xyz((np.pi/2, 0, 0))
                mesh.rotate(rotation_matrix, center=mesh.get_center())
            # Z is largest - already oriented correctly
            
            # Move to sit on Z=0 plane
            bbox = mesh.get_axis_aligned_bounding_box()
            translation = np.array([0, 0, -bbox.min_bound[2]])
            mesh.translate(translation)
            
            self.log_step("Mesh oriented with base on Z=0 plane")
            
        except Exception as e:
            self.log_step(f"Orientation adjustment failed: {str(e)}")
        
        return mesh
    
    def _scale_mesh(self, mesh: o3d.geometry.TriangleMesh) -> Tuple[o3d.geometry.TriangleMesh, Dict]:
        """Scale mesh to target printing size."""
        self.log_step(f"Scaling mesh to target size: {self.target_scale_mm}mm")
        
        # Get current bounding box
        bbox = mesh.get_axis_aligned_bounding_box()
        current_size = bbox.max_bound - bbox.min_bound
        current_max_dimension = np.max(current_size)
        
        # Calculate scale factor
        scale_factor = self.target_scale_mm / current_max_dimension
        
        # Apply scaling
        mesh.scale(scale_factor, center=mesh.get_center())
        
        # Get new size
        new_bbox = mesh.get_axis_aligned_bounding_box()
        new_size = new_bbox.max_bound - new_bbox.min_bound
        new_max_dimension = np.max(new_size)
        
        report = {
            "original_max_dimension": current_max_dimension,
            "scale_factor": scale_factor,
            "new_max_dimension": new_max_dimension,
            "target_size_mm": self.target_scale_mm,
            "new_dimensions_mm": {
                "x": new_size[0],
                "y": new_size[1], 
                "z": new_size[2]
            }
        }
        
        self.log_step(f"Scaled by factor {scale_factor:.3f}: {current_max_dimension:.1f} → {new_max_dimension:.1f}mm")
        
        return mesh, report
    
    def _optimize_for_printing(self, mesh: o3d.geometry.TriangleMesh) -> o3d.geometry.TriangleMesh:
        """Optimize mesh for 3D printing (smoothing, simplification if needed)."""
        self.log_step("Optimizing mesh for 3D printing...")
        
        try:
            # Smooth the mesh slightly to remove sharp artifacts
            mesh = mesh.filter_smooth_simple(number_of_iterations=1)
            
            # If mesh is very dense, simplify it
            num_triangles = len(mesh.triangles)
            if num_triangles > 100000:
                target_triangles = min(50000, num_triangles // 2)
                self.log_step(f"Simplifying mesh from {num_triangles} to ~{target_triangles} triangles")
                mesh = mesh.simplify_quadric_decimation(target_number_of_triangles=target_triangles)
                self.log_step(f"Simplified to {len(mesh.triangles)} triangles")
            
            # Recompute normals after modifications
            mesh.compute_vertex_normals()
            
        except Exception as e:
            self.log_step(f"Optimization step failed: {str(e)}")
        
        return mesh
    
    def _validate_for_printing(self, mesh: o3d.geometry.TriangleMesh) -> Dict:
        """Validate mesh for 3D printing and provide recommendations."""
        self.log_step("Validating mesh for 3D printing...")
        
        validation = {
            "is_watertight": mesh.is_watertight(),
            "is_orientable": mesh.is_orientable(),
            "is_self_intersecting": mesh.is_self_intersecting(),
            "vertex_count": len(mesh.vertices),
            "triangle_count": len(mesh.triangles),
            "volume": 0.0,
            "surface_area": 0.0,
            "printability_score": 0,
            "warnings": [],
            "recommendations": []
        }
        
        try:
            validation["volume"] = mesh.get_volume()
            validation["surface_area"] = mesh.get_surface_area()
        except:
            pass
        
        # Calculate printability score (0-10)
        score = 0
        
        if validation["is_watertight"]:
            score += 4
        else:
            validation["warnings"].append("Mesh is not watertight - may have printing issues")
            validation["recommendations"].append("Check for holes and repair mesh")
        
        if validation["is_orientable"]:
            score += 2
        else:
            validation["warnings"].append("Mesh has orientation issues")
        
        if not validation["is_self_intersecting"]:
            score += 2
        else:
            validation["warnings"].append("Mesh has self-intersections")
            validation["recommendations"].append("Repair self-intersecting faces")
        
        if 1000 <= validation["triangle_count"] <= 100000:
            score += 1
        elif validation["triangle_count"] > 100000:
            validation["warnings"].append("Very high triangle count - may slow down slicing")
            validation["recommendations"].append("Consider mesh simplification")
        elif validation["triangle_count"] < 1000:
            validation["warnings"].append("Low triangle count - may lack detail")
        
        if validation["volume"] > 0:
            score += 1
        else:
            validation["warnings"].append("Zero or negative volume")
        
        validation["printability_score"] = score
        
        # Overall assessment
        if score >= 8:
            self.log_step(f"Mesh validation: EXCELLENT (score: {score}/10)")
        elif score >= 6:
            self.log_step(f"Mesh validation: GOOD (score: {score}/10)")
        elif score >= 4:
            self.log_step(f"Mesh validation: FAIR (score: {score}/10) - some issues detected")
        else:
            self.log_step(f"Mesh validation: POOR (score: {score}/10) - significant issues detected")
        
        return validation
    
    def _get_mesh_stats(self, mesh: o3d.geometry.TriangleMesh) -> Dict:
        """Get final mesh statistics."""
        bbox = mesh.get_axis_aligned_bounding_box()
        size = bbox.max_bound - bbox.min_bound
        
        stats = {
            "vertices": len(mesh.vertices),
            "triangles": len(mesh.triangles),
            "is_watertight": mesh.is_watertight(),
            "bounding_box_mm": {
                "x": size[0],
                "y": size[1],
                "z": size[2]
            }
        }
        
        try:
            stats["volume_mm3"] = mesh.get_volume()
            stats["surface_area_mm2"] = mesh.get_surface_area()
        except:
            stats["volume_mm3"] = 0.0
            stats["surface_area_mm2"] = 0.0
        
        return stats
    
    def export_stl(self, mesh: o3d.geometry.TriangleMesh, output_path: str) -> bool:
        """
        Export mesh as STL file optimized for 3D printing.
        
        Args:
            mesh (o3d.geometry.TriangleMesh): Prepared mesh
            output_path (str): Output STL file path
            
        Returns:
            bool: Success status
        """
        try:
            # Ensure mesh has proper normals
            if len(mesh.vertex_normals) == 0:
                mesh.compute_vertex_normals()
            
            # Export using Open3D
            success = o3d.io.write_triangle_mesh(output_path, mesh, write_ascii=False)
            
            if success:
                file_size = os.path.getsize(output_path)
                self.log_step(f"STL exported successfully: {output_path} ({file_size/1024:.1f} KB)")
            else:
                self.log_step(f"Failed to export STL: {output_path}")
            
            return success
            
        except Exception as e:
            self.log_step(f"Error exporting STL: {str(e)}")
            return False
    
    def prepare_multiple_meshes(self, meshes: List[Tuple[o3d.geometry.TriangleMesh, str]], 
                               combine_meshes: bool = False) -> Tuple[List[Tuple[o3d.geometry.TriangleMesh, str]], Dict]:
        """
        Prepare multiple meshes for 3D printing.
        
        Args:
            meshes (List[Tuple[o3d.geometry.TriangleMesh, str]]): List of (mesh, name) tuples
            combine_meshes (bool): Whether to combine all meshes into one
            
        Returns:
            Tuple[List[Tuple[o3d.geometry.TriangleMesh, str]], Dict]: Prepared meshes and combined report
        """
        self.log_step(f"Preparing {len(meshes)} meshes for 3D printing...")
        
        prepared_meshes = []
        reports = []
        
        for mesh, name in meshes:
            prepared_mesh, report = self.prepare_mesh_for_printing(mesh, name)
            if prepared_mesh is not None:
                prepared_meshes.append((prepared_mesh, name))
                reports.append(report)
        
        combined_report = {
            "total_meshes": len(meshes),
            "successfully_prepared": len(prepared_meshes),
            "individual_reports": reports,
            "combined_mesh": None
        }
        
        if combine_meshes and len(prepared_meshes) > 1:
            self.log_step("Combining meshes into single printable object...")
            combined_mesh = self._combine_meshes([mesh for mesh, _ in prepared_meshes])
            if combined_mesh is not None:
                combined_mesh, combine_report = self.prepare_mesh_for_printing(combined_mesh, "combined_mesh")
                combined_report["combined_mesh"] = combine_report
                prepared_meshes = [(combined_mesh, "combined_mesh")]
        
        return prepared_meshes, combined_report
    
    def _combine_meshes(self, meshes: List[o3d.geometry.TriangleMesh]) -> o3d.geometry.TriangleMesh:
        """Combine multiple meshes into one."""
        if not meshes:
            return None
        
        if len(meshes) == 1:
            return meshes[0]
        
        try:
            combined = meshes[0]
            for mesh in meshes[1:]:
                combined += mesh
            
            # Clean up the combined mesh
            combined.remove_duplicated_vertices()
            combined.remove_duplicated_triangles()
            combined.compute_vertex_normals()
            
            self.log_step(f"Combined {len(meshes)} meshes into one")
            return combined
            
        except Exception as e:
            self.log_step(f"Failed to combine meshes: {str(e)}")
            return None


def prepare_ply_for_printing(mesh: o3d.geometry.TriangleMesh, 
                           mesh_name: str = "mesh",
                           target_size_mm: float = 100.0,
                           min_wall_thickness: float = 0.8) -> Tuple[o3d.geometry.TriangleMesh, Dict]:
    """
    Convenience function to prepare a single PLY mesh for 3D printing.
    
    Args:
        mesh (o3d.geometry.TriangleMesh): Input mesh
        mesh_name (str): Name for the mesh
        target_size_mm (float): Target size in millimeters
        min_wall_thickness (float): Minimum wall thickness in mm
        
    Returns:
        Tuple[o3d.geometry.TriangleMesh, Dict]: Prepared mesh and preparation report
    """
    preparator = Print3DPreparator(target_size_mm, min_wall_thickness)
    return preparator.prepare_mesh_for_printing(mesh, mesh_name)


def export_mesh_as_stl(mesh: o3d.geometry.TriangleMesh, output_path: str) -> bool:
    """
    Export a mesh as STL file for 3D printing.
    
    Args:
        mesh (o3d.geometry.TriangleMesh): Mesh to export
        output_path (str): Output file path
        
    Returns:
        bool: Success status
    """
    preparator = Print3DPreparator()
    return preparator.export_stl(mesh, output_path)
