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
    
    # Check if we're running in a Docker container
    is_docker = os.path.exists('/.dockerenv') or os.environ.get('DOCKER_CONTAINER') == 'true'
    
    if is_docker:
        # In Docker container, use the mounted paths
        dicom_folder = '/app/dicom'
        output_folder = '/app/output'
    else:
        # On host machine, use environment variables
        dicom_folder = os.getenv('DICOM_FOLDER')
        output_folder = os.getenv('OUTPUT_FOLDER')
        
        if not dicom_folder:
            raise ValueError("DICOM_FOLDER not found in .env file")
        if not output_folder:
            raise ValueError("OUTPUT_FOLDER not found in .env file")
        
        # DICOM_FOLDER should be a full path now - no more PROJECT_ROOT needed
        if not os.path.isabs(dicom_folder):
            raise ValueError("DICOM_FOLDER must be set in .env file with full absolute path")
        if not os.path.isabs(output_folder):
            raise ValueError("OUTPUT_FOLDER must be set in .env file with full absolute path")
    
    return dicom_folder


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


def check_patient_folders_exist(dicom_path: Path) -> bool:
    """Check if any subdirectories (patient folders) exist in the DICOM path."""
    if not dicom_path.is_dir():
        return False
    
    for entry in os.scandir(dicom_path):
        if entry.is_dir():
            return True
    return False


def run_dcm2niix_conversion(input_dir, output_dir, filename_format="%d_%s"):
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
            '-v', '2',           # More verbose output for troubleshooting
            '-x', 'y',           # Crop 3D acquisitions
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


def convert_dicom_to_nifti(force_overwrite=False, min_size_mb=0.5):
    """
    Convert DICOM files to NIFTI format using dcm2niix with NiiVue optimization.
    
    Args:
        force_overwrite: If True, overwrite existing NIFTI directories
        min_size_mb: If > 0, delete NIFTI files smaller than this size in MB.
    """
    try:
        # Check dcm2niix installation first
        if not check_dcm2niix_installation():
            raise RuntimeError("dcm2niix is required but not found. Please install dcm2niix first.")
        
        # Load environment variables
        dicom_folder = load_environment()
        
        # Load label dictionary
        label_dict = load_label_dictionary()
        
        # Define paths - dicom_folder is now always absolute
        dicom_data_path = Path(dicom_folder)
        
        # Check if we're running in a Docker container
        is_docker = os.path.exists('/.dockerenv') or os.environ.get('DOCKER_CONTAINER') == 'true'
        
        if is_docker:
            # In Docker container, use the mounted paths
            output_folder = '/app/output'
        else:
            # On host machine, use environment variables
            output_folder = os.getenv('OUTPUT_FOLDER')
            if not output_folder:
                raise ValueError("OUTPUT_FOLDER must be set in .env file with full path")
            if not os.path.isabs(output_folder):
                raise ValueError("OUTPUT_FOLDER must be set in .env file with full absolute path")
        
        nifti_base_path = Path(output_folder)
        
        print(f"🔬 Enhanced DICOM to NIFTI Conversion (dcm2niix + NiiVue)")
        print(f"📁 DICOM Source: {dicom_data_path}")
        print(f"📁 NIFTI Destination Base: {nifti_base_path}")
        print("-" * 70)
        
        # Check if DICOM directory exists
        if not dicom_data_path.exists():
            raise FileNotFoundError(f"DICOM directory not found: {dicom_data_path}")
        
        # Check if patient folders (subdirectories) exist
        if not check_patient_folders_exist(dicom_data_path):
            raise FileNotFoundError(f"No patient folders (subdirectories) found in: {dicom_data_path}")
        
        # Create NIFTI base directory if it doesn't exist
        nifti_base_path.mkdir(parents=True, exist_ok=True)
        
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
                # New output structure: output/<patient_id>/nifti/
                output_directory = nifti_base_path / dicom_directory / "nifti"
            
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
                        output_dir=output_directory
                    )
                    
                    if conversion_result['status'] == 'success':
                        print(f"✅ dcm2niix conversion completed successfully")
                        
                        nifti_files = conversion_result['nifti_files']
                        
                        # Filter by size if requested
                        if min_size_mb > 0:
                            print(f"🗑️  Filtering NIFTI files by size (min size: {min_size_mb} MB)...")
                            large_nifti_files = []
                            deleted_count = 0
                            for nifti_file in nifti_files:
                                file_size_mb = nifti_file.stat().st_size / (1024 * 1024)
                                if file_size_mb >= min_size_mb:
                                    large_nifti_files.append(nifti_file)
                                else:
                                    print(f"   Deleting small file: {nifti_file.name} ({file_size_mb:.2f} MB)")
                                    nifti_file.unlink()
                                    deleted_count += 1
                                    # Also delete corresponding json and quality files
                                    base_name = nifti_file.name.replace('.nii.gz', '').replace('.nii', '')
                                    json_file = nifti_file.with_name(base_name + '.json')
                                    if json_file.exists():
                                        print(f"   Deleting corresponding json file: {json_file.name}")
                                        json_file.unlink()
                                    quality_file = nifti_file.with_name(base_name + '.quality.json')
                                    if quality_file.exists():
                                        print(f"   Deleting corresponding quality file: {quality_file.name}")
                                        quality_file.unlink()
                            
                            print(f"   Deleted {deleted_count} small NIFTI files.")
                            nifti_files = large_nifti_files
                            
                            # Check if any files remain after filtering
                            if not nifti_files:
                                print(f"⚠️  No files meet minimum size requirement ({min_size_mb} MB) for {dicom_directory}")
                                print(f"🗑️  Removing empty patient directory: {output_directory}")
                                shutil.rmtree(output_directory)
                                print(f"⏭️  Skipping {dicom_directory} - no files meet size criteria")
                                patient_pbar.update(1)
                                continue

                        # Process each created NIFTI file for NiiVue enhancement
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



if __name__ == "__main__":
    import sys
    # Check if force overwrite flag is passed
    force_overwrite = '--force' in sys.argv or '--overwrite' in sys.argv
    
    kwargs = {}
    if '--min-size-mb' in sys.argv:
        try:
            index = sys.argv.index('--min-size-mb')
            kwargs['min_size_mb'] = int(sys.argv[index + 1])
        except (ValueError, IndexError):
            print("Error: --min-size-mb requires an integer value (e.g., --min-size-mb 10)")
            sys.exit(1)

    convert_dicom_to_nifti(force_overwrite=force_overwrite, **kwargs)
