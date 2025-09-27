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
    """

    def __init__(self, config_manager: ConfigManager, data_manager: DataManager):
        self.config = config_manager
        self.data = data_manager
        self.effects_config = self._load_effects_config()

    def _load_effects_config(self) -> Dict[str, Any]:
        """Load effects configuration from effects.json file."""
        try:
            # Get the path to the effects config file
            script_dir = os.path.dirname(os.path.abspath(__file__))
            conf_dir = os.path.join(os.path.dirname(script_dir), 'conf')
            effects_config_path = os.path.join(conf_dir, 'effects.json')
            
            with open(effects_config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load effects config: {e}")
            return {"available_effects": [], "folder_pattern": "{scan_name}_{effect_name}"}

    def get_available_effects(self) -> List[Dict[str, Any]]:
        """Get list of available effects from configuration."""
        return self.effects_config.get("available_effects", [])

    def get_effect_names(self) -> List[str]:
        """Get list of effect names for UI selection."""
        return [effect["name"] for effect in self.get_available_effects()]

    def get_effect_display_name(self, effect_name: str) -> str:
        """Get display name for an effect."""
        for effect in self.get_available_effects():
            if effect["name"] == effect_name:
                return effect.get("display_name", effect_name)
        return effect_name

    def detect_effect_folders(self, patient_id: str, scan_name: str) -> List[str]:
        """
        Detect effect-based folders for a given patient and scan.
        Returns list of effect names that have corresponding folders.
        """
        available_effects = []
        folder_pattern = self.effects_config.get("folder_pattern", "{scan_name}_{effect_name}")
        
        # Remove .nii.gz extension from scan name if present
        clean_scan_name = scan_name.replace('.nii.gz', '').replace('.nii', '')
        
        # Check for effect folders via image server first
        try:
            voxels_folder_url = f"{self.data.image_server_url}/output/{patient_id}/voxels/"
            resp = requests.get(voxels_folder_url, timeout=5)
            
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                for link in soup.find_all('a'):
                    href = link.get('href')
                    if href and not href.startswith('..') and href.endswith('/'):
                        # Extract folder name from the full path
                        # href is like "/output/PA00000002/voxels/2.5MM_ARTERIAL_3_gaussian_smooth/"
                        folder_name = href.rstrip('/').split('/')[-1]
                        
                        # Check if this folder matches the effect pattern
                        for effect in self.get_available_effects():
                            effect_name = effect["name"]
                            expected_folder = folder_pattern.format(
                                scan_name=clean_scan_name, 
                                effect_name=effect_name
                            )
                            if folder_name == expected_folder:
                                # Verify this folder contains .nii.gz files
                                # href already contains the full path, so use it directly
                                effect_folder_url = f"{self.data.image_server_url}{href}"
                                effect_resp = requests.get(effect_folder_url, timeout=5)
                                if effect_resp.status_code == 200:
                                    effect_soup = BeautifulSoup(effect_resp.text, 'html.parser')
                                    for effect_link in effect_soup.find_all('a'):
                                        effect_href = effect_link.get('href')
                                        if effect_href and effect_href.endswith('.nii.gz') and not effect_href.startswith('..'):
                                            available_effects.append(effect_name)
                                            break
                
                return available_effects
        except Exception:
            pass  # Fall through to local filesystem check
        
        # Fallback: Check local filesystem
        try:
            voxels_folder_path = os.path.join(OUTPUT_FOLDER_ABS, patient_id, 'voxels')
            if not os.path.exists(voxels_folder_path):
                return available_effects
            
            for item in os.listdir(voxels_folder_path):
                item_path = os.path.join(voxels_folder_path, item)
                if os.path.isdir(item_path):
                    # Check if this folder matches the effect pattern
                    for effect in self.get_available_effects():
                        effect_name = effect["name"]
                        expected_folder = folder_pattern.format(
                            scan_name=clean_scan_name,
                            effect_name=effect_name
                        )
                        if item == expected_folder:
                            # Verify this folder contains .nii.gz files
                            for file in os.listdir(item_path):
                                if file.endswith('.nii.gz'):
                                    available_effects.append(effect_name)
                                    break
            
            return available_effects
        except Exception:
            return available_effects

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
        voxel_mode: str,
        selected_effect: Optional[str] = None
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
            
            # Use effect-based folder if effect is selected
            query_filename = filename
            if selected_effect:
                folder_pattern = self.effects_config.get("folder_pattern", "{scan_name}_{effect_name}")
                ct_scan_folder_name = filename.replace('.nii.gz', '').replace('.nii', '')
                effect_folder_name = folder_pattern.format(
                    scan_name=ct_scan_folder_name,
                    effect_name=selected_effect
                )
                # For effect-based folders, we need to modify the query to look in the effect folder
                # This is a bit tricky since the data manager expects a different structure
                # We'll need to pass the effect folder name to the data manager
                
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
        """
        overlays = []
        
        # Use external URL for browser access if provided, otherwise use internal URL
        base_url = external_url if external_url else self.data.image_server_url

        # Determine the folder name based on whether an effect is selected
        ct_scan_folder_name = filename.replace('.nii.gz', '').replace('.nii', '')
        if selected_effect:
            folder_pattern = self.effects_config.get("folder_pattern", "{scan_name}_{effect_name}")
            ct_scan_folder_name = folder_pattern.format(
                scan_name=ct_scan_folder_name,
                effect_name=selected_effect
            )

        if voxel_mode == "all":
            # Show complete base segmentation file stored as voxels/<scan>/all.nii.gz
            overlays = [{
                'label_id': 'all',
                'label_name': 'All Segmentation' + (f' ({self.get_effect_display_name(selected_effect)})' if selected_effect else ''),
                'url': f"{base_url}/{OUTPUT_DIR}/{patient_id}/{VOXELS_DIR}/{ct_scan_folder_name}/all.nii.gz",
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
                        'url': f"{base_url}/{OUTPUT_DIR}/{patient_id}/{VOXELS_DIR}/{ct_scan_folder_name}/{voxel_filename}",
                        'color': label_color
                    })

        elif voxel_mode == "individual_voxels" and not selected_voxels:
            # No individual voxels selected, show base segmentation
            overlays = [{
                'label_id': 'all',
                'label_name': 'All Segmentation' + (f' ({self.get_effect_display_name(selected_effect)})' if selected_effect else ''),
                'url': f"{base_url}/{OUTPUT_DIR}/{patient_id}/{VOXELS_DIR}/{ct_scan_folder_name}/all.nii.gz",
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
