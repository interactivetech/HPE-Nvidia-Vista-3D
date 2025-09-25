#!/usr/bin/env python3
"""
MONAI Medical Image Processing Page

A standalone Streamlit page showcasing MONAI (Medical Open Network for AI) 
functionality for medical image processing, post-processing, and analysis.
This page is not included in the main navigation and serves as a standalone tool.

Features:
- MONAI transforms demonstration
- Medical image preprocessing
- Post-processing Vista3D segmentation outputs
- Interactive parameter tuning
- Batch processing capabilities
- Visualization of transform effects
"""

import streamlit as st
import numpy as np
import nibabel as nib
import os
import sys
from pathlib import Path
import tempfile
import json
from typing import List, Dict, Optional, Tuple
import plotly.graph_objects as go
import plotly.express as px
from PIL import Image
import io
import base64

# Add utils to path for imports
sys.path.append(str(Path(__file__).parent / 'utils'))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# MONAI imports
try:
    import monai
    from monai.transforms import (
        GaussianSmooth, 
        RandGaussianNoise,
        RandGaussianSharpen,
        RandAdjustContrast,
        RandHistogramShift,
        RandBiasField,
        RandGaussianSmooth,
        RandSpatialCrop,
        RandFlip,
        RandRotate,
        RandZoom,
        RandAffine,
        Rand2DElastic,
        Rand3DElastic,
        RandCoarseDropout,
        RandCoarseShuffle,
        RandScaleIntensity,
        RandShiftIntensity,
        RandGibbsNoise,
        RandRicianNoise,
        RandKSpaceSpikeNoise,
        RandSimulateLowResolution,
        RandSmoothDeform,
        RandSmoothFieldAdjustContrast,
        RandSmoothFieldAdjustIntensity,
        RandStdShiftIntensity,
        RandTorchVision,
        RandWeightedCrop,
        RandScaleCrop,
        RandCropByPosNegLabel,
        RandCropByLabelClasses,
        RandGridDistortion,
        RandGridPatch,
        RandImageFilter,
        RandIntensityRemap,
        RandLambda,
        RandMark,
        RandRangePop,
        RandRangePush,
        RandRotate90,
        RandSpatialCropSamples,
        RandTorchIO,
        Compose,
        LoadImage,
        EnsureChannelFirst,
        ScaleIntensity,
        NormalizeIntensity,
        Resize,
        CropForeground,
        ToTensor,
        EnsureType,
        Spacing,
        Orientation,
        LoadImaged,
        EnsureChannelFirstd,
        ScaleIntensityd,
        NormalizeIntensityd,
        Resized,
        CropForegroundd,
        RandCropByPosNegLabeld,
        RandGaussianNoised,
        RandGaussianSharpen,
        RandAdjustContrastd,
        RandHistogramShiftd,
        RandBiasFieldd,
        RandGaussianSmoothd,
        RandSpatialCropd,
        RandFlipd,
        RandRotated,
        RandZoomd,
        ToTensord,
        EnsureTyped,
        Spacingd,
        Orientationd,
        RandAffined,
        Rand2DElasticd,
        Rand3DElasticd,
        RandCoarseDropoutd,
        RandCoarseShuffled
    )
    from monai.data import DataLoader, Dataset, decollate_batch
    from monai.utils import first, set_determinism
    from monai.visualize import plot_2d_or_3d_image
    from monai.networks.nets import UNet
    from monai.losses import DiceLoss
    from monai.metrics import DiceMetric
    from monai.inferers import sliding_window_inference
    MONAI_AVAILABLE = True
except ImportError as e:
    MONAI_AVAILABLE = False
    st.error(f"MONAI is not available: {e}")
    st.stop()

# Configure page
st.set_page_config(
    page_title="MONAI Medical Image Processing",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.8rem;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.5rem;
    }
    .info-box {
        background-color: #e8f4fd;
        border-left: 4px solid #3498db;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 4px;
    }
    .warning-box {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 4px;
    }
    .success-box {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 4px;
    }
    .metric-card {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

def load_nifti_file(file_path: str) -> Tuple[np.ndarray, np.ndarray]:
    """Load a NIfTI file and return the data and affine."""
    try:
        img = nib.load(file_path)
        return img.get_fdata(), img.affine
    except Exception as e:
        st.error(f"Error loading NIfTI file: {e}")
        return None, None

def save_nifti_file(data: np.ndarray, affine: np.ndarray, output_path: str) -> bool:
    """Save data as a NIfTI file."""
    try:
        img = nib.Nifti1Image(data, affine)
        nib.save(img, output_path)
        return True
    except Exception as e:
        st.error(f"Error saving NIfTI file: {e}")
        return False

def create_sample_data() -> Tuple[np.ndarray, np.ndarray]:
    """Create sample 3D medical imaging data for demonstration."""
    # Create a 3D volume with some anatomical-like structures
    data = np.zeros((64, 64, 64))
    
    # Add some ellipsoidal structures to simulate organs
    y, x, z = np.ogrid[:64, :64, :64]
    
    # Main structure (like a liver)
    center1 = (32, 32, 32)
    radius1 = (15, 20, 12)
    mask1 = ((x - center1[0]) / radius1[0])**2 + ((y - center1[1]) / radius1[1])**2 + ((z - center1[2]) / radius1[2])**2 <= 1
    data[mask1] = 1.0
    
    # Secondary structure (like a kidney)
    center2 = (20, 20, 20)
    radius2 = (8, 6, 10)
    mask2 = ((x - center2[0]) / radius2[0])**2 + ((y - center2[1]) / radius2[1])**2 + ((z - center2[2]) / radius2[2])**2 <= 1
    data[mask2] = 0.7
    
    # Add some noise
    data += np.random.normal(0, 0.1, data.shape)
    data = np.clip(data, 0, 1)
    
    # Create identity affine
    affine = np.eye(4)
    return data, affine

def visualize_3d_slice(data: np.ndarray, slice_idx: int, axis: int = 0) -> go.Figure:
    """Create a 3D visualization of a slice."""
    if axis == 0:
        slice_data = data[slice_idx, :, :]
        title = f"Axial Slice {slice_idx}"
    elif axis == 1:
        slice_data = data[:, slice_idx, :]
        title = f"Coronal Slice {slice_idx}"
    else:
        slice_data = data[:, :, slice_idx]
        title = f"Sagittal Slice {slice_idx}"
    
    fig = go.Figure(data=go.Heatmap(
        z=slice_data,
        colorscale='gray',
        showscale=True
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="X",
        yaxis_title="Y",
        width=400,
        height=400
    )
    
    return fig

def apply_monai_transform(data: np.ndarray, transform_name: str, **kwargs) -> np.ndarray:
    """Apply a MONAI transform to the data."""
    try:
        # Add batch and channel dimensions
        data_with_dims = data[None, None, ...]  # [1, 1, H, W, D]
        
        if transform_name == "GaussianSmooth":
            transform = GaussianSmooth(sigma=kwargs.get('sigma', 1.0))
        elif transform_name == "RandGaussianNoise":
            transform = RandGaussianNoise(prob=1.0, std=kwargs.get('std', 0.1))
        elif transform_name == "RandGaussianSharpen":
            transform = RandGaussianSharpen(prob=1.0, alpha=kwargs.get('alpha', 0.5))
        elif transform_name == "RandAdjustContrast":
            transform = RandAdjustContrast(prob=1.0, gamma=kwargs.get('gamma', 1.0))
        elif transform_name == "RandHistogramShift":
            transform = RandHistogramShift(prob=1.0, num_control_points=kwargs.get('num_control_points', 10))
        elif transform_name == "RandBiasField":
            transform = RandBiasField(prob=1.0, coeff_range=kwargs.get('coeff_range', (0.0, 0.1)))
        elif transform_name == "RandGaussianSmooth":
            transform = RandGaussianSmooth(prob=1.0, sigma_x=kwargs.get('sigma_x', 1.0), sigma_y=kwargs.get('sigma_y', 1.0))
        elif transform_name == "RandSpatialCrop":
            transform = RandSpatialCrop(prob=1.0, roi_size=kwargs.get('roi_size', (32, 32, 32)))
        elif transform_name == "RandFlip":
            transform = RandFlip(prob=1.0, spatial_axis=kwargs.get('spatial_axis', 0))
        elif transform_name == "RandRotate":
            transform = RandRotate(prob=1.0, range_x=kwargs.get('range_x', 0.1), range_y=kwargs.get('range_y', 0.1), range_z=kwargs.get('range_z', 0.1))
        elif transform_name == "RandZoom":
            transform = RandZoom(prob=1.0, min_zoom=kwargs.get('min_zoom', 0.9), max_zoom=kwargs.get('max_zoom', 1.1))
        elif transform_name == "RandScaleIntensity":
            transform = RandScaleIntensity(prob=1.0, factors=kwargs.get('factors', 0.1))
        elif transform_name == "RandShiftIntensity":
            transform = RandShiftIntensity(prob=1.0, offsets=kwargs.get('offsets', 0.1))
        elif transform_name == "RandGibbsNoise":
            transform = RandGibbsNoise(prob=1.0, alpha=kwargs.get('alpha', 0.5))
        elif transform_name == "RandRicianNoise":
            transform = RandRicianNoise(prob=1.0, std=kwargs.get('std', 0.1))
        elif transform_name == "RandKSpaceSpikeNoise":
            transform = RandKSpaceSpikeNoise(prob=1.0, intensity_range=kwargs.get('intensity_range', (10, 25)))
        elif transform_name == "RandSimulateLowResolution":
            transform = RandSimulateLowResolution(prob=1.0, zoom_range=kwargs.get('zoom_range', (0.5, 1.0)))
        elif transform_name == "RandSmoothDeform":
            transform = RandSmoothDeform(prob=1.0, field_tensor=kwargs.get('field_tensor', None))
        elif transform_name == "RandSmoothFieldAdjustContrast":
            transform = RandSmoothFieldAdjustContrast(prob=1.0, gamma_range=kwargs.get('gamma_range', (0.5, 2.0)))
        elif transform_name == "RandSmoothFieldAdjustIntensity":
            transform = RandSmoothFieldAdjustIntensity(prob=1.0, field_range=kwargs.get('field_range', (0.0, 1.0)))
        elif transform_name == "RandStdShiftIntensity":
            transform = RandStdShiftIntensity(prob=1.0, factors=kwargs.get('factors', 0.1))
        elif transform_name == "RandWeightedCrop":
            transform = RandWeightedCrop(prob=1.0, spatial_size=kwargs.get('spatial_size', (32, 32, 32)))
        elif transform_name == "RandScaleCrop":
            transform = RandScaleCrop(prob=1.0, roi_scale=kwargs.get('roi_scale', 0.5))
        elif transform_name == "RandGridDistortion":
            transform = RandGridDistortion(prob=1.0, distort_limit=kwargs.get('distort_limit', 0.1))
        elif transform_name == "RandImageFilter":
            transform = RandImageFilter(prob=1.0, filter_type=kwargs.get('filter_type', 'gaussian'))
        elif transform_name == "RandIntensityRemap":
            transform = RandIntensityRemap(prob=1.0, num_knots=kwargs.get('num_knots', 5))
        elif transform_name == "RandRotate90":
            transform = RandRotate90(prob=1.0, max_k=kwargs.get('max_k', 3))
        else:
            st.error(f"Unknown transform: {transform_name}")
            return data
        
        # Apply transform
        result = transform(data_with_dims)
        return result[0, 0, ...]  # Remove batch and channel dimensions
        
    except Exception as e:
        st.error(f"Error applying transform {transform_name}: {e}")
        return data

def main():
    """Main function for the MONAI page."""
    
    # Header
    st.markdown('<h1 class="main-header">🧠 MONAI Medical Image Processing</h1>', unsafe_allow_html=True)
    
    st.info("""
    **MONAI (Medical Open Network for AI)** is a PyTorch-based, open-source framework for deep learning in healthcare imaging. 
    This page demonstrates MONAI's powerful transforms and utilities for medical image processing, 
    particularly useful for post-processing Vista3D segmentation outputs.
    """)
    
    # Sidebar for configuration
    st.sidebar.markdown("## ⚙️ Configuration")
    
    # Data source selection
    data_source = st.sidebar.selectbox(
        "Data Source",
        ["Sample Data", "Upload NIfTI File", "Browse Output Directory"],
        help="Choose the source of medical imaging data"
    )
    
    # Load data based on selection
    data = None
    affine = None
    file_name = "sample_data"
    
    if data_source == "Sample Data":
        st.sidebar.markdown("### Sample Data")
        if st.sidebar.button("Generate Sample Data"):
            with st.spinner("Generating sample 3D medical imaging data..."):
                data, affine = create_sample_data()
                st.sidebar.success("Sample data generated!")
    
    elif data_source == "Upload NIfTI File":
        st.sidebar.markdown("### Upload NIfTI File")
        uploaded_file = st.sidebar.file_uploader(
            "Choose a NIfTI file",
            type=['nii', 'nii.gz'],
            help="Upload a .nii or .nii.gz file for processing"
        )
        
        if uploaded_file is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.nii.gz') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name
            
            with st.spinner("Loading uploaded file..."):
                data, affine = load_nifti_file(tmp_file_path)
                file_name = uploaded_file.name.split('.')[0]
                os.unlink(tmp_file_path)
    
    elif data_source == "Browse Output Directory":
        st.sidebar.markdown("### Browse Output Directory")
        output_dir = Path("output")
        if output_dir.exists():
            patient_folders = [f for f in output_dir.iterdir() if f.is_dir()]
            if patient_folders:
                selected_patient = st.sidebar.selectbox(
                    "Select Patient",
                    [f.name for f in patient_folders],
                    help="Choose a patient folder from the output directory"
                )
                
                patient_path = output_dir / selected_patient
                nifti_dir = patient_path / "nifti"
                
                if nifti_dir.exists():
                    nifti_files = list(nifti_dir.glob("*.nii.gz"))
                    if nifti_files:
                        selected_file = st.sidebar.selectbox(
                            "Select NIfTI File",
                            [f.name for f in nifti_files],
                            help="Choose a NIfTI file to process"
                        )
                        
                        if st.sidebar.button("Load File"):
                            with st.spinner("Loading NIfTI file..."):
                                data, affine = load_nifti_file(str(nifti_dir / selected_file))
                                file_name = selected_file.split('.')[0]
            else:
                st.sidebar.warning("No patient folders found in output directory")
        else:
            st.sidebar.warning("Output directory not found")
    
    # Main content area
    if data is not None:
        st.markdown('<h2 class="section-header">📊 Data Information</h2>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Shape", f"{data.shape[0]}×{data.shape[1]}×{data.shape[2]}")
        
        with col2:
            st.metric("Data Type", str(data.dtype))
        
        with col3:
            st.metric("Min Value", f"{data.min():.3f}")
        
        with col4:
            st.metric("Max Value", f"{data.max():.3f}")
        
        # Data visualization
        st.markdown('<h2 class="section-header">🖼️ Data Visualization</h2>', unsafe_allow_html=True)
        
        # Slice selection
        col1, col2, col3 = st.columns(3)
        
        with col1:
            slice_idx = st.slider("Slice Index", 0, data.shape[0]-1, data.shape[0]//2, key="axial")
            fig_axial = visualize_3d_slice(data, slice_idx, 0)
            st.plotly_chart(fig_axial, use_container_width=True, key="axial_chart")
            st.caption("Axial View")
        
        with col2:
            slice_idx_coronal = st.slider("Slice Index", 0, data.shape[1]-1, data.shape[1]//2, key="coronal")
            fig_coronal = visualize_3d_slice(data, slice_idx_coronal, 1)
            st.plotly_chart(fig_coronal, use_container_width=True, key="coronal_chart")
            st.caption("Coronal View")
        
        with col3:
            slice_idx_sagittal = st.slider("Slice Index", 0, data.shape[2]-1, data.shape[2]//2, key="sagittal")
            fig_sagittal = visualize_3d_slice(data, slice_idx_sagittal, 2)
            st.plotly_chart(fig_sagittal, use_container_width=True, key="sagittal_chart")
            st.caption("Sagittal View")
        
        # MONAI Transforms
        st.markdown('<h2 class="section-header">🔧 MONAI Transforms</h2>', unsafe_allow_html=True)
        
        # Transform selection
        transform_options = {
            "GaussianSmooth": "Apply Gaussian smoothing to reduce noise",
            "RandGaussianNoise": "Add random Gaussian noise",
            "RandGaussianSharpen": "Apply random Gaussian sharpening",
            "RandAdjustContrast": "Randomly adjust contrast",
            "RandHistogramShift": "Randomly shift histogram",
            "RandBiasField": "Apply random bias field correction",
            "RandGaussianSmooth": "Apply random Gaussian smoothing",
            "RandSpatialCrop": "Randomly crop spatial region",
            "RandFlip": "Randomly flip along axis",
            "RandRotate": "Randomly rotate the image",
            "RandZoom": "Randomly zoom the image",
            "RandScaleIntensity": "Randomly scale intensity values",
            "RandShiftIntensity": "Randomly shift intensity values",
            "RandGibbsNoise": "Add Gibbs noise artifacts",
            "RandRicianNoise": "Add Rician noise",
            "RandKSpaceSpikeNoise": "Add k-space spike noise",
            "RandSimulateLowResolution": "Simulate low resolution",
            "RandSmoothDeform": "Apply smooth deformation",
            "RandSmoothFieldAdjustContrast": "Adjust contrast with smooth field",
            "RandSmoothFieldAdjustIntensity": "Adjust intensity with smooth field",
            "RandStdShiftIntensity": "Shift intensity by standard deviation",
            "RandWeightedCrop": "Randomly crop weighted regions",
            "RandScaleCrop": "Randomly scale and crop",
            "RandGridDistortion": "Apply grid distortion",
            "RandImageFilter": "Apply random image filter",
            "RandIntensityRemap": "Remap intensity values",
            "RandRotate90": "Randomly rotate by 90 degrees"
        }
        
        selected_transform = st.selectbox(
            "Select Transform",
            list(transform_options.keys()),
            help="Choose a MONAI transform to apply"
        )
        
        st.info(f"**{selected_transform}**: {transform_options[selected_transform]}")
        
        # Transform parameters
        st.markdown("### Transform Parameters")
        
        transform_params = {}
        
        if selected_transform == "GaussianSmooth":
            transform_params['sigma'] = st.slider("Sigma", 0.1, 5.0, 1.0, 0.1)
        
        elif selected_transform == "RandGaussianNoise":
            transform_params['std'] = st.slider("Noise Standard Deviation", 0.01, 0.5, 0.1, 0.01)
        
        elif selected_transform == "RandGaussianSharpen":
            transform_params['alpha'] = st.slider("Alpha", 0.1, 2.0, 0.5, 0.1)
        
        elif selected_transform == "RandAdjustContrast":
            transform_params['gamma'] = st.slider("Gamma", 0.1, 3.0, 1.0, 0.1)
        
        elif selected_transform == "RandHistogramShift":
            transform_params['num_control_points'] = st.slider("Control Points", 5, 20, 10, 1)
        
        elif selected_transform == "RandBiasField":
            transform_params['coeff_range'] = (0.0, st.slider("Max Coefficient", 0.01, 0.5, 0.1, 0.01))
        
        elif selected_transform == "RandGaussianSmooth":
            transform_params['sigma_x'] = st.slider("Sigma X", 0.1, 3.0, 1.0, 0.1)
            transform_params['sigma_y'] = st.slider("Sigma Y", 0.1, 3.0, 1.0, 0.1)
        
        elif selected_transform == "RandSpatialCrop":
            crop_size = st.slider("Crop Size", 16, min(data.shape), min(data.shape)//2, 8, key="spatial_crop_size")
            transform_params['roi_size'] = (crop_size, crop_size, crop_size)
        
        elif selected_transform == "RandFlip":
            transform_params['spatial_axis'] = st.selectbox("Flip Axis", [0, 1, 2], format_func=lambda x: ["X", "Y", "Z"][x], key="flip_axis")
        
        elif selected_transform == "RandRotate":
            transform_params['range_x'] = st.slider("Rotation Range X", 0.0, 1.0, 0.1, 0.05, key="rotate_range_x")
            transform_params['range_y'] = st.slider("Rotation Range Y", 0.0, 1.0, 0.1, 0.05, key="rotate_range_y")
            transform_params['range_z'] = st.slider("Rotation Range Z", 0.0, 1.0, 0.1, 0.05, key="rotate_range_z")
        
        elif selected_transform == "RandZoom":
            transform_params['min_zoom'] = st.slider("Min Zoom", 0.5, 1.0, 0.9, 0.05, key="zoom_min")
            transform_params['max_zoom'] = st.slider("Max Zoom", 1.0, 2.0, 1.1, 0.05, key="zoom_max")
        
        elif selected_transform == "RandScaleIntensity":
            transform_params['factors'] = st.slider("Scale Factors", 0.1, 2.0, 0.1, 0.05)
        
        elif selected_transform == "RandShiftIntensity":
            transform_params['offsets'] = st.slider("Shift Offsets", 0.0, 1.0, 0.1, 0.05)
        
        elif selected_transform == "RandGibbsNoise":
            transform_params['alpha'] = st.slider("Alpha", 0.1, 1.0, 0.5, 0.05)
        
        elif selected_transform == "RandRicianNoise":
            transform_params['std'] = st.slider("Noise Standard Deviation", 0.01, 0.5, 0.1, 0.01)
        
        elif selected_transform == "RandKSpaceSpikeNoise":
            transform_params['intensity_range'] = (st.slider("Min Intensity", 5, 50, 10, 1, key="kspace_min_intensity"), 
                                                 st.slider("Max Intensity", 10, 100, 25, 1, key="kspace_max_intensity"))
        
        elif selected_transform == "RandSimulateLowResolution":
            transform_params['zoom_range'] = (st.slider("Min Zoom", 0.1, 0.8, 0.5, 0.05, key="lowres_min_zoom"),
                                            st.slider("Max Zoom", 0.5, 1.0, 1.0, 0.05, key="lowres_max_zoom"))
        
        elif selected_transform == "RandSmoothDeform":
            st.info("SmoothDeform requires a field tensor - using default parameters")
        
        elif selected_transform == "RandSmoothFieldAdjustContrast":
            transform_params['gamma_range'] = (st.slider("Min Gamma", 0.1, 1.0, 0.5, 0.05, key="contrast_min_gamma"),
                                             st.slider("Max Gamma", 1.0, 3.0, 2.0, 0.05, key="contrast_max_gamma"))
        
        elif selected_transform == "RandSmoothFieldAdjustIntensity":
            transform_params['field_range'] = (st.slider("Min Field", 0.0, 0.5, 0.0, 0.05, key="intensity_min_field"),
                                             st.slider("Max Field", 0.5, 1.0, 1.0, 0.05, key="intensity_max_field"))
        
        elif selected_transform == "RandStdShiftIntensity":
            transform_params['factors'] = st.slider("Std Factors", 0.1, 2.0, 0.1, 0.05)
        
        elif selected_transform == "RandWeightedCrop":
            crop_size = st.slider("Crop Size", 16, min(data.shape), min(data.shape)//2, 8, key="weighted_crop_size")
            transform_params['spatial_size'] = (crop_size, crop_size, crop_size)
        
        elif selected_transform == "RandScaleCrop":
            transform_params['roi_scale'] = st.slider("ROI Scale", 0.1, 1.0, 0.5, 0.05, key="scale_crop_roi")
        
        elif selected_transform == "RandGridDistortion":
            transform_params['distort_limit'] = st.slider("Distort Limit", 0.01, 0.5, 0.1, 0.01, key="grid_distort_limit")
        
        elif selected_transform == "RandImageFilter":
            transform_params['filter_type'] = st.selectbox("Filter Type", ['gaussian', 'laplacian', 'sobel'], key="image_filter_type")
        
        elif selected_transform == "RandIntensityRemap":
            transform_params['num_knots'] = st.slider("Number of Knots", 3, 10, 5, 1, key="intensity_remap_knots")
        
        elif selected_transform == "RandRotate90":
            transform_params['max_k'] = st.slider("Max K (90° rotations)", 1, 4, 3, 1, key="rotate90_max_k")
        
        # Apply transform
        if st.button("Apply Transform", type="primary"):
            with st.spinner(f"Applying {selected_transform}..."):
                try:
                    transformed_data = apply_monai_transform(data, selected_transform, **transform_params)
                    
                    # Store in session state for comparison
                    st.session_state.original_data = data
                    st.session_state.transformed_data = transformed_data
                    st.session_state.transform_name = selected_transform
                    
                    st.success(f"Successfully applied {selected_transform}!")
                    
                except Exception as e:
                    st.error(f"Error applying transform: {e}")
        
        # Display results if transform was applied
        if 'transformed_data' in st.session_state:
            st.markdown('<h2 class="section-header">📈 Transform Results</h2>', unsafe_allow_html=True)
            
            original_data = st.session_state.original_data
            transformed_data = st.session_state.transformed_data
            transform_name = st.session_state.transform_name
            
            # Comparison metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Original Mean", f"{original_data.mean():.4f}")
                st.metric("Transformed Mean", f"{transformed_data.mean():.4f}")
            
            with col2:
                st.metric("Original Std", f"{original_data.std():.4f}")
                st.metric("Transformed Std", f"{transformed_data.std():.4f}")
            
            with col3:
                st.metric("Original Min", f"{original_data.min():.4f}")
                st.metric("Transformed Min", f"{transformed_data.min():.4f}")
            
            with col4:
                st.metric("Original Max", f"{original_data.max():.4f}")
                st.metric("Transformed Max", f"{transformed_data.max():.4f}")
            
            # Side-by-side visualization
            st.markdown("### Before vs After Comparison")
            
            # Use the same slice indices as the original visualization
            slice_idx = st.session_state.get('axial_slice', original_data.shape[0]//2)
            slice_idx_coronal = st.session_state.get('coronal_slice', original_data.shape[1]//2)
            slice_idx_sagittal = st.session_state.get('sagittal_slice', original_data.shape[2]//2)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Original**")
                fig_orig = visualize_3d_slice(original_data, slice_idx, 0)
                st.plotly_chart(fig_orig, use_container_width=True, key="original_chart")
            
            with col2:
                st.markdown(f"**After {transform_name}**")
                fig_trans = visualize_3d_slice(transformed_data, slice_idx, 0)
                st.plotly_chart(fig_trans, use_container_width=True, key="transformed_chart")
            
            # Download options
            st.markdown("### Download Results")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Download Transformed Data"):
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.nii.gz') as tmp_file:
                        if save_nifti_file(transformed_data, affine, tmp_file.name):
                            with open(tmp_file.name, 'rb') as f:
                                st.download_button(
                                    label="Download NIfTI File",
                                    data=f.read(),
                                    file_name=f"{file_name}_{transform_name.lower()}.nii.gz",
                                    mime="application/gzip"
                                )
                        os.unlink(tmp_file.name)
            
            with col2:
                if st.button("Reset to Original"):
                    if 'transformed_data' in st.session_state:
                        del st.session_state.transformed_data
                    st.rerun()
        
        # Batch Processing
        st.markdown('<h2 class="section-header">🔄 Batch Processing</h2>', unsafe_allow_html=True)
        
        st.info("""
        **Batch Processing:** Process multiple files with the same transform parameters. 
        This is particularly useful for post-processing Vista3D segmentation outputs.
        """)
        
        if st.button("Process All Files in Output Directory"):
            output_dir = Path("output")
            if output_dir.exists():
                with st.spinner("Processing all files..."):
                    processed_count = 0
                    error_count = 0
                    
                    for patient_folder in output_dir.iterdir():
                        if patient_folder.is_dir():
                            nifti_dir = patient_folder / "nifti"
                            if nifti_dir.exists():
                                for nifti_file in nifti_dir.glob("*.nii.gz"):
                                    try:
                                        # Load file
                                        file_data, file_affine = load_nifti_file(str(nifti_file))
                                        if file_data is not None:
                                            # Apply transform
                                            transformed_file_data = apply_monai_transform(
                                                file_data, selected_transform, **transform_params
                                            )
                                            
                                            # Save result
                                            output_file = nifti_file.parent / f"{nifti_file.stem}_MONAI.nii.gz"
                                            if save_nifti_file(transformed_file_data, file_affine, str(output_file)):
                                                processed_count += 1
                                            else:
                                                error_count += 1
                                        else:
                                            error_count += 1
                                    except Exception as e:
                                        st.error(f"Error processing {nifti_file}: {e}")
                                        error_count += 1
                    
                    st.success(f"Batch processing complete! Processed: {processed_count}, Errors: {error_count}")
            else:
                st.warning("Output directory not found")
    
    else:
        st.warning("""
        **No Data Loaded:** Please select a data source from the sidebar and load some medical imaging data to begin processing.
        """)
    
    # MONAI Information
    st.markdown('<h2 class="section-header">ℹ️ About MONAI</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    **MONAI (Medical Open Network for AI)** is a PyTorch-based, open-source framework for deep learning in healthcare imaging. 
    It provides domain-optimized foundational capabilities for developing and deploying machine learning models for medical imaging.
    """)
    
    st.markdown("### Key Features:")
    st.markdown("""
    - **Medical Image Transforms**: Comprehensive set of transforms for medical imaging data
    - **Deep Learning Models**: Pre-trained models and architectures for medical imaging
    - **Data Loading**: Efficient data loading and preprocessing for medical imaging datasets
    - **Loss Functions**: Specialized loss functions for medical imaging tasks
    - **Metrics**: Evaluation metrics for medical imaging models
    - **Visualization**: Tools for visualizing medical imaging data and model outputs
    """)
    
    st.markdown("### Common Use Cases:")
    st.markdown("""
    - **Image Preprocessing**: Normalization, resizing, cropping, and augmentation
    - **Post-processing**: Smoothing, denoising, and enhancement of segmentation outputs
    - **Data Augmentation**: Increasing dataset diversity for training
    - **Model Training**: Training deep learning models for medical imaging tasks
    - **Inference**: Running trained models on new medical imaging data
    """)
    
    st.markdown("### Integration with Vista3D:")
    st.markdown("""
    MONAI transforms are particularly useful for post-processing Vista3D segmentation outputs:
    - **Gaussian Smoothing**: Reduces noise in segmentation masks
    - **Morphological Operations**: Clean up segmentation boundaries
    - **Intensity Normalization**: Standardize image intensities
    - **Spatial Transforms**: Augment data for training or testing
    """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; margin-top: 2rem;">
        <p>MONAI Medical Image Processing Page • Powered by MONAI and Streamlit</p>
        <p>For more information, visit <a href="https://monai.io" target="_blank">monai.io</a></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
