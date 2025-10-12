#!/usr/bin/env python3
"""
Example usage of the OBJ Analyzer utility

This demonstrates how to use obj_analyzer.py from within Python code.
"""

from obj_analyzer import analyze_obj_file, print_analysis, export_analysis_json


def example_basic_analysis():
    """Basic analysis example."""
    print("="*70)
    print("EXAMPLE 1: Basic Analysis")
    print("="*70)
    
    # Analyze an OBJ file
    analysis = analyze_obj_file(
        "/Users/dave/AI/HPE/HPE-Nvidia-Vista-3D/output/PA00000002/obj/2.5MM_ARTERIAL_3/liver.obj"
    )
    
    # Print the analysis
    print_analysis(analysis)


def example_programmatic_access():
    """Example of accessing analysis data programmatically."""
    print("\n" + "="*70)
    print("EXAMPLE 2: Programmatic Access")
    print("="*70 + "\n")
    
    # Analyze an OBJ file
    analysis = analyze_obj_file(
        "/Users/dave/AI/HPE/HPE-Nvidia-Vista-3D/output/PA00000002/obj/2.5MM_ARTERIAL_3/liver.obj"
    )
    
    if analysis['success']:
        # Access specific data
        vertex_count = analysis['geometry']['vertex_count']
        face_count = analysis['geometry']['face_count']
        is_watertight = analysis['quality_metrics']['is_watertight']
        surface_area = analysis['quality_metrics']['surface_area']
        
        print(f"Mesh Statistics:")
        print(f"  Vertices: {vertex_count:,}")
        print(f"  Faces: {face_count:,}")
        print(f"  Watertight: {is_watertight}")
        print(f"  Surface Area: {surface_area:.2f}")
        
        # Check for issues
        if analysis['mesh_issues']['has_issues']:
            print(f"\n⚠️ Issues found:")
            for issue in analysis['mesh_issues']['issues']:
                print(f"  - {issue}")
        
        # Check connectivity
        components = analysis['connectivity']['connected_component_count']
        print(f"\nConnected Components: {components}")
        
        if components > 1:
            print("  Component details:")
            for comp in analysis['connectivity']['components']:
                print(f"    Component {comp['component_id']}: {comp['vertex_count']} vertices, {comp['face_count']} faces")


def example_batch_analysis():
    """Example of analyzing multiple files."""
    print("\n" + "="*70)
    print("EXAMPLE 3: Batch Analysis")
    print("="*70 + "\n")
    
    import os
    from pathlib import Path
    
    # Get all OBJ files in a directory
    obj_dir = "/Users/dave/AI/HPE/HPE-Nvidia-Vista-3D/output/PA00000002/obj/2.5MM_ARTERIAL_3"
    obj_files = list(Path(obj_dir).glob("*.obj"))[:5]  # Just analyze first 5 for demo
    
    print(f"Analyzing {len(obj_files)} files from {obj_dir}...\n")
    
    results = []
    for obj_file in obj_files:
        print(f"Analyzing {obj_file.name}...")
        analysis = analyze_obj_file(str(obj_file), verbose=False)
        
        if analysis['success']:
            results.append({
                'name': obj_file.name,
                'vertices': analysis['geometry']['vertex_count'],
                'faces': analysis['geometry']['face_count'],
                'watertight': analysis['quality_metrics']['is_watertight'],
                'surface_area': analysis['quality_metrics']['surface_area'],
            })
    
    # Print summary table
    print("\n" + "-"*80)
    print(f"{'File':<30} {'Vertices':>12} {'Faces':>12} {'Watertight':>12} {'Area':>12}")
    print("-"*80)
    
    for result in results:
        watertight_str = "✓" if result['watertight'] else "✗"
        print(f"{result['name']:<30} {result['vertices']:>12,} {result['faces']:>12,} {watertight_str:>12} {result['surface_area']:>12.2f}")
    
    print("-"*80)


def example_export_to_json():
    """Example of exporting analysis to JSON."""
    print("\n" + "="*70)
    print("EXAMPLE 4: Export to JSON")
    print("="*70 + "\n")
    
    # Analyze an OBJ file
    analysis = analyze_obj_file(
        "/Users/dave/AI/HPE/HPE-Nvidia-Vista-3D/output/PA00000002/obj/2.5MM_ARTERIAL_3/liver.obj",
        verbose=True
    )
    
    # Export to JSON
    output_path = "/tmp/liver_analysis.json"
    export_analysis_json(analysis, output_path)
    print(f"\nJSON file created at: {output_path}")


if __name__ == "__main__":
    # Run examples
    # Uncomment the ones you want to run
    
    # example_basic_analysis()
    example_programmatic_access()
    example_batch_analysis()
    # example_export_to_json()

