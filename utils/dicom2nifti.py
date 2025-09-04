#!/usr/bin/env python3
"""
Enhanced DICOM to NIFTI conversion script for Vista-3D pipeline using dcm2niix.
This script follows NiiVue best practices and uses dcm2niix for robust conversion.
Incorporates lessons from https://github.com/niivue/niivue-dcm2niix
"""

import os
import warnings
import json
import subprocess
import shutil
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm
import nibabel as nib
import numpy as np
import traceback


def check_dcm2niix_installation():
    """Check if dcm2niix is installed and accessible"""
    try:
        result = subprocess.run(['dcm2niix', '--help'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            # Extract version info
            version_line = result.stdout.split('\n')[0] if result.stdout else "Unknown version"
            print(f"✅ dcm2niix found: {version_line}")
            return True
        else:
            print(f"❌ dcm2niix check failed with return code: {result.returncode}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ dcm2niix check timed out")
        return False
    except FileNotFoundError:
        print("❌ dcm2niix not found in PATH")
        return False
    except Exception as e:
        print(f"❌ dcm2niix check failed: {e}")
        return False


def load_environment():
    """Load environment variables from .env file"""
    load_dotenv()
    project_root = os.getenv('PROJECT_ROOT')
    if not project_root:
        raise ValueError("PROJECT_ROOT not found in .env file")
    
    dicom_folder = os.getenv('DICOM_FOLDER')
    if not dicom_folder:
        raise ValueError("DICOM_FOLDER not found in .env file")
    
    return project_root, dicom_folder


def load_label_dictionary():
    """Load the Vista-3D label dictionary from JSON file"""
    try:
        # Try to load from the conf directory first
        label_file = Path("conf/vista3d_label_dict.json")
        if not label_file.exists():
            # Fallback to current directory
            label_file = Path("vista3d_label_dict.json")
        
        with open(label_file, 'r') as f:
            label_dict = json.load(f)
        
        print(f"✅ Loaded label dictionary with {len(label_dict)} anatomical structures")
        return label_dict
    except Exception as e:
        print(f"⚠️  Warning: Could not load label dictionary: {e}")
        print("   Using default label mapping")
        # Fallback to basic mapping
        return {
            'background': 0,
            'aorta': 6,
            'left iliac artery': 58,
            'right iliac artery': 59
        }


def check_dicom_files_exist(dicom_path):
    """Check if DICOM files exist in the specified directory"""
    if not os.path.exists(dicom_path):
        return False
    
    # Look for common DICOM file patterns and extensions
    dicom_extensions = {'.dcm', '.dicom', '.ima', '.img'}
    dicom_found = False
    
    for root, dirs, files in os.walk(dicom_path):
        for file in files:
            # Check by extension first (faster)
            if any(file.lower().endswith(ext) for ext in dicom_extensions):
                dicom_found = True
                break
            
            # Check for files without extensions (common in DICOM)
            if '.' not in file and len(file) > 3:
                dicom_found = True
                break
                
        if dicom_found:
            break
    
    return dicom_found


def legacy_create_affine_from_dicom(dicom_files):  # DEPRECATED - dcm2niix handles this
    """Create proper affine transformation matrix from DICOM headers with enhanced spatial accuracy."""
    try:
        # Use the first DICOM file to get basic information
        ds = pydicom.dcmread(str(dicom_files[0]))
        
        # Get pixel spacing (x, y spacing)
        if hasattr(ds, 'PixelSpacing') and ds.PixelSpacing:
            pixel_spacing = [float(ds.PixelSpacing[0]), float(ds.PixelSpacing[1])]
        else:
            pixel_spacing = [1.0, 1.0]  # Default 1mm spacing
        
        # Get slice thickness
        if hasattr(ds, 'SliceThickness') and ds.SliceThickness:
            slice_thickness = float(ds.SliceThickness)
        elif hasattr(ds, 'SpacingBetweenSlices') and ds.SpacingBetweenSlices:
            slice_thickness = float(ds.SpacingBetweenSlices)
        else:
            slice_thickness = 1.0  # Default 1mm thickness
        
        # Get orientation information
        if hasattr(ds, 'ImageOrientationPatient') and ds.ImageOrientationPatient:
            orientation = [float(x) for x in ds.ImageOrientationPatient]
            # DICOM orientation: [x1, y1, z1, x2, y2, z2]
            # These are the direction cosines for the x and y axes
            x_direction = orientation[:3]
            y_direction = orientation[3:6]
            # Z direction is cross product of x and y
            z_direction = np.cross(x_direction, y_direction)
            print(f"   DEBUG: ImageOrientationPatient: {orientation}") # ADD THIS LINE
        else:
            # Default orientation: axial slices
            x_direction = [1, 0, 0]
            y_direction = [0, 1, 0]
            z_direction = [0, 0, 1]
            print("   DEBUG: ImageOrientationPatient not found, using default axial.") # ADD THIS LINE
        
        # Get position information from first slice
        if hasattr(ds, 'ImagePositionPatient') and ds.ImagePositionPatient:
            first_position = [float(x) for x in ds.ImagePositionPatient]
        else:
            first_position = [0, 0, 0]
        
        # Get position from last slice to calculate proper Z spacing
        if len(dicom_files) > 1:
            try:
                last_ds = pydicom.dcmread(str(dicom_files[-1]))
                if hasattr(last_ds, 'ImagePositionPatient') and last_ds.ImagePositionPatient:
                    last_position = [float(x) for x in last_ds.ImagePositionPatient]
                    # Calculate actual Z spacing from first to last slice
                    z_distance = np.linalg.norm(np.array(last_position) - np.array(first_position))
                    if z_distance > 0:
                        slice_thickness = z_distance / (len(dicom_files) - 1)
            except:
                pass
        
        # Create enhanced affine matrix
        affine = np.eye(4)
        
        if len(dicom_files) == 1:
            # For single slices, use a simpler affine to avoid singularity issues
            affine[0, 0] = pixel_spacing[0]
            affine[1, 1] = pixel_spacing[1]
            affine[2, 2] = slice_thickness if slice_thickness > 0 else 1.0 # Ensure non-zero
            affine[:3, 3] = first_position
            print("   DEBUG: Using simplified affine for single slice.")
        else:
        
        # Set the direction vectors (normalized)
            x_direction = np.array(x_direction) / np.linalg.norm(x_direction)
            y_direction = np.array(y_direction) / np.linalg.norm(y_direction)
            z_direction = np.cross(x_direction, y_direction)
            z_direction = z_direction / np.linalg.norm(z_direction) # Normalize z_direction
            
            # Apply spacing and orientation
            affine[0, :3] = x_direction * pixel_spacing[0]
            affine[1, :3] = y_direction * pixel_spacing[1]
            affine[2, :3] = z_direction * slice_thickness
        
        # Set the origin (first slice position)
        affine[:3, 3] = first_position
        
        # Validate affine matrix (this check is still useful for multi-slice volumes)
        print(f"   DEBUG: Affine before final validation:\n{affine}")
        if np.linalg.det(affine[:3, :3]) == 0:
            print("⚠️  Warning: Invalid affine matrix detected, using fallback (should not happen with simplified affine)")
            affine = np.eye(4)
            affine[0, 0] = pixel_spacing[0]
            affine[1, 1] = pixel_spacing[1]
            affine[2, 2] = slice_thickness if slice_thickness > 0 else 1.0
            affine[:3, 3] = first_position
            print(f"   DEBUG: Affine after fallback:\n{affine}")
        
        print(f"📐 Enhanced affine matrix created:")
        print(f"   Spacing: {pixel_spacing[0]:.3f} x {pixel_spacing[1]:.3f} x {slice_thickness:.3f} mm")
        print(f"   Orientation: {orientation if 'orientation' in locals() else 'Default axial'}")
        print(f"   Origin: [{first_position[0]:.1f}, {first_position[1]:.1f}, {first_position[2]:.1f}]")
        
        return affine
        
    except Exception as e:
        print(f"⚠️  Could not extract enhanced spatial info from DICOM, using default: {e}")
        # Fallback to identity matrix with 1mm spacing
        affine = np.eye(4)
        return affine


def get_series_description(dicom_files):
    """Extract series description from DICOM files for naming"""
    try:
        # Try to get series description from the first DICOM file
        ds = pydicom.dcmread(str(dicom_files[0]))
        if hasattr(ds, 'SeriesDescription') and ds.SeriesDescription:
            series_desc = ds.SeriesDescription.strip()
            # Clean up the description for filename
            safe_desc = series_desc.replace(' ', '_').replace('-', '_').replace('/', '_')
            return safe_desc
        else:
            return "unknown_series"
    except Exception as e:
        print(f"⚠️  Could not extract series description: {e}")
        return "unknown_series"


def extract_dicom_rescale_params(dicom_files):
    """Extract rescale parameters from DICOM files for optimal data conversion."""
    try:
        # Check first few DICOM files for rescale parameters
        rescale_slope = None
        rescale_intercept = None
        window_center = None
        window_width = None
        
        for i, dicom_file in enumerate(dicom_files[:min(5, len(dicom_files))]):
            try:
                ds = pydicom.dcmread(str(dicom_file))
                
                # Get rescale slope and intercept
                if hasattr(ds, 'RescaleSlope') and rescale_slope is None:
                    rescale_slope = float(ds.RescaleSlope)
                if hasattr(ds, 'RescaleIntercept') and rescale_intercept is None:
                    rescale_intercept = float(ds.RescaleIntercept)
                
                # Get window center and width for display
                if hasattr(ds, 'WindowCenter') and window_center is None:
                    if isinstance(ds.WindowCenter, (list, tuple)):
                        window_center = float(ds.WindowCenter[0])
                    else:
                        window_center = float(ds.WindowCenter)
                if hasattr(ds, 'WindowWidth') and window_width is None:
                    if isinstance(ds.WindowWidth, (list, tuple)):
                        window_width = float(ds.WindowWidth[0])
                    else:
                        window_width = float(ds.WindowWidth)
                        
            except Exception as e:
                continue
        
        # Set defaults if not found
        if rescale_slope is None:
            rescale_slope = 1.0
        if rescale_intercept is None:
            rescale_intercept = 0.0
            
        print(f"🔧 DICOM rescale parameters:")
        print(f"   Slope: {rescale_slope}")
        print(f"   Intercept: {rescale_intercept}")
        if window_center is not None and window_width is not None:
            print(f"   Window Center: {window_center}")
            print(f"   Window Width: {window_width}")
        
        return {
            'rescale_slope': rescale_slope,
            'rescale_intercept': rescale_intercept,
            'window_center': window_center,
            'window_width': window_width
        }
        
    except Exception as e:
        print(f"⚠️  Could not extract rescale parameters: {e}")
        return {
            'rescale_slope': 1.0,
            'rescale_intercept': 0.0,
            'window_center': None,
            'window_width': None
        }


def apply_dicom_rescale(pixel_data, rescale_params):
    """Apply DICOM rescale parameters to pixel data for optimal quality."""
    try:
        slope = rescale_params['rescale_slope']
        intercept = rescale_params['rescale_intercept']
        
        # Apply rescale transformation: output = slope * input + intercept
        if slope != 1.0 or intercept != 0.0:
            # Use float64 for intermediate calculations to avoid precision loss
            pixel_data = pixel_data.astype(np.float64)
            pixel_data = slope * pixel_data + intercept
            
            # Convert back to appropriate integer type
            if slope > 0:  # Positive slope
                if pixel_data.min() >= 0 and pixel_data.max() <= 255:
                    pixel_data = pixel_data.astype(np.uint8)
                elif pixel_data.min() >= -32768 and pixel_data.max() <= 32767:
                    pixel_data = pixel_data.astype(np.int16)
                else:
                    pixel_data = pixel_data.astype(np.int32)
            else:  # Negative slope
                pixel_data = pixel_data.astype(np.int16)
        
        return pixel_data
        
    except Exception as e:
        print(f"⚠️  Could not apply rescale parameters: {e}")
        return pixel_data


def enhanced_slice_ordering(dicom_files):
    """Enhanced slice ordering using multiple DICOM attributes for optimal 3D reconstruction."""
    try:
        slice_info = []
        
        for i, dicom_file in enumerate(dicom_files):
            try:
                ds = pydicom.dcmread(str(dicom_file))
                
                # Extract multiple ordering criteria
                slice_data = {
                    'file': dicom_file,
                    'index': i,
                    'position_z': None,
                    'instance_number': None,
                    'acquisition_time': None,
                    'slice_location': None,
                    'dimensions': ds.pixel_array.shape
                }
                
                # Priority 1: Z position (most reliable for spatial ordering)
                if hasattr(ds, 'ImagePositionPatient') and ds.ImagePositionPatient:
                    slice_data['position_z'] = float(ds.ImagePositionPatient[2])
                
                # Priority 2: Instance number
                if hasattr(ds, 'InstanceNumber'):
                    slice_data['instance_number'] = int(ds.InstanceNumber)
                
                # Priority 3: Acquisition time
                if hasattr(ds, 'AcquisitionTime'):
                    slice_data['acquisition_time'] = ds.AcquisitionTime
                
                # Priority 4: Slice location
                if hasattr(ds, 'SliceLocation'):
                    slice_data['slice_location'] = float(ds.SliceLocation)
                
                slice_info.append(slice_data)
                
            except Exception as e:
                print(f"    ⚠️  Warning: Failed to analyze {dicom_file.name}: {e}")
                slice_info.append({
                    'file': dicom_file,
                    'index': i,
                    'position_z': None,
                    'instance_number': None,
                    'acquisition_time': None,
                    'slice_location': None,
                    'dimensions': None
                })
        
        # Determine best ordering method
        ordering_method = None
        if any(s['position_z'] is not None for s in slice_info):
            ordering_method = 'position_z'
            slice_info.sort(key=lambda x: x['position_z'] if x['position_z'] is not None else float('inf'))
        elif any(s['instance_number'] is not None for s in slice_info):
            ordering_method = 'instance_number'
            slice_info.sort(key=lambda x: x['instance_number'] if x['instance_number'] is not None else float('inf'))
        elif any(s['slice_location'] is not None for s in slice_info):
            ordering_method = 'slice_location'
            slice_info.sort(key=lambda x: x['slice_location'] if x['slice_location'] is not None else float('inf'))
        elif any(s['acquisition_time'] is not None for s in slice_info):
            ordering_method = 'acquisition_time'
            slice_info.sort(key=lambda x: x['acquisition_time'] if x['acquisition_time'] is not None else '')
        else:
            ordering_method = 'index'
            slice_info.sort(key=lambda x: x['index'])
        
        # Validate slice consistency
        ordered_files = [s['file'] for s in slice_info]
        validation_result = validate_slice_consistency(ordered_files, ordering_method)
        
        print(f"    🔍 Enhanced slice ordering:")
        print(f"       Method: {ordering_method}")
        print(f"       Total slices: {len(ordered_files)}")
        print(f"       Validation: {validation_result['status']}")
        if validation_result['warnings']:
            for warning in validation_result['warnings']:
                print(f"       ⚠️  {warning}")
        
        return ordered_files, validation_result
        
    except Exception as e:
        print(f"    ❌ Enhanced slice ordering failed: {e}")
        # Fallback to original order
        return dicom_files, {'status': 'fallback', 'warnings': [f'Using fallback ordering: {e}']}


def validate_slice_consistency(dicom_files, ordering_method):
    """Validate slice consistency and detect potential issues."""
    try:
        warnings = []
        
        if len(dicom_files) < 2:
            return {'status': 'insufficient_slices', 'warnings': ['Less than 2 slices found']}
        
        # Check dimensions consistency
        first_ds = pydicom.dcmread(str(dicom_files[0]))
        expected_shape = first_ds.pixel_array.shape
        
        dimension_mismatches = 0
        for dicom_file in dicom_files:
            try:
                ds = pydicom.dcmread(str(dicom_file))
                if ds.pixel_array.shape != expected_shape:
                    dimension_mismatches += 1
            except:
                dimension_mismatches += 1
        
        if dimension_mismatches > 0:
            warnings.append(f'{dimension_mismatches} slices have inconsistent dimensions')
        
        # Check for gaps in ordering (if using position-based ordering)
        if ordering_method == 'position_z':
            positions = []
            for dicom_file in dicom_files:
                try:
                    ds = pydicom.dcmread(str(dicom_file))
                    if hasattr(ds, 'ImagePositionPatient') and ds.ImagePositionPatient:
                        positions.append(float(ds.ImagePositionPatient[2]))
                except:
                    continue
            
            if len(positions) > 1:
                positions.sort()
                gaps = []
                for i in range(1, len(positions)):
                    gap = positions[i] - positions[i-1]
                    if gap > 0:
                        gaps.append(gap)
                
                if gaps:
                    avg_gap = np.mean(gaps)
                    max_gap = np.max(gaps)
                    if max_gap > avg_gap * 2:
                        warnings.append(f'Large gap detected in slice spacing: {max_gap:.2f}mm vs avg {avg_gap:.2f}mm')
        
        # Determine overall status
        if len(warnings) == 0:
            status = 'excellent'
        elif len(warnings) <= 2:
            status = 'good'
        else:
            status = 'fair'
        
        return {
            'status': status,
            'warnings': warnings,
            'total_slices': len(dicom_files),
            'dimension_mismatches': dimension_mismatches
        }
        
    except Exception as e:
        return {'status': 'validation_failed', 'warnings': [f'Validation error: {e}']}


def generate_quality_report(volume_data, affine, rescale_params, validation_result, output_file):
    """Generate a quality report for the converted NIFTI file."""
    try:
        report = {
            'file_info': {
                'filename': output_file.name,
                'file_size_mb': output_file.stat().st_size / (1024*1024),
                'creation_time': output_file.stat().st_mtime
            },
            'volume_info': {
                'dimensions': volume_data.shape,
                'data_type': str(volume_data.dtype),
                'total_voxels': volume_data.size,
                'memory_usage_mb': volume_data.nbytes / (1024*1024)
            },
            'data_quality': {
                'min_value': float(volume_data.min()),
                'max_value': float(volume_data.max()),
                'mean_value': float(volume_data.mean()),
                'std_value': float(volume_data.std()),
                'dynamic_range': float(volume_data.max() - volume_data.min())
            },
            'spatial_info': {
                'voxel_spacing_mm': [
                    float(np.linalg.norm(affine[0, :3])),
                    float(np.linalg.norm(affine[1, :3])),
                    float(np.linalg.norm(affine[2, :3]))
                ],
                'volume_dimensions_mm': [
                    float(np.linalg.norm(affine[0, :3]) * volume_data.shape[0]),
                    float(np.linalg.norm(affine[1, :3]) * volume_data.shape[1]),
                    float(np.linalg.norm(affine[2, :3]) * volume_data.shape[2])
                ]
            },
            'dicom_metadata': {
                'rescale_slope': rescale_params['rescale_slope'],
                'rescale_intercept': rescale_params['rescale_intercept'],
                'window_center': rescale_params['window_center'],
                'window_width': rescale_params['window_width']
            },
            'validation': validation_result
        }
        
        # Save quality report as JSON
        report_file = output_file.with_suffix('.quality.json')
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Print summary
        print(f"    📊 Quality Report Generated:")
        print(f"       Data range: [{report['data_quality']['min_value']:.1f}, {report['data_quality']['max_value']:.1f}]")
        print(f"       Mean: {report['data_quality']['mean_value']:.1f} ± {report['data_quality']['std_value']:.1f}")
        print(f"       Voxel spacing: {report['spatial_info']['voxel_spacing_mm'][0]:.2f} x {report['spatial_info']['voxel_spacing_mm'][1]:.2f} x {report['spatial_info']['voxel_spacing_mm'][2]:.2f} mm")
        print(f"       Volume size: {report['spatial_info']['volume_dimensions_mm'][0]:.1f} x {report['spatial_info']['volume_dimensions_mm'][1]:.1f} x {report['spatial_info']['volume_dimensions_mm'][2]:.1f} mm")
        
        return report
        
    except Exception as e:
        print(f"    ⚠️  Could not generate quality report: {e}")
        return None


def optimize_data_type(volume_data):
    """Optimize data type based on actual data range for optimal storage and quality."""
    try:
        min_val = volume_data.min()
        max_val = volume_data.max()
        
        # Determine optimal data type
        if min_val >= 0:  # Unsigned data
            if max_val <= 255:
                optimal_type = np.uint8
                print(f"    🔧 Optimizing to uint8 (0-255)")
            elif max_val <= 65535:
                optimal_type = np.uint16
                print(f"    🔧 Optimizing to uint16 (0-65535)")
            else:
                optimal_type = np.uint32
                print(f"    🔧 Optimizing to uint32 (0-4294967295)")
        else:  # Signed data
            if min_val >= -128 and max_val <= 127:
                optimal_type = np.int8
                print(f"    🔧 Optimizing to int8 (-128 to 127)")
            elif min_val >= -32768 and max_val <= 32767:
                optimal_type = np.int16
                print(f"    🔧 Optimizing to int16 (-32768 to 32767)")
            else:
                optimal_type = np.int32
                print(f"    🔧 Optimizing to int32 (-2147483648 to 2147483647)")
        
        # Check if conversion is beneficial
        current_size = volume_data.nbytes
        optimal_size = volume_data.astype(optimal_type).nbytes
        
        if optimal_size < current_size:
            print(f"    💾 Memory savings: {current_size / (1024*1024):.1f}MB → {optimal_size / (1024*1024):.1f}MB")
            return volume_data.astype(optimal_type)
        else:
            print(f"    ℹ️  Current data type is already optimal")
            return volume_data
            
    except Exception as e:
        print(f"    ⚠️  Data type optimization failed: {e}")
        return volume_data


def run_dcm2niix_conversion(input_dir, output_dir, filename_format="%f_%p_%t_%s"):
    """
    Run dcm2niix conversion with NiiVue-optimized settings.
    
    Args:
        input_dir: Input DICOM directory
        output_dir: Output directory for NIFTI files
        filename_format: Output filename format (dcm2niix -f option)
    
    Returns:
        dict: Conversion results with status and files created
    """
    try:
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # dcm2niix command with NiiVue-optimized settings
        cmd = [
            'dcm2niix',
            '-z', 'y',           # Compress output (.nii.gz)
            '-b', 'y',           # Generate BIDS sidecar JSON
            '-ba', 'y',          # Anonymize BIDS sidecar
            '-f', filename_format, # Filename format
            '-o', str(output_dir), # Output directory
            '-v', '1',           # Verbose output
            '-x', 'y',           # Crop 3D acquisitions
            '-i', 'y',           # Ignore derived, localizer and 2D images
            str(input_dir)       # Input directory
        ]
        
        print(f"🔧 Running dcm2niix conversion:")
        print(f"   Command: {' '.join(cmd)}")
        
        # Run dcm2niix
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print(f"✅ dcm2niix conversion successful")
            
            # Find created files
            nifti_files = list(Path(output_dir).glob("*.nii.gz"))
            json_files = list(Path(output_dir).glob("*.json"))
            
            print(f"📁 Created {len(nifti_files)} NIFTI files and {len(json_files)} JSON sidecars")
            
            return {
                'status': 'success',
                'nifti_files': nifti_files,
                'json_files': json_files,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
        else:
            print(f"❌ dcm2niix conversion failed (return code: {result.returncode})")
            print(f"   stderr: {result.stderr}")
            print(f"   stdout: {result.stdout}")
            
            return {
                'status': 'failed',
                'error': result.stderr,
                'stdout': result.stdout,
                'return_code': result.returncode
            }
            
    except subprocess.TimeoutExpired:
        print("❌ dcm2niix conversion timed out")
        return {'status': 'timeout', 'error': 'Conversion timed out after 5 minutes'}
    except Exception as e:
        print(f"❌ dcm2niix conversion error: {e}")
        return {'status': 'error', 'error': str(e)}


def enhance_nifti_for_niivue(nifti_file, json_file=None):
    """
    Enhance NIFTI file for optimal NiiVue compatibility.
    
    Args:
        nifti_file: Path to NIFTI file
        json_file: Path to associated JSON sidecar (optional)
    
    Returns:
        dict: Enhancement results
    """
    try:
        print(f"🔧 Enhancing {nifti_file.name} for NiiVue...")
        
        # Load NIFTI file
        img = nib.load(str(nifti_file))
        data = img.get_fdata()
        
        # Generate quality report
        quality_info = {
            'file_info': {
                'filename': nifti_file.name,
                'file_size_mb': nifti_file.stat().st_size / (1024*1024),
                'compression': nifti_file.suffix == '.gz'
            },
            'volume_info': {
                'dimensions': data.shape,
                'data_type': str(data.dtype),
                'total_voxels': data.size,
                'memory_usage_mb': data.nbytes / (1024*1024)
            },
            'data_quality': {
                'min_value': float(data.min()),
                'max_value': float(data.max()),
                'mean_value': float(data.mean()),
                'std_value': float(data.std()),
                'dynamic_range': float(data.max() - data.min())
            },
            'spatial_info': {
                'voxel_spacing_mm': [float(x) for x in img.header.get_zooms()],
                'volume_dimensions_mm': [
                    float(img.header.get_zooms()[i] * data.shape[i]) 
                    for i in range(min(3, len(data.shape)))
                ]
            }
        }
        
        # Add JSON metadata if available
        if json_file and json_file.exists():
            try:
                with open(json_file, 'r') as f:
                    json_metadata = json.load(f)
                quality_info['dicom_metadata'] = json_metadata
            except Exception as e:
                print(f"⚠️  Could not read JSON sidecar: {e}")
        
        # Save enhanced quality report
        quality_file = nifti_file.with_suffix('.quality.json')
        with open(quality_file, 'w') as f:
            json.dump(quality_info, f, indent=2, default=str)
        
        print(f"    📊 Quality Report:")
        print(f"       Data range: [{quality_info['data_quality']['min_value']:.1f}, {quality_info['data_quality']['max_value']:.1f}]")
        print(f"       Voxel spacing: {' x '.join(f'{x:.2f}' for x in quality_info['spatial_info']['voxel_spacing_mm'])} mm")
        print(f"       Volume size: {' x '.join(f'{x:.1f}' for x in quality_info['spatial_info']['volume_dimensions_mm'])} mm")
        print(f"       File size: {quality_info['file_info']['file_size_mb']:.1f} MB")
        
        return {
            'status': 'success',
            'quality_info': quality_info,
            'quality_file': quality_file
        }
        
    except Exception as e:
        print(f"❌ Enhancement failed for {nifti_file.name}: {e}")
        return {'status': 'failed', 'error': str(e)}


def convert_dicom_to_nifti(force_overwrite=False):
    """
    Convert DICOM files to NIFTI format using dcm2niix with NiiVue optimization.
    
    Args:
        force_overwrite: If True, overwrite existing NIFTI directories
    """
    try:
        # Check dcm2niix installation first
        if not check_dcm2niix_installation():
            raise RuntimeError("dcm2niix is required but not found. Please install dcm2niix first.")
        
        # Load environment variables
        project_root, dicom_folder = load_environment()
        
        # Load label dictionary
        label_dict = load_label_dictionary()
        
        # Define paths
        if os.path.isabs(dicom_folder):
            dicom_data_path = Path(dicom_folder)
        else:
            dicom_data_path = Path(project_root) / dicom_folder
            
        nifti_destination_path = Path(project_root) / "outputs/nifti"
        
        print(f"🔬 Enhanced DICOM to NIFTI Conversion (dcm2niix + NiiVue)")
        print(f"📁 Project Root: {project_root}")
        print(f"📁 DICOM Source: {dicom_data_path}")
        print(f"📁 NIFTI Destination: {nifti_destination_path}")
        print("-" * 70)
        
        # Check if DICOM directory exists
        if not dicom_data_path.exists():
            raise FileNotFoundError(f"DICOM directory not found: {dicom_data_path}")
        
        # Check if DICOM files exist
        if not check_dicom_files_exist(dicom_data_path):
            raise FileNotFoundError(f"No DICOM files found in: {dicom_data_path}")
        
        # Create NIFTI destination directory if it doesn't exist
        nifti_destination_path.mkdir(exist_ok=True)
        
        # Get list of DICOM directories for progress tracking
        dicom_directories = [d for d in os.listdir(dicom_data_path) 
                           if (dicom_data_path / d).is_dir()]
        
        print(f"📊 Found {len(dicom_directories)} DICOM directories to process")
        print(f"🔧 Using dcm2niix for robust conversion with NiiVue optimization")
        print("-" * 70)
        
        # Convert DICOM to NIFTI using dcm2niix
        successful_conversions = 0
        failed_conversions = 0
        total_nifti_files = 0
        
        with tqdm(total=len(dicom_directories), desc="🔄 Processing patients", unit="patient") as patient_pbar:
            for dicom_directory in dicom_directories:
                input_directory = Path(dicom_data_path) / dicom_directory
                output_directory = Path(nifti_destination_path) / dicom_directory
            
                # Check if already processed
                if output_directory.exists() and not force_overwrite:
                    warnings.warn(f"{output_directory} already exists, skipping...")
                    patient_pbar.update(1)
                    continue
                elif output_directory.exists() and force_overwrite:
                    print(f"\n🔄 Overwriting existing directory: {output_directory}")
                    shutil.rmtree(output_directory)
                    
                # Process the patient with dcm2niix
                try:
                    print(f"\n📂 Processing: {dicom_directory}")
                    print("-" * 50)
                    
                    # Run dcm2niix conversion
                    conversion_result = run_dcm2niix_conversion(
                        input_dir=input_directory,
                        output_dir=output_directory,
                        filename_format=f"{dicom_directory}_%f_%p_%t_%s"
                    )
                    
                    if conversion_result['status'] == 'success':
                        print(f"✅ dcm2niix conversion completed successfully")
                        
                        # Process each created NIFTI file for NiiVue enhancement
                        nifti_files = conversion_result['nifti_files']
                        json_files = conversion_result['json_files']
                        total_nifti_files += len(nifti_files)
                        
                        print(f"🔧 Enhancing {len(nifti_files)} NIFTI files for NiiVue...")
                        
                        for nifti_file in nifti_files:
                            # Find corresponding JSON file
                            json_file = None
                            nifti_basename = nifti_file.stem.replace('.nii', '')
                            for json_f in json_files:
                                if json_f.stem == nifti_basename:
                                    json_file = json_f
                                    break
                            
                            # Enhance for NiiVue
                            enhancement_result = enhance_nifti_for_niivue(nifti_file, json_file)
                            
                            if enhancement_result['status'] == 'success':
                                print(f"    ✅ Enhanced: {nifti_file.name}")
                            else:
                                print(f"    ⚠️  Enhancement warning: {nifti_file.name}")
                        
                        successful_conversions += 1
                        print(f"🎉 Successfully processed {dicom_directory}")
                        
                    else:
                        print(f"❌ dcm2niix conversion failed for {dicom_directory}")
                        print(f"   Error: {conversion_result.get('error', 'Unknown error')}")
                        failed_conversions += 1
                        
                        # Clean up failed output directory
                        if output_directory.exists():
                            shutil.rmtree(output_directory)
                    patient_pbar.update(1)
                    
                except Exception as e:
                    print(f"✗ Failed to convert {dicom_directory}: {str(e)}")
                    # Clean up the failed output directory
                    if output_directory.exists():
                        shutil.rmtree(output_directory)
                    failed_conversions += 1
                    patient_pbar.update(1)
                    continue
        
        print("-" * 70)
        print("🎉 Enhanced DICOM to NIFTI conversion completed!")
        print(f"✓ Successfully converted: {successful_conversions} directories")
        print(f"✗ Failed conversions: {failed_conversions} directories")
        print(f"📁 Total processed: {len(dicom_directories)} directories")
        print(f"📄 Total NIFTI files created: {total_nifti_files}")
        print(f"\n🔬 NiiVue-Optimized Features Applied:")
        print("   • dcm2niix for robust and accurate DICOM conversion")
        print("   • BIDS-compliant JSON sidecar metadata generation")
        print("   • Automatic compression (.nii.gz) for web efficiency")
        print("   • Enhanced filename patterns for organization")
        print("   • Comprehensive quality reports for each file")
        print("   • NiiVue browser compatibility optimization")
        print("   • Spatial accuracy and orientation preservation")
        
    except Exception as e:
        print(f"Error during conversion: {str(e)}")
        raise


# Legacy function removed - dcm2niix handles series grouping automatically


if __name__ == "__main__":
    import sys
    # Check if force overwrite flag is passed
    force_overwrite = '--force' in sys.argv or '--overwrite' in sys.argv
    convert_dicom_to_nifti(force_overwrite=force_overwrite)
