"""
Data Manager for Vista3D Application
Handles all server interactions and data fetching operations.
"""

import os
import re
import requests
from typing import List, Dict, Optional, Tuple, Set
from bs4 import BeautifulSoup
from .constants import SERVER_TIMEOUT


class DataManager:
    """
    Handles all interactions with the image server.
    Provides methods for fetching directory listings, files, and voxel information.
    """

    def __init__(self, image_server_url: str):
        self.image_server_url = image_server_url.rstrip('/')

    def parse_directory_listing(self, html_content: str) -> List[Dict[str, str]]:
        """Parse HTML directory listing to extract file and folder information."""
        items = []
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            for item in soup.find_all('li'):
                link = item.find('a')
                if link and link.get('href'):
                    text = link.get_text().strip()
                    if text == "📁 ../" or text.endswith('../'):
                        continue
                    is_directory = text.startswith('📁') or text.endswith('/')
                    name = re.sub(r'^📁\s*|📄\s*', '', text).strip('/')
                    items.append({'name': name, 'is_directory': is_directory})
        except Exception as e:
            print(f"Error parsing directory listing: {e}")
        return items

    def get_folder_contents(self, folder_path: str) -> Optional[List[Dict[str, str]]]:
        """Fetch contents of a specific folder from the image server."""
        url = f"{self.image_server_url}/output/{folder_path.strip('/')}/"
        try:
            response = requests.get(url, timeout=SERVER_TIMEOUT)
            if response.status_code == 200:
                return self.parse_directory_listing(response.text)
            elif response.status_code != 404:
                print(f"Image server returned HTTP {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Could not connect to image server: {e}")
        return None

    def get_server_data(self, path: str, data_type: str, file_extensions: tuple) -> List[str]:
        """Get folders or files from the server based on path and type."""
        items = self.get_folder_contents(path)
        if items is None:
            return []

        if data_type == 'folders':
            return sorted([item['name'] for item in items if item['is_directory']])
        elif data_type == 'files':
            return sorted([
                item['name'] for item in items
                if not item['is_directory'] and item['name'].lower().endswith(file_extensions)
            ])
        return []

    def fetch_available_voxel_labels(
        self,
        patient_id: str,
        filename: str,
        filename_to_id_mapping: Dict[str, int]
    ) -> Tuple[Set[int], Dict[int, str]]:
        """
        Query image server for available voxel files.
        Returns (available_label_ids, id_to_name_map).
        """
        if not patient_id or not filename:
            return set(), {}

        try:
            # Convert filename to folder name for voxels directory
            ct_scan_folder_name = filename.replace('.nii.gz', '').replace('.nii', '')

            # Check the voxels directory for this CT scan
            voxels_folder_url = f"{self.image_server_url}/output/{patient_id}/voxels/{ct_scan_folder_name}/"

            if __debug__:
                print(f"DEBUG: Checking voxels URL: {voxels_folder_url}")

            resp = requests.get(voxels_folder_url, timeout=SERVER_TIMEOUT)
            if __debug__:
                print(f"DEBUG: Response status: {resp.status_code}")

            if resp.status_code != 200:
                if __debug__:
                    print(f"DEBUG: Failed to access voxels directory. Status: {resp.status_code}")
                return set(), {}

            # Parse directory listing to find individual voxel files
            soup = BeautifulSoup(resp.text, 'html.parser')
            voxel_files = []
            for link in soup.find_all('a'):
                href = link.get('href')
                if href and href.endswith('.nii.gz') and not href.startswith('..'):
                    voxel_files.append(href)

            if __debug__:
                print(f"DEBUG: Found {len(voxel_files)} voxel files: {voxel_files}")

            # Find which label IDs are available based on existing voxel files
            available_ids = set()
            matched_files = []
            for voxel_file in voxel_files:
                # Extract just the filename from the full path
                filename_only = voxel_file.split('/')[-1]
                if filename_only in filename_to_id_mapping:
                    available_ids.add(filename_to_id_mapping[filename_only])
                    matched_files.append(filename_only)

            if __debug__:
                print(f"DEBUG: Matched {len(matched_files)} files to label IDs: {matched_files}")
                print(f"DEBUG: Available label IDs: {available_ids}")

            # Create id_to_name mapping for available labels
            id_to_name = {
                label_id: name for name, label_id in filename_to_id_mapping.items()
                if label_id in available_ids
            }

            return available_ids, id_to_name

        except Exception as e:
            print(f"Error fetching available voxel labels: {e}")
            return set(), {}

    def get_voxel_directory_url(self, patient_id: str, filename: str) -> str:
        """Generate the URL for the voxel directory."""
        ct_scan_folder_name = filename.replace('.nii.gz', '').replace('.nii', '') if filename else ''
        return f"{self.image_server_url}/output/{patient_id}/voxels/{ct_scan_folder_name}/"
    
    def get_ply_directory_url(self, patient_id: str, filename: str) -> str:
        """Generate the URL for the PLY directory."""
        ct_scan_folder_name = filename.replace('.nii.gz', '').replace('.nii', '') if filename else ''
        return f"{self.image_server_url}/output/{patient_id}/ply/{ct_scan_folder_name}/"
    
    def get_file_url(self, patient_id: str, file_path: str) -> str:
        """Generate the full URL for a file within a patient's directory."""
        return f"{self.image_server_url}/output/{patient_id}/{file_path}"