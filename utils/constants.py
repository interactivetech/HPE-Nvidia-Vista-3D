"""
Constants for the Vista3D application.
Centralized location for all magic strings, numbers, and configuration values.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# File extensions
NIFTI_EXTENSIONS = ('.nii', '.nii.gz')
DICOM_EXTENSIONS = ('.dcm',)
IMAGE_EXTENSIONS = NIFTI_EXTENSIONS + DICOM_EXTENSIONS

# Directory structure - get from environment variables
OUTPUT_DIR = os.getenv('OUTPUT_FOLDER', 'output')
SEGMENTS_DIR = "segments"
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
WINDOW_PRESETS = {
    "Custom": (0, 1000),
    "Standard (W:1000, L:0)": (0, 1000),
    "Soft Tissue (W:400, L:40)": (40, 400),
    "Bone (W:1500, L:300)": (300, 1500),
    "Lung (W:1500, L:-600)": (-600, 1500),
    "Air/Background (W:500, L:-1000)": (-1000, 500)
}

# Color maps available for NIfTI images
def load_colormaps():
    """Load colormap names from all JSON files, with fallback to basic set."""
    import json
    import os
    import glob
    
    try:
        # Use absolute path to avoid issues with exec() context
        current_dir = os.path.dirname(os.path.abspath(__file__))
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
MIN_FILE_SIZE_MB = 5.0  # Minimum file size in MB for processing

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
