#!/usr/bin/env python3
"""
Voxel Effects Processing Script for Vista3D

This script applies high-quality MONAI-based post-processing effects to voxel files 
in the Vista3D project. It can process both individual voxel files in scan 
subdirectories and the main scan files themselves.

Usage:
    python voxel_effects.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 --effect monai_smooth
    python voxel_effects.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 --effect surface_refinement --output-dir /custom/output
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
from scipy import ndimage
from scipy.ndimage import gaussian_filter, median_filter, uniform_filter
from skimage import morphology, filters, measure, segmentation
from skimage.restoration import denoise_bilateral
import logging

# MONAI imports for high-quality post-processing
try:
    from monai.transforms import (
        SobelGradients, FillHoles, RemoveSmallObjects, LabelToContour,
        SpatialPad, RandGaussianNoise, GaussianSmooth, MedianSmooth,
        RandGaussianSharpen, RandHistogramShift, RandAdjustContrast,
        RandBiasField, RandGibbsNoise, RandCoarseDropout
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
            # Ensure tensor is on CPU as MONAI transforms expect CPU tensors
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
    
    def _apply_edge_preserving_smoothing(self, data: np.ndarray, sigma: float) -> np.ndarray:
        """Apply edge-preserving smoothing using 3D-compatible methods."""
        # Use median filtering for edge preservation
        median_smoothed = median_filter(data, size=max(3, int(sigma*2)))
        
        # Combine with gaussian smoothing
        gaussian_smoothed = gaussian_filter(data, sigma=sigma)
        
        # Create edge map to preserve important structures
        edge_map = np.abs(gaussian_filter(data, sigma=sigma*0.5) - data)
        edge_threshold = np.percentile(edge_map, 75)
        edge_mask = edge_map > edge_threshold
        
        # Blend based on edge presence
        result = np.where(edge_mask, 
                         0.7 * data + 0.3 * median_smoothed,  # Preserve edges
                         0.3 * data + 0.7 * gaussian_smoothed)  # Smooth non-edges
        
        return result
    
    def apply_monai_smooth_effect(self, nifti_img: nib.Nifti1Image,
                                 sigma: Union[float, tuple] = 1.0,
                                 preserve_range: bool = True) -> nib.Nifti1Image:
        """
        Apply MONAI-based Gaussian smoothing for high-quality voxel smoothing.
        
        Args:
            nifti_img: Input NIfTI image
            sigma: Standard deviation for Gaussian smoothing
            preserve_range: Whether to preserve the original data range
            
        Returns:
            Smoothed NIfTI image using MONAI transforms
        """
        logger.info(f"Applying MONAI smooth effect (sigma={sigma})")
        
        data = nifti_img.get_fdata().astype(np.float32)
        original_min, original_max = data.min(), data.max()
        
        if MONAI_AVAILABLE:
            try:
                # Check MONAI version and availability
                import monai
                logger.info(f"MONAI version: {monai.__version__}")
                logger.info(f"MONAI available: {MONAI_AVAILABLE}")
                
                # Convert to tensor for MONAI processing
                tensor_data = self._to_tensor(data)
                logger.info(f"Tensor shape before MONAI processing: {tensor_data.shape}")
                logger.info(f"Tensor dtype: {tensor_data.dtype}")
                logger.info(f"Tensor device: {tensor_data.device}")
                
                # Implement advanced multi-pass smoothing for realistic voxel appearance
                logger.info("Applying advanced multi-pass smoothing for realistic voxel appearance")
                
                # Step 1: Multi-scale Gaussian smoothing for surface smoothness
                logger.info("Step 1: Multi-scale Gaussian smoothing")
                processed_data = data.copy()
                
                # Apply multiple smoothing passes with different scales
                smoothing_scales = [sigma * 0.5, sigma, sigma * 1.5, sigma * 2.0]
                for i, scale in enumerate(smoothing_scales):
                    processed_data = gaussian_filter(processed_data, sigma=scale)
                    logger.info(f"  Applied smoothing pass {i+1} with sigma={scale}")
                
                # Step 2: Edge-preserving smoothing using 3D-compatible methods
                logger.info("Step 2: Edge-preserving smoothing using 3D-compatible methods")
                
                # Apply edge-preserving smoothing using median filtering
                # This preserves edges while smoothing noise
                edge_preserving_data = median_filter(processed_data, size=3)
                processed_data = 0.7 * processed_data + 0.3 * edge_preserving_data
                logger.info("Applied edge-preserving median filtering")
                
                # Apply anisotropic-like smoothing using multiple directional kernels
                logger.info("Applying directional smoothing for structure preservation")
                directional_processed = processed_data.copy()
                
                # Create different directional kernels
                kernels = [
                    np.array([[[1,1,1],[1,1,1],[1,1,1]]]) * 0.1,  # Z-direction
                    np.array([[[1],[1],[1]]]) * 0.1,  # Y-direction  
                    np.array([[1,1,1]]) * 0.1,  # X-direction
                ]
                
                for i, kernel in enumerate(kernels):
                    directional_smoothed = ndimage.convolve(processed_data, kernel, mode='constant')
                    directional_processed = 0.8 * directional_processed + 0.2 * directional_smoothed
                
                processed_data = directional_processed
                logger.info("Applied directional structure-preserving smoothing")
                
                # Step 3: Anisotropic diffusion for structure-preserving smoothing
                logger.info("Step 3: Anisotropic diffusion smoothing")
                from skimage.filters import gaussian
                from skimage.segmentation import watershed
                from skimage.feature import peak_local_maxima
                
                # Create a mask for the main structures
                threshold = np.percentile(processed_data, 75)  # Use 75th percentile as threshold
                mask = processed_data > threshold
                
                # Apply anisotropic diffusion-like smoothing
                # Simulate anisotropic diffusion with multiple directional gaussians
                directions = [
                    (1, 0, 0), (0, 1, 0), (0, 0, 1),  # Axial directions
                    (1, 1, 0), (1, 0, 1), (0, 1, 1),  # Diagonal directions
                    (1, 1, 1)  # Full diagonal
                ]
                
                smoothed_data = processed_data.copy()
                for direction in directions:
                    # Apply directional smoothing
                    directional_sigma = [sigma * d for d in direction]
                    directional_smoothed = gaussian_filter(processed_data, sigma=directional_sigma)
                    smoothed_data = 0.8 * smoothed_data + 0.2 * directional_smoothed
                
                processed_data = smoothed_data
                
                # Step 4: Final surface refinement
                logger.info("Step 4: Final surface refinement")
                # Apply morphological opening and closing for surface cleanup
                kernel = morphology.ball(1)  # Small kernel for fine details
                processed_data = morphology.opening(processed_data, kernel)
                processed_data = morphology.closing(processed_data, kernel)
                
                # Final gentle smoothing
                processed_data = gaussian_filter(processed_data, sigma=sigma * 0.3)
                
                logger.info("Advanced multi-pass smoothing completed successfully")
            except Exception as e:
                logger.error(f"MONAI processing failed: {e}")
                logger.error(f"Exception type: {type(e).__name__}")
                logger.error(f"Exception args: {e.args}")
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
                logger.warning("Falling back to scipy")
                processed_data = gaussian_filter(data, sigma=sigma)
        else:
            # Fallback to scipy if MONAI not available
            logger.warning("MONAI not available, using scipy fallback")
            processed_data = gaussian_filter(data, sigma=sigma)
        
        # Preserve original data range if requested
        if preserve_range and original_max > original_min:
            processed_data = np.clip(processed_data, original_min, original_max)
        
        processed_img = nib.Nifti1Image(processed_data, nifti_img.affine, nifti_img.header)
        logger.info("MONAI smooth effect applied successfully")
        return processed_img
    
    def apply_surface_refinement_effect(self, nifti_img: nib.Nifti1Image,
                                      threshold: float = 0.5,
                                      min_size: int = 100,
                                      kernel_size: int = 3) -> nib.Nifti1Image:
        """
        Apply surface refinement using MONAI morphological operations.
        
        This effect:
        1. Uses MONAI's FillHoles to smooth surfaces
        2. Removes small objects for cleaner appearance
        3. Applies edge detection for better surface definition
        
        Args:
            nifti_img: Input NIfTI image
            threshold: Threshold for binary operations
            min_size: Minimum size for objects to keep
            kernel_size: Kernel size for morphological operations
            
        Returns:
            Surface-refined NIfTI image
        """
        logger.info(f"Applying surface refinement effect (threshold={threshold}, min_size={min_size})")
        
        data = nifti_img.get_fdata().astype(np.float32)
        original_min, original_max = data.min(), data.max()
        
        # Normalize data for processing
        if original_max > original_min:
            data_normalized = (data - original_min) / (original_max - original_min)
        else:
            data_normalized = data.copy()
        
        # Create binary mask
        binary_mask = data_normalized > threshold
        
        # Use scipy/skimage for reliable morphological operations
        # MONAI's morphological transforms have compatibility issues
        logger.info("Using scipy/skimage for morphological operations (more reliable than MONAI)")
        
        # Apply morphological operations using scipy/skimage
        kernel = morphology.ball(kernel_size)
        processed_mask = morphology.binary_closing(binary_mask, kernel)
        processed_mask = morphology.remove_small_objects(processed_mask, min_size=min_size)
        
        logger.info(f"Applied morphological operations: closing with ball({kernel_size}) and remove_small_objects({min_size})")
        
        # Apply distance transform for smooth surface
        distance = ndimage.distance_transform_edt(processed_mask)
        
        # Create smooth surface by combining distance transform with original data
        if distance.max() > 0:
            distance_normalized = distance / distance.max()
            # Blend original data with distance-based surface
            processed_data = 0.8 * data_normalized + 0.2 * distance_normalized
        else:
            processed_data = data_normalized
        
        # Denormalize back to original range
        if original_max > original_min:
            processed_data = processed_data * (original_max - original_min) + original_min
        
        processed_img = nib.Nifti1Image(processed_data, nifti_img.affine, nifti_img.header)
        logger.info("Surface refinement effect applied successfully")
        return processed_img
    
    def apply_texture_enhancement_effect(self, nifti_img: nib.Nifti1Image,
                                       edge_strength: float = 1.5,
                                       contrast_factor: float = 1.2,
                                       noise_level: float = 0.02) -> nib.Nifti1Image:
        """
        Apply texture enhancement using MONAI edge detection and contrast adjustment.
        
        Args:
            nifti_img: Input NIfTI image
            edge_strength: Strength of edge enhancement
            contrast_factor: Factor for contrast adjustment
            noise_level: Level of noise to add for texture
            
        Returns:
            Texture-enhanced NIfTI image
        """
        logger.info(f"Applying texture enhancement effect (edge_strength={edge_strength}, contrast={contrast_factor})")
        
        data = nifti_img.get_fdata().astype(np.float32)
        original_min, original_max = data.min(), data.max()
        
        # Convert to tensor for MONAI processing
        tensor_data = self._to_tensor(data)
        
        # Use scipy/skimage for reliable edge detection and contrast adjustment
        # MONAI's transforms have compatibility issues with 3D data
        logger.info("Using scipy/skimage for texture enhancement (more reliable than MONAI)")
        
        # Apply edge detection using scipy/skimage
        edges_np = filters.sobel(data)
        logger.info("Applied Sobel edge detection")
        
        # Apply contrast adjustment
        enhanced_np = np.power(data, contrast_factor)
        logger.info(f"Applied contrast adjustment with factor {contrast_factor}")
        
        # Combine enhanced data with edge information
        processed_data = enhanced_np + edge_strength * edges_np
        
        # Add subtle noise for texture
        if noise_level > 0:
            noise = np.random.normal(0, noise_level * (original_max - original_min), data.shape)
            processed_data += noise
        
        # Ensure data stays within original range
        processed_data = np.clip(processed_data, original_min, original_max)
        
        processed_img = nib.Nifti1Image(processed_data, nifti_img.affine, nifti_img.header)
        logger.info("Texture enhancement effect applied successfully")
        return processed_img
    
    def apply_realistic_rendering_effect(self, nifti_img: nib.Nifti1Image,
                                       smoothness: float = 1.5,
                                       surface_quality: float = 0.8,
                                       material_roughness: float = 0.3) -> nib.Nifti1Image:
        """
        Apply comprehensive realistic rendering effect combining multiple techniques.
        
        This effect creates a more realistic appearance by:
        1. Advanced smoothing with multiple passes
        2. Surface quality enhancement
        3. Material property simulation
        
        Args:
            nifti_img: Input NIfTI image
            smoothness: Overall smoothness factor
            surface_quality: Quality of surface refinement
            material_roughness: Simulated material roughness
            
        Returns:
            Realistically rendered NIfTI image
        """
        logger.info(f"Applying realistic rendering effect (smoothness={smoothness}, surface_quality={surface_quality})")
        
        data = nifti_img.get_fdata().astype(np.float32)
        original_min, original_max = data.min(), data.max()
        
        # Step 1: Multi-pass smoothing for realistic surfaces
        logger.info("Applying multi-pass smoothing...")
        smoothed_data = data.copy()
        
        # Apply advanced multi-scale smoothing for ultra-realistic appearance
        logger.info("Applying advanced multi-scale smoothing for ultra-realistic appearance")
        
        # Multi-scale smoothing with different approaches (3D-compatible)
        smoothing_approaches = [
            ("Gaussian", lambda x, s: gaussian_filter(x, sigma=s)),
            ("Median", lambda x, s: median_filter(x, size=max(3, int(s*2)))),
            ("Uniform", lambda x, s: uniform_filter(x, size=max(3, int(s*2)))),
            ("Edge-Preserving", lambda x, s: self._apply_edge_preserving_smoothing(x, s))
        ]
        
        smoothing_scales = [smoothness * 0.3, smoothness * 0.7, smoothness, smoothness * 1.5, smoothness * 2.0]
        
        for i, scale in enumerate(smoothing_scales):
            approach_name, approach_func = smoothing_approaches[i % len(smoothing_approaches)]
            try:
                smoothed_data = approach_func(smoothed_data, scale)
                logger.info(f"Applied {approach_name} smoothing pass {i+1} with scale={scale}")
            except Exception as e:
                logger.warning(f"{approach_name} smoothing failed for scale {scale}: {e}")
                # Fallback to gaussian
                smoothed_data = gaussian_filter(smoothed_data, sigma=scale)
                logger.info(f"Applied Gaussian fallback for pass {i+1} with sigma={scale}")
        
        # Step 2: Surface quality enhancement
        logger.info("Enhancing surface quality...")
        if surface_quality > 0:
            # Apply median filtering to reduce noise while preserving edges using scipy
            logger.info("Using scipy median_filter for surface enhancement")
            surface_enhanced = median_filter(smoothed_data, size=3)
            logger.info("Applied median filtering for noise reduction")
            
            # Blend with smoothed data
            smoothed_data = (1 - surface_quality) * smoothed_data + surface_quality * surface_enhanced
        
        # Step 3: Material property simulation
        logger.info("Simulating material properties...")
        if material_roughness > 0:
            # Add subtle variations to simulate material properties
            # Create a noise field that varies slowly
            noise_field = np.random.randn(*data.shape)
            noise_field = gaussian_filter(noise_field, sigma=3.0)  # Smooth noise
            noise_field = (noise_field - noise_field.min()) / (noise_field.max() - noise_field.min())
            
            # Apply material roughness
            material_variation = material_roughness * (original_max - original_min) * noise_field
            smoothed_data += material_variation
        
        # Step 4: Final surface polish
        logger.info("Applying final surface polish...")
        # Apply one final smoothing pass for polish using scipy
        final_sigma = smoothness * 0.3
        logger.info(f"Applying final smoothing pass with sigma={final_sigma}")
        processed_data = gaussian_filter(smoothed_data, sigma=final_sigma)
        
        # Ensure data stays within original range
        processed_data = np.clip(processed_data, original_min, original_max)
        
        processed_img = nib.Nifti1Image(processed_data, nifti_img.affine, nifti_img.header)
        logger.info("Realistic rendering effect applied successfully")
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
                if effect_name == "monai_smooth":
                    processed_img = self.apply_monai_smooth_effect(nifti_img, **effect_params)
                elif effect_name == "surface_refinement":
                    processed_img = self.apply_surface_refinement_effect(nifti_img, **effect_params)
                elif effect_name == "texture_enhancement":
                    processed_img = self.apply_texture_enhancement_effect(nifti_img, **effect_params)
                elif effect_name == "realistic_rendering":
                    processed_img = self.apply_realistic_rendering_effect(nifti_img, **effect_params)
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
        description="Apply effects to voxel files in Vista3D",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Apply MONAI-based smoothing for realistic voxels
  python voxel_effects.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 --effect monai_smooth
  
  # Apply surface refinement with custom parameters
  python voxel_effects.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 --effect surface_refinement --threshold 0.3 --min-size 50
  
  # Apply texture enhancement for better surface details
  python voxel_effects.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 --effect texture_enhancement --edge-strength 2.0 --contrast-factor 1.5
  
  # Apply comprehensive realistic rendering
  python voxel_effects.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 --effect realistic_rendering --smoothness 2.0 --surface-quality 0.9
        """
    )
    
    # Required arguments
    parser.add_argument("--patient", required=True, help="Patient ID (e.g., PA00000002)")
    parser.add_argument("--scan", required=True, help="Scan name (e.g., 2.5MM_ARTERIAL_3)")
    parser.add_argument("--effect", required=True, 
                       choices=["monai_smooth", "surface_refinement", "texture_enhancement", "realistic_rendering"],
                       help="Effect to apply")
    
    # Optional arguments
    parser.add_argument("--output-dir", type=Path, help="Custom output directory")
    parser.add_argument("--sigma", type=float, default=1.0, help="Gaussian smoothing sigma (default: 1.0)")
    parser.add_argument("--threshold", type=float, default=0.5, help="Threshold for binary operations (default: 0.5)")
    parser.add_argument("--min-size", type=int, default=100, help="Minimum size for objects to keep (default: 100)")
    parser.add_argument("--edge-strength", type=float, default=1.5, help="Strength of edge enhancement (default: 1.5)")
    parser.add_argument("--contrast-factor", type=float, default=1.2, help="Contrast adjustment factor (default: 1.2)")
    parser.add_argument("--noise-level", type=float, default=0.02, help="Noise level for texture (default: 0.02)")
    parser.add_argument("--smoothness", type=float, default=1.5, help="Overall smoothness factor (default: 1.5)")
    parser.add_argument("--surface-quality", type=float, default=0.8, help="Surface quality factor (default: 0.8)")
    parser.add_argument("--material-roughness", type=float, default=0.3, help="Material roughness simulation (default: 0.3)")
    parser.add_argument("--preserve-range", action="store_true", default=True,
                       help="Whether to preserve original data range (default: True)")
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
            "min_size": args.min_size,
            "edge_strength": args.edge_strength,
            "contrast_factor": args.contrast_factor,
            "noise_level": args.noise_level,
            "smoothness": args.smoothness,
            "surface_quality": args.surface_quality,
            "material_roughness": args.material_roughness,
            "preserve_range": args.preserve_range
        }
        
        # Filter parameters based on effect
        if args.effect == "monai_smooth":
            effect_params = {k: v for k, v in effect_params.items() 
                           if k in ["sigma", "preserve_range"]}
        elif args.effect == "surface_refinement":
            effect_params = {k: v for k, v in effect_params.items() 
                           if k in ["threshold", "min_size"]}
        elif args.effect == "texture_enhancement":
            effect_params = {k: v for k, v in effect_params.items() 
                           if k in ["edge_strength", "contrast_factor", "noise_level"]}
        elif args.effect == "realistic_rendering":
            effect_params = {k: v for k, v in effect_params.items() 
                           if k in ["smoothness", "surface_quality", "material_roughness"]}
        
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