#!/usr/bin/env python3
"""
Voxel Effects Processing Script for Vista3D

This script applies MONAI-recommended post-processing effects to voxel files 
in the Vista3D project. It uses only official MONAI transforms for medical imaging
post-processing to ensure compatibility and best practices.

Usage:
    python voxel_effects.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 --effect gaussian_smooth
    python voxel_effects.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 --effect median_smooth --output-dir /custom/output
    python voxel_effects.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 --effect edge_enhancement
    python voxel_effects.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 --effect surface_cleanup
"""

import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
import numpy as np
import nibabel as nib
import torch
import torch.nn.functional as F
import logging

# MONAI imports for medical imaging post-processing
try:
    from monai.transforms import (
        # Smoothing transforms
        GaussianSmooth, MedianSmooth,
        # Enhancement transforms  
        SobelGradients, GaussianSharpen, AdjustContrast, HistogramEqualize,
        # Post-processing transforms
        FillHoles, RemoveSmallObjects, KeepLargestConnectedComponent,
        # Utility transforms
        EnsureChannelFirst, SaveImage, Compose
    )
    from monai.data import MetaTensor
    MONAI_AVAILABLE = True
except ImportError:
    MONAI_AVAILABLE = False
    logging.warning("MONAI not available. Install with: pip install monai")

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
    
    def _to_tensor(self, data: np.ndarray) -> torch.Tensor:
        """Convert numpy array to torch tensor with proper dimensions for MONAI."""
        if len(data.shape) == 3:
            # MONAI expects (batch, channel, height, width, depth) for 3D data
            return torch.from_numpy(data).float().unsqueeze(0).unsqueeze(0).cpu()
        elif len(data.shape) == 4:
            # Already has batch dimension, just add channel
            return torch.from_numpy(data).float().unsqueeze(1).cpu()
        else:
            return torch.from_numpy(data).float().cpu()
    
    def _to_numpy(self, tensor: torch.Tensor) -> np.ndarray:
        """Convert torch tensor back to numpy array."""
        # Remove batch and channel dimensions if they exist
        while tensor.dim() > 3:
            tensor = tensor.squeeze(0)
        return tensor.detach().cpu().numpy()
    
    def _apply_monai_transform(self, nifti_img: nib.Nifti1Image, transform, **kwargs) -> nib.Nifti1Image:
        """Apply MONAI transform to NIfTI image."""
        if not MONAI_AVAILABLE:
            raise ImportError("MONAI is required for this operation. Install with: pip install monai")
        
        # Convert to tensor format expected by MONAI
        data = nifti_img.get_fdata().astype(np.float32)
        tensor = self._to_tensor(data)
        
        # Apply MONAI transform
        transformed_tensor = transform(tensor, **kwargs)
        
        # Convert back to numpy
        processed_data = self._to_numpy(transformed_tensor)
        
        # Create new NIfTI image with same metadata
        processed_img = nib.Nifti1Image(processed_data, nifti_img.affine, nifti_img.header)
        return processed_img
    
    def apply_gaussian_smooth_effect(self, nifti_img: nib.Nifti1Image,
                                    sigma: Union[float, tuple] = 1.0) -> nib.Nifti1Image:
        """
        Apply MONAI Gaussian smoothing to improve voxel visualization quality.
        
        Args:
            nifti_img: Input NIfTI image
            sigma: Standard deviation for Gaussian smoothing
            
        Returns:
            Smoothly processed NIfTI image using MONAI GaussianSmooth transform
        """
        logger.info(f"Applying MONAI Gaussian smooth effect (sigma={sigma})")
        
        # Create MONAI GaussianSmooth transform
        gaussian_smooth = GaussianSmooth(sigma=sigma)
        
        # Apply MONAI transform
        processed_img = self._apply_monai_transform(nifti_img, gaussian_smooth)
        
        logger.info("MONAI Gaussian smooth effect applied successfully")
        return processed_img
    
    def apply_median_smooth_effect(self, nifti_img: nib.Nifti1Image,
                                  radius: Union[float, tuple] = 1.0) -> nib.Nifti1Image:
        """
        Apply MONAI median smoothing for improved medical visualization quality.
        
        Median smoothing is particularly effective for removing noise while preserving edges.
        
        Args:
            nifti_img: Input NIfTI image
            radius: Radius for median filtering
            
        Returns:
            Smoothly processed NIfTI image using MONAI MedianSmooth transform
        """
        logger.info(f"Applying MONAI median smooth effect (radius={radius})")
        
        # Create MONAI MedianSmooth transform
        median_smooth = MedianSmooth(radius=radius)
        
        # Apply MONAI transform
        processed_img = self._apply_monai_transform(nifti_img, median_smooth)
        
        logger.info("MONAI median smooth effect applied successfully")
        return processed_img
    
    def apply_surface_cleanup_effect(self, nifti_img: nib.Nifti1Image,
                                    min_size: int = 100,
                                    connectivity: int = 1) -> nib.Nifti1Image:
        """
        Apply MONAI surface cleanup for improved voxel visualization.
        
        This effect uses MONAI post-processing transforms to clean up surface artifacts
        and remove small objects while maintaining anatomical accuracy.
        
        Args:
            nifti_img: Input NIfTI image
            min_size: Minimum size for objects to keep
            connectivity: Connectivity for morphological operations
            
        Returns:
            Cleaned NIfTI image with improved surface quality using MONAI transforms
        """
        logger.info(f"Applying MONAI surface cleanup effect (min_size={min_size})")
        
        # Convert to tensor format
        data = nifti_img.get_fdata().astype(np.float32)
        tensor = self._to_tensor(data)
        
        # Create MONAI transforms pipeline
        # Step 1: Fill holes
        fill_holes = FillHoles()
        filled_tensor = fill_holes(tensor)
        
        # Step 2: Remove small objects
        remove_small = RemoveSmallObjects(min_size=min_size, connectivity=connectivity)
        cleaned_tensor = remove_small(filled_tensor)
        
        # Step 3: Keep largest connected component
        keep_largest = KeepLargestConnectedComponent()
        final_tensor = keep_largest(cleaned_tensor)
        
        # Convert back to numpy
        processed_data = self._to_numpy(final_tensor)
        
        # Create new NIfTI image
        processed_img = nib.Nifti1Image(processed_data, nifti_img.affine, nifti_img.header)
        logger.info("MONAI surface cleanup applied successfully")
        return processed_img
    
    def apply_edge_enhancement_effect(self, nifti_img: nib.Nifti1Image,
                                     kernel_size: int = 3,
                                     normalize_kernels: bool = True) -> nib.Nifti1Image:
        """
        Apply MONAI edge enhancement for improved voxel visualization.
        
        This effect uses MONAI SobelGradients to enhance edges and improve
        anatomical structure visibility.
        
        Args:
            nifti_img: Input NIfTI image
            kernel_size: Size of the Sobel kernel
            normalize_kernels: Whether to normalize the gradient kernels
            
        Returns:
            Edge-enhanced NIfTI image using MONAI SobelGradients transform
        """
        logger.info(f"Applying MONAI edge enhancement effect (kernel_size={kernel_size})")
        
        # Create MONAI SobelGradients transform
        sobel_gradients = SobelGradients(kernel_size=kernel_size, normalize_kernels=normalize_kernels)
        
        # Apply MONAI transform
        processed_img = self._apply_monai_transform(nifti_img, sobel_gradients)
        
        logger.info("MONAI edge enhancement applied successfully")
        return processed_img

    def apply_contrast_enhancement_effect(self, nifti_img: nib.Nifti1Image,
                                         contrast_factor: float = 1.5,
                                         gamma: float = 1.0) -> nib.Nifti1Image:
        """
        Apply MONAI contrast enhancement for improved voxel visualization.
        
        This effect uses MONAI AdjustContrast to enhance contrast and improve
        anatomical structure visibility.
        
        Args:
            nifti_img: Input NIfTI image
            contrast_factor: Factor for contrast adjustment
            gamma: Gamma correction factor
            
        Returns:
            Contrast-enhanced NIfTI image using MONAI AdjustContrast transform
        """
        logger.info(f"Applying MONAI contrast enhancement effect (contrast_factor={contrast_factor})")
        
        # Create MONAI AdjustContrast transform
        adjust_contrast = AdjustContrast(gamma=gamma)
        
        # Apply MONAI transform
        processed_img = self._apply_monai_transform(nifti_img, adjust_contrast)
        
        # Apply additional contrast scaling if needed
        if contrast_factor != 1.0:
            data = processed_img.get_fdata().astype(np.float32)
            # Simple contrast scaling
            data_mean = np.mean(data)
            enhanced_data = (data - data_mean) * contrast_factor + data_mean
            processed_img = nib.Nifti1Image(enhanced_data, processed_img.affine, processed_img.header)
        
        logger.info("MONAI contrast enhancement applied successfully")
        return processed_img

    def apply_histogram_equalization_effect(self, nifti_img: nib.Nifti1Image,
                                           num_bins: int = 256,
                                           min: float = 0.0,
                                           max: float = 1.0) -> nib.Nifti1Image:
        """
        Apply MONAI histogram equalization for improved voxel visualization.
        
        This effect uses MONAI HistogramEqualize to improve contrast distribution
        and enhance anatomical structure visibility.
        
        Args:
            nifti_img: Input NIfTI image
            num_bins: Number of histogram bins
            min: Minimum value for normalization
            max: Maximum value for normalization
            
        Returns:
            Histogram-equalized NIfTI image using MONAI HistogramEqualize transform
        """
        logger.info(f"Applying MONAI histogram equalization effect (num_bins={num_bins})")
        
        # Create MONAI HistogramEqualize transform
        histogram_equalize = HistogramEqualize(num_bins=num_bins, min=min, max=max)
        
        # Apply MONAI transform
        processed_img = self._apply_monai_transform(nifti_img, histogram_equalize)
        
        logger.info("MONAI histogram equalization applied successfully")
        return processed_img

    def apply_no_processing_effect(self, nifti_img: nib.Nifti1Image) -> nib.Nifti1Image:
        """
        Apply no processing - return the original voxel exactly as it is.
        
        This effect is useful for comparison and ensures the original voxel
        appearance is completely preserved without any modifications.
        
        Args:
            nifti_img: Input NIfTI image
            
        Returns:
            Original NIfTI image unchanged
        """
        logger.info("Applying no processing effect - returning original voxel unchanged")
        
        # Simply return the original image without any processing
        processed_img = nib.Nifti1Image(nifti_img.get_fdata(), nifti_img.affine, nifti_img.header)
        logger.info("No processing effect applied successfully - original voxel preserved exactly")
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
                
                # Apply MONAI-based effect
                if effect_name == "gaussian_smooth":
                    processed_img = self.apply_gaussian_smooth_effect(nifti_img, **effect_params)
                elif effect_name == "median_smooth":
                    processed_img = self.apply_median_smooth_effect(nifti_img, **effect_params)
                elif effect_name == "surface_cleanup":
                    processed_img = self.apply_surface_cleanup_effect(nifti_img, **effect_params)
                elif effect_name == "edge_enhancement":
                    processed_img = self.apply_edge_enhancement_effect(nifti_img, **effect_params)
                elif effect_name == "contrast_enhancement":
                    processed_img = self.apply_contrast_enhancement_effect(nifti_img, **effect_params)
                elif effect_name == "histogram_equalization":
                    processed_img = self.apply_histogram_equalization_effect(nifti_img, **effect_params)
                elif effect_name == "no_processing":
                    processed_img = self.apply_no_processing_effect(nifti_img)
                else:
                    raise ValueError(f"Unknown effect: {effect_name}")
                
                # Save processed image
                # For individual voxel files in effect-specific folders, use original name
                # For main scan files, append effect name to distinguish from original
                if file_path in voxel_files['individual_voxels']:
                    # Individual voxel files: use original name since folder indicates effect
                    output_filename = file_path.name
                else:
                    # Main scan files: append effect name to distinguish from original
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
        description="Apply MONAI-recommended post-processing effects to voxel files in Vista3D",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Apply MONAI Gaussian smoothing
  python voxel_effects.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 --effect gaussian_smooth --sigma 1.0
  
  # Apply MONAI median smoothing for noise reduction
  python voxel_effects.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 --effect median_smooth --radius 1.0
  
  # Apply MONAI surface cleanup (fill holes, remove small objects)
  python voxel_effects.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 --effect surface_cleanup --min-size 100
  
  # Apply MONAI edge enhancement using Sobel gradients
  python voxel_effects.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 --effect edge_enhancement --kernel-size 3
  
  # Apply MONAI contrast enhancement
  python voxel_effects.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 --effect contrast_enhancement --contrast-factor 1.5 --gamma 1.0
  
  # Apply MONAI histogram equalization
  python voxel_effects.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 --effect histogram_equalization --num-bins 256
  
  # Return original voxel without any processing (for comparison)
  python voxel_effects.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 --effect no_processing
        """
    )
    
    # Required arguments
    parser.add_argument("--patient", required=True, help="Patient ID (e.g., PA00000002)")
    parser.add_argument("--scan", required=True, help="Scan name (e.g., 2.5MM_ARTERIAL_3)")
    parser.add_argument("--effect", required=True, 
                       choices=["gaussian_smooth", "median_smooth", "surface_cleanup", "edge_enhancement", "contrast_enhancement", "histogram_equalization", "no_processing"],
                       help="MONAI-based effect to apply")
    
    # Optional arguments
    parser.add_argument("--output-dir", type=Path, help="Custom output directory")
    
    # Gaussian smooth parameters
    parser.add_argument("--sigma", type=float, default=1.0, help="Gaussian smoothing sigma (default: 1.0)")
    
    # Median smooth parameters
    parser.add_argument("--radius", type=float, default=1.0, help="Median smoothing radius (default: 1.0)")
    
    # Surface cleanup parameters
    parser.add_argument("--min-size", type=int, default=100, help="Minimum size for objects to keep (default: 100)")
    parser.add_argument("--connectivity", type=int, default=1, help="Connectivity for morphological operations (default: 1)")
    
    # Edge enhancement parameters
    parser.add_argument("--kernel-size", type=int, default=3, help="Size of Sobel kernel (default: 3)")
    parser.add_argument("--normalize-kernels", action="store_true", default=True, help="Normalize gradient kernels (default: True)")
    
    # Contrast enhancement parameters
    parser.add_argument("--contrast-factor", type=float, default=1.5, help="Contrast adjustment factor (default: 1.5)")
    parser.add_argument("--gamma", type=float, default=1.0, help="Gamma correction factor (default: 1.0)")
    
    # Histogram equalization parameters
    parser.add_argument("--num-bins", type=int, default=256, help="Number of histogram bins (default: 256)")
    parser.add_argument("--min", type=float, default=0.0, help="Minimum value for normalization (default: 0.0)")
    parser.add_argument("--max", type=float, default=1.0, help="Maximum value for normalization (default: 1.0)")
    
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Create processor
        processor = VoxelEffectsProcessor()
        
        # Prepare effect parameters based on MONAI-based effects
        effect_params = {
            # Gaussian smooth parameters
            "sigma": args.sigma,
            # Median smooth parameters
            "radius": args.radius,
            # Surface cleanup parameters
            "min_size": args.min_size,
            "connectivity": args.connectivity,
            # Edge enhancement parameters
            "kernel_size": args.kernel_size,
            "normalize_kernels": args.normalize_kernels,
            # Contrast enhancement parameters
            "contrast_factor": args.contrast_factor,
            "gamma": args.gamma,
            # Histogram equalization parameters
            "num_bins": args.num_bins,
            "min": args.min,
            "max": args.max,
        }
        
        # Filter parameters based on effect
        if args.effect == "gaussian_smooth":
            effect_params = {k: v for k, v in effect_params.items() if k in ["sigma"]}
        elif args.effect == "median_smooth":
            effect_params = {k: v for k, v in effect_params.items() if k in ["radius"]}
        elif args.effect == "surface_cleanup":
            effect_params = {k: v for k, v in effect_params.items() if k in ["min_size", "connectivity"]}
        elif args.effect == "edge_enhancement":
            effect_params = {k: v for k, v in effect_params.items() if k in ["kernel_size", "normalize_kernels"]}
        elif args.effect == "contrast_enhancement":
            effect_params = {k: v for k, v in effect_params.items() if k in ["contrast_factor", "gamma"]}
        elif args.effect == "histogram_equalization":
            effect_params = {k: v for k, v in effect_params.items() if k in ["num_bins", "min", "max"]}
        elif args.effect == "no_processing":
            effect_params = {}  # No parameters needed for no processing
        
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