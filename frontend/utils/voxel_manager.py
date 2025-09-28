"""
Voxel Manager for Vista3D Application
Handles voxel selection, overlay management, and related logic.
"""

from typing import List, Dict, Optional, Any, Set, Tuple
import os
import json
import requests
from bs4 import BeautifulSoup
from .config_manager import ConfigManager
from .data_manager import DataManager
from .constants import OUTPUT_FOLDER_ABS, OUTPUT_DIR, VOXELS_DIR


class VoxelManager:
    """
    Manages voxel selection and overlay configuration.
    Provides a clean interface for handling different voxel display modes.
    New folder structure: output/patient/voxels/scan_name/effect_name/
    """

    def __init__(self, config_manager: ConfigManager, data_manager: DataManager):
        self.config = config_manager
        self.data = data_manager

    def get_effect_display_name(self, effect_name: str) -> str:
        """Get display name for an effect."""
        # Convert effect name to display name
        display_names = {
            'no_processing': 'Original (No Processing)',
            'realistic_medical': 'Realistic Medical Visualization',
            'anatomical_enhancement': 'Anatomical Structure Enhancement',
            'monai_smooth': 'Subtle Smooth',
            'ultra_smooth_medical': 'Gentle Smooth',
            'surface_refinement': 'Minimal Refinement',
            'texture_enhancement': 'Minimal Enhancement',
            'realistic_rendering': 'Minimal Rendering',
            'ultra_realistic_anatomy': 'Ultra-Realistic Anatomy',
            'photorealistic_organs': 'Photorealistic Organs',
            'medical_grade_rendering': 'Medical-Grade Rendering'
        }
        return display_names.get(effect_name, effect_name.replace('_', ' ').title())

    def detect_effect_folders(self, patient_id: str, scan_name: str) -> List[str]:
        """
        Detect effect-based folders for a given patient and scan.
        Returns list of effect names that have corresponding folders.
        New structure: output/patient/voxels/scan_name/effect_name/
        """
        available_effects = []
        
        # Return empty list if scan_name is None
        if scan_name is None:
            return available_effects
            
        # Remove .nii.gz extension from scan name if present
        clean_scan_name = scan_name.replace('.nii.gz', '').replace('.nii', '')
        
        # Check for effect folders via image server first
        try:
            # New structure: /output/patient/voxels/scan_name/
            scan_voxels_folder_url = f"{self.data.image_server_url}/output/{patient_id}/voxels/{clean_scan_name}/"
            resp = requests.get(scan_voxels_folder_url, timeout=5)
            
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                for link in soup.find_all('a'):
                    href = link.get('href')
                    if href and not href.startswith('..') and href.endswith('/'):
                        # Extract effect folder name from the full path
                        # href is like "/output/PA00000002/voxels/2.5MM_ARTERIAL_3/no_processing/"
                        effect_folder_name = href.rstrip('/').split('/')[-1]
                        
                        # Verify this folder contains .nii.gz files
                        effect_folder_url = f"{self.data.image_server_url}{href}"
                        effect_resp = requests.get(effect_folder_url, timeout=5)
                        if effect_resp.status_code == 200:
                            effect_soup = BeautifulSoup(effect_resp.text, 'html.parser')
                            for effect_link in effect_soup.find_all('a'):
                                effect_href = effect_link.get('href')
                                if effect_href and effect_href.endswith('.nii.gz') and not effect_href.startswith('..'):
                                    available_effects.append(effect_folder_name)
                                    break
                
                return available_effects
        except Exception:
            pass  # Fall through to local filesystem check
        
        # Fallback: Check local filesystem
        try:
            # New structure: output/patient/voxels/scan_name/
            scan_voxels_folder_path = os.path.join(OUTPUT_FOLDER_ABS, patient_id, 'voxels', clean_scan_name)
            if not os.path.exists(scan_voxels_folder_path):
                return available_effects
            
            for item in os.listdir(scan_voxels_folder_path):
                item_path = os.path.join(scan_voxels_folder_path, item)
                if os.path.isdir(item_path):
                    # Check if this folder contains .nii.gz files
                    for file in os.listdir(item_path):
                        if file.endswith('.nii.gz'):
                            available_effects.append(item)
                            break
            
            return available_effects
        except Exception:
            return available_effects

    def has_voxels_for_patient(self, patient_id: str) -> bool:
        """
        Check if there are any voxels available for the given patient.
        Returns True if voxels exist, False otherwise.
        New structure: output/patient/voxels/scan_name/effect_name/
        """
        if not patient_id:
            return False
        
        # First try to check via image server
        try:
            voxels_folder_url = f"{self.data.image_server_url}/output/{patient_id}/voxels/"
            
            resp = requests.get(voxels_folder_url, timeout=5)
            if resp.status_code == 200:
                # Parse directory listing to see if there are any scan subdirectories
                soup = BeautifulSoup(resp.text, 'html.parser')
                scan_subdirs = []
                for link in soup.find_all('a'):
                    href = link.get('href')
                    if href and not href.startswith('..') and href.endswith('/'):
                        scan_subdirs.append(href)
                
                # Check if any of the scan subdirectories contain effect subdirectories with .nii.gz files
                for scan_subdir in scan_subdirs:
                    scan_url = f"{self.data.image_server_url}{scan_subdir}"
                    scan_resp = requests.get(scan_url, timeout=5)
                    if scan_resp.status_code == 200:
                        scan_soup = BeautifulSoup(scan_resp.text, 'html.parser')
                        for link in scan_soup.find_all('a'):
                            href = link.get('href')
                            if href and not href.startswith('..') and href.endswith('/'):
                                # This is an effect subdirectory, check if it contains .nii.gz files
                                effect_url = f"{self.data.image_server_url}{href}"
                                effect_resp = requests.get(effect_url, timeout=5)
                                if effect_resp.status_code == 200:
                                    effect_soup = BeautifulSoup(effect_resp.text, 'html.parser')
                                    for effect_link in effect_soup.find_all('a'):
                                        effect_href = effect_link.get('href')
                                        if effect_href and effect_href.endswith('.nii.gz') and not effect_href.startswith('..'):
                                            return True
        except Exception:
            pass  # Fall through to local filesystem check
        
        # Fallback: Check local filesystem
        try:
            voxels_folder_path = os.path.join(OUTPUT_FOLDER_ABS, patient_id, 'voxels')
            
            if not os.path.exists(voxels_folder_path):
                return False
            
            # Check if there are any scan subdirectories with effect subdirectories containing .nii.gz files
            for scan_item in os.listdir(voxels_folder_path):
                scan_path = os.path.join(voxels_folder_path, scan_item)
                if os.path.isdir(scan_path):
                    # This is a scan directory, check for effect subdirectories
                    for effect_item in os.listdir(scan_path):
                        effect_path = os.path.join(scan_path, effect_item)
                        if os.path.isdir(effect_path):
                            # Check if this effect directory contains .nii.gz files
                            for file in os.listdir(effect_path):
                                if file.endswith('.nii.gz'):
                                    return True
            
            return False
            
        except Exception:
            return False

    def get_available_voxels(
        self,
        patient_id: str,
        filename: str,
        voxel_mode: str,
        selected_effect: Optional[str] = None
    ) -> Tuple[Set[int], Dict[int, str], List[str]]:
        """
        Get available voxel information for the given patient and file.
        Returns (available_ids, id_to_name_map, available_voxel_names).
        """
        # Return empty results if filename is None
        if filename is None:
            return set(), {}, []
            
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
            
            # Use effect-based folder if effect is selected
            query_filename = filename
            if selected_effect:
                # For new structure, we need to modify the query to look in the effect folder
                # This is handled by the data manager's fetch_available_voxel_labels method
                pass
                
            available_ids, id_to_name_map = self.data.fetch_available_voxel_labels(
                patient_id, query_filename, filename_to_id, selected_effect
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
        external_url: Optional[str] = None,
        selected_effect: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Create overlay configuration based on voxel mode and selection.
        New structure: output/patient/voxels/scan_name/effect_name/
        """
        overlays = []
        
        # Return empty list if filename is None
        if filename is None:
            return overlays
        
        # Use external URL for browser access if provided, otherwise use internal URL
        base_url = external_url if external_url else self.data.image_server_url

        # Determine the folder structure based on whether an effect is selected
        ct_scan_folder_name = filename.replace('.nii.gz', '').replace('.nii', '')
        
        # Default to no_processing if no effect is selected
        if not selected_effect:
            selected_effect = 'no_processing'

        if voxel_mode == "all":
            # Show complete base segmentation file stored as voxels/scan_name/effect_name/all.nii.gz
            overlays = [{
                'label_id': 'all',
                'label_name': 'All Segmentation' + (f' ({self.get_effect_display_name(selected_effect)})' if selected_effect else ''),
                'url': f"{base_url}/{OUTPUT_DIR}/{patient_id}/{VOXELS_DIR}/{ct_scan_folder_name}/{selected_effect}/all.nii.gz",
                'is_all_segmentation': True
            }]

        elif voxel_mode == "individual_voxels" and selected_voxels:
            # Show individual voxels from selection

            for voxel_name in selected_voxels:
                if voxel_name in self.config.label_dict:
                    label_id = self.config.label_dict[voxel_name]

                    # Convert voxel name to filename format
                    voxel_filename = voxel_name.lower().replace(' ', '_').replace('-', '_') + '.nii.gz'

                    # Get color for this label
                    label_color = self.config.get_label_color(label_id)

                    overlays.append({
                        'label_id': label_id,
                        'label_name': voxel_name + (f' ({self.get_effect_display_name(selected_effect)})' if selected_effect else ''),
                        'url': f"{base_url}/{OUTPUT_DIR}/{patient_id}/{VOXELS_DIR}/{ct_scan_folder_name}/{selected_effect}/{voxel_filename}",
                        'color': label_color
                    })

        elif voxel_mode == "individual_voxels" and not selected_voxels:
            # No individual voxels selected, show base segmentation
            overlays = [{
                'label_id': 'all',
                'label_name': 'All Segmentation' + (f' ({self.get_effect_display_name(selected_effect)})' if selected_effect else ''),
                'url': f"{base_url}/{OUTPUT_DIR}/{patient_id}/{VOXELS_DIR}/{ct_scan_folder_name}/{selected_effect}/all.nii.gz",
                'is_all_segmentation': True
            }]

        return overlays

    def create_custom_colormap_js(self) -> str:
        """Generate JavaScript for custom segmentation colormap."""
        try:
            label_colors_list = self.config.label_colors
            if not label_colors_list:
                return ""

            r_values, g_values, b_values, a_values, labels = [0]*256, [0]*256, [0]*256, [0]*256, [""]*256
            r_values[0], g_values[0], b_values[0], a_values[0], labels[0] = 0, 0, 0, 0, "Background"

            max_id = 0
            for item in label_colors_list:
                idx = item.get('id', 0)
                label_name = item.get('name', '')
                color = item.get('color', [0, 0, 0])

                if 0 <= idx < 256:
                    r_values[idx] = color[0]
                    g_values[idx] = color[1]
                    b_values[idx] = color[2]
                    a_values[idx] = 255
                    labels[idx] = label_name

                if idx > max_id:
                    max_id = idx

            # Trim arrays to max_id + 1
            r_values = r_values[:max_id+1]
            g_values = g_values[:max_id+1]
            b_values = b_values[:max_id+1]
            a_values = a_values[:max_id+1]
            labels = labels[:max_id+1]

            # Format labels for JavaScript
            js_labels = []
            for label in labels:
                escaped_label = label.replace('"', '\\"')
                js_labels.append(f'"{escaped_label}"')
            labels_string = ",".join(js_labels)

            return f"""
            const customSegmentationColormap = {{
                R: [{",".join(map(str, r_values))}],
                G: [{",".join(map(str, g_values))}],
                B: [{",".join(map(str, b_values))}],
                A: [{",".join(map(str, a_values))}],
                labels: [{labels_string}]
            }};
            console.log('Vista3D colormap loaded from vista3d_label_colors.json:', customSegmentationColormap);
            """

        except Exception as e:
            print(f"Error creating custom colormap: {e}")
            return ""

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