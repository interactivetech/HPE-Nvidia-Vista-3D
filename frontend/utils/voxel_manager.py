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
            'original': 'Original (No Processing)',
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
                        # href is like "/output/PA00000002/voxels/2.5MM_ARTERIAL_3/original/"
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
            
        # Detect scan modality to filter appropriate structures
        scan_modality = self._detect_scan_modality(patient_id, filename)
            
        if voxel_mode == "All":
            # For "All" mode, return all configured labels (filtered by modality)
            available_ids = set()
            id_to_name_map = {}
            available_voxel_names = []

            for name, label_id in self.config.label_dict.items():
                if isinstance(label_id, int):
                    # Filter out inappropriate structures for brain scans
                    if scan_modality == 'brain' and not self._is_brain_relevant_structure(label_id, name):
                        continue
                        
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

            # Get names for available labels, filtered by modality
            available_voxel_names = []
            for name, label_id in self.config.label_dict.items():
                if isinstance(label_id, int) and label_id in available_ids:
                    # Filter out inappropriate structures for brain scans
                    if scan_modality == 'brain' and not self._is_brain_relevant_structure(label_id, name):
                        continue
                    available_voxel_names.append(name)

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
        
        # Default to original if no effect is selected
        if not selected_effect:
            selected_effect = 'original'

        # Detect scan modality to filter appropriate anatomical structures
        scan_modality = self._detect_scan_modality(patient_id, filename)
        
        if voxel_mode == "all":
            # For brain scans, filter out inappropriate anatomical structures
            if scan_modality == 'brain':
                # Create filtered segmentation for brain scans
                filtered_overlay = self._create_brain_filtered_overlay(
                    patient_id, filename, selected_effect, base_url
                )
                if filtered_overlay:
                    overlays = [filtered_overlay]
                else:
                    # Fallback to original if filtering fails
                    overlays = [{
                        'label_id': 'all',
                        'label_name': 'All Segmentation (Brain Filtered)' + (f' ({self.get_effect_display_name(selected_effect)})' if selected_effect else ''),
                        'url': f"{base_url}/{OUTPUT_DIR}/{patient_id}/{VOXELS_DIR}/{ct_scan_folder_name}/{selected_effect}/all.nii.gz",
                        'is_all_segmentation': True
                    }]
            else:
                # For non-brain scans, show complete segmentation
                overlays = [{
                    'label_id': 'all',
                    'label_name': 'All Segmentation' + (f' ({self.get_effect_display_name(selected_effect)})' if selected_effect else ''),
                    'url': f"{base_url}/{OUTPUT_DIR}/{patient_id}/{VOXELS_DIR}/{ct_scan_folder_name}/{selected_effect}/all.nii.gz",
                    'is_all_segmentation': True
                }]

        elif voxel_mode == "individual_voxels" and selected_voxels:
            # Show individual voxels from selection, filtered by modality
            for voxel_name in selected_voxels:
                if voxel_name in self.config.label_dict:
                    label_id = self.config.label_dict[voxel_name]
                    
                    # Filter out inappropriate structures for brain scans
                    if scan_modality == 'brain' and not self._is_brain_relevant_structure(label_id, voxel_name):
                        continue

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
            # No individual voxels selected, show base segmentation with modality filtering
            if scan_modality == 'brain':
                # For brain scans, show only brain-relevant structures
                brain_structures = self._get_brain_relevant_structures()
                for structure_name in brain_structures:
                    if structure_name in self.config.label_dict:
                        label_id = self.config.label_dict[structure_name]
                        voxel_filename = structure_name.lower().replace(' ', '_').replace('-', '_') + '.nii.gz'
                        label_color = self.config.get_label_color(label_id)
                        
                        overlays.append({
                            'label_id': label_id,
                            'label_name': structure_name + (f' ({self.get_effect_display_name(selected_effect)})' if selected_effect else ''),
                            'url': f"{base_url}/{OUTPUT_DIR}/{patient_id}/{VOXELS_DIR}/{ct_scan_folder_name}/{selected_effect}/{voxel_filename}",
                            'color': label_color
                        })
            else:
                # For non-brain scans, show base segmentation
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

    def _detect_scan_modality(self, patient_id: str, filename: str) -> str:
        """
        Detect if this is a brain scan based on filename patterns and metadata.
        Returns 'brain' for brain scans, 'body' for other scans.
        """
        if not filename:
            return 'body'
            
        # Check filename for brain-related patterns
        filename_lower = filename.lower()
        brain_keywords = ['brain', 'mri', 't1', 't2', 'flair', 'dwi', 'adc', 'swi', 'gre', 'irspgr']
        
        for keyword in brain_keywords:
            if keyword in filename_lower:
                return 'brain'
        
        # Check metadata if available
        try:
            import os
            import json
            from .constants import OUTPUT_FOLDER_ABS
            
            base_filename = filename.replace('.nii.gz', '').replace('.nii', '')
            metadata_file = os.path.join(OUTPUT_FOLDER_ABS, patient_id, "nifti", f"{base_filename}.json")
            
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                # Check modality
                modality = metadata.get('Modality', '').upper()
                if modality == 'MR':
                    return 'brain'
                    
                # Check study description
                study_desc = metadata.get('StudyDescription', '').lower()
                if any(keyword in study_desc for keyword in ['brain', 'head', 'skull', 'cranial']):
                    return 'brain'
                    
        except Exception:
            pass  # Fall back to filename-based detection
        
        return 'body'

    def _is_brain_relevant_structure(self, label_id: int, structure_name: str) -> bool:
        """
        Check if a structure is relevant for brain imaging.
        Returns True for brain-relevant structures, False for body structures.
        """
        # Brain-relevant structures (based on label IDs and names)
        brain_relevant_ids = {
            22,  # brain
            120, # skull
            121, # spinal cord
            57,  # trachea (upper part)
            115, # heart (for brain-heart connection studies)
            125, # superior vena cava (for brain blood flow)
            126, # thyroid gland (for brain-thyroid studies)
        }
        
        brain_relevant_names = [
            'brain', 'skull', 'spinal cord', 'trachea', 'heart', 
            'superior vena cava', 'thyroid gland', 'airway'
        ]
        
        # Check by label ID
        if label_id in brain_relevant_ids:
            return True
            
        # Check by structure name
        structure_lower = structure_name.lower()
        if any(name in structure_lower for name in brain_relevant_names):
            return True
            
        return False

    def _get_brain_relevant_structures(self) -> List[str]:
        """
        Get list of brain-relevant anatomical structures.
        """
        brain_structures = []
        
        for label_info in self.config.label_colors:
            label_id = label_info.get('id')
            label_name = label_info.get('name', '')
            
            if self._is_brain_relevant_structure(label_id, label_name):
                brain_structures.append(label_name)
                
        return brain_structures

    def _create_brain_filtered_overlay(self, patient_id: str, filename: str, selected_effect: str, base_url: str) -> Optional[Dict[str, Any]]:
        """
        Create a filtered overlay that only shows brain-relevant structures.
        For brain scans where Vista3D has misclassified structures, create a proper brain segmentation.
        """
        try:
            import os
            import nibabel as nib
            import numpy as np
            from .constants import OUTPUT_FOLDER_ABS, OUTPUT_DIR, VOXELS_DIR
            
            # Path to original segmentation
            ct_scan_folder_name = filename.replace('.nii.gz', '').replace('.nii', '')
            original_seg_path = os.path.join(
                OUTPUT_FOLDER_ABS, patient_id, VOXELS_DIR, ct_scan_folder_name, 
                selected_effect, 'all.nii.gz'
            )
            
            if not os.path.exists(original_seg_path):
                return None
                
            # Load original segmentation
            original_img = nib.load(original_seg_path)
            data = original_img.get_fdata()
            
            # For brain scans, Vista3D often misclassifies structures
            # Create a proper brain segmentation by identifying the largest connected component
            # and treating it as brain tissue
            filtered_data = np.zeros_like(data)
            
            # Check if we have proper brain segmentation (label 22)
            brain_mask = (data == 22)
            brain_voxels = np.count_nonzero(brain_mask)
            
            if brain_voxels > 1000:  # If brain segmentation is reasonable
                # Use the existing brain segmentation
                filtered_data[brain_mask] = 22
            else:
                # Vista3D has misclassified - create brain segmentation from largest structure
                # Find the largest non-background connected component
                from scipy import ndimage
                
                # Get all non-zero labels
                non_zero_mask = (data > 0)
                if np.any(non_zero_mask):
                    # Label connected components
                    labeled_array, num_features = ndimage.label(non_zero_mask)
                    
                    if num_features > 0:
                        # Find the largest component
                        component_sizes = [np.count_nonzero(labeled_array == i) for i in range(1, num_features + 1)]
                        largest_component = np.argmax(component_sizes) + 1
                        
                        # Use the largest component as brain tissue
                        brain_mask = (labeled_array == largest_component)
                        filtered_data[brain_mask] = 22  # Label as brain
                        
                        print(f"Created brain segmentation from largest component: {np.count_nonzero(brain_mask)} voxels")
            
            # Add skull if available
            skull_mask = (data == 120)
            if np.any(skull_mask):
                filtered_data[skull_mask] = 120
                print(f"Added skull segmentation: {np.count_nonzero(skull_mask)} voxels")
            
            # Add other brain-relevant structures if they exist and are reasonable
            brain_structures = self._get_brain_relevant_structures()
            for structure_name in brain_structures:
                if structure_name in self.config.label_dict:
                    label_id = self.config.label_dict[structure_name]
                    structure_mask = (data == label_id)
                    structure_voxels = np.count_nonzero(structure_mask)
                    
                    # Only include if it has a reasonable number of voxels
                    if structure_voxels > 10:  # Minimum threshold
                        filtered_data[structure_mask] = label_id
                        print(f"Added {structure_name}: {structure_voxels} voxels")
            
            # Create filtered image
            filtered_img = nib.Nifti1Image(filtered_data, original_img.affine, original_img.header)
            
            # Save filtered segmentation
            filtered_path = original_seg_path.replace('all.nii.gz', 'brain_filtered.nii.gz')
            nib.save(filtered_img, filtered_path)
            
            total_voxels = np.count_nonzero(filtered_data)
            print(f"Created brain-filtered segmentation with {total_voxels} total voxels")
            
            return {
                'label_id': 'brain_filtered',
                'label_name': 'Brain Structures Only' + (f' ({self.get_effect_display_name(selected_effect)})' if selected_effect else ''),
                'url': f"{base_url}/{OUTPUT_DIR}/{patient_id}/{VOXELS_DIR}/{ct_scan_folder_name}/{selected_effect}/brain_filtered.nii.gz",
                'is_all_segmentation': True
            }
            
        except Exception as e:
            print(f"Error creating brain filtered overlay: {e}")
            return None