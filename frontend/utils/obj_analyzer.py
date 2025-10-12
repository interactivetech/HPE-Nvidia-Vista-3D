#!/usr/bin/env python3
"""
obj_analyzer.py

A comprehensive utility to analyze .obj files and provide detailed mesh statistics,
quality metrics, and structural information.

Requirements
------------
- trimesh
- numpy
- python-dotenv (optional)

Example
-------
    # Analyze a single file
    python obj_analyzer.py path/to/model.obj
    
    # Analyze with detailed output
    python obj_analyzer.py path/to/model.obj --verbose
    
    # Export analysis to JSON
    python obj_analyzer.py path/to/model.obj --json output.json
    
    # Analyze from code
    from utils.obj_analyzer import analyze_obj_file, print_analysis
    
    analysis = analyze_obj_file("model.obj")
    print_analysis(analysis)
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

import numpy as np
import trimesh


def get_file_info(file_path: str) -> Dict[str, Any]:
    """Get basic file information."""
    file_stat = os.stat(file_path)
    
    return {
        'file_path': os.path.abspath(file_path),
        'file_name': os.path.basename(file_path),
        'file_size_bytes': file_stat.st_size,
        'file_size_mb': round(file_stat.st_size / (1024 * 1024), 3),
        'last_modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
    }


def parse_obj_raw(file_path: str) -> Dict[str, Any]:
    """Parse OBJ file to get raw element counts."""
    vertex_count = 0
    normal_count = 0
    texcoord_count = 0
    face_count = 0
    material_count = 0
    group_count = 0
    object_count = 0
    
    materials_used = set()
    groups = set()
    objects = set()
    
    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split(None, 1)
                if not parts:
                    continue
                
                cmd = parts[0]
                
                if cmd == 'v':
                    vertex_count += 1
                elif cmd == 'vn':
                    normal_count += 1
                elif cmd == 'vt':
                    texcoord_count += 1
                elif cmd == 'f':
                    face_count += 1
                elif cmd == 'usemtl' and len(parts) > 1:
                    materials_used.add(parts[1])
                elif cmd == 'g' and len(parts) > 1:
                    groups.add(parts[1])
                elif cmd == 'o' and len(parts) > 1:
                    objects.add(parts[1])
    
    except Exception as e:
        print(f"Warning: Error parsing OBJ file: {e}", file=sys.stderr)
    
    return {
        'vertex_count': vertex_count,
        'normal_count': normal_count,
        'texcoord_count': texcoord_count,
        'face_count': face_count,
        'material_count': len(materials_used),
        'materials_used': list(materials_used),
        'group_count': len(groups),
        'groups': list(groups),
        'object_count': len(objects),
        'objects': list(objects),
    }


def get_mesh_geometry(mesh: trimesh.Trimesh) -> Dict[str, Any]:
    """Get basic mesh geometry information."""
    return {
        'vertex_count': len(mesh.vertices),
        'face_count': len(mesh.faces),
        'edge_count': len(mesh.edges_unique),
        'has_vertex_normals': mesh.vertex_normals is not None and len(mesh.vertex_normals) > 0,
        'has_face_normals': mesh.face_normals is not None and len(mesh.face_normals) > 0,
        'has_vertex_colors': hasattr(mesh.visual, 'vertex_colors') and mesh.visual.vertex_colors is not None,
        'has_uv_coordinates': hasattr(mesh.visual, 'uv') and mesh.visual.uv is not None,
    }


def get_bounding_box_info(mesh: trimesh.Trimesh) -> Dict[str, Any]:
    """Get bounding box information."""
    bounds = mesh.bounds
    extents = mesh.extents
    
    return {
        'min': bounds[0].tolist(),
        'max': bounds[1].tolist(),
        'dimensions': extents.tolist(),
        'center': mesh.centroid.tolist(),
        'bounding_box_volume': float(np.prod(extents)),
    }


def get_mesh_quality_metrics(mesh: trimesh.Trimesh) -> Dict[str, Any]:
    """Get mesh quality metrics."""
    metrics = {
        'is_watertight': bool(mesh.is_watertight),
        'is_winding_consistent': bool(mesh.is_winding_consistent),
        'is_volume': bool(mesh.is_volume),
        'euler_number': int(mesh.euler_number),
    }
    
    # Surface area
    try:
        metrics['surface_area'] = float(mesh.area)
    except Exception as e:
        metrics['surface_area'] = None
        metrics['surface_area_error'] = str(e)
    
    # Volume (only meaningful for watertight meshes)
    try:
        if mesh.is_watertight:
            metrics['volume'] = float(mesh.volume)
        else:
            metrics['volume'] = None
            metrics['volume_note'] = "Mesh is not watertight"
    except Exception as e:
        metrics['volume'] = None
        metrics['volume_error'] = str(e)
    
    # Center of mass (only for watertight meshes)
    try:
        if mesh.is_watertight:
            metrics['center_of_mass'] = mesh.center_mass.tolist()
        else:
            metrics['center_of_mass'] = None
    except Exception as e:
        metrics['center_of_mass'] = None
    
    # Scale
    try:
        metrics['scale'] = float(mesh.scale)
    except Exception as e:
        metrics['scale'] = None
    
    return metrics


def get_edge_statistics(mesh: trimesh.Trimesh) -> Dict[str, Any]:
    """Get edge length statistics."""
    try:
        edges = mesh.edges_unique
        edge_vectors = mesh.vertices[edges[:, 1]] - mesh.vertices[edges[:, 0]]
        edge_lengths = np.linalg.norm(edge_vectors, axis=1)
        
        return {
            'edge_count': len(edges),
            'min_edge_length': float(np.min(edge_lengths)),
            'max_edge_length': float(np.max(edge_lengths)),
            'mean_edge_length': float(np.mean(edge_lengths)),
            'median_edge_length': float(np.median(edge_lengths)),
            'std_edge_length': float(np.std(edge_lengths)),
        }
    except Exception as e:
        return {
            'error': str(e)
        }


def get_face_statistics(mesh: trimesh.Trimesh) -> Dict[str, Any]:
    """Get face statistics."""
    try:
        face_angles = mesh.face_angles
        
        stats = {
            'triangle_count': len(mesh.faces),
            'degenerate_face_count': int(np.sum(mesh.area_faces < 1e-10)),
        }
        
        # Face angle statistics
        if face_angles is not None and len(face_angles) > 0:
            stats['min_face_angle_deg'] = float(np.min(face_angles) * 180 / np.pi)
            stats['max_face_angle_deg'] = float(np.max(face_angles) * 180 / np.pi)
            stats['mean_face_angle_deg'] = float(np.mean(face_angles) * 180 / np.pi)
        
        # Face area statistics
        if mesh.area_faces is not None and len(mesh.area_faces) > 0:
            stats['min_face_area'] = float(np.min(mesh.area_faces))
            stats['max_face_area'] = float(np.max(mesh.area_faces))
            stats['mean_face_area'] = float(np.mean(mesh.area_faces))
            stats['median_face_area'] = float(np.median(mesh.area_faces))
        
        return stats
    except Exception as e:
        return {
            'triangle_count': len(mesh.faces),
            'error': str(e)
        }


def get_connectivity_info(mesh: trimesh.Trimesh) -> Dict[str, Any]:
    """Get mesh connectivity information."""
    try:
        # Split into connected components
        components = mesh.split(only_watertight=False)
        
        component_info = []
        for i, comp in enumerate(components):
            component_info.append({
                'component_id': i,
                'vertex_count': len(comp.vertices),
                'face_count': len(comp.faces),
                'is_watertight': bool(comp.is_watertight),
                'surface_area': float(comp.area),
                'volume': float(comp.volume) if comp.is_watertight else None,
            })
        
        return {
            'connected_component_count': len(components),
            'components': component_info,
            'is_single_body': len(components) == 1,
        }
    except Exception as e:
        return {
            'error': str(e)
        }


def get_vertex_statistics(mesh: trimesh.Trimesh) -> Dict[str, Any]:
    """Get vertex statistics."""
    try:
        vertices = mesh.vertices
        
        return {
            'min_coordinates': vertices.min(axis=0).tolist(),
            'max_coordinates': vertices.max(axis=0).tolist(),
            'mean_coordinates': vertices.mean(axis=0).tolist(),
            'std_coordinates': vertices.std(axis=0).tolist(),
        }
    except Exception as e:
        return {
            'error': str(e)
        }


def check_mesh_issues(mesh: trimesh.Trimesh) -> Dict[str, Any]:
    """Check for common mesh issues."""
    issues = []
    warnings = []
    
    # Check if watertight
    if not mesh.is_watertight:
        issues.append("Mesh is not watertight (has holes or open boundaries)")
    
    # Check winding consistency
    if not mesh.is_winding_consistent:
        issues.append("Face winding is inconsistent (normals may be flipped)")
    
    # Check for degenerate faces
    degenerate_count = int(np.sum(mesh.area_faces < 1e-10))
    if degenerate_count > 0:
        warnings.append(f"Found {degenerate_count} degenerate faces (near-zero area)")
    
    # Check for duplicate vertices
    try:
        merged = mesh.merge_vertices()
        removed_vertices = len(mesh.vertices) - len(merged.vertices)
        if removed_vertices > 0:
            warnings.append(f"Found {removed_vertices} duplicate vertices")
    except Exception:
        pass
    
    # Check for duplicate faces
    try:
        unique_faces = np.unique(np.sort(mesh.faces, axis=1), axis=0)
        duplicate_faces = len(mesh.faces) - len(unique_faces)
        if duplicate_faces > 0:
            warnings.append(f"Found {duplicate_faces} duplicate faces")
    except Exception:
        pass
    
    # Check for unreferenced vertices
    try:
        referenced_vertices = np.unique(mesh.faces.flatten())
        unreferenced = len(mesh.vertices) - len(referenced_vertices)
        if unreferenced > 0:
            warnings.append(f"Found {unreferenced} unreferenced vertices")
    except Exception:
        pass
    
    return {
        'has_issues': len(issues) > 0,
        'has_warnings': len(warnings) > 0,
        'issues': issues,
        'warnings': warnings,
    }


def get_visual_info(mesh: trimesh.Trimesh) -> Dict[str, Any]:
    """Get visual/material information."""
    visual_info = {
        'has_visual': hasattr(mesh, 'visual') and mesh.visual is not None,
    }
    
    if visual_info['has_visual']:
        visual = mesh.visual
        
        # Vertex colors
        if hasattr(visual, 'vertex_colors') and visual.vertex_colors is not None:
            colors = visual.vertex_colors
            visual_info['has_vertex_colors'] = True
            visual_info['vertex_color_count'] = len(colors)
            
            # Get unique colors
            if len(colors) > 0:
                unique_colors = np.unique(colors, axis=0)
                visual_info['unique_color_count'] = len(unique_colors)
                
                # Sample some colors
                if len(unique_colors) <= 10:
                    visual_info['color_palette'] = unique_colors.tolist()
        else:
            visual_info['has_vertex_colors'] = False
        
        # UV coordinates
        if hasattr(visual, 'uv') and visual.uv is not None:
            visual_info['has_uv'] = True
            visual_info['uv_count'] = len(visual.uv)
        else:
            visual_info['has_uv'] = False
        
        # Material
        if hasattr(visual, 'material'):
            visual_info['has_material'] = True
            try:
                if hasattr(visual.material, 'name'):
                    visual_info['material_name'] = visual.material.name
            except Exception:
                pass
        else:
            visual_info['has_material'] = False
    
    return visual_info


def analyze_obj_file(file_path: str, verbose: bool = False) -> Dict[str, Any]:
    """
    Perform a comprehensive analysis of an OBJ file.
    
    Args:
        file_path: Path to the .obj file
        verbose: If True, print progress messages
        
    Returns:
        Dictionary containing all analysis results
    """
    if verbose:
        print(f"[*] Analyzing: {file_path}")
    
    # Check if file exists
    if not os.path.exists(file_path):
        return {
            'error': f"File not found: {file_path}",
            'success': False,
        }
    
    # Get file info
    if verbose:
        print("[*] Getting file information...")
    file_info = get_file_info(file_path)
    
    # Parse raw OBJ
    if verbose:
        print("[*] Parsing OBJ file...")
    raw_info = parse_obj_raw(file_path)
    
    # Load mesh with trimesh
    if verbose:
        print("[*] Loading mesh with trimesh...")
    
    try:
        mesh = trimesh.load(file_path, force='mesh', process=False)
        
        # If we got a Scene instead of a Mesh, try to extract the mesh
        if isinstance(mesh, trimesh.Scene):
            if verbose:
                print("[*] Converting scene to mesh...")
            meshes = list(mesh.geometry.values())
            if len(meshes) == 0:
                return {
                    'error': "Scene contains no geometry",
                    'success': False,
                }
            elif len(meshes) == 1:
                mesh = meshes[0]
            else:
                # Combine multiple meshes
                mesh = trimesh.util.concatenate(meshes)
        
        # Get all analysis components
        if verbose:
            print("[*] Analyzing mesh geometry...")
        geometry = get_mesh_geometry(mesh)
        
        if verbose:
            print("[*] Analyzing bounding box...")
        bounding_box = get_bounding_box_info(mesh)
        
        if verbose:
            print("[*] Analyzing mesh quality...")
        quality = get_mesh_quality_metrics(mesh)
        
        if verbose:
            print("[*] Analyzing edges...")
        edges = get_edge_statistics(mesh)
        
        if verbose:
            print("[*] Analyzing faces...")
        faces = get_face_statistics(mesh)
        
        if verbose:
            print("[*] Analyzing connectivity...")
        connectivity = get_connectivity_info(mesh)
        
        if verbose:
            print("[*] Analyzing vertices...")
        vertices = get_vertex_statistics(mesh)
        
        if verbose:
            print("[*] Checking for mesh issues...")
        issues = check_mesh_issues(mesh)
        
        if verbose:
            print("[*] Analyzing visual properties...")
        visual = get_visual_info(mesh)
        
        # Compile full analysis
        analysis = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'file_info': file_info,
            'raw_obj_data': raw_info,
            'geometry': geometry,
            'bounding_box': bounding_box,
            'quality_metrics': quality,
            'edge_statistics': edges,
            'face_statistics': faces,
            'vertex_statistics': vertices,
            'connectivity': connectivity,
            'visual_properties': visual,
            'mesh_issues': issues,
        }
        
        if verbose:
            print("[✓] Analysis complete!")
        
        return analysis
        
    except Exception as e:
        return {
            'error': f"Failed to load mesh: {str(e)}",
            'success': False,
            'file_info': file_info,
            'raw_obj_data': raw_info,
        }


def print_analysis(analysis: Dict[str, Any], detailed: bool = False):
    """
    Print analysis results in a human-readable format.
    
    Args:
        analysis: Analysis dictionary from analyze_obj_file()
        detailed: If True, print all details including lists
    """
    if not analysis.get('success', False):
        print(f"\n❌ Analysis failed: {analysis.get('error', 'Unknown error')}")
        return
    
    print("\n" + "="*70)
    print("OBJ FILE ANALYSIS REPORT")
    print("="*70)
    
    # File Info
    print("\n📄 FILE INFORMATION")
    print("-" * 70)
    file_info = analysis['file_info']
    print(f"  File Name:        {file_info['file_name']}")
    print(f"  File Path:        {file_info['file_path']}")
    print(f"  File Size:        {file_info['file_size_mb']} MB ({file_info['file_size_bytes']:,} bytes)")
    print(f"  Last Modified:    {file_info['last_modified']}")
    
    # Geometry
    print("\n📐 GEOMETRY")
    print("-" * 70)
    geometry = analysis['geometry']
    print(f"  Vertices:         {geometry['vertex_count']:,}")
    print(f"  Faces:            {geometry['face_count']:,}")
    print(f"  Edges:            {geometry['edge_count']:,}")
    print(f"  Vertex Normals:   {'Yes' if geometry['has_vertex_normals'] else 'No'}")
    print(f"  Face Normals:     {'Yes' if geometry['has_face_normals'] else 'No'}")
    print(f"  Vertex Colors:    {'Yes' if geometry['has_vertex_colors'] else 'No'}")
    print(f"  UV Coordinates:   {'Yes' if geometry['has_uv_coordinates'] else 'No'}")
    
    # Bounding Box
    print("\n📦 BOUNDING BOX")
    print("-" * 70)
    bbox = analysis['bounding_box']
    print(f"  Dimensions:       X={bbox['dimensions'][0]:.2f}, Y={bbox['dimensions'][1]:.2f}, Z={bbox['dimensions'][2]:.2f}")
    print(f"  Center:           X={bbox['center'][0]:.2f}, Y={bbox['center'][1]:.2f}, Z={bbox['center'][2]:.2f}")
    print(f"  Min Point:        X={bbox['min'][0]:.2f}, Y={bbox['min'][1]:.2f}, Z={bbox['min'][2]:.2f}")
    print(f"  Max Point:        X={bbox['max'][0]:.2f}, Y={bbox['max'][1]:.2f}, Z={bbox['max'][2]:.2f}")
    print(f"  BB Volume:        {bbox['bounding_box_volume']:.2f}")
    
    # Quality Metrics
    print("\n✨ QUALITY METRICS")
    print("-" * 70)
    quality = analysis['quality_metrics']
    print(f"  Watertight:       {'✓ Yes' if quality['is_watertight'] else '✗ No'}")
    print(f"  Winding:          {'✓ Consistent' if quality['is_winding_consistent'] else '✗ Inconsistent'}")
    print(f"  Is Volume:        {'✓ Yes' if quality['is_volume'] else '✗ No'}")
    print(f"  Euler Number:     {quality['euler_number']}")
    
    if quality['surface_area'] is not None:
        print(f"  Surface Area:     {quality['surface_area']:.2f}")
    else:
        print(f"  Surface Area:     N/A")
    
    if quality['volume'] is not None:
        print(f"  Volume:           {quality['volume']:.2f}")
    else:
        print(f"  Volume:           N/A (mesh not watertight)")
    
    if quality['scale'] is not None:
        print(f"  Scale:            {quality['scale']:.2f}")
    
    # Edge Statistics
    print("\n📏 EDGE STATISTICS")
    print("-" * 70)
    edges = analysis['edge_statistics']
    if 'error' not in edges:
        print(f"  Edge Count:       {edges['edge_count']:,}")
        print(f"  Min Length:       {edges['min_edge_length']:.4f}")
        print(f"  Max Length:       {edges['max_edge_length']:.4f}")
        print(f"  Mean Length:      {edges['mean_edge_length']:.4f}")
        print(f"  Median Length:    {edges['median_edge_length']:.4f}")
        print(f"  Std Deviation:    {edges['std_edge_length']:.4f}")
    else:
        print(f"  Error: {edges['error']}")
    
    # Face Statistics
    print("\n🔺 FACE STATISTICS")
    print("-" * 70)
    faces = analysis['face_statistics']
    if 'error' not in faces:
        print(f"  Triangle Count:   {faces['triangle_count']:,}")
        if 'degenerate_face_count' in faces:
            print(f"  Degenerate Faces: {faces['degenerate_face_count']}")
        if 'min_face_angle_deg' in faces:
            print(f"  Min Angle:        {faces['min_face_angle_deg']:.2f}°")
            print(f"  Max Angle:        {faces['max_face_angle_deg']:.2f}°")
            print(f"  Mean Angle:       {faces['mean_face_angle_deg']:.2f}°")
        if 'min_face_area' in faces:
            print(f"  Min Face Area:    {faces['min_face_area']:.6f}")
            print(f"  Max Face Area:    {faces['max_face_area']:.6f}")
            print(f"  Mean Face Area:   {faces['mean_face_area']:.6f}")
    else:
        print(f"  Triangle Count:   {faces['triangle_count']:,}")
        print(f"  Error: {faces['error']}")
    
    # Connectivity
    print("\n🔗 CONNECTIVITY")
    print("-" * 70)
    connectivity = analysis['connectivity']
    if 'error' not in connectivity:
        print(f"  Components:       {connectivity['connected_component_count']}")
        print(f"  Single Body:      {'✓ Yes' if connectivity['is_single_body'] else '✗ No'}")
        
        if detailed and connectivity['connected_component_count'] > 1:
            print("\n  Component Details:")
            for comp in connectivity['components'][:10]:  # Limit to first 10
                print(f"    Component {comp['component_id']}:")
                print(f"      Vertices:   {comp['vertex_count']:,}")
                print(f"      Faces:      {comp['face_count']:,}")
                print(f"      Watertight: {'Yes' if comp['is_watertight'] else 'No'}")
    else:
        print(f"  Error: {connectivity['error']}")
    
    # Visual Properties
    print("\n🎨 VISUAL PROPERTIES")
    print("-" * 70)
    visual = analysis['visual_properties']
    print(f"  Has Visual Data:  {'Yes' if visual['has_visual'] else 'No'}")
    
    if visual.get('has_vertex_colors'):
        print(f"  Vertex Colors:    Yes ({visual['vertex_color_count']:,} colors)")
        if 'unique_color_count' in visual:
            print(f"  Unique Colors:    {visual['unique_color_count']}")
    else:
        print(f"  Vertex Colors:    No")
    
    if visual.get('has_uv'):
        print(f"  UV Coordinates:   Yes ({visual['uv_count']} coordinates)")
    else:
        print(f"  UV Coordinates:   No")
    
    if visual.get('has_material'):
        print(f"  Material:         Yes")
        if 'material_name' in visual:
            print(f"  Material Name:    {visual['material_name']}")
    else:
        print(f"  Material:         No")
    
    # Mesh Issues
    print("\n⚠️  MESH ISSUES")
    print("-" * 70)
    issues = analysis['mesh_issues']
    
    if issues['has_issues']:
        print("  Issues Found:")
        for issue in issues['issues']:
            print(f"    ❌ {issue}")
    else:
        print("  ✓ No critical issues found")
    
    if issues['has_warnings']:
        print("\n  Warnings:")
        for warning in issues['warnings']:
            print(f"    ⚠️  {warning}")
    
    # Raw OBJ Data
    if detailed:
        print("\n📝 RAW OBJ DATA")
        print("-" * 70)
        raw = analysis['raw_obj_data']
        print(f"  Vertices (v):     {raw['vertex_count']:,}")
        print(f"  Normals (vn):     {raw['normal_count']:,}")
        print(f"  Tex Coords (vt):  {raw['texcoord_count']:,}")
        print(f"  Faces (f):        {raw['face_count']:,}")
        print(f"  Materials:        {raw['material_count']}")
        if raw['materials_used']:
            print(f"    Used: {', '.join(raw['materials_used'][:5])}")
        print(f"  Groups (g):       {raw['group_count']}")
        print(f"  Objects (o):      {raw['object_count']}")
    
    print("\n" + "="*70)
    print()


def export_analysis_json(analysis: Dict[str, Any], output_path: str):
    """Export analysis to JSON file."""
    with open(output_path, 'w') as f:
        json.dump(analysis, f, indent=2)
    print(f"[✓] Analysis exported to: {output_path}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Comprehensive OBJ file analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s model.obj
  %(prog)s model.obj --verbose
  %(prog)s model.obj --detailed
  %(prog)s model.obj --json analysis.json
  %(prog)s model.obj --detailed --json analysis.json
        """
    )
    
    parser.add_argument(
        'obj_file',
        help='Path to the .obj file to analyze'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show verbose progress messages during analysis'
    )
    
    parser.add_argument(
        '-d', '--detailed',
        action='store_true',
        help='Show detailed output including all component information'
    )
    
    parser.add_argument(
        '-j', '--json',
        metavar='OUTPUT',
        help='Export analysis results to JSON file'
    )
    
    parser.add_argument(
        '--json-only',
        action='store_true',
        help='Only export JSON, do not print to console'
    )
    
    return parser.parse_args()


def main():
    args = parse_args()
    
    # Perform analysis
    analysis = analyze_obj_file(args.obj_file, verbose=args.verbose)
    
    # Print results (unless json-only)
    if not args.json_only:
        print_analysis(analysis, detailed=args.detailed)
    
    # Export JSON if requested
    if args.json:
        export_analysis_json(analysis, args.json)
    
    # Exit with appropriate code
    if not analysis.get('success', False):
        sys.exit(1)


if __name__ == "__main__":
    main()

