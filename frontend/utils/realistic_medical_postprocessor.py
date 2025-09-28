#!/usr/bin/env python3
"""
Realistic Medical Post-Processing Script for Vista3D

This script applies realistic medical visualization effects to voxel files to create
high-quality 3D medical renderings similar to professional medical visualization software.
It enhances anatomical structures with realistic textures, colors, and visual effects.

Usage:
    python realistic_medical_postprocessor.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 --effect realistic_medical
    python realistic_medical_postprocessor.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 --effect anatomical_enhancement
    python realistic_medical_postprocessor.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 --effect vessel_enhancement
"""

import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any, Union, Tuple
import numpy as np
import nibabel as nib
import torch
import torch.nn.functional as F
from scipy import ndimage
from scipy.ndimage import gaussian_filter, median_filter, uniform_filter, sobel, laplace
from skimage import morphology, filters, measure, segmentation, exposure
from skimage.restoration import denoise_bilateral, denoise_tv_chambolle
from skimage.filters import unsharp_mask, gabor
import logging
import json

# MONAI imports for advanced medical image processing
try:
    from monai.transforms import (
        SobelGradients, FillHoles, RemoveSmallObjects, LabelToContour,
        SpatialPad, RandGaussianNoise, GaussianSmooth, MedianSmooth,
        RandGaussianSharpen, RandHistogramShift, RandAdjustContrast,
        RandBiasField, RandGibbsNoise, RandCoarseDropout, Compose
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

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RealisticMedicalPostProcessor:
    """Advanced post-processor for creating realistic medical visualizations."""
    
    def __init__(self, output_base_dir: Optional[Path] = None):
        """
        Initialize the post-processor.
        
        Args:
            output_base_dir: Base directory for output files. If None, uses project output directory.
        """
        self.output_base_dir = output_base_dir or self._get_default_output_dir()
        self.anatomical_colors = self._load_anatomical_colors()
        self.texture_patterns = self._load_texture_patterns()
        logger.info(f"Using output directory: {self.output_base_dir}")
    
    def _get_default_output_dir(self) -> Path:
        """Get the default output directory from environment or project structure."""
        output_folder = os.getenv('OUTPUT_FOLDER')
        if output_folder:
            logger.info(f"Using OUTPUT_FOLDER from environment: {output_folder}")
            return Path(output_folder)
        
        # Fallback to project structure
        script_dir = Path(__file__).parent
        project_root = script_dir.parent.parent
        fallback_path = project_root / "output"
        logger.warning(f"OUTPUT_FOLDER not found in environment, using fallback: {fallback_path}")
        return fallback_path
    
    def _load_anatomical_colors(self) -> Dict[str, Dict[str, Any]]:
        """Load anatomical structure color mappings for realistic rendering."""
        return {
            'liver': {
                'base_color': [0.6, 0.3, 0.2],  # Reddish-brown
                'texture_strength': 0.4,
                'roughness': 0.7,
                'metallic': 0.1
            },
            'gallbladder': {
                'base_color': [0.3, 0.6, 0.4],  # Light green
                'texture_strength': 0.3,
                'roughness': 0.5,
                'metallic': 0.0
            },
            'aorta': {
                'base_color': [0.8, 0.2, 0.2],  # Bright red
                'texture_strength': 0.5,
                'roughness': 0.3,
                'metallic': 0.2
            },
            'inferior_vena_cava': {
                'base_color': [0.2, 0.3, 0.8],  # Blue
                'texture_strength': 0.5,
                'roughness': 0.3,
                'metallic': 0.2
            },
            'iliac_artery': {
                'base_color': [0.7, 0.2, 0.2],  # Red
                'texture_strength': 0.4,
                'roughness': 0.4,
                'metallic': 0.1
            },
            'iliac_vena': {
                'base_color': [0.2, 0.2, 0.7],  # Blue
                'texture_strength': 0.4,
                'roughness': 0.4,
                'metallic': 0.1
            },
            'rib': {
                'base_color': [0.9, 0.85, 0.8],  # Bone beige
                'texture_strength': 0.6,
                'roughness': 0.8,
                'metallic': 0.0
            },
            'hip': {
                'base_color': [0.9, 0.85, 0.8],  # Bone beige
                'texture_strength': 0.6,
                'roughness': 0.8,
                'metallic': 0.0
            },
            'femur': {
                'base_color': [0.9, 0.85, 0.8],  # Bone beige
                'texture_strength': 0.6,
                'roughness': 0.8,
                'metallic': 0.0
            },
            'vertebrae': {
                'base_color': [0.9, 0.85, 0.8],  # Bone beige
                'texture_strength': 0.6,
                'roughness': 0.8,
                'metallic': 0.0
            },
            'sacrum': {
                'base_color': [0.9, 0.85, 0.8],  # Bone beige
                'texture_strength': 0.6,
                'roughness': 0.8,
                'metallic': 0.0
            },
            'sternum': {
                'base_color': [0.9, 0.85, 0.8],  # Bone beige
                'texture_strength': 0.6,
                'roughness': 0.8,
                'metallic': 0.0
            },
            'skull': {
                'base_color': [0.9, 0.85, 0.8],  # Bone beige
                'texture_strength': 0.6,
                'roughness': 0.8,
                'metallic': 0.0
            },
            'heart': {
                'base_color': [0.7, 0.2, 0.2],  # Red
                'texture_strength': 0.5,
                'roughness': 0.6,
                'metallic': 0.1
            },
            'kidney': {
                'base_color': [0.4, 0.6, 0.4],  # Green
                'texture_strength': 0.4,
                'roughness': 0.6,
                'metallic': 0.0
            },
            'lung': {
                'base_color': [0.7, 0.8, 0.9],  # Light blue-gray
                'texture_strength': 0.3,
                'roughness': 0.7,
                'metallic': 0.0
            },
            'default': {
                'base_color': [0.5, 0.5, 0.5],  # Gray
                'texture_strength': 0.3,
                'roughness': 0.5,
                'metallic': 0.0
            }
        }
    
    def _load_texture_patterns(self) -> Dict[str, Any]:
        """Load texture pattern configurations for different anatomical structures."""
        return {
            'organic': {
                'noise_scale': 0.1,
                'noise_octaves': 4,
                'roughness_variation': 0.3,
                'bump_strength': 0.2
            },
            'vascular': {
                'noise_scale': 0.05,
                'noise_octaves': 6,
                'roughness_variation': 0.2,
                'bump_strength': 0.3
            },
            'bone': {
                'noise_scale': 0.15,
                'noise_octaves': 3,
                'roughness_variation': 0.4,
                'bump_strength': 0.4
            }
        }
    
    def _get_anatomical_type(self, filename: str) -> str:
        """Determine anatomical type from filename for appropriate color/texture mapping."""
        filename_lower = filename.lower()
        
        # Organ mappings
        if 'liver' in filename_lower:
            return 'liver'
        elif 'gallbladder' in filename_lower:
            return 'gallbladder'
        elif 'heart' in filename_lower:
            return 'heart'
        elif 'kidney' in filename_lower:
            return 'kidney'
        elif 'lung' in filename_lower:
            return 'lung'
        
        # Vascular mappings
        elif 'aorta' in filename_lower:
            return 'aorta'
        elif 'vena_cava' in filename_lower or 'cava' in filename_lower:
            return 'inferior_vena_cava'
        elif 'iliac_artery' in filename_lower:
            return 'iliac_artery'
        elif 'iliac_vena' in filename_lower:
            return 'iliac_vena'
        
        # Skeletal mappings
        elif 'rib' in filename_lower:
            return 'rib'
        elif 'hip' in filename_lower:
            return 'hip'
        elif 'femur' in filename_lower:
            return 'femur'
        elif 'vertebrae' in filename_lower or 'vertebra' in filename_lower:
            return 'vertebrae'
        elif 'sacrum' in filename_lower:
            return 'sacrum'
        elif 'sternum' in filename_lower:
            return 'sternum'
        elif 'skull' in filename_lower:
            return 'skull'
        
        return 'default'
    
    def _generate_organic_texture(self, shape: Tuple[int, ...], pattern_config: Dict[str, Any]) -> np.ndarray:
        """Generate organic texture pattern for anatomical structures."""
        noise_scale = pattern_config['noise_scale']
        octaves = pattern_config['noise_octaves']
        
        # Generate multi-octave Perlin-like noise
        texture = np.zeros(shape)
        amplitude = 1.0
        frequency = 1.0
        
        for i in range(octaves):
            # Create coordinate grids
            coords = np.meshgrid(*[np.linspace(0, frequency, s) for s in shape], indexing='ij')
            
            # Generate noise at this octave
            noise = np.random.random(shape) * 2 - 1
            for j in range(len(shape)):
                noise = gaussian_filter(noise, sigma=noise_scale * (2 ** i))
            
            texture += amplitude * noise
            amplitude *= 0.5
            frequency *= 2.0
        
        # Normalize to [0, 1]
        texture = (texture - texture.min()) / (texture.max() - texture.min())
        return texture
    
    def _generate_vascular_texture(self, shape: Tuple[int, ...], pattern_config: Dict[str, Any]) -> np.ndarray:
        """Generate vascular texture pattern for blood vessels."""
        noise_scale = pattern_config['noise_scale']
        
        # Generate fine-grained noise for vascular texture
        texture = np.random.random(shape)
        texture = gaussian_filter(texture, sigma=noise_scale)
        
        # Add directional patterns to simulate vessel walls
        for i in range(3):  # Apply in 3 directions
            coords = np.linspace(0, 10, shape[i])
            pattern = np.sin(coords) * 0.1
            for j in range(shape[i]):
                if i == 0:
                    texture[j, :, :] += pattern[j]
                elif i == 1:
                    texture[:, j, :] += pattern[j]
                else:
                    texture[:, :, j] += pattern[j]
        
        # Normalize
        texture = (texture - texture.min()) / (texture.max() - texture.min())
        return texture
    
    def _generate_bone_texture(self, shape: Tuple[int, ...], pattern_config: Dict[str, Any]) -> np.ndarray:
        """Generate bone texture pattern with porous appearance."""
        noise_scale = pattern_config['noise_scale']
        
        # Generate base noise
        texture = np.random.random(shape)
        texture = gaussian_filter(texture, sigma=noise_scale)
        
        # Add porous patterns
        porous_pattern = np.random.random(shape)
        porous_pattern = porous_pattern > 0.7  # Create holes
        porous_pattern = gaussian_filter(porous_pattern.astype(float), sigma=2.0)
        
        texture = texture * (1 - porous_pattern * 0.3)
        
        # Add trabecular patterns
        for i in range(3):
            coords = np.linspace(0, 20, shape[i])
            pattern = np.sin(coords) * 0.2
            for j in range(shape[i]):
                if i == 0:
                    texture[j, :, :] += pattern[j]
                elif i == 1:
                    texture[:, j, :] += pattern[j]
                else:
                    texture[:, :, j] += pattern[j]
        
        # Normalize
        texture = (texture - texture.min()) / (texture.max() - texture.min())
        return texture
    
    def _apply_anatomical_coloring(self, data: np.ndarray, anatomical_type: str) -> np.ndarray:
        """Apply realistic anatomical coloring based on structure type."""
        color_config = self.anatomical_colors.get(anatomical_type, self.anatomical_colors['default'])
        base_color = np.array(color_config['base_color'])
        
        # Normalize data to [0, 1]
        data_norm = (data - data.min()) / (data.max() - data.min()) if data.max() > data.min() else data
        
        # Apply color mapping
        colored_data = data_norm[..., np.newaxis] * base_color
        
        return colored_data
    
    def _apply_texture_enhancement(self, data: np.ndarray, anatomical_type: str) -> np.ndarray:
        """Apply conservative texture enhancement based on anatomical structure type."""
        color_config = self.anatomical_colors.get(anatomical_type, self.anatomical_colors['default'])
        texture_strength = color_config['texture_strength'] * 0.2  # Reduce texture strength significantly
        
        # Determine texture pattern type
        if anatomical_type in ['liver', 'heart', 'kidney', 'lung']:
            pattern_type = 'organic'
        elif anatomical_type in ['aorta', 'inferior_vena_cava', 'iliac_artery', 'iliac_vena']:
            pattern_type = 'vascular'
        elif anatomical_type in ['rib', 'hip', 'femur', 'vertebrae', 'sacrum', 'sternum', 'skull']:
            pattern_type = 'bone'
        else:
            pattern_type = 'organic'
        
        pattern_config = self.texture_patterns[pattern_type]
        
        # Generate appropriate texture with reduced intensity
        if pattern_type == 'organic':
            texture = self._generate_organic_texture(data.shape, pattern_config)
        elif pattern_type == 'vascular':
            texture = self._generate_vascular_texture(data.shape, pattern_config)
        elif pattern_type == 'bone':
            texture = self._generate_bone_texture(data.shape, pattern_config)
        else:
            texture = self._generate_organic_texture(data.shape, pattern_config)
        
        # Apply very conservative texture enhancement to avoid noise
        # Only apply to areas with significant data values
        data_range = data.max() - data.min()
        if data_range > 0:
            # Only enhance areas above 20th percentile to avoid noise in background
            threshold = np.percentile(data, 20)
            mask = data > threshold
            texture_contribution = texture * texture_strength * data_range
            enhanced_data = np.where(mask, data + texture_contribution, data)
        else:
            enhanced_data = data
        
        return enhanced_data
    
    def _apply_surface_refinement(self, data: np.ndarray, anatomical_type: str) -> np.ndarray:
        """Apply conservative surface refinement for realistic medical visualization."""
        # Apply very gentle smoothing to preserve detail
        smoothed = gaussian_filter(data, sigma=0.3)
        
        # Apply minimal unsharp masking for subtle detail enhancement
        sharpened = unsharp_mask(smoothed, radius=0.5, amount=0.5)
        
        # Combine with original data to preserve structure
        refined_data = 0.9 * data + 0.1 * sharpened
        
        return refined_data
    
    def _apply_volume_rendering_enhancement(self, data: np.ndarray, anatomical_type: str) -> np.ndarray:
        """Apply conservative volume rendering enhancements for realistic visualization."""
        # Apply gentle histogram equalization for better contrast
        equalized = exposure.equalize_hist(data)
        
        # Apply subtle gamma correction for realistic lighting
        gamma_corrected = exposure.adjust_gamma(equalized, gamma=1.1)
        
        # Apply conservative contrast stretching
        p5, p95 = np.percentile(gamma_corrected, (5, 95))  # Use 5-95% instead of 2-98%
        stretched = exposure.rescale_intensity(gamma_corrected, in_range=(p5, p95))
        
        # Blend with original to preserve data integrity
        enhanced_data = 0.7 * data + 0.3 * stretched
        
        return enhanced_data
    
    def apply_realistic_medical_effect(self, nifti_img: nib.Nifti1Image, 
                                     filename: str,
                                     translucency: float = 0.3,  # Reduced from 0.8 to make voxels more opaque
                                     texture_strength: float = 0.3,  # Reduced from 1.0 to avoid noise
                                     color_enhancement: bool = True) -> nib.Nifti1Image:
        """
        Apply comprehensive realistic medical visualization effects.
        
        Args:
            nifti_img: Input NIfTI image
            filename: Filename to determine anatomical type
            translucency: Translucency factor (0.0 = opaque, 1.0 = transparent) - reduced for better visibility
            texture_strength: Strength of texture enhancement - reduced to avoid noise
            color_enhancement: Whether to apply anatomical coloring
            
        Returns:
            Realistically enhanced NIfTI image with improved quality and density
        """
        logger.info(f"Applying realistic medical effect to {filename}")
        
        data = nifti_img.get_fdata().astype(np.float32)
        anatomical_type = self._get_anatomical_type(filename)
        
        logger.info(f"Detected anatomical type: {anatomical_type}")
        
        # Preserve original data range first
        original_min, original_max = data.min(), data.max()
        
        # Apply gentle smoothing to improve quality without losing detail
        logger.info("Applying gentle smoothing for better quality...")
        from scipy.ndimage import gaussian_filter
        smoothed_data = gaussian_filter(data, sigma=0.5)
        
        # Apply minimal surface refinement to preserve structure
        logger.info("Applying minimal surface refinement...")
        refined_data = self._apply_surface_refinement(smoothed_data, anatomical_type)
        
        # Apply very light texture enhancement to avoid noise
        logger.info("Applying light texture enhancement...")
        if texture_strength > 0:
            textured_data = self._apply_texture_enhancement(refined_data, anatomical_type)
            # Blend with original to avoid over-processing
            textured_data = 0.8 * refined_data + 0.2 * textured_data
        else:
            textured_data = refined_data
        
        # Apply conservative volume rendering enhancement
        logger.info("Applying conservative volume rendering enhancement...")
        enhanced_data = self._apply_volume_rendering_enhancement(textured_data, anatomical_type)
        
        # Apply minimal translucency to maintain visibility
        if translucency < 1.0:
            logger.info(f"Applying minimal translucency factor: {translucency}")
            # Use a more conservative approach - only reduce very high values
            enhanced_data = np.where(enhanced_data > np.percentile(enhanced_data, 90), 
                                   enhanced_data * translucency, 
                                   enhanced_data)
        
        # Ensure we maintain good data density and contrast
        logger.info("Applying contrast enhancement for better visibility...")
        # Apply histogram equalization for better contrast
        from skimage import exposure
        enhanced_data = exposure.equalize_hist(enhanced_data)
        
        # Scale back to original range but with better distribution
        if original_max > original_min:
            enhanced_data = enhanced_data * (original_max - original_min) + original_min
        
        # Ensure minimum threshold to maintain voxel density
        threshold = np.percentile(enhanced_data, 10)  # Keep bottom 10% of values
        enhanced_data = np.where(enhanced_data < threshold, threshold, enhanced_data)
        
        processed_img = nib.Nifti1Image(enhanced_data, nifti_img.affine, nifti_img.header)
        logger.info("Realistic medical effect applied successfully with improved quality")
        return processed_img
    
    def apply_anatomical_enhancement_effect(self, nifti_img: nib.Nifti1Image,
                                          filename: str,
                                          structure_preservation: float = 0.9,
                                          detail_enhancement: float = 1.2) -> nib.Nifti1Image:
        """
        Apply anatomical structure enhancement for better visualization.
        
        Args:
            nifti_img: Input NIfTI image
            filename: Filename to determine anatomical type
            structure_preservation: Factor for preserving original structure
            detail_enhancement: Factor for enhancing details
            
        Returns:
            Anatomically enhanced NIfTI image
        """
        logger.info(f"Applying anatomical enhancement to {filename}")
        
        data = nifti_img.get_fdata().astype(np.float32)
        anatomical_type = self._get_anatomical_type(filename)
        
        # Apply structure-preserving smoothing
        logger.info("Applying structure-preserving smoothing...")
        smoothed = gaussian_filter(data, sigma=0.3)
        
        # Enhance details using unsharp masking
        logger.info("Enhancing anatomical details...")
        sharpened = unsharp_mask(smoothed, radius=1.5, amount=detail_enhancement)
        
        # Combine with original structure
        enhanced_data = structure_preservation * data + (1 - structure_preservation) * sharpened
        
        # Apply texture enhancement
        logger.info("Applying anatomical texture enhancement...")
        textured_data = self._apply_texture_enhancement(enhanced_data, anatomical_type)
        
        processed_img = nib.Nifti1Image(textured_data, nifti_img.affine, nifti_img.header)
        logger.info("Anatomical enhancement applied successfully")
        return processed_img
    
    def apply_vessel_enhancement_effect(self, nifti_img: nib.Nifti1Image,
                                      filename: str,
                                      vessel_contrast: float = 1.5,
                                      wall_thickness: float = 1.0) -> nib.Nifti1Image:
        """
        Apply specialized enhancement for vascular structures.
        
        Args:
            nifti_img: Input NIfTI image
            filename: Filename to determine anatomical type
            vessel_contrast: Contrast enhancement for vessels
            wall_thickness: Simulated wall thickness enhancement
            
        Returns:
            Vessel-enhanced NIfTI image
        """
        logger.info(f"Applying vessel enhancement to {filename}")
        
        data = nifti_img.get_fdata().astype(np.float32)
        anatomical_type = self._get_anatomical_type(filename)
        
        # Apply vessel-specific contrast enhancement
        logger.info("Applying vessel contrast enhancement...")
        contrast_enhanced = exposure.adjust_log(data, gain=vessel_contrast)
        
        # Apply vessel texture enhancement
        logger.info("Applying vessel texture enhancement...")
        textured_data = self._apply_texture_enhancement(contrast_enhanced, anatomical_type)
        
        # Apply wall thickness simulation
        if wall_thickness > 1.0:
            logger.info("Simulating vessel wall thickness...")
            # Dilate the vessel structure slightly
            binary_vessel = textured_data > np.percentile(textured_data, 50)
            dilated = morphology.binary_dilation(binary_vessel, 
                                               selem=morphology.ball(int(wall_thickness)))
            textured_data = np.where(dilated, textured_data, textured_data * 0.8)
        
        processed_img = nib.Nifti1Image(textured_data, nifti_img.affine, nifti_img.header)
        logger.info("Vessel enhancement applied successfully")
        return processed_img
    
    def get_voxel_files(self, patient_id: str, scan_name: str) -> Dict[str, List[Path]]:
        """Get all voxel files for a patient and scan."""
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
                if effect_name == "realistic_medical":
                    processed_img = self.apply_realistic_medical_effect(
                        nifti_img, file_path.name, **effect_params)
                elif effect_name == "anatomical_enhancement":
                    processed_img = self.apply_anatomical_enhancement_effect(
                        nifti_img, file_path.name, **effect_params)
                elif effect_name == "vessel_enhancement":
                    processed_img = self.apply_vessel_enhancement_effect(
                        nifti_img, file_path.name, **effect_params)
                else:
                    raise ValueError(f"Unknown effect: {effect_name}")
                
                # Save processed image
                if file_path in voxel_files['individual_voxels']:
                    output_filename = file_path.name
                else:
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
        description="Apply realistic medical visualization effects to voxel files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Apply comprehensive realistic medical visualization
  python realistic_medical_postprocessor.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 --effect realistic_medical
  
  # Apply anatomical structure enhancement
  python realistic_medical_postprocessor.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 --effect anatomical_enhancement
  
  # Apply vessel-specific enhancement
  python realistic_medical_postprocessor.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 --effect vessel_enhancement
        """
    )
    
    # Required arguments
    parser.add_argument("--patient", required=True, help="Patient ID (e.g., PA00000002)")
    parser.add_argument("--scan", required=True, help="Scan name (e.g., 2.5MM_ARTERIAL_3)")
    parser.add_argument("--effect", required=True, 
                       choices=["realistic_medical", "anatomical_enhancement", "vessel_enhancement"],
                       help="Effect to apply")
    
    # Optional arguments
    parser.add_argument("--output-dir", type=Path, help="Custom output directory")
    parser.add_argument("--translucency", type=float, default=0.8, help="Translucency factor (0.0-1.0)")
    parser.add_argument("--texture-strength", type=float, default=1.0, help="Texture enhancement strength")
    parser.add_argument("--color-enhancement", action="store_true", default=True, help="Apply anatomical coloring")
    parser.add_argument("--structure-preservation", type=float, default=0.9, help="Structure preservation factor")
    parser.add_argument("--detail-enhancement", type=float, default=1.2, help="Detail enhancement factor")
    parser.add_argument("--vessel-contrast", type=float, default=1.5, help="Vessel contrast enhancement")
    parser.add_argument("--wall-thickness", type=float, default=1.0, help="Vessel wall thickness simulation")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Create processor
        processor = RealisticMedicalPostProcessor()
        
        # Prepare effect parameters
        effect_params = {
            "translucency": args.translucency,
            "texture_strength": args.texture_strength,
            "color_enhancement": args.color_enhancement,
            "structure_preservation": args.structure_preservation,
            "detail_enhancement": args.detail_enhancement,
            "vessel_contrast": args.vessel_contrast,
            "wall_thickness": args.wall_thickness
        }
        
        # Filter parameters based on effect
        if args.effect == "realistic_medical":
            effect_params = {k: v for k, v in effect_params.items() 
                           if k in ["translucency", "texture_strength", "color_enhancement"]}
        elif args.effect == "anatomical_enhancement":
            effect_params = {k: v for k, v in effect_params.items() 
                           if k in ["structure_preservation", "detail_enhancement"]}
        elif args.effect == "vessel_enhancement":
            effect_params = {k: v for k, v in effect_params.items() 
                           if k in ["vessel_contrast", "wall_thickness"]}
        
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
