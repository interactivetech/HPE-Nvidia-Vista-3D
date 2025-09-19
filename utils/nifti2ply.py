#!/usr/bin/env python3
"""
Enhanced NIfTI to PLY Converter for Vista-3D Pipeline

This script converts NIfTI medical imaging files to PLY (Polygon File Format) mesh files.
It supports both single file conversion and batch processing of voxels folders from the
Vista-3D output structure.

Features:
- Single file conversion with command line interface
- Batch processing of all voxels folders in output directory
- Automatic PLY folder creation matching voxels structure
- Progress tracking and error handling
- High-quality mesh generation with marching cubes

Usage:
    # Single file conversion
    python nifti2ply.py input.nii.gz output.ply [options]
    
    # Batch processing of all voxels folders
    python nifti2ply.py --batch [options]
    
    # Batch processing with specific patient
    python nifti2ply.py --batch --patient PA00000002 [options]

Requirements:
    - nibabel: For NIfTI file handling
    - skimage: For marching cubes algorithm
    - numpy: For numerical operations
    - plyfile: For PLY file writing
    - tqdm: For progress bars
    - dotenv: For environment configuration
"""

import argparse
import sys
import os
import warnings
import json
import shutil
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm
import numpy as np
import nibabel as nib
from skimage import measure
from plyfile import PlyData, PlyElement


def load_environment():
    """Load environment variables from .env file and get project root"""
    load_dotenv()
    # Import PROJECT_ROOT from constants - it's auto-detected
    from utils.constants import PROJECT_ROOT
    return str(PROJECT_ROOT)


def check_voxels_folders_exist(output_path: Path) -> bool:
    """Check if any voxels folders exist in the output directory."""
    if not output_path.is_dir():
        return False
    
    for patient_dir in output_path.iterdir():
        if patient_dir.is_dir():
            voxels_dir = patient_dir / "voxels"
            if voxels_dir.exists() and voxels_dir.is_dir():
                return True
    return False


def get_patient_directories(output_path: Path, specific_patient=None):
    """Get list of patient directories that have voxels folders."""
    patient_dirs = []
    
    for patient_dir in output_path.iterdir():
        if patient_dir.is_dir():
            # If specific patient requested, only process that one
            if specific_patient and patient_dir.name != specific_patient:
                continue
                
            voxels_dir = patient_dir / "voxels"
            if voxels_dir.exists() and voxels_dir.is_dir():
                patient_dirs.append(patient_dir)
    
    return patient_dirs


def get_voxels_subfolders(voxels_dir: Path):
    """Get list of voxels subfolders containing NIfTI files."""
    subfolders = []
    
    for item in voxels_dir.iterdir():
        if item.is_dir():
            # Check if this subfolder contains NIfTI files
            nifti_files = list(item.glob("*.nii.gz")) + list(item.glob("*.nii"))
            if nifti_files:
                subfolders.append(item)
    
    return subfolders


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
        sys.exit(1)


def apply_threshold(data, threshold=0.5):
    """
    Apply threshold to create binary mask.
    
    Args:
        data (numpy.ndarray): Input image data
        threshold (float): Threshold value
        
    Returns:
        numpy.ndarray: Binary mask
    """
    return data > threshold


def apply_label_mask(data, label_value):
    """
    Create mask for specific label value.
    
    Args:
        data (numpy.ndarray): Input image data
        label_value (int): Label value to extract
        
    Returns:
        numpy.ndarray: Binary mask for the label
    """
    return data == label_value


def generate_mesh(data, threshold=0.1, label_value=None, smooth=1.0, spacing=None):
    """
    Generate mesh from 3D data using marching cubes.
    
    Args:
        data (numpy.ndarray): 3D image data
        threshold (float): Threshold for binary mask (default: 0.1 for high quality)
        label_value (int, optional): Specific label value to extract
        smooth (float): Smoothing factor for mesh (default: 1.0 for high quality)
        spacing (tuple, optional): Voxel spacing (x, y, z). If None, uses (1.0, 1.0, 1.0)
        
    Returns:
        tuple: (vertices, faces, normals)
    """
    # Create binary mask
    if label_value is not None:
        mask = apply_label_mask(data, label_value)
    else:
        # Auto-adjust threshold if it's outside the data range
        data_min, data_max = data.min(), data.max()
        if threshold >= data_max:
            # If threshold is too high, use a value just below the max
            threshold = max(0.1, data_max * 0.9)
            print(f"Warning: Threshold adjusted to {threshold:.3f} (data range: {data_min:.3f} to {data_max:.3f})")
        elif threshold <= data_min:
            # If threshold is too low, use a value just above the min
            threshold = min(data_max * 0.1, data_min + 0.1)
            print(f"Warning: Threshold adjusted to {threshold:.3f} (data range: {data_min:.3f} to {data_max:.3f})")
        
        mask = apply_threshold(data, threshold)
    
    # Ensure mask is boolean
    mask = mask.astype(bool)
    
    # Check if mask has any True values
    if not np.any(mask):
        print("Warning: No voxels found above threshold. Try adjusting threshold or label value.")
        return None, None, None
    
    try:
        # Use actual voxel spacing if provided, otherwise use unit spacing
        if spacing is None:
            spacing = (1.0, 1.0, 1.0)
        
        # Apply smoothing if requested
        if smooth > 0:
            try:
                from scipy.ndimage import gaussian_filter
                # Apply Gaussian smoothing to the mask before mesh generation
                smoothed_mask = gaussian_filter(mask.astype(float), sigma=smooth)
                mesh_data = smoothed_mask
            except ImportError:
                print("Warning: scipy not available for smoothing. Install scipy for better mesh quality.")
                mesh_data = mask.astype(float)
        else:
            mesh_data = mask.astype(float)
        
        # Try different level values if the default fails
        level_values = [0.5, 0.0, 0.1, 0.9, 0.2, 0.8, 0.01, 0.99, 0.05, 0.95]
        
        for level in level_values:
            try:
                # Generate mesh using marching cubes
                verts, faces, normals, values = measure.marching_cubes(
                    mesh_data, 
                    level=level,
                    spacing=spacing,
                    gradient_direction='descent'
                )
                
                # Check if we got a valid mesh
                if len(verts) > 0 and len(faces) > 0:
                    if level != 0.5:
                        print(f"Warning: Used level {level} instead of default 0.5 for successful mesh generation")
                    return verts, faces, normals
                    
            except Exception as e:
                # Try next level value
                continue
        
        # If all level values failed, try with a different approach
        print("Warning: All standard level values failed, trying alternative approach...")
        
        # Try with different gradient directions
        gradient_directions = ['descent', 'ascent']
        for grad_dir in gradient_directions:
            for level in [0.0, 0.5, 0.1, 0.9]:
                try:
                    verts, faces, normals, values = measure.marching_cubes(
                        mesh_data, 
                        level=level,
                        spacing=spacing,
                        gradient_direction=grad_dir
                    )
                    if len(verts) > 0 and len(faces) > 0:
                        print(f"Warning: Used level {level} with gradient direction '{grad_dir}' for successful mesh generation")
                        return verts, faces, normals
                except:
                    continue
        
        # Try with the original data without smoothing
        for grad_dir in gradient_directions:
            for level in [0.0, 0.5, 0.1, 0.9]:
                try:
                    verts, faces, normals, values = measure.marching_cubes(
                        mask.astype(float), 
                        level=level,
                        spacing=spacing,
                        gradient_direction=grad_dir
                    )
                    if len(verts) > 0 and len(faces) > 0:
                        print(f"Warning: Used original data without smoothing, level {level} with gradient direction '{grad_dir}' for successful mesh generation")
                        return verts, faces, normals
                except:
                    continue
        
        # Last resort: try with a very sparse threshold
        try:
            # Use a much lower threshold to capture more data
            sparse_mask = data > (data.max() * 0.01)  # Use 1% of max value as threshold
            if np.any(sparse_mask):
                verts, faces, normals, values = measure.marching_cubes(
                    sparse_mask.astype(float), 
                    level=0.5,
                    spacing=spacing,
                    gradient_direction='descent'
                )
                if len(verts) > 0 and len(faces) > 0:
                    print("Warning: Used sparse threshold (1% of max value) for successful mesh generation")
                    return verts, faces, normals
        except:
            pass
        
        print("Error: Could not generate mesh with any method")
        return None, None, None
        
    except Exception as e:
        print(f"Error generating mesh: {e}")
        return None, None, None


def write_ply(vertices, faces, normals, output_path, binary=True):
    """
    Write mesh data to PLY file.
    
    Args:
        vertices (numpy.ndarray): Vertex coordinates
        faces (numpy.ndarray): Face indices
        normals (numpy.ndarray): Vertex normals
        output_path (str): Output file path
        binary (bool): Whether to write binary PLY format
    """
    try:
        # Prepare vertex data
        vertex_data = np.empty(vertices.shape[0], dtype=[
            ('x', 'f4'), ('y', 'f4'), ('z', 'f4'),
            ('nx', 'f4'), ('ny', 'f4'), ('nz', 'f4')
        ])
        
        vertex_data['x'] = vertices[:, 0]
        vertex_data['y'] = vertices[:, 1]
        vertex_data['z'] = vertices[:, 2]
        vertex_data['nx'] = normals[:, 0]
        vertex_data['ny'] = normals[:, 1]
        vertex_data['nz'] = normals[:, 2]
        
        # Prepare face data
        face_data = np.empty(faces.shape[0], dtype=[('vertex_indices', 'i4', (3,))])
        face_data['vertex_indices'] = faces
        
        # Create PLY elements
        vertex_element = PlyElement.describe(vertex_data, 'vertex')
        face_element = PlyElement.describe(face_data, 'face')
        
        # Write PLY file
        PlyData([vertex_element, face_element], text=not binary).write(output_path)
        
        print(f"Successfully wrote PLY file: {output_path}")
        print(f"  Vertices: {len(vertices)}")
        print(f"  Faces: {len(faces)}")
        print(f"  Format: {'Binary' if binary else 'ASCII'}")
        
    except Exception as e:
        print(f"Error writing PLY file: {e}")
        sys.exit(1)


def convert_single_file(input_file, output_file, threshold=0.1, label_value=None, 
                       smooth=1.0, ascii=False, verbose=False):
    """Convert a single NIfTI file to PLY format."""
    if verbose:
        print(f"Converting {input_file} to {output_file}")
        print(f"Threshold: {threshold}")
        if label_value is not None:
            print(f"Label value: {label_value}")
        print(f"Smoothing: {smooth}")
        print(f"Format: {'ASCII' if ascii else 'Binary'}")
    
    # Load NIfTI file
    if verbose:
        print("Loading NIfTI file...")
    data, affine = load_nifti(input_file)
    
    # Extract voxel spacing from affine matrix for high quality
    spacing = None
    if affine is not None:
        # Extract spacing from diagonal elements of affine matrix
        spacing = tuple(np.abs(np.diag(affine[:3, :3])))
        if verbose:
            print(f"Voxel spacing: {spacing}")
    
    if verbose:
        print(f"Data shape: {data.shape}")
        print(f"Data range: {data.min():.3f} to {data.max():.3f}")
        print(f"Data type: {data.dtype}")
    
    # Generate mesh
    if verbose:
        print("Generating mesh...")
    vertices, faces, normals = generate_mesh(
        data, 
        threshold=threshold,
        label_value=label_value,
        smooth=smooth,
        spacing=spacing
    )
    
    if vertices is None:
        print(f"Failed to generate mesh for {input_file}")
        return False
    
    # Write PLY file
    if verbose:
        print("Writing PLY file...")
    write_ply(vertices, faces, normals, output_file, binary=not ascii)
    
    return True


def convert_voxels_to_ply(force_overwrite=False, threshold=0.1, label_value=None, 
                         smooth=1.0, ascii=False, specific_patient=None, verbose=False):
    """
    Convert all NIfTI files in voxels folders to PLY format.
    
    Args:
        force_overwrite: If True, overwrite existing PLY files
        threshold: Threshold value for binary mask
        label_value: Specific label value to extract
        smooth: Smoothing factor for mesh
        ascii: Whether to write ASCII PLY format
        specific_patient: Process only specific patient ID
        verbose: Enable verbose output
    """
    try:
        # Load environment variables
        project_root = load_environment()
        
        # Define paths
        output_folder = os.getenv('OUTPUT_FOLDER', 'output')
        output_base_path = Path(project_root) / output_folder
        
        print(f"🔬 Enhanced NIfTI to PLY Conversion (Vista-3D Pipeline)")
        print(f"📁 Project Root: {project_root}")
        print(f"📁 Output Base: {output_base_path}")
        print("-" * 70)
        
        # Check if output directory exists
        if not output_base_path.exists():
            raise FileNotFoundError(f"Output directory not found: {output_base_path}")
        
        # Get patient directories (this will only return those with voxels folders)
        patient_dirs = get_patient_directories(output_base_path, specific_patient)
        
        if not patient_dirs:
            if specific_patient:
                print(f"⚠️  Patient {specific_patient} not found or has no voxels folder - skipping")
                return
            else:
                print(f"⚠️  No patient directories with voxels folders found - skipping conversion")
                return
        
        print(f"📊 Found {len(patient_dirs)} patient directories to process")
        print(f"🔧 Converting NIfTI files to PLY format with high-quality settings")
        print("-" * 70)
        
        # Process each patient directory
        successful_conversions = 0
        failed_conversions = 0
        total_ply_files = 0
        
        with tqdm(total=len(patient_dirs), desc="🔄 Processing patients", unit="patient") as patient_pbar:
            for patient_dir in patient_dirs:
                patient_id = patient_dir.name
                voxels_dir = patient_dir / "voxels"
                ply_dir = patient_dir / "ply"
                
                # Create PLY directory if it doesn't exist
                ply_dir.mkdir(parents=True, exist_ok=True)
                
                try:
                    print(f"\n📂 Processing: {patient_id}")
                    print("-" * 50)
                    
                    # Get voxels subfolders
                    voxels_subfolders = get_voxels_subfolders(voxels_dir)
                    
                    if not voxels_subfolders:
                        print(f"⚠️  No voxels subfolders found in {voxels_dir}")
                        patient_pbar.update(1)
                        continue
                    
                    print(f"📁 Found {len(voxels_subfolders)} voxels subfolders")
                    
                    # Process each voxels subfolder
                    subfolder_success = 0
                    subfolder_failed = 0
                    
                    for voxels_subfolder in voxels_subfolders:
                        subfolder_name = voxels_subfolder.name
                        ply_subfolder = ply_dir / subfolder_name
                        ply_subfolder.mkdir(exist_ok=True)
                        
                        # Get NIfTI files in this subfolder
                        nifti_files = list(voxels_subfolder.glob("*.nii.gz")) + list(voxels_subfolder.glob("*.nii"))
                        
                        if not nifti_files:
                            continue
                        
                        print(f"  📁 Processing subfolder: {subfolder_name} ({len(nifti_files)} files)")
                        
                        # Convert each NIfTI file
                        for nifti_file in nifti_files:
                            # Generate output PLY filename
                            if nifti_file.suffix == '.gz' and nifti_file.stem.endswith('.nii'):
                                base_name = nifti_file.stem[:-4]  # Remove .nii from .nii.gz
                            else:
                                base_name = nifti_file.stem
                            
                            ply_file = ply_subfolder / f"{base_name}.ply"
                            
                            # Skip if PLY file already exists and not forcing overwrite
                            if ply_file.exists() and not force_overwrite:
                                if verbose:
                                    print(f"    ⏭️  Skipping existing: {ply_file.name}")
                                continue
                            
                            # Convert NIfTI to PLY
                            try:
                                success = convert_single_file(
                                    input_file=str(nifti_file),
                                    output_file=str(ply_file),
                                    threshold=threshold,
                                    label_value=label_value,
                                    smooth=smooth,
                                    ascii=ascii,
                                    verbose=verbose
                                )
                                
                                if success:
                                    subfolder_success += 1
                                    total_ply_files += 1
                                    if verbose:
                                        print(f"    ✅ Converted: {nifti_file.name} -> {ply_file.name}")
                                else:
                                    subfolder_failed += 1
                                    if verbose:
                                        print(f"    ❌ Failed: {nifti_file.name}")
                                        
                            except Exception as e:
                                subfolder_failed += 1
                                print(f"    ❌ Error converting {nifti_file.name}: {e}")
                        
                        if subfolder_success > 0:
                            print(f"    ✅ Subfolder {subfolder_name}: {subfolder_success} successful, {subfolder_failed} failed")
                    
                    if subfolder_success > 0:
                        successful_conversions += 1
                        print(f"🎉 Successfully processed {patient_id} ({subfolder_success} PLY files created)")
                    else:
                        failed_conversions += 1
                        print(f"❌ No successful conversions for {patient_id}")
                        # Clean up empty PLY directory
                        if ply_dir.exists() and not any(ply_dir.iterdir()):
                            ply_dir.rmdir()
                    
                    patient_pbar.update(1)
                    
                except Exception as e:
                    print(f"✗ Failed to process {patient_id}: {str(e)}")
                    # Clean up failed PLY directory
                    if ply_dir.exists():
                        shutil.rmtree(ply_dir)
                    failed_conversions += 1
                    patient_pbar.update(1)
                    continue
        
        print("-" * 70)
        print("🎉 Enhanced NIfTI to PLY conversion completed!")
        print(f"✓ Successfully processed: {successful_conversions} patients")
        print(f"✗ Failed patients: {failed_conversions} patients")
        print(f"📄 Total PLY files created: {total_ply_files}")
        print(f"\n🔬 High-Quality Features Applied:")
        print("   • Marching cubes algorithm for accurate mesh generation")
        print("   • Automatic voxel spacing preservation")
        print("   • Gaussian smoothing for mesh quality")
        print("   • Binary PLY format for efficiency (unless ASCII requested)")
        print("   • Comprehensive error handling and progress tracking")
        print("   • Organized output structure matching voxels folders")
        
    except Exception as e:
        print(f"Error during batch conversion: {str(e)}")
        raise


def main():
    """Main function to handle command line arguments and conversion."""
    parser = argparse.ArgumentParser(
        description="Convert NIfTI medical imaging files to PLY mesh format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single file conversion
  python nifti2ply.py input.nii.gz                    # Creates input.ply
  python nifti2ply.py input.nii.gz output.ply         # Creates output.ply
  python nifti2ply.py input.nii.gz --threshold 0.5    # Creates input.ply with custom threshold
  python nifti2ply.py input.nii.gz --label 1 --smooth 1.0  # Creates input.ply with label extraction
  python nifti2ply.py input.nii.gz --ascii --verbose  # Creates input.ply in ASCII format
  
  # Batch processing
  python nifti2ply.py --batch                         # Process all voxels folders
  python nifti2ply.py --batch --patient PA00000002    # Process specific patient
  python nifti2ply.py --batch --force --threshold 0.5 # Force overwrite with custom threshold
        """
    )
    
    # Input/output arguments (for single file mode)
    parser.add_argument('input', nargs='?', help='Input NIfTI file (.nii or .nii.gz)')
    parser.add_argument('output', nargs='?', help='Output PLY file (.ply). If not provided, uses input filename with .ply extension')
    
    # Batch processing arguments
    parser.add_argument('--batch', action='store_true',
                       help='Process all voxels folders in output directory')
    parser.add_argument('--patient', type=str, default=None,
                       help='Process specific patient ID (only with --batch)')
    parser.add_argument('--force', action='store_true',
                       help='Force overwrite existing PLY files')
    
    # Conversion parameters
    parser.add_argument('--threshold', type=float, default=0.1,
                       help='Threshold value for binary mask (default: 0.1 for high quality)')
    parser.add_argument('--label', type=int, default=None,
                       help='Extract specific label value instead of using threshold')
    parser.add_argument('--smooth', type=float, default=1.0,
                       help='Smoothing factor for mesh (default: 1.0 for high quality)')
    parser.add_argument('--ascii', action='store_true',
                       help='Write ASCII PLY format (default: binary)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Determine mode
    if args.batch:
        # Batch processing mode
        convert_voxels_to_ply(
            force_overwrite=args.force,
            threshold=args.threshold,
            label_value=args.label,
            smooth=args.smooth,
            ascii=args.ascii,
            specific_patient=args.patient,
            verbose=args.verbose
        )
    else:
        # Single file mode
        if not args.input:
            print("Error: Input file required for single file mode, or use --batch for batch processing")
            parser.print_help()
            sys.exit(1)
        
        # Validate input file
        if not os.path.exists(args.input):
            print(f"Error: Input file '{args.input}' does not exist.")
            sys.exit(1)
        
        # Generate output filename if not provided
        if args.output is None:
            input_path = Path(args.input)
            # Handle both .nii and .nii.gz extensions
            if input_path.suffix == '.gz' and input_path.stem.endswith('.nii'):
                # For .nii.gz files, remove both .nii and .gz
                base_name = input_path.stem[:-4]  # Remove .nii from .nii.gz
            else:
                # For .nii files, just remove the extension
                base_name = input_path.stem
            args.output = f"{base_name}.ply"
        
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Convert single file
        success = convert_single_file(
            input_file=args.input,
            output_file=args.output,
            threshold=args.threshold,
            label_value=args.label,
            smooth=args.smooth,
            ascii=args.ascii,
            verbose=args.verbose
        )
        
        if success:
            print("Conversion completed successfully!")
        else:
            print("Conversion failed!")
            sys.exit(1)


if __name__ == "__main__":
    main()
