#!/usr/bin/env python3
"""
NiiVue-Style 3D PNG Renderer for Vista-3D Pipeline

This script creates 3D PNG renders from NIfTI files using NiiVue-compatible rendering methods.
It processes all NIfTI files in the output directory structure and generates high-quality
PNG images optimized for 3D visualization and web-based viewers.

Features:
- Batch processing of all patient NIfTI files
- NiiVue-compatible 3D rendering approach
- PNG format output with proper lighting and shading
- Progress tracking and error handling
- Configurable mesh settings

Usage:
    # Process all patients
    python mini3d_render.py
    
    # Process specific patient
    python mini3d_render.py --patient PA00000002
    
    # Custom settings
    python mini3d_render.py --threshold 0.1

Requirements:
    - nibabel: For NIfTI file handling
    - skimage: For marching cubes algorithm
    - numpy: For numerical operations
    - matplotlib: For 3D rendering and PNG export
    - tqdm: For progress bars
    - dotenv: For environment configuration
"""

import argparse
import sys
import os
import warnings
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm
import numpy as np
import nibabel as nib
from skimage import measure
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend



def load_environment():
    """Load environment variables from .env file and get output folder"""
    load_dotenv()
    output_folder = os.getenv('OUTPUT_FOLDER')
    
    if not output_folder:
        raise ValueError("OUTPUT_FOLDER must be set in .env file")
    
    if not os.path.isabs(output_folder):
        raise ValueError("OUTPUT_FOLDER must be an absolute path")
    
    return Path(output_folder)


def load_nifti(filepath):
    """
    Load NIfTI file and return image data and affine transformation.
    
    Args:
        filepath (str): Path to NIfTI file
        
    Returns:
        tuple: (image_data, affine_matrix)
    """
    try:
        nifti_img = nib.load(filepath)
        data = nifti_img.get_fdata()
        affine = nifti_img.affine
        return data, affine
    except Exception as e:
        print(f"Error loading NIfTI file {filepath}: {e}")
        return None, None


def apply_threshold(data, threshold=0.1):
    """
    Apply threshold to NIfTI data for surface extraction.
    
    Args:
        data (np.ndarray): Input data
        threshold (float): Threshold value
        
    Returns:
        np.ndarray: Thresholded data
    """
    return (data > threshold).astype(np.float32)


def generate_mesh(data, threshold=0.1, label_value=None, smooth=1.0, spacing=None):
    """
    Generate mesh from NIfTI data using marching cubes.
    
    Args:
        data (np.ndarray): Input data
        threshold (float): Threshold for surface extraction
        label_value (int): Specific label value to extract (None for all)
        smooth (float): Smoothing factor
        spacing (tuple): Voxel spacing
        
    Returns:
        tuple: (vertices, faces, normals) or (None, None, None) if failed
    """
    try:
        # Apply threshold
        if label_value is not None:
            binary_data = (data == label_value).astype(np.float32)
        else:
            binary_data = apply_threshold(data, threshold)
        
        # Check if we have any data to work with
        if np.sum(binary_data) == 0:
            print("Warning: No data above threshold found")
            return None, None, None
        
        # Apply smoothing if requested
        if smooth > 0:
            from scipy import ndimage
            binary_data = ndimage.gaussian_filter(binary_data, sigma=smooth)
        
        # Generate mesh using marching cubes
        if spacing is None:
            spacing = (1.0, 1.0, 1.0)
        
        vertices, faces, normals, values = measure.marching_cubes(
            binary_data, 
            level=0.5, 
            spacing=spacing,
            allow_degenerate=False
        )
        
        return vertices, faces, normals
        
    except Exception as e:
        print(f"Error generating mesh: {e}")
        return None, None, None


def render_3d_png(vertices, faces, normals, output_path, title="NIfTI 3D Render"):
    """
    Render 3D mesh to PNG image using NiiVue-style visualization.
    
    Args:
        vertices (np.ndarray): Mesh vertices
        faces (np.ndarray): Mesh faces
        normals (np.ndarray): Mesh normals
        output_path (Path): Path to output PNG file
        title (str): Title for the render
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create figure with NiiVue-style dark background
        fig = plt.figure(figsize=(12, 10), facecolor='black')
        ax = fig.add_subplot(111, projection='3d')
        
        # Set NiiVue-style appearance
        ax.set_facecolor('black')
        ax.grid(False)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_zticks([])
        
        # Remove axis spines
        ax._axis3don = False
        
        # Set viewing angle similar to NiiVue
        ax.view_init(elev=20, azim=45)
        
        # Plot the mesh with NiiVue-style coloring
        if len(faces) > 0:
            # Create a colormap based on vertex positions (similar to NiiVue)
            colors = plt.cm.viridis(vertices[:, 2] / vertices[:, 2].max())
            
            # Plot the mesh
            ax.plot_trisurf(
                vertices[:, 0], 
                vertices[:, 1], 
                vertices[:, 2], 
                triangles=faces,
                facecolors=colors,
                edgecolor='none',
                alpha=0.8,
                shade=True
            )
        else:
            # If no faces, plot as point cloud
            ax.scatter(vertices[:, 0], vertices[:, 1], vertices[:, 2], 
                      c=vertices[:, 2], cmap='viridis', s=1, alpha=0.6)
        
        # Set equal aspect ratio
        max_range = np.array([vertices[:, 0].max() - vertices[:, 0].min(),
                             vertices[:, 1].max() - vertices[:, 1].min(),
                             vertices[:, 2].max() - vertices[:, 2].min()]).max() / 2.0
        
        mid_x = (vertices[:, 0].max() + vertices[:, 0].min()) * 0.5
        mid_y = (vertices[:, 1].max() + vertices[:, 1].min()) * 0.5
        mid_z = (vertices[:, 2].max() + vertices[:, 2].min()) * 0.5
        
        ax.set_xlim(mid_x - max_range, mid_x + max_range)
        ax.set_ylim(mid_y - max_range, mid_y + max_range)
        ax.set_zlim(mid_z - max_range, mid_z + max_range)
        
        # Add title with NiiVue-style formatting
        plt.suptitle(title, color='white', fontsize=14, fontweight='bold')
        
        # Add info text
        info_text = f"Vertices: {len(vertices):,}\nFaces: {len(faces):,}"
        ax.text2D(0.02, 0.98, info_text, transform=ax.transAxes, 
                 fontsize=10, color='white', verticalalignment='top',
                 bbox=dict(boxstyle='round', facecolor='black', alpha=0.7))
        
        # Save as PNG with high DPI
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight', 
                   facecolor='black', edgecolor='none')
        plt.close(fig)
        
        return True
        
    except Exception as e:
        print(f"Error rendering PNG: {e}")
        return False




def process_nifti_file(nifti_path, output_path, threshold=0.1, label_value=None, smooth=1.0, verbose=False):
    """
    Process a single NIfTI file and create a PNG render using NiiVue-style rendering.
    
    Args:
        nifti_path (Path): Path to input NIfTI file
        output_path (Path): Path to output PNG file
        threshold (float): Threshold for surface extraction
        label_value (int): Specific label value to extract
        smooth (float): Smoothing factor
        verbose (bool): Verbose output
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if verbose:
            print(f"Processing: {nifti_path.name}")
        
        # Load NIfTI file
        data, affine = load_nifti(str(nifti_path))
        if data is None:
            return False
        
        # Extract voxel spacing
        spacing = None
        if affine is not None:
            spacing = tuple(np.abs(np.diag(affine[:3, :3])))
        
        if verbose:
            print(f"  Data shape: {data.shape}")
            print(f"  Data range: {data.min():.3f} to {data.max():.3f}")
            if spacing:
                print(f"  Voxel spacing: {spacing}")
        
        # Generate mesh using NiiVue-compatible approach
        vertices, faces, normals = generate_mesh(
            data, 
            threshold=threshold,
            label_value=label_value,
            smooth=smooth,
            spacing=spacing
        )
        
        if vertices is None:
            if verbose:
                print("  No mesh generated - skipping")
            return False
        
        if verbose:
            print(f"  Generated mesh: {len(vertices)} vertices, {len(faces)} faces")
        
        # Render 3D PNG with NiiVue-style visualization
        title = f"NiiVue 3D Render: {nifti_path.stem.replace('.nii', '')}"
        success = render_3d_png(vertices, faces, normals, output_path, title)
        
        if not success:
            if verbose:
                print("  Failed to create PNG render")
            return False
        
        if verbose:
            print(f"  Saved PNG render: {output_path}")
        
        return True
        
    except Exception as e:
        print(f"Error processing {nifti_path}: {e}")
        return False


def process_patient_folder(patient_path, output_folder, threshold=0.1, label_value=None, smooth=1.0, 
                          force_overwrite=False, verbose=False):
    """
    Process all NIfTI files in a patient folder.
    
    Args:
        patient_path (Path): Path to patient folder
        output_folder (Path): Path to output folder (patient's nifti folder)
        threshold (float): Threshold for surface extraction
        label_value (int): Specific label value to extract
        smooth (float): Smoothing factor
        force_overwrite (bool): Overwrite existing renders
        verbose (bool): Verbose output
        
    Returns:
        tuple: (success_count, total_count)
    """
    nifti_folder = patient_path / "nifti"
    
    if not nifti_folder.exists():
        if verbose:
            print(f"No nifti folder found for {patient_path.name}")
        return 0, 0
    
    # Find all NIfTI files
    nifti_files = list(nifti_folder.glob("*.nii.gz")) + list(nifti_folder.glob("*.nii"))
    
    if not nifti_files:
        if verbose:
            print(f"No NIfTI files found in {nifti_folder}")
        return 0, 0
    
    if verbose:
        print(f"Processing {len(nifti_files)} NIfTI files in {patient_path.name}")
    
    success_count = 0
    total_count = len(nifti_files)
    
    # Process each NIfTI file
    for nifti_file in tqdm(nifti_files, desc=f"Processing {patient_path.name}"):
        # Create output filename for PNG file
        output_filename = nifti_file.stem.replace('.nii', '') + "_3d_render.png"
        output_path = nifti_folder / output_filename
        
        # Skip if file exists and not forcing overwrite
        if output_path.exists() and not force_overwrite:
            if verbose:
                print(f"  Skipping existing PNG: {output_filename}")
            continue
        
        # Process the file
        if process_nifti_file(nifti_file, output_path, threshold, label_value, smooth, verbose):
            success_count += 1
    
    return success_count, total_count


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Create NiiVue-style 3D PNG renders of NIfTI files for all patients",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python mini3d_render.py                           # Process all patients
  python mini3d_render.py --patient PA00000002      # Process specific patient
  python mini3d_render.py --threshold 0.2           # Custom threshold
  python mini3d_render.py --smooth 2.0              # Custom smoothing
  python mini3d_render.py --force                   # Overwrite existing renders
        """
    )
    
    parser.add_argument('--patient', type=str, help='Process specific patient folder')
    parser.add_argument('--threshold', type=float, default=0.1, help='Surface threshold (default: 0.1)')
    parser.add_argument('--label-value', type=int, help='Extract specific label value')
    parser.add_argument('--smooth', type=float, default=1.0, help='Smoothing factor (default: 1.0)')
    parser.add_argument('--force', action='store_true', help='Overwrite existing renders')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Load environment
    try:
        output_folder = load_environment()
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    if not output_folder.exists():
        print(f"Error: Output folder does not exist: {output_folder}")
        sys.exit(1)
    
    print("NiiVue-Style 3D PNG Renderer for Vista-3D Pipeline")
    print("=" * 50)
    
    print("Generating PNG renders from NIfTI data using NiiVue-compatible rendering")
    
    print(f"Output folder: {output_folder}")
    print(f"Threshold: {args.threshold}")
    if args.label_value:
        print(f"Label value: {args.label_value}")
    print(f"Smoothing: {args.smooth}")
    print(f"Force overwrite: {args.force}")
    print()
    
    # Find patient folders
    if args.patient:
        patient_folders = [output_folder / args.patient]
        if not patient_folders[0].exists():
            print(f"Error: Patient folder not found: {args.patient}")
            sys.exit(1)
    else:
        # Find all patient folders (PA* pattern)
        patient_folders = [p for p in output_folder.iterdir() 
                          if p.is_dir() and p.name.startswith('PA')]
        
        if not patient_folders:
            print("No patient folders found (PA* pattern)")
            sys.exit(1)
        
        # Sort for consistent processing
        patient_folders.sort(key=lambda x: x.name)
    
    print(f"Found {len(patient_folders)} patient folder(s)")
    print()
    
    # Process each patient folder
    total_success = 0
    total_files = 0
    
    for patient_folder in patient_folders:
        print(f"Processing patient: {patient_folder.name}")
        
        success, files = process_patient_folder(
            patient_folder, 
            patient_folder / "nifti",  # Output to patient's nifti folder
            threshold=args.threshold,
            label_value=args.label_value,
            smooth=args.smooth,
            force_overwrite=args.force,
            verbose=args.verbose
        )
        
        total_success += success
        total_files += files
        
        print(f"  Completed: {success}/{files} files")
        print()
    
    # Summary
    print("=" * 50)
    print("Processing Summary:")
    print(f"Total patients processed: {len(patient_folders)}")
    print(f"Total files processed: {total_files}")
    print(f"Successful renders: {total_success}")
    
    if total_files > 0:
        success_rate = (total_success / total_files) * 100
        print(f"Success rate: {success_rate:.1f}%")
    
    if total_success > 0:
        print(f"\nPNG renders saved to each patient's nifti folder")
        print("PNG files follow the pattern: <filename>_3d_render.png")
        print("PNG renders use NiiVue-style visualization with dark backgrounds")
        print("PNG renders can be viewed in any image viewer or web browser")
    
    print("\nDone!")


if __name__ == "__main__":
    # Suppress warnings for cleaner output
    warnings.filterwarnings("ignore")
    main()
