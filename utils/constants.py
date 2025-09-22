"""
Constants for the Vista3D application.
Centralized location for all magic strings, numbers, and configuration values.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# PROJECT_ROOT is no longer needed - all paths should be full paths from .env

# File extensions
NIFTI_EXTENSIONS = ('.nii', '.nii.gz')
DICOM_EXTENSIONS = ('.dcm',)
IMAGE_EXTENSIONS = NIFTI_EXTENSIONS + DICOM_EXTENSIONS

# Directory structure - get from environment variables
OUTPUT_DIR = os.getenv('OUTPUT_FOLDER')
if not OUTPUT_DIR:
    raise ValueError("OUTPUT_FOLDER must be set in .env file with absolute path")
if not os.path.isabs(OUTPUT_DIR):
    raise ValueError("OUTPUT_FOLDER must be set in .env file with absolute path")
VOXELS_DIR = "voxels"
NIFTI_DIR = "nifti"

# Viewer settings defaults
DEFAULT_VIEWER_SETTINGS = {
    'slice_type': 'Multiplanar',
    'orientation': 'Axial',
    'color_map': 'gray',
    'nifti_opacity': 0.5,
    'nifti_gamma': 1.0,
    'show_nifti': True,
    'show_overlay': False,
    'segment_opacity': 0.5,
    'segment_gamma': 1.0,
    'window_center': 0,
    'window_width': 1000,
}

# Slice type mappings
SLICE_TYPE_MAP = {
    "Axial": 0,
    "Coronal": 1,
    "Sagittal": 2,
    "Multiplanar": 3,
    "3D Render": 4
}

# Window presets for CT imaging
WINDOW_PRESETS_CT = {
    "Custom": (0, 1000),
    "Standard (W:1000, L:0)": (0, 1000),
    "Soft Tissue (W:400, L:40)": (40, 400),
    "Bone (W:1500, L:300)": (300, 1500),
    "Lung (W:1500, L:-600)": (-600, 1500),
    "Air/Background (W:500, L:-1000)": (-1000, 500)
}

# Window presets for MRI imaging
WINDOW_PRESETS_MRI = {
    "Custom": (360, 720),
    "Standard (W:720, L:360)": (360, 720),
    "T1 Weighted (W:500, L:250)": (250, 500),
    "T2 Weighted (W:800, L:400)": (400, 800),
    "High Contrast (W:300, L:150)": (150, 300),
    "Low Contrast (W:1000, L:500)": (500, 1000)
}

# Combined window presets (legacy support)
WINDOW_PRESETS = WINDOW_PRESETS_CT.copy()
WINDOW_PRESETS.update(WINDOW_PRESETS_MRI)

# Default window settings by modality
DEFAULT_WINDOW_SETTINGS = {
    'CT': {'window_center': 0, 'window_width': 1000},
    'MRI': {'window_center': 360, 'window_width': 720}
}

def detect_modality_from_data(min_value: float, max_value: float, mean_value: float) -> str:
    """
    Detect imaging modality based on data characteristics.
    
    Args:
        min_value: Minimum pixel value in the dataset
        max_value: Maximum pixel value in the dataset  
        mean_value: Mean pixel value in the dataset
        
    Returns:
        'CT' or 'MRI' based on data characteristics
    """
    # CT scans typically have negative values (HU scale) and wider dynamic range
    # MRI scans typically have positive values and smaller dynamic range
    dynamic_range = max_value - min_value
    
    # CT characteristics: negative values, wide dynamic range (>1000)
    if min_value < -100 and dynamic_range > 1000:
        return 'CT'
    # MRI characteristics: positive values, smaller dynamic range (<1000)
    elif min_value >= 0 and dynamic_range < 1000:
        return 'MRI'
    # Default fallback based on mean value
    elif mean_value < 0:
        return 'CT'
    else:
        return 'MRI'

def get_optimal_window_settings(min_value: float, max_value: float, mean_value: float) -> tuple:
    """
    Get optimal window center and width based on data characteristics.
    
    Args:
        min_value: Minimum pixel value in the dataset
        max_value: Maximum pixel value in the dataset
        mean_value: Mean pixel value in the dataset
        
    Returns:
        Tuple of (window_center, window_width)
    """
    modality = detect_modality_from_data(min_value, max_value, mean_value)
    
    if modality == 'CT':
        # For CT, use standard windowing around mean
        window_center = mean_value
        window_width = max(1000, (max_value - min_value) * 0.8)
    else:  # MRI
        # For MRI, center around mean with appropriate width
        window_center = mean_value
        window_width = min(800, (max_value - min_value) * 0.6)
    
    return int(window_center), int(window_width)

# Color maps available for NIfTI images
def load_colormaps():
    """Load colormap names in a specific order from configuration file."""
    import json
    import os
    import glob
    
    try:
        # First, try to load the colormap order configuration
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_file = os.path.join(current_dir, '..', 'conf', 'colormap_order.json')
        config_file = os.path.abspath(config_file)
        
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
                if 'colormap_order' in config:
                    # Get all available colormaps from the JSON files
                    colormaps_dir = os.path.join(current_dir, '..', 'assets', 'colormaps')
                    colormaps_dir = os.path.abspath(colormaps_dir)
                    
                    colormap_files = glob.glob(os.path.join(colormaps_dir, '*.json'))
                    
                    available_colormaps = set()
                    for colormap_file in colormap_files:
                        try:
                            with open(colormap_file, 'r') as cf:
                                data = json.load(cf)
                                if 'colormaps' in data and isinstance(data['colormaps'], dict):
                                    available_colormaps.update(data['colormaps'].keys())
                        except (json.JSONDecodeError, KeyError) as e:
                            print(f"Warning: Could not load colormaps from {colormap_file}: {e}")
                            continue
                    
                    # Filter the ordered list to only include available colormaps
                    ordered_colormaps = []
                    for colormap in config['colormap_order']:
                        if colormap in available_colormaps:
                            ordered_colormaps.append(colormap)
                    
                    # Add any available colormaps not in the order list
                    for colormap in available_colormaps:
                        if colormap not in ordered_colormaps:
                            ordered_colormaps.append(colormap)
                    
                    return ordered_colormaps if ordered_colormaps else config.get('fallback_colormaps', ['gray', 'viridis', 'plasma', 'inferno', 'magma'])
        
        # Fallback to original method if config file doesn't exist
        colormaps_dir = os.path.join(current_dir, '..', 'assets', 'colormaps')
        colormaps_dir = os.path.abspath(colormaps_dir)
        
        colormap_files = glob.glob(os.path.join(colormaps_dir, '*.json'))
        
        all_colormaps = []
        for colormap_file in colormap_files:
            try:
                with open(colormap_file, 'r') as f:
                    data = json.load(f)
                    if 'colormaps' in data and isinstance(data['colormaps'], dict):
                        # Extract colormap names from the keys
                        all_colormaps.extend(list(data['colormaps'].keys()))
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Could not load colormaps from {colormap_file}: {e}")
                continue
        
        # Remove duplicates and return
        return list(set(all_colormaps)) if all_colormaps else ['gray', 'viridis', 'plasma', 'inferno', 'magma']
        
    except Exception as e:
        print(f"Warning: Could not load colormaps from JSON files, using fallback: {e}")
        # Fallback to basic set
        return ['gray', 'viridis', 'plasma', 'inferno', 'magma']

AVAILABLE_COLOR_MAPS = load_colormaps()

# Voxel selection modes
VOXEL_MODES = ["All", "Individual Voxels"]

# Timeout settings
SERVER_TIMEOUT = 10  # seconds

# Viewer dimensions
VIEWER_HEIGHT = 1000

# UI messages
MESSAGES = {
    'no_voxels_available': "No voxels available for this patient/file.",
    'no_nifti_or_voxels': "Nothing to display. Enable 'Show NIfTI' or 'Show Voxels' with selected label sets.",
    'select_patient_file': "Select a patient and file to begin.",
    'enable_voxels': "Enable 'Show Voxels' to display overlays.",
    'no_individual_voxels_selected': "No individual voxels selected. Select specific structures to display.",
}

# Debug settings
DEBUG_MODE = False

# File size filtering
MIN_FILE_SIZE_MB = 3.5  # Minimum file size in MB for processing

# Configuration file paths
CONFIG_FILES = {
    'label_colors': 'conf/vista3d_label_colors.json',
    'label_dict': 'conf/vista3d_label_dict.json',
    'label_sets': 'conf/vista3d_label_sets.json'
}

# Template paths
TEMPLATE_FILES = {
    'viewer': 'assets/niivue_viewer.html'
}
