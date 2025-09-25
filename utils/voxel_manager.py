"""
Voxel Manager for Vista3D Application
Handles voxel selection, overlay management, and related logic.
"""

from typing import List, Dict, Optional, Any, Set, Tuple
import os
import requests
from bs4 import BeautifulSoup
from .config_manager import ConfigManager
from .data_manager import DataManager
from .constants import OUTPUT_FOLDER_ABS, OUTPUT_DIR, VOXELS_DIR


class VoxelManager:
    """
    Manages voxel selection and overlay configuration.
    Provides a clean interface for handling different voxel display modes.
    """

    def __init__(self, config_manager: ConfigManager, data_manager: DataManager):
        self.config = config_manager
        self.data = data_manager

    def has_voxels_for_patient(self, patient_id: str) -> bool:
        """
        Check if there are any voxels available for the given patient.
        Returns True if voxels exist, False otherwise.
        """
        if not patient_id:
            return False
        
        # First try to check via image server
        try:
            voxels_folder_url = f"{self.data.image_server_url}/output/{patient_id}/voxels/"
            
            resp = requests.get(voxels_folder_url, timeout=5)
            if resp.status_code == 200:
                # Parse directory listing to see if there are any subdirectories (CT scan folders)
                soup = BeautifulSoup(resp.text, 'html.parser')
                voxel_subdirs = []
                for link in soup.find_all('a'):
                    href = link.get('href')
                    if href and not href.startswith('..') and href.endswith('/'):
                        voxel_subdirs.append(href)
                
                # Check if any of the subdirectories contain .nii.gz files
                for subdir in voxel_subdirs:
                    subdir_url = f"{voxels_folder_url}{subdir}"
                    subdir_resp = requests.get(subdir_url, timeout=5)
                    if subdir_resp.status_code == 200:
                        subdir_soup = BeautifulSoup(subdir_resp.text, 'html.parser')
                        for link in subdir_soup.find_all('a'):
                            href = link.get('href')
                            if href and href.endswith('.nii.gz') and not href.startswith('..'):
                                return True
        except Exception:
            pass  # Fall through to local filesystem check
        
        # Fallback: Check local filesystem
        try:
            voxels_folder_path = os.path.join(OUTPUT_FOLDER_ABS, patient_id, 'voxels')
            
            if not os.path.exists(voxels_folder_path):
                return False
            
            # Check if there are any subdirectories with .nii.gz files
            for item in os.listdir(voxels_folder_path):
                item_path = os.path.join(voxels_folder_path, item)
                if os.path.isdir(item_path):
                    # Check if this subdirectory contains .nii.gz files
                    for file in os.listdir(item_path):
                        if file.endswith('.nii.gz'):
                            return True
            
            return False
            
        except Exception:
            return False

    def get_available_voxels(
        self,
        patient_id: str,
        filename: str,
        voxel_mode: str
    ) -> Tuple[Set[int], Dict[int, str], List[str]]:
        """
        Get available voxel information for the given patient and file.
        Returns (available_ids, id_to_name_map, available_voxel_names).
        """
        if voxel_mode == "All":
            # For "All" mode, return all configured labels
            available_ids = set()
            id_to_name_map = {}
            available_voxel_names = []

            for name, label_id in self.config.label_dict.items():
                if isinstance(label_id, int):
                    available_ids.add(label_id)
                    id_to_name_map[label_id] = name
                    available_voxel_names.append(name)

            return available_ids, id_to_name_map, sorted(available_voxel_names)

        elif voxel_mode == "Individual Voxels":
            # Query server for actually available voxel files
            filename_to_id = self.config.create_filename_to_id_mapping()
            available_ids, id_to_name_map = self.data.fetch_available_voxel_labels(
                patient_id, filename, filename_to_id
            )

            # Get names for available labels
            available_voxel_names = [
                name for name, label_id in self.config.label_dict.items()
                if isinstance(label_id, int) and label_id in available_ids
            ]

            return available_ids, id_to_name_map, sorted(available_voxel_names)

        return set(), {}, []

    def create_overlays(
        self,
        patient_id: str,
        filename: str,
        voxel_mode: str,
        selected_voxels: Optional[List[str]] = None,
        external_url: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Create overlay configuration based on voxel mode and selection.
        """
        overlays = []
        
        # Use external URL for browser access if provided, otherwise use internal URL
        base_url = external_url if external_url else self.data.image_server_url

        if voxel_mode == "all":
            # Show complete base segmentation file
            overlays = [{
                'label_id': 'all',
                'label_name': 'All Segmentation',
                'url': f"{base_url}/{OUTPUT_DIR}/{patient_id}/{VOXELS_DIR}/{filename}",
                'is_all_segmentation': True
            }]

        elif voxel_mode == "individual_voxels" and selected_voxels:
            # Show individual voxels from selection
            ct_scan_folder_name = filename.replace('.nii.gz', '').replace('.nii', '')

            for voxel_name in selected_voxels:
                if voxel_name in self.config.label_dict:
                    label_id = self.config.label_dict[voxel_name]

                    # Convert voxel name to filename format
                    voxel_filename = voxel_name.lower().replace(' ', '_').replace('-', '_') + '.nii.gz'

                    # Get color for this label
                    label_color = self.config.get_label_color(label_id)

                    overlays.append({
                        'label_id': label_id,
                        'label_name': voxel_name,
                        'url': f"{base_url}/{OUTPUT_DIR}/{patient_id}/{VOXELS_DIR}/{ct_scan_folder_name}/{voxel_filename}",
                        'color': label_color
                    })

        elif voxel_mode == "individual_voxels" and not selected_voxels:
            # No individual voxels selected, show base segmentation
            overlays = [{
                'label_id': 'all',
                'label_name': 'All Segmentation',
                'url': f"{base_url}/{OUTPUT_DIR}/{patient_id}/{VOXELS_DIR}/{filename}",
                'is_all_segmentation': True
            }]

        return overlays

    def create_custom_colormap_js(self) -> str:
        """
        Legacy method for backward compatibility.
        The colormap is now loaded directly in the HTML template from the colormap system.
        """
        return "// Vista3D voxels colormap now loaded from colormap system in HTML template"

    def get_voxel_legend_html(self) -> str:
        """Generate HTML for the voxel legend display."""
        try:
            legend_items = []
            for label_info in self.config.label_colors:
                label_name = label_info.get("name", "")
                label_id = label_info.get("id", 0)
                color_rgb = label_info.get("color", [0, 0, 0])
                color_hex = f"#{color_rgb[0]:02x}{color_rgb[1]:02x}{color_rgb[2]:02x}"

                legend_items.append(f'''
                <div style="display: flex; align-items: center; margin-bottom: 5px;">
                    <div style="width: 20px; height: 20px; background-color: {color_hex}; border: 1px solid #ccc; margin-right: 10px;"></div>
                    <span>{label_name} (ID: {label_id})</span>
                </div>''')

            return "".join(legend_items)

        except Exception as e:
            return f'<div style="color: red;">Error loading segment colors: {e}</div>'
