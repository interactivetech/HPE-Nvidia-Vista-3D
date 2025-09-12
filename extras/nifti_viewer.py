#!/usr/bin/env python3
"""
NIfTI Viewer: Interactive 3D NIfTI File Viewer

A Streamlit application for viewing and analyzing NIfTI (.nii.gz) medical imaging files
with interactive 3D volume visualization, 2D slice viewing, and analysis capabilities.

Features:
- Upload and view NIfTI files
- Interactive 3D volume rendering
- 2D slice viewer (axial, sagittal, coronal)
- Volume statistics and properties display
- Window/level controls for intensity adjustment
- Export to different formats
- Integration with voxel2mesh pipeline

Dependencies:
    - streamlit: For the web interface
    - plotly: For 3D visualization
    - nibabel: For NIfTI file processing
    - numpy: For numerical operations
    - pandas: For data display
    - scipy: For image processing
    - matplotlib: For 2D slice visualization

Usage:
    streamlit run nifti_viewer.py
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import nibabel as nib
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import os
from typing import Dict, List, Tuple, Optional
import io
import matplotlib.pyplot as plt
from scipy import ndimage
import cv2


def load_nifti_file(file_path: str) -> nib.Nifti1Image:
    """
    Load a NIfTI file and return a nibabel image object.
    
    Args:
        file_path (str): Path to the NIfTI file
        
    Returns:
        nib.Nifti1Image: Loaded NIfTI image object
    """
    try:
        img = nib.load(file_path)
        return img
    except Exception as e:
        st.error(f"Error loading NIfTI file: {e}")
        return None


def get_nifti_info(img: nib.Nifti1Image) -> Dict:
    """
    Extract comprehensive information about a NIfTI image.
    
    Args:
        img (nib.Nifti1Image): NIfTI image object
        
    Returns:
        Dict: Dictionary containing image statistics and properties
    """
    if img is None:
        return {}
    
    data = img.get_fdata()
    header = img.header
    affine = img.affine
    
    # Basic image properties
    info = {
        "Shape": str(data.shape),
        "Data Type": str(data.dtype),
        "Voxel Size": str(header.get_zooms()),
        "Volume (mm³)": f"{np.prod(header.get_zooms()):.2f}",
        "Total Voxels": f"{data.size:,}",
        "Non-zero Voxels": f"{np.count_nonzero(data):,}",
        "Min Value": f"{np.min(data):.6f}",
        "Max Value": f"{np.max(data):.6f}",
        "Mean Value": f"{np.mean(data):.6f}",
        "Std Value": f"{np.std(data):.6f}",
        "Memory Size (MB)": f"{data.nbytes / (1024*1024):.2f}"
    }
    
    # Header information
    try:
        info["Description"] = str(header.get('descrip', 'N/A'))
        info["Units"] = str(header.get_xyzt_units()[0])
        info["Time Units"] = str(header.get_xyzt_units()[1])
        info["Intent Code"] = str(header.get('intent_code', 'N/A'))
        info["Slice Duration"] = f"{header.get('slice_duration', 0):.3f} ms"
    except:
        pass
    
    # Spatial properties
    try:
        # Calculate volume in mm³
        voxel_volume = np.prod(header.get_zooms())
        total_volume = voxel_volume * np.count_nonzero(data)
        info["Total Volume (mm³)"] = f"{total_volume:.2f}"
        
        # Calculate bounding box
        non_zero_coords = np.where(data > 0)
        if len(non_zero_coords[0]) > 0:
            bbox_min = [np.min(non_zero_coords[i]) for i in range(3)]
            bbox_max = [np.max(non_zero_coords[i]) for i in range(3)]
            info["Bounding Box"] = f"{bbox_min} to {bbox_max}"
    except:
        pass
    
    # Ensure all values are strings to avoid PyArrow issues
    for key, value in info.items():
        if not isinstance(value, str):
            info[key] = str(value)
    
    return info


def create_3d_volume_plot(data: np.ndarray, threshold: float = 0.1, opacity: float = 0.3) -> go.Figure:
    """
    Create a 3D volume rendering of the NIfTI data.
    
    Args:
        data (np.ndarray): 3D volume data
        threshold (float): Threshold for volume rendering
        opacity (float): Opacity of the volume
        
    Returns:
        go.Figure: Plotly figure object
    """
    if data is None or data.size == 0:
        return go.Figure()
    
    # Normalize data to 0-1 range
    data_min, data_max = np.min(data), np.max(data)
    if data_max > data_min:
        data_norm = (data - data_min) / (data_max - data_min)
    else:
        data_norm = np.zeros_like(data)
    
    # For sparse data, also try a different approach with scatter3d
    non_zero_mask = data > 0
    if np.sum(non_zero_mask) < data.size * 0.01:  # Less than 1% non-zero
        # Use scatter3d for very sparse data
        coords = np.where(non_zero_mask)
        values = data[non_zero_mask]
        
        # Normalize values for color mapping
        if len(values) > 0:
            val_norm = (values - np.min(values)) / (np.max(values) - np.min(values))
        else:
            val_norm = values
        
        fig = go.Figure(data=go.Scatter3d(
            x=coords[0],
            y=coords[1],
            z=coords[2],
            mode='markers',
            marker=dict(
                size=2,
                color=val_norm,
                colorscale='Viridis',
                opacity=opacity,
                showscale=True
            ),
            text=[f'Value: {v:.3f}' for v in values],
            hovertemplate='X: %{x}<br>Y: %{y}<br>Z: %{z}<br>Value: %{text}<extra></extra>'
        ))
        
        fig.update_layout(
            title="3D Volume Rendering (Sparse Data)",
            scene=dict(
                xaxis_title="X",
                yaxis_title="Y",
                zaxis_title="Z",
                aspectmode="data"
            ),
            width=800,
            height=600
        )
    else:
        # Use volume rendering for dense data
        fig = go.Figure(data=go.Volume(
            x=np.arange(data.shape[0]),
            y=np.arange(data.shape[1]),
            z=np.arange(data.shape[2]),
            value=data_norm.flatten(),
            isomin=threshold,
            isomax=1.0,
            opacity=opacity,
            surface_count=20,
            colorscale='Viridis'
        ))
        
        fig.update_layout(
            title="3D Volume Rendering",
            scene=dict(
                xaxis_title="X",
                yaxis_title="Y",
                zaxis_title="Z",
                aspectmode="data"
            ),
            width=800,
            height=600
        )
    
    return fig


def create_slice_plot(data: np.ndarray, slice_idx: int, orientation: str = 'axial', 
                     window: float = None, level: float = None) -> go.Figure:
    """
    Create a 2D slice visualization.
    
    Args:
        data (np.ndarray): 3D volume data
        slice_idx (int): Slice index
        orientation (str): 'axial', 'sagittal', or 'coronal'
        window (float): Window width for intensity adjustment
        level (float): Window level for intensity adjustment
        
    Returns:
        go.Figure: Plotly figure object
    """
    if data is None or data.size == 0:
        return go.Figure()
    
    # Extract slice based on orientation
    if orientation == 'axial':
        if slice_idx >= data.shape[2]:
            slice_idx = data.shape[2] - 1
        slice_data = data[:, :, slice_idx]
        x_title, y_title = "X", "Y"
    elif orientation == 'sagittal':
        if slice_idx >= data.shape[0]:
            slice_idx = data.shape[0] - 1
        slice_data = data[slice_idx, :, :]
        x_title, y_title = "Z", "Y"
    else:  # coronal
        if slice_idx >= data.shape[1]:
            slice_idx = data.shape[1] - 1
        slice_data = data[:, slice_idx, :]
        x_title, y_title = "X", "Z"
    
    # Apply window/level if provided
    if window is not None and level is not None:
        min_val = level - window / 2
        max_val = level + window / 2
        slice_data = np.clip(slice_data, min_val, max_val)
        slice_data = (slice_data - min_val) / (max_val - min_val)
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=slice_data,
        colorscale='Gray',
        showscale=True
    ))
    
    fig.update_layout(
        title=f"{orientation.capitalize()} Slice {slice_idx}",
        xaxis_title=x_title,
        yaxis_title=y_title,
        width=600,
        height=600
    )
    
    return fig


def create_histogram_plot(data: np.ndarray, bins: int = 100) -> go.Figure:
    """
    Create a histogram of the intensity values.
    
    Args:
        data (np.ndarray): Volume data
        bins (int): Number of histogram bins
        
    Returns:
        go.Figure: Plotly figure object
    """
    if data is None or data.size == 0:
        return go.Figure()
    
    # Flatten data and remove zeros for better visualization
    flat_data = data.flatten()
    non_zero_data = flat_data[flat_data > 0]
    
    fig = go.Figure(data=[
        go.Histogram(
            x=non_zero_data,
            nbinsx=bins,
            name='Intensity Distribution'
        )
    ])
    
    fig.update_layout(
        title="Intensity Histogram",
        xaxis_title="Intensity Value",
        yaxis_title="Frequency",
        width=800,
        height=400
    )
    
    return fig


def calculate_window_level(data: np.ndarray, percentile: float = 99.5) -> Tuple[float, float]:
    """
    Calculate appropriate window and level for display.
    
    Args:
        data (np.ndarray): Volume data
        percentile (float): Percentile for window calculation
        
    Returns:
        Tuple[float, float]: (window, level)
    """
    if data is None or data.size == 0:
        return 1.0, 0.0
    
    # Calculate window and level based on data distribution
    non_zero_data = data[data > 0]
    if len(non_zero_data) == 0:
        return 1.0, 0.0
    
    level = np.percentile(non_zero_data, 50)  # Median
    window = np.percentile(non_zero_data, percentile) - np.percentile(non_zero_data, 100 - percentile)
    
    return window, level


def export_nifti_data(img: nib.Nifti1Image, format: str = "nifti") -> bytes:
    """
    Export NIfTI data in the specified format.
    
    Args:
        img (nib.Nifti1Image): NIfTI image object
        format (str): Export format (nifti, npy)
        
    Returns:
        bytes: Exported data
    """
    if img is None:
        return b""
    
    try:
        if format == "nifti":
            # Save to bytes
            with tempfile.NamedTemporaryFile(suffix='.nii.gz', delete=False) as tmp_file:
                nib.save(img, tmp_file.name)
                with open(tmp_file.name, 'rb') as f:
                    data = f.read()
                os.unlink(tmp_file.name)
                return data
        elif format == "npy":
            return img.get_fdata().tobytes()
        else:
            return b""
    except Exception as e:
        st.error(f"Error exporting data: {e}")
        return b""


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="NIfTI Viewer",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🧠 NIfTI File Viewer")
    st.markdown("Interactive 3D visualization and analysis of NIfTI medical imaging files")
    
    # Sidebar for file upload and controls
    st.sidebar.header("File Upload")
    
    # File upload
    uploaded_file = st.sidebar.file_uploader(
        "Choose a NIfTI file",
        type=['nii', 'nii.gz'],
        help="Upload a NIfTI file to view and analyze"
    )
    
    # Preload the default file
    default_file = "/Users/dave/AI/HPE/HPE-Nvidia-Vista-3D/output.mesh/left_iliac_artery.nii.gz"
    
    # Load from existing files
    st.sidebar.header("Load Files")
    
    # Check if default file exists and load it
    if os.path.exists(default_file):
        file_to_load = default_file
        st.sidebar.success(f"✅ Preloaded: {os.path.basename(default_file)}")
    else:
        file_to_load = None
        st.sidebar.error(f"❌ Default file not found: {default_file}")
    
    # Optional: Load different file
    st.sidebar.subheader("Load Different File")
    file_path_input = st.sidebar.text_input(
        "Enter different NIfTI file path:",
        placeholder="/path/to/your/file.nii.gz",
        help="Enter the full path to a different NIfTI file",
        key="file_path_input"
    )
    
    if file_path_input and os.path.exists(file_path_input):
        file_to_load = file_path_input
        st.sidebar.success(f"✅ Loaded: {os.path.basename(file_path_input)}")
    elif file_path_input:
        st.sidebar.error(f"❌ File not found: {file_path_input}")
    
    # Load image
    img = None
    if uploaded_file is not None:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.nii.gz') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name
        
        img = load_nifti_file(tmp_file_path)
        
        # Clean up temporary file
        os.unlink(tmp_file_path)
        
    elif file_to_load is not None:
        img = load_nifti_file(file_to_load)
    
    # Visualization controls
    st.sidebar.header("Visualization Controls")
    view_mode = st.sidebar.selectbox(
        "View Mode",
        ["3D Volume", "2D Slices", "Histogram", "All"],
        help="Choose how to display the volume"
    )
    
    # Volume rendering controls
    if view_mode in ["3D Volume", "All"]:
        st.sidebar.subheader("3D Volume Controls")
        
        # Calculate appropriate threshold based on data
        if img is not None:
            data = img.get_fdata()
            data_min, data_max = np.min(data), np.max(data)
            data_range = data_max - data_min
            # Use a lower threshold - 1% of the data range
            suggested_threshold = max(0.01, (data_min + 0.01 * data_range - data_min) / (data_max - data_min))
        else:
            suggested_threshold = 0.01
        
        threshold = st.sidebar.slider(
            "Volume Threshold",
            min_value=0.0,
            max_value=1.0,
            value=float(suggested_threshold),
            step=0.001,
            help="Threshold for volume rendering (lower values show more data)"
        )
        
        volume_opacity = st.sidebar.slider(
            "Volume Opacity",
            min_value=0.1,
            max_value=1.0,
            value=0.7,
            step=0.1,
            help="Opacity of the volume rendering"
        )
        
        # Show data statistics for threshold adjustment
        if img is not None:
            st.sidebar.caption(f"Data range: {data_min:.3f} to {data_max:.3f}")
            st.sidebar.caption(f"Suggested threshold: {suggested_threshold:.3f}")
            
            # Add buttons for quick threshold adjustment
            col1, col2 = st.sidebar.columns(2)
            with col1:
                if st.button("Auto Threshold", key="auto_thresh"):
                    st.rerun()
            with col2:
                if st.button("Show All", key="show_all"):
                    st.rerun()
    
    # Slice viewing controls
    if view_mode in ["2D Slices", "All"]:
        st.sidebar.subheader("2D Slice Controls")
        orientation = st.sidebar.selectbox(
            "Slice Orientation",
            ["axial", "sagittal", "coronal"],
            help="Choose slice orientation"
        )
        
        auto_window_level = st.sidebar.checkbox(
            "Auto Window/Level",
            value=True,
            help="Automatically calculate window and level"
        )
        
        if not auto_window_level:
            window = st.sidebar.number_input(
                "Window Width",
                min_value=0.0,
                value=1000.0,
                step=10.0,
                help="Window width for intensity adjustment"
            )
            
            level = st.sidebar.number_input(
                "Window Level",
                value=500.0,
                step=10.0,
                help="Window level for intensity adjustment"
            )
        else:
            window, level = None, None
    
    # Main content area
    if img is not None:
        data = img.get_fdata()
        
        # Show current file info
        if file_to_load:
            if file_to_load == default_file:
                st.success(f"📁 Preloaded: {os.path.basename(file_to_load)}")
            else:
                st.success(f"📁 Loaded: {file_to_load}")
        elif uploaded_file:
            st.success(f"📁 Uploaded: {uploaded_file.name}")
        
        # Display image information
        st.header("Image Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            img_info = get_nifti_info(img)
            info_df = pd.DataFrame(list(img_info.items()), columns=['Property', 'Value'])
            st.dataframe(info_df, use_container_width=True)
        
        with col2:
            # Quick stats
            st.metric("Shape", f"{data.shape}")
            st.metric("Data Type", str(data.dtype))
            st.metric("Min Value", f"{np.min(data):.3f}")
            st.metric("Max Value", f"{np.max(data):.3f}")
            st.metric("Mean Value", f"{np.mean(data):.3f}")
            st.metric("Non-zero Voxels", f"{np.count_nonzero(data):,}")
        
        # 3D Volume Visualization
        if view_mode in ["3D Volume", "All"]:
            st.header("3D Volume Rendering")
            
            fig_3d = create_3d_volume_plot(data, threshold=threshold, opacity=volume_opacity)
            st.plotly_chart(fig_3d, use_container_width=True)
        
        # 2D Slice Visualization
        if view_mode in ["2D Slices", "All"]:
            st.header("2D Slice Viewer")
            
            # Calculate appropriate slice range
            if orientation == 'axial':
                max_slices = data.shape[2]
            elif orientation == 'sagittal':
                max_slices = data.shape[0]
            else:  # coronal
                max_slices = data.shape[1]
            
            # Slice selector
            col1, col2 = st.columns([3, 1])
            
            with col1:
                slice_idx = st.slider(
                    f"Select {orientation.capitalize()} Slice",
                    min_value=0,
                    max_value=max_slices - 1,
                    value=max_slices // 2,
                    help=f"Choose slice to display (0 to {max_slices - 1})"
                )
            
            with col2:
                if st.button("Center Slice"):
                    slice_idx = max_slices // 2
            
            # Calculate window/level if auto
            if auto_window_level:
                window, level = calculate_window_level(data)
                st.info(f"Auto Window/Level: Window={window:.1f}, Level={level:.1f}")
            
            # Create slice plot
            fig_slice = create_slice_plot(data, slice_idx, orientation, window, level)
            st.plotly_chart(fig_slice, use_container_width=True)
            
            # Show slice statistics
            if orientation == 'axial':
                slice_data = data[:, :, slice_idx]
            elif orientation == 'sagittal':
                slice_data = data[slice_idx, :, :]
            else:  # coronal
                slice_data = data[:, slice_idx, :]
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Slice Min", f"{np.min(slice_data):.3f}")
            with col2:
                st.metric("Slice Max", f"{np.max(slice_data):.3f}")
            with col3:
                st.metric("Slice Mean", f"{np.mean(slice_data):.3f}")
            with col4:
                st.metric("Non-zero Pixels", f"{np.count_nonzero(slice_data):,}")
        
        # Histogram
        if view_mode in ["Histogram", "All"]:
            st.header("Intensity Histogram")
            
            fig_hist = create_histogram_plot(data)
            st.plotly_chart(fig_hist, use_container_width=True)
        
        # Export options
        st.header("Export Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Export as NIfTI"):
                nifti_data = export_nifti_data(img, "nifti")
                if nifti_data:
                    st.download_button(
                        label="Download NIfTI",
                        data=nifti_data,
                        file_name="volume.nii.gz",
                        mime="application/octet-stream"
                    )
        
        with col2:
            if st.button("Export as NumPy"):
                npy_data = export_nifti_data(img, "npy")
                if npy_data:
                    st.download_button(
                        label="Download NumPy",
                        data=npy_data,
                        file_name="volume.npy",
                        mime="application/octet-stream"
                    )
        
        with col3:
            if st.button("Convert to Mesh"):
                st.info("Use the voxel2mesh.py script to convert this NIfTI file to a 3D mesh")
                st.code(f"python voxel2mesh.py {file_to_load if file_to_load else 'uploaded_file.nii.gz'}")
        
        # Advanced analysis
        st.header("Advanced Analysis")
        
        if st.checkbox("Show Volume Statistics"):
            # Calculate additional statistics
            non_zero_data = data[data > 0]
            if len(non_zero_data) > 0:
                stats = {
                    "Volume (voxels)": f"{len(non_zero_data):,}",
                    "Volume (mm³)": f"{len(non_zero_data) * np.prod(img.header.get_zooms()):.2f}",
                    "Density": f"{len(non_zero_data) / data.size * 100:.2f}%",
                    "25th Percentile": f"{np.percentile(non_zero_data, 25):.3f}",
                    "75th Percentile": f"{np.percentile(non_zero_data, 75):.3f}",
                    "95th Percentile": f"{np.percentile(non_zero_data, 95):.3f}",
                    "99th Percentile": f"{np.percentile(non_zero_data, 99):.3f}"
                }
                
                stats_df = pd.DataFrame(list(stats.items()), columns=['Statistic', 'Value'])
                st.dataframe(stats_df, use_container_width=True)
    
    else:
        st.info("👆 The default file should be preloaded automatically. If not, please check the sidebar or upload a file.")
        
        # Show example usage
        st.subheader("How to Use")
        st.markdown("""
        **Default File (Preloaded)**
        - The `left_iliac_artery.nii.gz` file is automatically loaded when you start the viewer
        
        **Option 1: Upload a different file**
        - Use the file uploader above to select a different NIfTI file from your computer
        
        **Option 2: Load from file path**
        - Enter the full path to a different NIfTI file in the sidebar
        - The default file will be replaced with your new file
        
        **Option 3: Drag and drop**
        - Drag a NIfTI file directly onto the upload area
        """)


if __name__ == "__main__":
    main()
