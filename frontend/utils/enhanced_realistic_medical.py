#!/usr/bin/env python3
"""
Enhanced Realistic Medical Post-Processing Script for Vista3D

This script creates highly realistic medical visualizations with advanced anatomical
rendering effects that produce professional-quality 3D medical renderings similar
to the image shown. It implements sophisticated texture synthesis, material properties,
and anatomical coloring to create voxels that look like real anatomical structures.

Usage:
    python enhanced_realistic_medical.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 --effect ultra_realistic_anatomy
    python enhanced_realistic_medical.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 --effect photorealistic_organs
    python enhanced_realistic_medical.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 --effect medical_grade_rendering
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
from scipy.ndimage import gaussian_filter, median_filter, uniform_filter, sobel, laplace, distance_transform_edt
from skimage import morphology, filters, measure, segmentation, exposure, restoration
from skimage.restoration import denoise_bilateral, denoise_tv_chambolle
from skimage.filters import unsharp_mask, gabor, rank
from skimage.morphology import ball, disk, erosion, dilation, opening, closing
from skimage.segmentation import watershed
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


class EnhancedRealisticMedicalProcessor:
    """Advanced processor for creating ultra-realistic medical visualizations."""
    
    def __init__(self, output_base_dir: Optional[Path] = None):
        """
        Initialize the enhanced processor.
        
        Args:
            output_base_dir: Base directory for output files. If None, uses project output directory.
        """
        self.output_base_dir = output_base_dir or self._get_default_output_dir()
        self.anatomical_materials = self._load_anatomical_materials()
        self.texture_generators = self._load_texture_generators()
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
    
    def _load_anatomical_materials(self) -> Dict[str, Dict[str, Any]]:
        """Load advanced anatomical material properties for ultra-realistic rendering."""
        return {
            'liver': {
                'base_color': [0.75, 0.45, 0.35],  # Rich reddish-brown like in medical image
                'texture_type': 'organic_granular',
                'roughness': 0.9,
                'metallic': 0.02,
                'subsurface_scattering': 0.4,
                'bump_strength': 0.6,
                'detail_scale': 1.0,
                'color_variation': 0.2,
                'surface_pattern': 'lobular',
                'texture_granularity': 0.8,
                'surface_roughness': 0.7,
                'organic_detail': 0.9
            },
            'gallbladder': {
                'base_color': [0.35, 0.65, 0.45],  # Organic green like in medical image
                'texture_type': 'smooth_organic',
                'roughness': 0.5,
                'metallic': 0.0,
                'subsurface_scattering': 0.3,
                'bump_strength': 0.3,
                'detail_scale': 0.7,
                'color_variation': 0.15,
                'surface_pattern': 'smooth',
                'texture_granularity': 0.4,
                'surface_roughness': 0.3,
                'organic_detail': 0.6
            },
            'aorta': {
                'base_color': [0.9, 0.2, 0.2],  # Bright arterial red like in medical image
                'texture_type': 'vascular_elastic',
                'roughness': 0.4,
                'metallic': 0.15,
                'subsurface_scattering': 0.5,
                'bump_strength': 0.4,
                'detail_scale': 0.5,
                'color_variation': 0.1,
                'surface_pattern': 'longitudinal',
                'texture_granularity': 0.6,
                'surface_roughness': 0.3,
                'organic_detail': 0.7
            },
            'inferior_vena_cava': {
                'base_color': [0.2, 0.3, 0.8],  # Deep venous blue like in medical image
                'texture_type': 'vascular_elastic',
                'roughness': 0.4,
                'metallic': 0.15,
                'subsurface_scattering': 0.5,
                'bump_strength': 0.4,
                'detail_scale': 0.5,
                'color_variation': 0.1,
                'surface_pattern': 'longitudinal',
                'texture_granularity': 0.6,
                'surface_roughness': 0.3,
                'organic_detail': 0.7
            },
            'iliac_artery': {
                'base_color': [0.75, 0.18, 0.18],  # Arterial red
                'texture_type': 'vascular_elastic',
                'roughness': 0.35,
                'metallic': 0.08,
                'subsurface_scattering': 0.35,
                'bump_strength': 0.25,
                'detail_scale': 0.5,
                'color_variation': 0.1,
                'surface_pattern': 'longitudinal'
            },
            'iliac_vena': {
                'base_color': [0.18, 0.18, 0.65],  # Venous blue
                'texture_type': 'vascular_elastic',
                'roughness': 0.35,
                'metallic': 0.08,
                'subsurface_scattering': 0.35,
                'bump_strength': 0.25,
                'detail_scale': 0.5,
                'color_variation': 0.1,
                'surface_pattern': 'longitudinal'
            },
            'rib': {
                'base_color': [0.95, 0.92, 0.88],  # Bone ivory like in medical image
                'texture_type': 'trabecular_bone',
                'roughness': 0.95,
                'metallic': 0.0,
                'subsurface_scattering': 0.15,
                'bump_strength': 0.7,
                'detail_scale': 1.4,
                'color_variation': 0.25,
                'surface_pattern': 'trabecular',
                'texture_granularity': 0.9,
                'surface_roughness': 0.8,
                'organic_detail': 1.0
            },
            'hip': {
                'base_color': [0.95, 0.92, 0.88],  # Bone ivory like in medical image
                'texture_type': 'trabecular_bone',
                'roughness': 0.95,
                'metallic': 0.0,
                'subsurface_scattering': 0.15,
                'bump_strength': 0.7,
                'detail_scale': 1.4,
                'color_variation': 0.25,
                'surface_pattern': 'trabecular',
                'texture_granularity': 0.9,
                'surface_roughness': 0.8,
                'organic_detail': 1.0
            },
            'femur': {
                'base_color': [0.92, 0.88, 0.82],  # Bone ivory
                'texture_type': 'trabecular_bone',
                'roughness': 0.9,
                'metallic': 0.0,
                'subsurface_scattering': 0.1,
                'bump_strength': 0.6,
                'detail_scale': 1.2,
                'color_variation': 0.2,
                'surface_pattern': 'trabecular'
            },
            'vertebrae': {
                'base_color': [0.92, 0.88, 0.82],  # Bone ivory
                'texture_type': 'trabecular_bone',
                'roughness': 0.9,
                'metallic': 0.0,
                'subsurface_scattering': 0.1,
                'bump_strength': 0.6,
                'detail_scale': 1.2,
                'color_variation': 0.2,
                'surface_pattern': 'trabecular'
            },
            'sacrum': {
                'base_color': [0.92, 0.88, 0.82],  # Bone ivory
                'texture_type': 'trabecular_bone',
                'roughness': 0.9,
                'metallic': 0.0,
                'subsurface_scattering': 0.1,
                'bump_strength': 0.6,
                'detail_scale': 1.2,
                'color_variation': 0.2,
                'surface_pattern': 'trabecular'
            },
            'heart': {
                'base_color': [0.7, 0.2, 0.2],  # Cardiac red
                'texture_type': 'muscle_fiber',
                'roughness': 0.7,
                'metallic': 0.0,
                'subsurface_scattering': 0.25,
                'bump_strength': 0.35,
                'detail_scale': 0.7,
                'color_variation': 0.12,
                'surface_pattern': 'fibrous'
            },
            'kidney': {
                'base_color': [0.4, 0.6, 0.4],  # Renal green
                'texture_type': 'organic_granular',
                'roughness': 0.6,
                'metallic': 0.0,
                'subsurface_scattering': 0.2,
                'bump_strength': 0.3,
                'detail_scale': 0.9,
                'color_variation': 0.1,
                'surface_pattern': 'granular'
            },
            'lung': {
                'base_color': [0.75, 0.85, 0.9],  # Pulmonary blue-gray
                'texture_type': 'spongy_organic',
                'roughness': 0.8,
                'metallic': 0.0,
                'subsurface_scattering': 0.15,
                'bump_strength': 0.5,
                'detail_scale': 1.0,
                'color_variation': 0.18,
                'surface_pattern': 'alveolar'
            },
            'default': {
                'base_color': [0.5, 0.5, 0.5],  # Neutral gray
                'texture_type': 'organic_granular',
                'roughness': 0.6,
                'metallic': 0.0,
                'subsurface_scattering': 0.2,
                'bump_strength': 0.3,
                'detail_scale': 0.8,
                'color_variation': 0.1,
                'surface_pattern': 'smooth'
            }
        }
    
    def _load_texture_generators(self) -> Dict[str, Any]:
        """Load advanced texture generation configurations."""
        return {
            'organic_granular': {
                'noise_octaves': 6,
                'noise_scale': 0.08,
                'detail_octaves': 4,
                'detail_scale': 0.15,
                'roughness_variation': 0.4,
                'color_variation_strength': 0.2,
                'bump_depth': 0.3,
                'surface_detail': 0.7
            },
            'smooth_organic': {
                'noise_octaves': 3,
                'noise_scale': 0.12,
                'detail_octaves': 2,
                'detail_scale': 0.08,
                'roughness_variation': 0.2,
                'color_variation_strength': 0.1,
                'bump_depth': 0.1,
                'surface_detail': 0.3
            },
            'vascular_elastic': {
                'noise_octaves': 5,
                'noise_scale': 0.04,
                'detail_octaves': 3,
                'detail_scale': 0.06,
                'roughness_variation': 0.15,
                'color_variation_strength': 0.08,
                'bump_depth': 0.2,
                'surface_detail': 0.5
            },
            'trabecular_bone': {
                'noise_octaves': 4,
                'noise_scale': 0.15,
                'detail_octaves': 3,
                'detail_scale': 0.2,
                'roughness_variation': 0.6,
                'color_variation_strength': 0.3,
                'bump_depth': 0.5,
                'surface_detail': 0.9
            },
            'muscle_fiber': {
                'noise_octaves': 5,
                'noise_scale': 0.06,
                'detail_octaves': 4,
                'detail_scale': 0.1,
                'roughness_variation': 0.35,
                'color_variation_strength': 0.15,
                'bump_depth': 0.25,
                'surface_detail': 0.6
            },
            'spongy_organic': {
                'noise_octaves': 6,
                'noise_scale': 0.1,
                'detail_octaves': 5,
                'detail_scale': 0.18,
                'roughness_variation': 0.5,
                'color_variation_strength': 0.25,
                'bump_depth': 0.4,
                'surface_detail': 0.8
            }
        }
    
    def _get_anatomical_type(self, filename: str) -> str:
        """Determine anatomical type from filename for appropriate material mapping."""
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
        
        return 'default'
    
    def _generate_advanced_organic_texture(self, shape: Tuple[int, ...], pattern_config: Dict[str, Any], 
                                         anatomical_type: str) -> np.ndarray:
        """Generate sophisticated organic texture with anatomical-specific patterns."""
        noise_octaves = pattern_config['noise_octaves']
        noise_scale = pattern_config['noise_scale']
        detail_octaves = pattern_config['detail_octaves']
        detail_scale = pattern_config['detail_scale']
        roughness_variation = pattern_config['roughness_variation']
        color_variation_strength = pattern_config['color_variation_strength']
        bump_depth = pattern_config['bump_depth']
        surface_detail = pattern_config['surface_detail']
        
        # Generate base Perlin-like noise with improved organic patterns
        texture = np.zeros(shape)
        amplitude = 1.0
        frequency = 1.0
        
        for i in range(noise_octaves):
            # Create coordinate grids with different frequencies
            coords = np.meshgrid(*[np.linspace(0, frequency * 4, s) for s in shape], indexing='ij')
            
            # Generate noise at this octave with improved organic characteristics
            noise = np.random.random(shape) * 2 - 1
            for j in range(len(shape)):
                noise = gaussian_filter(noise, sigma=noise_scale * (2 ** i))
            
            # Add organic variation to noise
            organic_variation = np.sin(coords[0] * 0.1) * np.cos(coords[1] * 0.1) * 0.2
            noise = noise + organic_variation
            
            texture += amplitude * noise
            amplitude *= 0.5
            frequency *= 2.0
        
        # Add anatomical-specific patterns
        if anatomical_type == 'liver':
            # Add enhanced lobular pattern for liver with granular texture
            for i in range(3):
                coords = np.linspace(0, 20, shape[i])
                # Create more complex lobular pattern
                pattern = np.sin(coords) * 0.4 + np.sin(coords * 2) * 0.2 + np.sin(coords * 4) * 0.1
                for j in range(shape[i]):
                    if i == 0:
                        texture[j, :, :] += pattern[j]
                    elif i == 1:
                        texture[:, j, :] += pattern[j]
                    else:
                        texture[:, :, j] += pattern[j]
            
            # Add granular texture for liver surface
            granular_noise = np.random.random(shape) * 0.3
            granular_noise = gaussian_filter(granular_noise, sigma=0.5)
            texture += granular_noise
            
            # Add organic surface irregularities
            surface_irregularities = np.random.random(shape) * 0.2
            surface_irregularities = gaussian_filter(surface_irregularities, sigma=1.0)
            texture += surface_irregularities
        
        elif anatomical_type in ['aorta', 'inferior_vena_cava', 'iliac_artery', 'iliac_vena']:
            # Add enhanced longitudinal vessel patterns with elastic texture
            for i in range(2):  # Only in 2 directions for vessels
                coords = np.linspace(0, 30, shape[i])
                # Create more complex vessel pattern with elastic characteristics
                pattern = np.sin(coords * 2) * 0.2 + np.sin(coords * 4) * 0.1 + np.sin(coords * 8) * 0.05
                for j in range(shape[i]):
                    if i == 0:
                        texture[j, :, :] += pattern[j]
                    elif i == 1:
                        texture[:, j, :] += pattern[j]
            
            # Add vascular surface texture
            vascular_texture = np.random.random(shape) * 0.15
            vascular_texture = gaussian_filter(vascular_texture, sigma=0.3)
            texture += vascular_texture
            
            # Add elastic fiber patterns
            fiber_pattern = np.random.random(shape) * 0.1
            fiber_pattern = gaussian_filter(fiber_pattern, sigma=0.2)
            texture += fiber_pattern
        
        elif anatomical_type in ['rib', 'hip', 'femur', 'vertebrae', 'sacrum']:
            # Add enhanced trabecular bone patterns with realistic porosity
            porous_pattern = np.random.random(shape)
            porous_pattern = porous_pattern > 0.7  # Create more realistic pores
            porous_pattern = gaussian_filter(porous_pattern.astype(float), sigma=1.8)
            texture = texture * (1 - porous_pattern * 0.5)
            
            # Add complex trabecular lines with multiple scales
            for i in range(3):
                coords = np.linspace(0, 25, shape[i])
                # Create multi-scale trabecular pattern
                pattern = np.sin(coords) * 0.3 + np.sin(coords * 2) * 0.15 + np.sin(coords * 4) * 0.08
                for j in range(shape[i]):
                    if i == 0:
                        texture[j, :, :] += pattern[j]
                    elif i == 1:
                        texture[:, j, :] += pattern[j]
                    else:
                        texture[:, :, j] += pattern[j]
            
            # Add bone surface roughness
            bone_roughness = np.random.random(shape) * 0.25
            bone_roughness = gaussian_filter(bone_roughness, sigma=0.8)
            texture += bone_roughness
            
            # Add trabecular network pattern
            network_pattern = np.random.random(shape) * 0.2
            network_pattern = gaussian_filter(network_pattern, sigma=1.2)
            texture += network_pattern
        
        elif anatomical_type == 'heart':
            # Add muscle fiber patterns
            for i in range(3):
                coords = np.linspace(0, 15, shape[i])
                pattern = np.sin(coords * 3) * 0.2
                for j in range(shape[i]):
                    if i == 0:
                        texture[j, :, :] += pattern[j]
                    elif i == 1:
                        texture[:, j, :] += pattern[j]
                    else:
                        texture[:, :, j] += pattern[j]
        
        elif anatomical_type == 'lung':
            # Add alveolar patterns
            alveolar_pattern = np.random.random(shape)
            alveolar_pattern = alveolar_pattern > 0.65  # Create alveoli
            alveolar_pattern = gaussian_filter(alveolar_pattern.astype(float), sigma=2.0)
            texture = texture * (1 + alveolar_pattern * 0.3)
        
        # Add fine detail layer
        detail_texture = np.zeros(shape)
        detail_amplitude = 0.3
        detail_frequency = 1.0
        
        for i in range(detail_octaves):
            coords = np.meshgrid(*[np.linspace(0, detail_frequency * 8, s) for s in shape], indexing='ij')
            
            detail_noise = np.random.random(shape) * 2 - 1
            for j in range(len(shape)):
                detail_noise = gaussian_filter(detail_noise, sigma=detail_scale * (2 ** i))
            
            detail_texture += detail_amplitude * detail_noise
            detail_amplitude *= 0.6
            detail_frequency *= 2.0
        
        # Combine textures
        final_texture = texture + detail_texture * surface_detail
        
        # Normalize to [0, 1]
        final_texture = (final_texture - final_texture.min()) / (final_texture.max() - final_texture.min())
        
        return final_texture
    
    def _apply_advanced_material_properties(self, data: np.ndarray, anatomical_type: str) -> np.ndarray:
        """Apply sophisticated material properties for ultra-realistic rendering."""
        material = self.anatomical_materials.get(anatomical_type, self.anatomical_materials['default'])
        texture_config = self.texture_generators[material['texture_type']]
        
        # Generate advanced texture
        texture = self._generate_advanced_organic_texture(data.shape, texture_config, anatomical_type)
        
        # Apply material properties with enhanced realism
        base_color = np.array(material['base_color'])
        roughness = material['roughness']
        bump_strength = material['bump_strength']
        color_variation = material['color_variation']
        detail_scale = material['detail_scale']
        texture_granularity = material.get('texture_granularity', 0.5)
        surface_roughness = material.get('surface_roughness', 0.5)
        organic_detail = material.get('organic_detail', 0.5)
        
        # Create enhanced color variation
        color_variation_map = texture * color_variation
        varied_color = base_color + color_variation_map[..., np.newaxis] * 0.4
        
        # Apply enhanced roughness simulation
        roughness_map = texture * roughness * surface_roughness
        surface_bumps = texture * bump_strength * detail_scale * organic_detail
        
        # Create final material-enhanced data
        material_enhanced = data.copy()
        
        # Apply enhanced color enhancement with anatomical accuracy
        for i in range(3):  # RGB channels
            material_enhanced = material_enhanced + varied_color[..., i] * 0.15
        
        # Apply enhanced surface detail
        material_enhanced = material_enhanced + surface_bumps * 0.08
        
        # Apply enhanced roughness-based noise
        roughness_noise = np.random.normal(0, roughness * surface_roughness * 0.03, data.shape)
        material_enhanced = material_enhanced + roughness_noise
        
        # Apply texture granularity
        if texture_granularity > 0:
            granular_noise = np.random.normal(0, texture_granularity * 0.02, data.shape)
            material_enhanced = material_enhanced + granular_noise
        
        # Apply organic detail enhancement
        if organic_detail > 0:
            organic_noise = np.random.normal(0, organic_detail * 0.015, data.shape)
            material_enhanced = material_enhanced + organic_noise
        
        return material_enhanced
    
    def _apply_photorealistic_lighting(self, data: np.ndarray, anatomical_type: str) -> np.ndarray:
        """Apply photorealistic lighting simulation for enhanced realism."""
        material = self.anatomical_materials.get(anatomical_type, self.anatomical_materials['default'])
        
        # Simulate subsurface scattering
        subsurface_scattering = material['subsurface_scattering']
        if subsurface_scattering > 0:
            # Apply multiple scattering passes
            scattered = data.copy()
            for i in range(3):
                scattered = gaussian_filter(scattered, sigma=1.0 + i * 0.5)
                scattered = scattered * 0.8 + data * 0.2
            
            # Blend based on material properties
            data = data * (1 - subsurface_scattering) + scattered * subsurface_scattering
        
        # Simulate ambient occlusion (darker in cavities)
        # Create distance transform for occlusion
        binary_data = data > np.percentile(data, 30)
        distance = distance_transform_edt(binary_data)
        
        # Normalize distance
        if distance.max() > 0:
            distance_norm = distance / distance.max()
            # Invert for occlusion (closer to surface = lighter)
            occlusion = 1.0 - distance_norm * 0.3
            
            # Apply occlusion
            data = data * occlusion
        
        # Simulate rim lighting
        # Calculate surface normals using gradients
        grad_x = sobel(data, axis=0)
        grad_y = sobel(data, axis=1)
        grad_z = sobel(data, axis=2)
        
        # Normalize gradients
        grad_magnitude = np.sqrt(grad_x**2 + grad_y**2 + grad_z**2)
        grad_magnitude = np.where(grad_magnitude > 0, grad_magnitude, 1.0)
        
        grad_x = grad_x / grad_magnitude
        grad_y = grad_y / grad_magnitude
        grad_z = grad_z / grad_magnitude
        
        # Simulate rim lighting (light coming from behind)
        rim_light = grad_z * 0.5 + 0.5  # Z-component for rim lighting
        rim_enhancement = rim_light * 0.1
        
        data = data + rim_enhancement
        
        return data
    
    def _apply_medical_grade_enhancement(self, data: np.ndarray, anatomical_type: str) -> np.ndarray:
        """Apply medical-grade enhancement for professional visualization quality."""
        # Apply advanced histogram equalization
        equalized = exposure.equalize_adapthist(data, clip_limit=0.02)
        
        # Apply gamma correction for realistic lighting
        gamma_corrected = exposure.adjust_gamma(equalized, gamma=1.05)
        
        # Apply contrast enhancement
        p2, p98 = np.percentile(gamma_corrected, (2, 98))
        contrast_stretched = exposure.rescale_intensity(gamma_corrected, in_range=(p2, p98))
        
        # Apply unsharp masking for detail enhancement
        sharpened = unsharp_mask(contrast_stretched, radius=1.0, amount=1.2)
        
        # Blend with original to maintain data integrity
        enhanced_data = 0.8 * data + 0.2 * sharpened
        
        # Apply noise reduction while preserving edges
        denoised = denoise_bilateral(enhanced_data, sigma_color=0.05, sigma_spatial=1.0)
        
        # Final blend
        final_data = 0.9 * enhanced_data + 0.1 * denoised
        
        return final_data
    
    def apply_ultra_realistic_anatomy_effect(self, nifti_img: nib.Nifti1Image, 
                                           filename: str,
                                           material_realism: float = 0.9,
                                           lighting_quality: float = 0.8,
                                           texture_detail: float = 0.7) -> nib.Nifti1Image:
        """
        Apply ultra-realistic anatomical visualization effects.
        
        This creates the most realistic possible medical visualization with
        advanced material properties, photorealistic lighting, and anatomical
        accuracy similar to professional medical imaging software.
        
        Args:
            nifti_img: Input NIfTI image
            filename: Filename to determine anatomical type
            material_realism: Level of material property simulation (0.0-1.0)
            lighting_quality: Quality of lighting simulation (0.0-1.0)
            texture_detail: Level of texture detail (0.0-1.0)
            
        Returns:
            Ultra-realistic NIfTI image with professional medical quality
        """
        logger.info(f"Applying ultra-realistic anatomy effect to {filename}")
        
        data = nifti_img.get_fdata().astype(np.float32)
        anatomical_type = self._get_anatomical_type(filename)
        
        logger.info(f"Detected anatomical type: {anatomical_type}")
        
        # Preserve original data range
        original_min, original_max = data.min(), data.max()
        
        # Step 1: Apply medical-grade enhancement
        logger.info("Applying medical-grade enhancement...")
        enhanced_data = self._apply_medical_grade_enhancement(data, anatomical_type)
        
        # Step 2: Apply advanced material properties
        logger.info("Applying advanced material properties...")
        if material_realism > 0:
            material_enhanced = self._apply_advanced_material_properties(enhanced_data, anatomical_type)
            # Blend based on realism level
            enhanced_data = enhanced_data * (1 - material_realism) + material_enhanced * material_realism
        
        # Step 3: Apply photorealistic lighting
        logger.info("Applying photorealistic lighting...")
        if lighting_quality > 0:
            lighting_enhanced = self._apply_photorealistic_lighting(enhanced_data, anatomical_type)
            # Blend based on lighting quality
            enhanced_data = enhanced_data * (1 - lighting_quality) + lighting_enhanced * lighting_quality
        
        # Step 4: Apply texture detail enhancement
        logger.info("Applying texture detail enhancement...")
        if texture_detail > 0:
            # Generate high-detail texture
            material = self.anatomical_materials.get(anatomical_type, self.anatomical_materials['default'])
            texture_config = self.texture_generators[material['texture_type']]
            
            # Scale texture parameters based on detail level
            scaled_config = texture_config.copy()
            scaled_config['detail_octaves'] = int(texture_config['detail_octaves'] * texture_detail)
            scaled_config['surface_detail'] = texture_config['surface_detail'] * texture_detail
            
            detail_texture = self._generate_advanced_organic_texture(
                enhanced_data.shape, scaled_config, anatomical_type)
            
            # Apply texture detail
            texture_enhancement = detail_texture * texture_detail * 0.05
            enhanced_data = enhanced_data + texture_enhancement
        
        # Step 5: Final quality enhancement
        logger.info("Applying final quality enhancement...")
        
        # Apply edge-preserving smoothing
        edge_preserved = gaussian_filter(enhanced_data, sigma=0.3)
        
        # Create edge map
        edge_map = np.sqrt(sobel(enhanced_data, axis=0)**2 + 
                          sobel(enhanced_data, axis=1)**2 + 
                          sobel(enhanced_data, axis=2)**2)
        
        # Blend based on edge presence
        final_data = np.where(edge_map > np.percentile(edge_map, 80),
                             enhanced_data * 0.9 + edge_preserved * 0.1,  # Preserve edges
                             enhanced_data * 0.7 + edge_preserved * 0.3)  # Smooth non-edges
        
        # Preserve original data range
        if original_max > original_min:
            final_min, final_max = final_data.min(), final_data.max()
            if final_max > final_min:
                final_data = (final_data - final_min) / (final_max - final_min)
                final_data = final_data * (original_max - original_min) + original_min
        
        processed_img = nib.Nifti1Image(final_data, nifti_img.affine, nifti_img.header)
        logger.info("Ultra-realistic anatomy effect applied successfully")
        return processed_img
    
    def apply_photorealistic_organs_effect(self, nifti_img: nib.Nifti1Image,
                                         filename: str,
                                         organ_detail: float = 0.8,
                                         surface_quality: float = 0.9) -> nib.Nifti1Image:
        """
        Apply photorealistic organ visualization with enhanced surface quality.
        
        Args:
            nifti_img: Input NIfTI image
            filename: Filename to determine anatomical type
            organ_detail: Level of organ-specific detail (0.0-1.0)
            surface_quality: Quality of surface rendering (0.0-1.0)
            
        Returns:
            Photorealistic organ NIfTI image
        """
        logger.info(f"Applying photorealistic organs effect to {filename}")
        
        data = nifti_img.get_fdata().astype(np.float32)
        anatomical_type = self._get_anatomical_type(filename)
        
        # Apply ultra-realistic anatomy with organ-specific parameters
        return self.apply_ultra_realistic_anatomy_effect(
            nifti_img, filename, 
            material_realism=organ_detail,
            lighting_quality=surface_quality,
            texture_detail=organ_detail * 0.8
        )
    
    def apply_medical_grade_rendering_effect(self, nifti_img: nib.Nifti1Image,
                                           filename: str,
                                           professional_quality: float = 1.0,
                                           clinical_accuracy: float = 0.9) -> nib.Nifti1Image:
        """
        Apply medical-grade rendering for clinical-quality visualization.
        
        Args:
            nifti_img: Input NIfTI image
            filename: Filename to determine anatomical type
            professional_quality: Level of professional quality (0.0-1.0)
            clinical_accuracy: Level of clinical accuracy (0.0-1.0)
            
        Returns:
            Medical-grade rendered NIfTI image
        """
        logger.info(f"Applying medical-grade rendering effect to {filename}")
        
        data = nifti_img.get_fdata().astype(np.float32)
        anatomical_type = self._get_anatomical_type(filename)
        
        # Apply ultra-realistic anatomy with medical-grade parameters
        return self.apply_ultra_realistic_anatomy_effect(
            nifti_img, filename,
            material_realism=professional_quality,
            lighting_quality=clinical_accuracy,
            texture_detail=professional_quality * 0.7
        )
    
    def apply_medical_visualization_effect(self, nifti_img: nib.Nifti1Image,
                                         filename: str,
                                         anatomical_realism: float = 1.0,
                                         surface_quality: float = 1.0,
                                         material_accuracy: float = 1.0) -> nib.Nifti1Image:
        """
        Apply specialized medical visualization effect for anatomical structures
        like those shown in the medical image (liver, gallbladder, vessels, bones).
        
        This effect is specifically designed to create realistic voxels that match
        the appearance of professional medical visualization software.
        
        Args:
            nifti_img: Input NIfTI image
            filename: Filename to determine anatomical type
            anatomical_realism: Level of anatomical realism (0.0-1.0)
            surface_quality: Quality of surface rendering (0.0-1.0)
            material_accuracy: Accuracy of material properties (0.0-1.0)
            
        Returns:
            Medical visualization NIfTI image with enhanced realism
        """
        logger.info(f"Applying medical visualization effect to {filename}")
        
        data = nifti_img.get_fdata().astype(np.float32)
        anatomical_type = self._get_anatomical_type(filename)
        
        logger.info(f"Detected anatomical type: {anatomical_type}")
        
        # Preserve original data range
        original_min, original_max = data.min(), data.max()
        
        # Step 1: Apply enhanced medical-grade enhancement
        logger.info("Applying enhanced medical-grade enhancement...")
        enhanced_data = self._apply_medical_grade_enhancement(data, anatomical_type)
        
        # Step 2: Apply specialized anatomical material properties
        logger.info("Applying specialized anatomical material properties...")
        if anatomical_realism > 0:
            material_enhanced = self._apply_advanced_material_properties(enhanced_data, anatomical_type)
            # Blend based on anatomical realism level
            enhanced_data = enhanced_data * (1 - anatomical_realism) + material_enhanced * anatomical_realism
        
        # Step 3: Apply enhanced photorealistic lighting
        logger.info("Applying enhanced photorealistic lighting...")
        if surface_quality > 0:
            lighting_enhanced = self._apply_photorealistic_lighting(enhanced_data, anatomical_type)
            # Blend based on surface quality
            enhanced_data = enhanced_data * (1 - surface_quality) + lighting_enhanced * surface_quality
        
        # Step 4: Apply material accuracy enhancement
        logger.info("Applying material accuracy enhancement...")
        if material_accuracy > 0:
            # Apply additional material-specific enhancements
            material = self.anatomical_materials.get(anatomical_type, self.anatomical_materials['default'])
            
            # Apply color accuracy
            base_color = np.array(material['base_color'])
            color_strength = material_accuracy * 0.1
            for i in range(3):  # RGB channels
                enhanced_data = enhanced_data + base_color[i] * color_strength
            
            # Apply surface accuracy
            surface_accuracy = material_accuracy * 0.05
            surface_noise = np.random.normal(0, surface_accuracy, data.shape)
            enhanced_data = enhanced_data + surface_noise
        
        # Step 5: Apply final medical visualization enhancement
        logger.info("Applying final medical visualization enhancement...")
        
        # Apply edge-preserving smoothing for medical quality
        edge_preserved = gaussian_filter(enhanced_data, sigma=0.4)
        
        # Create enhanced edge map
        edge_map = np.sqrt(sobel(enhanced_data, axis=0)**2 + 
                          sobel(enhanced_data, axis=1)**2 + 
                          sobel(enhanced_data, axis=2)**2)
        
        # Apply medical-grade blending
        final_data = np.where(edge_map > np.percentile(edge_map, 85),
                             enhanced_data * 0.95 + edge_preserved * 0.05,  # Preserve important edges
                             enhanced_data * 0.8 + edge_preserved * 0.2)   # Smooth non-critical areas
        
        # Preserve original data range
        if original_max > original_min:
            final_min, final_max = final_data.min(), final_data.max()
            if final_max > final_min:
                final_data = (final_data - final_min) / (final_max - final_min)
                final_data = final_data * (original_max - original_min) + original_min
        
        processed_img = nib.Nifti1Image(final_data, nifti_img.affine, nifti_img.header)
        logger.info("Medical visualization effect applied successfully")
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
                if effect_name == "ultra_realistic_anatomy":
                    processed_img = self.apply_ultra_realistic_anatomy_effect(
                        nifti_img, file_path.name, **effect_params)
                elif effect_name == "photorealistic_organs":
                    processed_img = self.apply_photorealistic_organs_effect(
                        nifti_img, file_path.name, **effect_params)
                elif effect_name == "medical_grade_rendering":
                    processed_img = self.apply_medical_grade_rendering_effect(
                        nifti_img, file_path.name, **effect_params)
                elif effect_name == "medical_visualization":
                    processed_img = self.apply_medical_visualization_effect(
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
        description="Apply enhanced realistic medical visualization effects to voxel files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Apply ultra-realistic anatomical visualization
  python enhanced_realistic_medical.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 --effect ultra_realistic_anatomy
  
  # Apply photorealistic organ rendering
  python enhanced_realistic_medical.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 --effect photorealistic_organs
  
  # Apply medical-grade professional rendering
  python enhanced_realistic_medical.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 --effect medical_grade_rendering
  
  # Apply specialized medical visualization (like the medical image)
  python enhanced_realistic_medical.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 --effect medical_visualization
        """
    )
    
    # Required arguments
    parser.add_argument("--patient", required=True, help="Patient ID (e.g., PA00000002)")
    parser.add_argument("--scan", required=True, help="Scan name (e.g., 2.5MM_ARTERIAL_3)")
    parser.add_argument("--effect", required=True, 
                       choices=["ultra_realistic_anatomy", "photorealistic_organs", "medical_grade_rendering", "medical_visualization"],
                       help="Effect to apply")
    
    # Optional arguments
    parser.add_argument("--output-dir", type=Path, help="Custom output directory")
    parser.add_argument("--material-realism", type=float, default=0.9, help="Material realism level (0.0-1.0)")
    parser.add_argument("--lighting-quality", type=float, default=0.8, help="Lighting quality level (0.0-1.0)")
    parser.add_argument("--texture-detail", type=float, default=0.7, help="Texture detail level (0.0-1.0)")
    parser.add_argument("--organ-detail", type=float, default=0.8, help="Organ detail level for photorealistic_organs (0.0-1.0)")
    parser.add_argument("--surface-quality", type=float, default=0.9, help="Surface quality for photorealistic_organs (0.0-1.0)")
    parser.add_argument("--professional-quality", type=float, default=1.0, help="Professional quality for medical_grade_rendering (0.0-1.0)")
    parser.add_argument("--clinical-accuracy", type=float, default=0.9, help="Clinical accuracy for medical_grade_rendering (0.0-1.0)")
    parser.add_argument("--anatomical-realism", type=float, default=1.0, help="Anatomical realism for medical_visualization (0.0-1.0)")
    parser.add_argument("--surface-quality", type=float, default=1.0, help="Surface quality for medical_visualization (0.0-1.0)")
    parser.add_argument("--material-accuracy", type=float, default=1.0, help="Material accuracy for medical_visualization (0.0-1.0)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Create processor
        processor = EnhancedRealisticMedicalProcessor()
        
        # Prepare effect parameters
        effect_params = {
            "material_realism": args.material_realism,
            "lighting_quality": args.lighting_quality,
            "texture_detail": args.texture_detail,
            "organ_detail": args.organ_detail,
            "surface_quality": args.surface_quality,
            "professional_quality": args.professional_quality,
            "clinical_accuracy": args.clinical_accuracy,
            "anatomical_realism": args.anatomical_realism,
            "material_accuracy": args.material_accuracy
        }
        
        # Filter parameters based on effect
        if args.effect == "ultra_realistic_anatomy":
            effect_params = {k: v for k, v in effect_params.items() 
                           if k in ["material_realism", "lighting_quality", "texture_detail"]}
        elif args.effect == "photorealistic_organs":
            effect_params = {k: v for k, v in effect_params.items() 
                           if k in ["organ_detail", "surface_quality"]}
        elif args.effect == "medical_grade_rendering":
            effect_params = {k: v for k, v in effect_params.items() 
                           if k in ["professional_quality", "clinical_accuracy"]}
        elif args.effect == "medical_visualization":
            effect_params = {k: v for k, v in effect_params.items() 
                           if k in ["anatomical_realism", "surface_quality", "material_accuracy"]}
        
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
