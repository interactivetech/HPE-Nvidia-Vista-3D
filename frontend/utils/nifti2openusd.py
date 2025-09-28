#!/usr/bin/env python3
"""
NIfTI to OpenUSD Conversion Script for Vista3D

This script converts NIfTI medical imaging files to OpenUSD format for use in
3D visualization and rendering pipelines. It supports various conversion methods
including isosurface extraction, volume rendering, and mesh generation.

Folder Structure:
    For patient data, the script follows this structure:
    - Input:  PA00000002/voxel/2.5MM_ARTERIAL_3/file.nii.gz
    - Output: PA00000002/openusd/2.5MM_ARTERIAL_3/file_isosurface.usda
    
    The script automatically creates the openusd folder and maintains the same
    subfolder structure as the input voxel folder.

Usage:
    python nifti2openusd.py --input /path/to/file.nii.gz --output /path/to/output.usda
    python nifti2openusd.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 --method isosurface
    python nifti2openusd.py --input /path/to/file.nii.gz --output /path/to/output.usda --method volume --threshold 0.5
"""

import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any, Union, Tuple
import numpy as np
import nibabel as nib
import logging
import json
from datetime import datetime

# OpenUSD imports
try:
    from pxr import Usd, UsdGeom, Gf, Sdf, UsdShade, UsdLux, Vt
    USD_AVAILABLE = True
except ImportError:
    USD_AVAILABLE = False
    logging.warning("OpenUSD not available. Install with: pip install usd-core")

# Medical imaging processing
try:
    from skimage import measure, morphology, filters
    from scipy import ndimage
    SKIMAGE_AVAILABLE = True
except ImportError:
    SKIMAGE_AVAILABLE = False
    logging.warning("scikit-image not available. Install with: pip install scikit-image")

# Add the project root to the Python path
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent  # frontend/utils -> frontend -> project_root
sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NIfTI2OpenUSDConverter:
    """
    Converts NIfTI medical imaging files to OpenUSD format.
    
    Supports multiple conversion methods:
    - isosurface: Extract isosurfaces using marching cubes
    - volume: Create volume primitives for volume rendering
    - mesh: Generate mesh from segmented regions
    - pointcloud: Convert to point cloud representation
    """
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize the converter.
        
        Args:
            output_dir: Directory to save USD files. If None, uses input file directory.
        """
        self.output_dir = output_dir
        self.conversion_methods = {
            'isosurface': self._convert_to_isosurface,
            'volume': self._convert_to_volume,
            'mesh': self._convert_to_mesh,
            'pointcloud': self._convert_to_pointcloud
        }
        
        if not USD_AVAILABLE:
            raise ImportError("OpenUSD (usd-core) is required but not installed. Install with: pip install usd-core")
    
    def convert_file(self, input_path: Path, output_path: Optional[Path] = None, 
                    method: str = 'isosurface', **kwargs) -> Path:
        """
        Convert a single NIfTI file to USD format.
        
        Args:
            input_path: Path to input NIfTI file
            output_path: Path for output USD file. If None, auto-generates from input.
            method: Conversion method ('isosurface', 'volume', 'mesh', 'pointcloud')
            **kwargs: Additional parameters for conversion method
            
        Returns:
            Path to the created USD file
        """
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        if method not in self.conversion_methods:
            raise ValueError(f"Unknown conversion method: {method}. Available: {list(self.conversion_methods.keys())}")
        
        # Generate output path if not provided
        if output_path is None:
            output_path = self._generate_output_path(input_path, method)
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Converting {input_path} to {output_path} using {method} method")
        
        # Load NIfTI file
        nifti_img = nib.load(input_path)
        data = nifti_img.get_fdata()
        affine = nifti_img.affine
        header = nifti_img.header
        
        logger.info(f"Loaded NIfTI data: shape={data.shape}, dtype={data.dtype}")
        
        # Apply conversion method
        conversion_func = self.conversion_methods[method]
        
        # Filter kwargs based on method
        method_kwargs = {}
        if method == 'isosurface':
            method_kwargs = {k: v for k, v in kwargs.items() if k in ['threshold', 'smoothing', 'decimation']}
        elif method == 'volume':
            method_kwargs = {k: v for k, v in kwargs.items() if k in ['volume_type']}
        elif method == 'mesh':
            method_kwargs = {k: v for k, v in kwargs.items() if k in ['segmentation_threshold']}
        elif method == 'pointcloud':
            method_kwargs = {k: v for k, v in kwargs.items() if k in ['sampling_rate']}
        
        stage = conversion_func(data, affine, header, input_path.name, **method_kwargs)
        
        # Save USD file
        stage.GetRootLayer().Save()
        # Copy the temporary file to the final location
        import shutil
        shutil.move("temp.usda", str(output_path))
        logger.info(f"Saved USD file: {output_path}")
        
        return output_path
    
    def _generate_output_path(self, input_path: Path, method: str) -> Path:
        """
        Generate output path following the patient folder structure.
        
        For files in PA00000002/voxel/2.5MM_ARTERIAL_3/, creates PA00000002/openusd/2.5MM_ARTERIAL_3/
        
        Args:
            input_path: Path to input NIfTI file
            method: Conversion method
            
        Returns:
            Generated output path
        """
        # If using custom output directory, use it
        if self.output_dir:
            return self.output_dir / f"{input_path.stem}_{method}.usda"
        
        # Try to detect patient folder structure
        path_parts = input_path.parts
        
        # Look for patient ID pattern (PA followed by digits)
        patient_id = None
        patient_index = -1
        
        for i, part in enumerate(path_parts):
            if part.startswith('PA') and part[2:].isdigit():
                patient_id = part
                patient_index = i
                break
        
        if patient_id and patient_index >= 0:
            # Reconstruct path with openusd folder
            new_parts = list(path_parts)
            
            # Replace 'voxel' or 'voxels' with 'openusd' in the path
            for i in range(patient_index + 1, len(new_parts)):
                if new_parts[i].lower() in ['voxel', 'voxels']:
                    new_parts[i] = 'openusd'
                    break
            
            # Create output filename with method suffix
            filename = input_path.stem
            if not filename.endswith(f'_{method}'):
                filename = f"{filename}_{method}"
            
            # Remove the filename from the path parts and add the new filename
            new_parts = new_parts[:-1]  # Remove the original filename
            output_path = Path(*new_parts) / f"{filename}.usda"
        else:
            # Fallback to same directory as input
            output_path = input_path.parent / f"{input_path.stem}_{method}.usda"
        
        return output_path
    
    def _convert_to_isosurface(self, data: np.ndarray, affine: np.ndarray, 
                              header: nib.Nifti1Header, filename: str, 
                              threshold: float = 0.5, smoothing: float = 0.0,
                              decimation: float = 0.0) -> Usd.Stage:
        """
        Convert NIfTI data to USD isosurface using marching cubes.
        
        Args:
            data: 3D numpy array from NIfTI
            affine: Affine transformation matrix
            header: NIfTI header
            filename: Original filename for metadata
            threshold: Isosurface threshold value
            smoothing: Gaussian smoothing factor
            decimation: Mesh decimation factor (0-1)
            
        Returns:
            USD Stage with isosurface geometry
        """
        if not SKIMAGE_AVAILABLE:
            raise ImportError("scikit-image is required for isosurface conversion")
        
        # Normalize data to 0-1 range
        data_normalized = self._normalize_data(data)
        
        # Apply smoothing if requested
        if smoothing > 0:
            data_normalized = ndimage.gaussian_filter(data_normalized, sigma=smoothing)
        
        # Extract isosurface using marching cubes
        try:
            verts, faces, normals, values = measure.marching_cubes(
                data_normalized, 
                level=threshold,
                spacing=self._get_voxel_spacing(header)
            )
        except ValueError as e:
            logger.warning(f"Marching cubes failed: {e}. Trying with different parameters.")
            # Try with a different threshold
            threshold = np.percentile(data_normalized, 50)
            verts, faces, normals, values = measure.marching_cubes(
                data_normalized, 
                level=threshold,
                spacing=self._get_voxel_spacing(header)
            )
        
        # Apply decimation if requested
        if decimation > 0:
            verts, faces = self._decimate_mesh(verts, faces, decimation)
        
        # Create USD stage
        stage = Usd.Stage.CreateNew("temp.usda")
        
        # Define root transform
        root = UsdGeom.Xform.Define(stage, '/Root')
        root.AddTranslateOp().Set(Gf.Vec3f(0, 0, 0))
        
        # Define mesh
        mesh_path = '/Root/Isosurface'
        mesh = UsdGeom.Mesh.Define(stage, mesh_path)
        
        # Set mesh attributes
        mesh.CreatePointsAttr(Vt.Vec3fArray.FromNumpy(verts.astype(np.float32)))
        mesh.CreateFaceVertexIndicesAttr(Vt.IntArray.FromNumpy(faces.flatten().astype(np.int32)))
        mesh.CreateFaceVertexCountsAttr(Vt.IntArray.FromNumpy(np.full(faces.shape[0], 3, dtype=np.int32)))
        
        # Set normals
        if normals is not None:
            mesh.CreateNormalsAttr(Vt.Vec3fArray.FromNumpy(normals.astype(np.float32)))
            mesh.SetNormalsInterpolation(UsdGeom.Tokens.faceVarying)
        
        # Apply material
        self._create_medical_material(stage, mesh_path, filename)
        
        # Add metadata
        self._add_metadata(stage, filename, 'isosurface', {
            'threshold': threshold,
            'smoothing': smoothing,
            'decimation': decimation,
            'vertex_count': len(verts),
            'face_count': len(faces)
        })
        
        return stage
    
    def _convert_to_volume(self, data: np.ndarray, affine: np.ndarray,
                          header: nib.Nifti1Header, filename: str,
                          volume_type: str = 'density') -> Usd.Stage:
        """
        Convert NIfTI data to USD volume primitive for volume rendering.
        
        Args:
            data: 3D numpy array from NIfTI
            affine: Affine transformation matrix
            header: NIfTI header
            filename: Original filename for metadata
            volume_type: Type of volume ('density', 'opacity', 'color')
            
        Returns:
            USD Stage with volume primitive
        """
        # Create USD stage
        stage = Usd.Stage.CreateNew("temp.usda")
        
        # Define root transform
        root = UsdGeom.Xform.Define(stage, '/Root')
        
        # Define volume
        volume_path = '/Root/Volume'
        volume = UsdGeom.Volume.Define(stage, volume_path)
        
        # Set volume dimensions
        dims = data.shape
        volume.CreateExtentAttr().Set(Vt.Vec3iArray([(0, dims[0]-1), (0, dims[1]-1), (0, dims[2]-1)]))
        
        # Set field name
        field_name = f"density_{filename.replace('.nii.gz', '')}"
        volume.CreateFieldNameAttr().Set(field_name)
        
        # Create field
        field_path = f'/Root/Volume/{field_name}'
        field = UsdVol.Volume.Define(stage, field_path)
        
        # Set field data
        field.CreateFieldDataTypeAttr().Set('float')
        field.CreateFieldIndexAttr().Set(0)
        
        # Create field asset
        field_asset_path = f"{filename.replace('.nii.gz', '')}_volume.raw"
        field.CreateFieldAssetPathAttr().Set(field_asset_path)
        
        # Save volume data as raw file
        self._save_volume_data(data, stage.GetRootLayer().realPath.replace('.usda', '_volume.raw'))
        
        # Add material for volume rendering
        self._create_volume_material(stage, volume_path, filename)
        
        # Add metadata
        self._add_metadata(stage, filename, 'volume', {
            'volume_type': volume_type,
            'dimensions': dims,
            'field_name': field_name
        })
        
        return stage
    
    def _convert_to_mesh(self, data: np.ndarray, affine: np.ndarray,
                        header: nib.Nifti1Header, filename: str,
                        segmentation_threshold: float = 0.5) -> Usd.Stage:
        """
        Convert NIfTI data to USD mesh by creating multiple mesh objects.
        
        Args:
            data: 3D numpy array from NIfTI
            affine: Affine transformation matrix
            header: NIfTI header
            filename: Original filename for metadata
            segmentation_threshold: Threshold for segmentation
            
        Returns:
            USD Stage with mesh geometry
        """
        # Create USD stage
        stage = Usd.Stage.CreateNew("temp.usda")
        
        # Define root transform
        root = UsdGeom.Xform.Define(stage, '/Root')
        
        # Segment data into regions
        segmented_data = self._segment_data(data, segmentation_threshold)
        
        # Create mesh for each segment
        for i, segment in enumerate(segmented_data):
            if np.sum(segment) == 0:
                continue
                
            # Create mesh from segment
            verts, faces = self._create_mesh_from_segment(segment, i)
            
            if len(verts) == 0:
                continue
            
            # Define mesh
            mesh_path = f'/Root/Segment_{i}'
            mesh = UsdGeom.Mesh.Define(stage, mesh_path)
            
            # Set mesh attributes
            mesh.CreatePointsAttr(Vt.Vec3fArray.FromNumpy(verts.astype(np.float32)))
            mesh.CreateFaceVertexIndicesAttr(Vt.IntArray.FromNumpy(faces.flatten().astype(np.int32)))
            mesh.CreateFaceVertexCountsAttr(Vt.IntArray.FromNumpy(np.full(faces.shape[0], 3, dtype=np.int32)))
            
            # Apply material
            self._create_segment_material(stage, mesh_path, i)
        
        # Add metadata
        self._add_metadata(stage, filename, 'mesh', {
            'segmentation_threshold': segmentation_threshold,
            'segment_count': len(segmented_data)
        })
        
        return stage
    
    def _convert_to_pointcloud(self, data: np.ndarray, affine: np.ndarray,
                              header: nib.Nifti1Header, filename: str,
                              sampling_rate: float = 0.1) -> Usd.Stage:
        """
        Convert NIfTI data to USD point cloud.
        
        Args:
            data: 3D numpy array from NIfTI
            affine: Affine transformation matrix
            header: NIfTI header
            filename: Original filename for metadata
            sampling_rate: Fraction of voxels to sample (0-1)
            
        Returns:
            USD Stage with point cloud
        """
        # Create USD stage
        stage = Usd.Stage.CreateNew("temp.usda")
        
        # Define root transform
        root = UsdGeom.Xform.Define(stage, '/Root')
        
        # Sample points
        points, colors = self._sample_points(data, sampling_rate)
        
        if len(points) == 0:
            logger.warning("No points sampled from data")
            return stage
        
        # Define points
        points_path = '/Root/PointCloud'
        points_prim = UsdGeom.Points.Define(stage, points_path)
        
        # Set point positions
        points_prim.CreatePointsAttr().Set(Vt.Vec3fArray.FromNumpy(points.astype(np.float32)))
        
        # Set point colors
        if colors is not None:
            points_prim.CreateDisplayColorAttr().Set(Vt.Vec3fArray.FromNumpy(colors.astype(np.float32)))
        
        # Set point size
        points_prim.CreateWidthsAttr().Set(Vt.FloatArray([1.0] * len(points)))
        
        # Add metadata
        self._add_metadata(stage, filename, 'pointcloud', {
            'sampling_rate': sampling_rate,
            'point_count': len(points)
        })
        
        return stage
    
    def _normalize_data(self, data: np.ndarray) -> np.ndarray:
        """Normalize data to 0-1 range."""
        data_min = np.min(data)
        data_max = np.max(data)
        if data_max > data_min:
            return (data - data_min) / (data_max - data_min)
        return data
    
    def _get_voxel_spacing(self, header: nib.Nifti1Header) -> Tuple[float, float, float]:
        """Get voxel spacing from NIfTI header."""
        pixdim = header.get_zooms()
        return (float(pixdim[0]), float(pixdim[1]), float(pixdim[2]))
    
    def _decimate_mesh(self, verts: np.ndarray, faces: np.ndarray, 
                      decimation_factor: float) -> Tuple[np.ndarray, np.ndarray]:
        """Decimate mesh by removing faces."""
        if decimation_factor <= 0:
            return verts, faces
        
        # Simple decimation by removing every nth face
        keep_every = int(1 / decimation_factor)
        keep_faces = faces[::keep_every]
        
        # Find vertices that are still used
        used_verts = np.unique(keep_faces.flatten())
        vert_map = {old_idx: new_idx for new_idx, old_idx in enumerate(used_verts)}
        
        # Remap face indices
        new_faces = np.array([[vert_map[old_idx] for old_idx in face] for face in keep_faces])
        new_verts = verts[used_verts]
        
        return new_verts, new_faces
    
    def _create_medical_material(self, stage: Usd.Stage, mesh_path: str, filename: str):
        """Create medical visualization material."""
        material_path = f'{mesh_path}_Material'
        material = UsdShade.Material.Define(stage, material_path)
        
        # Create shader
        shader_path = f'{material_path}/Shader'
        shader = UsdShade.Shader.Define(stage, shader_path)
        shader.CreateIdAttr().Set('UsdPreviewSurface')
        
        # Set material properties
        shader.CreateInput('diffuseColor', Sdf.ValueTypeNames.Color3f).Set((0.8, 0.8, 0.9))
        shader.CreateInput('metallic', Sdf.ValueTypeNames.Float).Set(0.0)
        shader.CreateInput('roughness', Sdf.ValueTypeNames.Float).Set(0.3)
        shader.CreateInput('opacity', Sdf.ValueTypeNames.Float).Set(0.8)
        
        # Connect shader to material (simplified)
        # material.CreateSurfaceOutput().ConnectToSource(shader.GetOutput('surface'))
        
        # Bind material to mesh
        mesh = UsdGeom.Mesh.Get(stage, mesh_path)
        UsdShade.MaterialBindingAPI(mesh).Bind(material)
    
    def _create_volume_material(self, stage: Usd.Stage, volume_path: str, filename: str):
        """Create volume rendering material."""
        material_path = f'{volume_path}_Material'
        material = UsdShade.Material.Define(stage, material_path)
        
        # Create volume shader
        shader_path = f'{material_path}/VolumeShader'
        shader = UsdShade.Shader.Define(stage, shader_path)
        shader.CreateIdAttr().Set('UsdVolVolume')
        
        # Set volume properties
        shader.CreateInput('density', Sdf.ValueTypeNames.Float).Set(1.0)
        shader.CreateInput('color', Sdf.ValueTypeNames.Color3f).Set((0.8, 0.9, 1.0))
        
        # Connect shader to material (simplified)
        # material.CreateVolumeOutput().ConnectToSource(shader.GetOutput('volume'))
        
        # Bind material to volume
        volume = UsdGeom.Volume.Get(stage, volume_path)
        UsdShade.MaterialBindingAPI(volume).Bind(material)
    
    def _create_segment_material(self, stage: Usd.Stage, mesh_path: str, segment_id: int):
        """Create material for segmented mesh."""
        material_path = f'{mesh_path}_Material'
        material = UsdShade.Material.Define(stage, material_path)
        
        # Create shader
        shader_path = f'{material_path}/Shader'
        shader = UsdShade.Shader.Define(stage, shader_path)
        shader.CreateIdAttr().Set('UsdPreviewSurface')
        
        # Generate color based on segment ID
        colors = [
            (0.8, 0.2, 0.2),  # Red
            (0.2, 0.8, 0.2),  # Green
            (0.2, 0.2, 0.8),  # Blue
            (0.8, 0.8, 0.2),  # Yellow
            (0.8, 0.2, 0.8),  # Magenta
            (0.2, 0.8, 0.8),  # Cyan
        ]
        color = colors[segment_id % len(colors)]
        
        # Set material properties
        shader.CreateInput('diffuseColor', Sdf.ValueTypeNames.Color3f).Set(color)
        shader.CreateInput('metallic', Sdf.ValueTypeNames.Float).Set(0.0)
        shader.CreateInput('roughness', Sdf.ValueTypeNames.Float).Set(0.4)
        shader.CreateInput('opacity', Sdf.ValueTypeNames.Float).Set(0.9)
        
        # Connect shader to material (simplified)
        # material.CreateSurfaceOutput().ConnectToSource(shader.GetOutput('surface'))
        
        # Bind material to mesh
        mesh = UsdGeom.Mesh.Get(stage, mesh_path)
        UsdShade.MaterialBindingAPI(mesh).Bind(material)
    
    def _add_metadata(self, stage: Usd.Stage, filename: str, method: str, params: Dict[str, Any]):
        """Add metadata to USD stage."""
        stage.SetMetadata('comment', f'Converted from NIfTI: {filename} using {method} method')
    
    def _save_volume_data(self, data: np.ndarray, filepath: str):
        """Save volume data as raw file."""
        data.astype(np.float32).tofile(filepath)
        logger.info(f"Saved volume data: {filepath}")
    
    def _segment_data(self, data: np.ndarray, threshold: float) -> List[np.ndarray]:
        """Segment data into regions."""
        # Simple threshold-based segmentation
        binary_data = data > threshold
        
        # Find connected components
        labeled_data = ndimage.label(binary_data)[0]
        
        segments = []
        for label_id in range(1, np.max(labeled_data) + 1):
            segment = (labeled_data == label_id).astype(np.float32)
            if np.sum(segment) > 100:  # Only keep segments with significant size
                segments.append(segment)
        
        return segments
    
    def _create_mesh_from_segment(self, segment: np.ndarray, segment_id: int) -> Tuple[np.ndarray, np.ndarray]:
        """Create mesh from segmented data."""
        if not SKIMAGE_AVAILABLE:
            return np.array([]), np.array([])
        
        try:
            verts, faces, _, _ = measure.marching_cubes(segment, level=0.5)
            return verts, faces
        except ValueError:
            return np.array([]), np.array([])
    
    def _sample_points(self, data: np.ndarray, sampling_rate: float) -> Tuple[np.ndarray, np.ndarray]:
        """Sample points from volume data."""
        # Create coordinate grid
        coords = np.mgrid[0:data.shape[0], 0:data.shape[1], 0:data.shape[2]]
        coords = coords.reshape(3, -1).T
        
        # Sample points based on data values and sampling rate
        flat_data = data.flatten()
        probabilities = flat_data / np.max(flat_data) * sampling_rate
        
        # Random sampling
        random_mask = np.random.random(len(flat_data)) < probabilities
        sampled_coords = coords[random_mask]
        sampled_values = flat_data[random_mask]
        
        # Convert to colors
        colors = self._values_to_colors(sampled_values)
        
        return sampled_coords, colors
    
    def _values_to_colors(self, values: np.ndarray) -> np.ndarray:
        """Convert data values to colors using medical colormap."""
        # Normalize values
        normalized = (values - np.min(values)) / (np.max(values) - np.min(values))
        
        # Apply medical colormap (grayscale to blue-red)
        colors = np.zeros((len(normalized), 3))
        colors[:, 0] = normalized  # Red channel
        colors[:, 1] = 0.3  # Green channel
        colors[:, 2] = 1.0 - normalized  # Blue channel
        
        return colors


def find_voxel_files(patient_id: str, scan_name: Optional[str] = None) -> Dict[str, List[Path]]:
    """
    Find voxel files for a patient and optionally specific scan.
    
    Looks for files in structure: PA00000002/voxel/2.5MM_ARTERIAL_3/*.nii.gz
    
    Args:
        patient_id: Patient identifier
        scan_name: Optional scan name to filter by
        
    Returns:
        Dictionary containing lists of voxel files
    """
    # Define search paths - prioritize voxel/voxels folders
    # Use absolute paths from project root
    project_root = Path(__file__).parent.parent.parent  # frontend/utils -> frontend -> project_root
    search_paths = [
        project_root / f"output/{patient_id}/voxels",
        project_root / f"output/{patient_id}/voxel",
        project_root / f"output/{patient_id}",
        project_root / f"dicom/{patient_id}/voxels",
        project_root / f"dicom/{patient_id}/voxel",
        project_root / f"dicom/{patient_id}",
        project_root / f"frontend/dicom/{patient_id}/voxels",
        project_root / f"frontend/dicom/{patient_id}/voxel",
        project_root / f"frontend/dicom/{patient_id}"
    ]
    
    voxel_files = {
        'individual_voxels': [],
        'all_voxels': [],
        'other_files': []
    }
    
    for search_path in search_paths:
        if not search_path.exists():
            continue
            
        # Find all NIfTI files
        nifti_files = list(search_path.rglob("*.nii.gz"))
        
        for file_path in nifti_files:
            if scan_name and scan_name not in file_path.name:
                continue
                
            if "voxel" in file_path.name.lower():
                if "all_voxels" in file_path.name:
                    voxel_files['all_voxels'].append(file_path)
                else:
                    voxel_files['individual_voxels'].append(file_path)
            else:
                voxel_files['other_files'].append(file_path)
    
    return voxel_files


def find_existing_openusd_files(patient_id: str, scan_name: Optional[str] = None) -> Dict[str, List[Path]]:
    """
    Find existing OpenUSD files for a patient to avoid re-processing.
    
    Looks for files in structure: PA00000002/openusd/2.5MM_ARTERIAL_3/*.usda
    
    Args:
        patient_id: Patient identifier
        scan_name: Optional scan name to filter by
        
    Returns:
        Dictionary containing lists of existing USD files
    """
    # Define search paths for openusd folders
    # Use absolute paths from project root
    project_root = Path(__file__).parent.parent.parent  # frontend/utils -> frontend -> project_root
    search_paths = [
        project_root / f"output/{patient_id}/openusd",
        project_root / f"dicom/{patient_id}/openusd",
        project_root / f"frontend/dicom/{patient_id}/openusd"
    ]
    
    usd_files = {
        'isosurface': [],
        'volume': [],
        'mesh': [],
        'pointcloud': [],
        'other': []
    }
    
    for search_path in search_paths:
        if not search_path.exists():
            continue
            
        # Find all USD files
        usd_file_list = list(search_path.rglob("*.usda")) + list(search_path.rglob("*.usd"))
        
        for file_path in usd_file_list:
            if scan_name and scan_name not in file_path.name:
                continue
                
            filename = file_path.name.lower()
            if 'isosurface' in filename:
                usd_files['isosurface'].append(file_path)
            elif 'volume' in filename:
                usd_files['volume'].append(file_path)
            elif 'mesh' in filename:
                usd_files['mesh'].append(file_path)
            elif 'pointcloud' in filename:
                usd_files['pointcloud'].append(file_path)
            else:
                usd_files['other'].append(file_path)
    
    return usd_files


def main():
    """Main command-line interface."""
    parser = argparse.ArgumentParser(
        description="Convert NIfTI medical imaging files to OpenUSD format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert single file
  python nifti2openusd.py --input /path/to/file.nii.gz --output /path/to/output.usda
  
  # Convert patient data with isosurface method (creates PA00000002/openusd/2.5MM_ARTERIAL_3/)
  python nifti2openusd.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 --method isosurface
  
  # Convert with volume rendering
  python nifti2openusd.py --patient PA00000002 --method volume --threshold 0.5
  
  # Convert to point cloud
  python nifti2openusd.py --patient PA00000002 --method pointcloud --sampling-rate 0.1
  
  # Skip existing files to avoid re-processing
  python nifti2openusd.py --patient PA00000002 --method isosurface --skip-existing
  
  # Force re-processing of existing files
  python nifti2openusd.py --patient PA00000002 --method isosurface --force
        """
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--input', type=Path, help='Input NIfTI file path')
    input_group.add_argument('--patient', type=str, help='Patient ID to process')
    
    # Output options
    parser.add_argument('--output', type=Path, help='Output USD file path (auto-generated if not provided)')
    parser.add_argument('--output-dir', type=Path, help='Output directory for USD files')
    parser.add_argument('--scan', type=str, help='Specific scan name to process (when using --patient)')
    
    # Conversion options
    parser.add_argument('--method', type=str, choices=['isosurface', 'volume', 'mesh', 'pointcloud'],
                       default='isosurface', help='Conversion method')
    
    # Method-specific parameters
    parser.add_argument('--threshold', type=float, default=0.5, help='Threshold for isosurface/mesh conversion')
    parser.add_argument('--smoothing', type=float, default=0.0, help='Gaussian smoothing factor for isosurface')
    parser.add_argument('--decimation', type=float, default=0.0, help='Mesh decimation factor (0-1)')
    parser.add_argument('--sampling-rate', type=float, default=0.1, help='Point cloud sampling rate (0-1)')
    parser.add_argument('--volume-type', type=str, choices=['density', 'opacity', 'color'],
                       default='density', help='Volume type for volume conversion')
    
    # Processing options
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--skip-existing', action='store_true', help='Skip files that already have USD equivalents')
    parser.add_argument('--force', action='store_true', help='Force re-processing of existing files')
    
    args = parser.parse_args()
    
    # Set up logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize converter
    try:
        converter = NIfTI2OpenUSDConverter(output_dir=args.output_dir)
    except ImportError as e:
        logger.error(f"Failed to initialize converter: {e}")
        return 1
    
    # Process files
    try:
        if args.input:
            # Single file conversion
            output_path = converter.convert_file(
                input_path=args.input,
                output_path=args.output,
                method=args.method,
                threshold=args.threshold,
                smoothing=args.smoothing,
                decimation=args.decimation,
                sampling_rate=args.sampling_rate,
                volume_type=args.volume_type
            )
            logger.info(f"Conversion complete: {output_path}")
            
        elif args.patient:
            # Patient data conversion
            voxel_files = find_voxel_files(args.patient, args.scan)
            
            if not voxel_files['individual_voxels'] and not voxel_files['all_voxels'] and not voxel_files['other_files']:
                logger.error(f"No NIfTI files found for patient {args.patient}")
                return 1
            
            # Check for existing USD files if skip-existing is enabled
            existing_usd_files = {}
            if args.skip_existing and not args.force:
                existing_usd_files = find_existing_openusd_files(args.patient, args.scan)
                logger.info(f"Found {sum(len(files) for files in existing_usd_files.values())} existing USD files")
            
            # Process all found files
            all_files = voxel_files['individual_voxels'] + voxel_files['all_voxels'] + voxel_files['other_files']
            converted_files = []
            skipped_files = []
            
            for file_path in all_files:
                try:
                    # Check if we should skip this file
                    if args.skip_existing and not args.force:
                        # Generate expected output path
                        expected_output = converter._generate_output_path(file_path, args.method)
                        
                        # Check if output already exists
                        if expected_output.exists():
                            logger.info(f"Skipping {file_path.name} - output already exists: {expected_output.name}")
                            skipped_files.append(file_path)
                            continue
                        
                        # Check if there's an existing USD file for this input
                        base_name = file_path.stem
                        for existing_files in existing_usd_files.values():
                            for existing_file in existing_files:
                                if base_name in existing_file.name and args.method in existing_file.name:
                                    logger.info(f"Skipping {file_path.name} - similar file exists: {existing_file.name}")
                                    skipped_files.append(file_path)
                                    break
                            else:
                                continue
                            break
                        else:
                            continue
                    
                    output_path = converter.convert_file(
                        input_path=file_path,
                        method=args.method,
                        threshold=args.threshold,
                        smoothing=args.smoothing,
                        decimation=args.decimation,
                        sampling_rate=args.sampling_rate,
                        volume_type=args.volume_type
                    )
                    converted_files.append(output_path)
                    logger.info(f"Converted: {file_path.name} -> {output_path.name}")
                    
                except Exception as e:
                    logger.error(f"Failed to convert {file_path}: {e}")
                    continue
            
            logger.info(f"Conversion complete. {len(converted_files)} files converted, {len(skipped_files)} files skipped.")
            
    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
