#!/usr/bin/env python3
"""
Voxel Effects Processing Script for Vista3D

This script applies various effects to voxel files in the Vista3D project.
It can process both individual voxel files in scan subdirectories and 
the main scan files themselves.

Usage:
    python voxel_effects.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 --effect smooth_texture
    python voxel_effects.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 --effect smooth_texture --output-dir /custom/output
"""

import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
import numpy as np
import nibabel as nib
from scipy import ndimage
from scipy.ndimage import gaussian_filter, binary_erosion, binary_dilation
from skimage import morphology, filters, measure
import logging

# Add the project root to the Python path
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent  # frontend/utils -> frontend -> project_root
sys.path.insert(0, str(project_root))

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    # Load .env file from project root
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    # python-dotenv not available, rely on system environment variables
    pass

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Log that .env was loaded if available
try:
    from dotenv import load_dotenv
    env_path = project_root / ".env"
    if env_path.exists():
        logger.info(f"Loaded environment from: {env_path}")
except ImportError:
    pass


class VoxelEffectsProcessor:
    """Main class for processing voxel effects on NIfTI files."""
    
    def __init__(self, output_base_dir: Optional[Path] = None):
        """
        Initialize the processor.
        
        Args:
            output_base_dir: Base directory for output files. If None, uses project output directory.
        """
        self.output_base_dir = output_base_dir or self._get_default_output_dir()
        logger.info(f"Using output directory: {self.output_base_dir}")
    
    def _get_default_output_dir(self) -> Path:
        """Get the default output directory from environment or project structure."""
        output_folder = os.getenv('OUTPUT_FOLDER')
        if output_folder:
            logger.info(f"Using OUTPUT_FOLDER from environment: {output_folder}")
            return Path(output_folder)
        
        # Fallback to project structure - go up to project root
        script_dir = Path(__file__).parent
        project_root = script_dir.parent.parent  # frontend/utils -> frontend -> project_root
        fallback_path = project_root / "output"
        logger.warning(f"OUTPUT_FOLDER not found in environment, using fallback: {fallback_path}")
        return fallback_path
    
    def get_voxel_files(self, patient_id: str, scan_name: str) -> Dict[str, List[Path]]:
        """
        Get all voxel files for a patient and scan.
        
        Args:
            patient_id: Patient identifier (e.g., 'PA00000002')
            scan_name: Scan name (e.g., '2.5MM_ARTERIAL_3')
            
        Returns:
            Dictionary with 'individual_voxels' and 'main_scan' keys containing file paths
        """
        patient_dir = self.output_base_dir / patient_id
        voxels_dir = patient_dir / "voxels"
        
        if not voxels_dir.exists():
            raise FileNotFoundError(f"Voxels directory not found: {voxels_dir}")
        
        # Get individual voxel files from scan subdirectory
        scan_voxels_dir = voxels_dir / scan_name
        individual_voxels = []
        if scan_voxels_dir.exists():
            individual_voxels = [
                f for f in scan_voxels_dir.glob("*.nii.gz")
                if f.is_file()
            ]
            logger.info(f"Found {len(individual_voxels)} individual voxel files in {scan_voxels_dir}")
        else:
            logger.warning(f"Scan voxels directory not found: {scan_voxels_dir}")
        
        # Get main scan file
        main_scan_path = voxels_dir / f"{scan_name}.nii.gz"
        main_scan = [main_scan_path] if main_scan_path.exists() else []
        
        if main_scan:
            logger.info(f"Found main scan file: {main_scan_path}")
        else:
            logger.warning(f"Main scan file not found: {main_scan_path}")
        
        return {
            'individual_voxels': individual_voxels,
            'main_scan': main_scan
        }
    
    def apply_smooth_texture_effect(self, nifti_img: nib.Nifti1Image, 
                                  sigma: float = 1.0, 
                                  threshold: float = 0.5,
                                  preserve_structure: bool = True) -> nib.Nifti1Image:
        """
        Apply smooth texture effect to create surface-like appearance.
        
        This effect:
        1. Applies Gaussian smoothing to reduce noise and create smooth surfaces
        2. Optionally applies morphological operations to preserve structure
        3. Creates a more surface-like appearance from voxel data
        
        Args:
            nifti_img: Input NIfTI image
            sigma: Standard deviation for Gaussian smoothing (higher = smoother)
            threshold: Threshold for binary operations (0.0-1.0)
            preserve_structure: Whether to apply structure-preserving operations
            
        Returns:
            Processed NIfTI image with smooth texture effect
        """
        logger.info(f"Applying smooth texture effect (sigma={sigma}, threshold={threshold})")
        
        # Get the data
        data = nifti_img.get_fdata().astype(np.float32)
        original_shape = data.shape
        
        # Normalize data to 0-1 range for processing
        data_min, data_max = data.min(), data.max()
        if data_max > data_min:
            data_normalized = (data - data_min) / (data_max - data_min)
        else:
            data_normalized = data.copy()
        
        # Apply Gaussian smoothing for surface-like effect
        logger.info("Applying Gaussian smoothing...")
        smoothed = gaussian_filter(data_normalized, sigma=sigma)
        
        if preserve_structure:
            # Apply structure-preserving operations
            logger.info("Applying structure-preserving operations...")
            
            # Create binary mask from thresholded data
            binary_mask = smoothed > threshold
            
            # Apply morphological operations to smooth boundaries
            # Use opening to remove small noise, then closing to fill gaps
            kernel = morphology.ball(2)  # 3D spherical kernel
            binary_mask = morphology.binary_opening(binary_mask, kernel)
            binary_mask = morphology.binary_closing(binary_mask, kernel)
            
            # Apply distance transform and then smooth the result
            logger.info("Applying distance transform for surface enhancement...")
            distance = ndimage.distance_transform_edt(binary_mask)
            
            # Normalize distance transform and combine with smoothed data
            if distance.max() > 0:
                distance_normalized = distance / distance.max()
                # Blend original smoothed data with distance-based surface
                smoothed = 0.7 * smoothed + 0.3 * distance_normalized
        
        # Apply additional smoothing to enhance surface appearance
        logger.info("Applying final surface smoothing...")
        smoothed = gaussian_filter(smoothed, sigma=sigma * 0.5)
        
        # Denormalize back to original range
        if data_max > data_min:
            processed_data = smoothed * (data_max - data_min) + data_min
        else:
            processed_data = smoothed
        
        # Ensure data type consistency
        processed_data = processed_data.astype(data.dtype)
        
        # Create new NIfTI image with processed data
        processed_img = nib.Nifti1Image(processed_data, nifti_img.affine, nifti_img.header)
        
        logger.info(f"Smooth texture effect applied successfully. Shape: {original_shape}")
        return processed_img
    
    def apply_gaussian_smooth_effect(self, nifti_img: nib.Nifti1Image, 
                                   sigma: float = 2.0) -> nib.Nifti1Image:
        """
        Apply simple Gaussian smoothing effect.
        
        Args:
            nifti_img: Input NIfTI image
            sigma: Standard deviation for Gaussian smoothing
            
        Returns:
            Smoothed NIfTI image
        """
        logger.info(f"Applying Gaussian smooth effect (sigma={sigma})")
        
        data = nifti_img.get_fdata()
        smoothed_data = gaussian_filter(data, sigma=sigma)
        
        processed_img = nib.Nifti1Image(smoothed_data, nifti_img.affine, nifti_img.header)
        logger.info("Gaussian smooth effect applied successfully")
        return processed_img
    
    def apply_edge_enhancement_effect(self, nifti_img: nib.Nifti1Image,
                                    sigma: float = 1.0,
                                    alpha: float = 2.0) -> nib.Nifti1Image:
        """
        Apply edge enhancement effect to highlight boundaries.
        
        Args:
            nifti_img: Input NIfTI image
            sigma: Standard deviation for smoothing before edge detection
            alpha: Enhancement factor for edges
            
        Returns:
            Edge-enhanced NIfTI image
        """
        logger.info(f"Applying edge enhancement effect (sigma={sigma}, alpha={alpha})")
        
        data = nifti_img.get_fdata().astype(np.float32)
        
        # Apply Gaussian smoothing first
        smoothed = gaussian_filter(data, sigma=sigma)
        
        # Calculate edges using Laplacian
        edges = filters.laplace(smoothed)
        
        # Enhance edges
        enhanced = smoothed + alpha * edges
        
        # Clip values to prevent overflow
        enhanced = np.clip(enhanced, data.min(), data.max())
        
        processed_img = nib.Nifti1Image(enhanced, nifti_img.affine, nifti_img.header)
        logger.info("Edge enhancement effect applied successfully")
        return processed_img
    
    def process_files(self, patient_id: str, scan_name: str, effect_name: str, 
                     effect_params: Dict[str, Any], output_dir: Optional[Path] = None) -> List[Path]:
        """
        Process all voxel files for a patient and scan with the specified effect.
        
        Args:
            patient_id: Patient identifier
            scan_name: Scan name
            effect_name: Name of the effect to apply
            effect_params: Parameters for the effect
            output_dir: Custom output directory (optional)
            
        Returns:
            List of processed file paths
        """
        logger.info(f"Processing {patient_id}/{scan_name} with effect: {effect_name}")
        
        # Get all voxel files
        voxel_files = self.get_voxel_files(patient_id, scan_name)
        all_files = voxel_files['individual_voxels'] + voxel_files['main_scan']
        
        if not all_files:
            logger.warning(f"No voxel files found for {patient_id}/{scan_name}")
            return []
        
        # Determine output directory
        if output_dir:
            output_base = output_dir
        else:
            output_base = self.output_base_dir / patient_id / "voxels"
        
        # Create effect-specific output directory
        effect_output_dir = output_base / f"{scan_name}_{effect_name}"
        effect_output_dir.mkdir(parents=True, exist_ok=True)
        
        processed_files = []
        
        # Process each file
        for file_path in all_files:
            try:
                logger.info(f"Processing file: {file_path.name}")
                
                # Load NIfTI image
                nifti_img = nib.load(file_path)
                
                # Apply effect based on name
                if effect_name == "smooth_texture":
                    processed_img = self.apply_smooth_texture_effect(nifti_img, **effect_params)
                elif effect_name == "gaussian_smooth":
                    processed_img = self.apply_gaussian_smooth_effect(nifti_img, **effect_params)
                elif effect_name == "edge_enhancement":
                    processed_img = self.apply_edge_enhancement_effect(nifti_img, **effect_params)
                else:
                    raise ValueError(f"Unknown effect: {effect_name}")
                
                # Save processed image with effect name appended to original filename
                # Remove .nii.gz extension and add effect name
                original_name = file_path.name.replace('.nii.gz', '')
                output_filename = f"{original_name}_{effect_name}.nii.gz"
                output_path = effect_output_dir / output_filename
                nib.save(processed_img, output_path)
                
                processed_files.append(output_path)
                logger.info(f"Saved processed file: {output_path}")
                
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                continue
        
        logger.info(f"Processing complete. {len(processed_files)} files processed.")
        return processed_files


def main():
    """Main command-line interface."""
    parser = argparse.ArgumentParser(
        description="Apply effects to voxel files in Vista3D",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Apply smooth texture effect
  python voxel_effects.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 --effect smooth_texture
  
  # Apply smooth texture with custom parameters
  python voxel_effects.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 --effect smooth_texture --sigma 2.0 --threshold 0.3
  
  # Apply Gaussian smoothing
  python voxel_effects.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 --effect gaussian_smooth --sigma 1.5
  
  # Apply edge enhancement
  python voxel_effects.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 --effect edge_enhancement --sigma 1.0 --alpha 2.5
        """
    )
    
    # Required arguments
    parser.add_argument("--patient", required=True, help="Patient ID (e.g., PA00000002)")
    parser.add_argument("--scan", required=True, help="Scan name (e.g., 2.5MM_ARTERIAL_3)")
    parser.add_argument("--effect", required=True, 
                       choices=["smooth_texture", "gaussian_smooth", "edge_enhancement"],
                       help="Effect to apply")
    
    # Optional arguments
    parser.add_argument("--output-dir", type=Path, help="Custom output directory")
    parser.add_argument("--sigma", type=float, default=1.0, help="Gaussian smoothing sigma (default: 1.0)")
    parser.add_argument("--threshold", type=float, default=0.5, help="Threshold for binary operations (default: 0.5)")
    parser.add_argument("--alpha", type=float, default=2.0, help="Enhancement factor for edges (default: 2.0)")
    parser.add_argument("--preserve-structure", action="store_true", default=True,
                       help="Whether to preserve structure in smooth_texture effect (default: True)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Create processor
        processor = VoxelEffectsProcessor()
        
        # Prepare effect parameters
        effect_params = {
            "sigma": args.sigma,
            "threshold": args.threshold,
            "alpha": args.alpha,
            "preserve_structure": args.preserve_structure
        }
        
        # Filter parameters based on effect
        if args.effect == "smooth_texture":
            effect_params = {k: v for k, v in effect_params.items() 
                           if k in ["sigma", "threshold", "preserve_structure"]}
        elif args.effect == "gaussian_smooth":
            effect_params = {"sigma": effect_params["sigma"]}
        elif args.effect == "edge_enhancement":
            effect_params = {k: v for k, v in effect_params.items() 
                           if k in ["sigma", "alpha"]}
        
        # Process files
        processed_files = processor.process_files(
            patient_id=args.patient,
            scan_name=args.scan,
            effect_name=args.effect,
            effect_params=effect_params,
            output_dir=args.output_dir
        )
        
        if processed_files:
            print(f"\n✅ Successfully processed {len(processed_files)} files:")
            for file_path in processed_files:
                print(f"  - {file_path}")
        else:
            print("\n❌ No files were processed.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()