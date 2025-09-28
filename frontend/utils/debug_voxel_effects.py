#!/usr/bin/env python3
"""
Debug script to test voxel effects detection in the NiiVue Viewer context.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent
sys.path.insert(0, str(project_root))

from frontend.utils.config_manager import ConfigManager
from frontend.utils.data_manager import DataManager
from frontend.utils.voxel_manager import VoxelManager

def debug_voxel_effects():
    """Debug voxel effects detection."""
    print("🔍 Debugging Voxel Effects Detection")
    print("=" * 50)
    
    try:
        # Initialize managers
        config_manager = ConfigManager()
        data_manager = DataManager("http://localhost:8888")
        voxel_manager = VoxelManager(config_manager, data_manager)
        
        # Simulate the NiiVue Viewer file selection process
        patient_id = "PA00000002"
        
        # Get available files (simulating the NiiVue Viewer logic)
        filenames = data_manager.get_server_data(f"{patient_id}/nifti", 'files', ['.nii.gz', '.nii', '.dcm'])
        print(f"📁 Available files: {len(filenames)}")
        for filename in filenames[:5]:  # Show first 5
            print(f"   - {filename}")
        
        if filenames:
            # Simulate the display name creation
            display_names = [
                filename.replace('.nii.gz', '').replace('.nii', '').replace('.dcm', '')
                for filename in filenames
            ]
            print(f"\\n📝 Display names (first 5):")
            for display_name in display_names[:5]:
                print(f"   - {display_name}")
            
            # Simulate selecting the first file
            selected_display_name = display_names[0]
            selected_index = display_names.index(selected_display_name)
            selected_file = filenames[selected_index]
            
            print(f"\\n🎯 Selected file: {selected_file}")
            print(f"🎯 Selected display name: {selected_display_name}")
            
            # Test voxel detection
            print(f"\\n🔍 Testing voxel detection...")
            has_voxels = voxel_manager.has_voxels_for_patient(patient_id)
            print(f"Has voxels: {has_voxels}")
            
            if has_voxels:
                # Test effect detection with the actual selected file
                print(f"\\n🎨 Testing effect detection with selected file: '{selected_file}'")
                available_effects = voxel_manager.detect_effect_folders(patient_id, selected_file)
                print(f"Available effects: {available_effects}")
                
                if available_effects:
                    print(f"\\n✨ Effect display names:")
                    for effect in available_effects:
                        display_name = voxel_manager.get_effect_display_name(effect)
                        print(f"   - {effect}: {display_name}")
                else:
                    print("❌ No effects detected!")
                    
                    # Debug the detection process
                    print(f"\\n🔍 Debugging detection process...")
                    clean_scan_name = selected_file.replace('.nii.gz', '').replace('.nii', '')
                    print(f"Clean scan name: '{clean_scan_name}'")
                    
                    folder_pattern = voxel_manager.effects_config.get("folder_pattern", "{scan_name}_{effect_name}")
                    print(f"Folder pattern: {folder_pattern}")
                    
                    # Check what folders exist
                    voxels_folder_url = f"{data_manager.image_server_url}/output/{patient_id}/voxels/"
                    print(f"Voxels folder URL: {voxels_folder_url}")
                    
                    import requests
                    from bs4 import BeautifulSoup
                    resp = requests.get(voxels_folder_url, timeout=5)
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, 'html.parser')
                        found_folders = []
                        for link in soup.find_all('a'):
                            href = link.get('href')
                            if href and not href.startswith('..') and href.endswith('/'):
                                folder_name = href.rstrip('/').split('/')[-1]
                                found_folders.append(folder_name)
                        
                        print(f"Found folders: {found_folders}")
                        
                        # Check which ones match the pattern
                        for effect in voxel_manager.get_available_effects():
                            effect_name = effect["name"]
                            expected_folder = folder_pattern.format(
                                scan_name=clean_scan_name, 
                                effect_name=effect_name
                            )
                            matches = expected_folder in found_folders
                            print(f"   - {effect_name}: expected '{expected_folder}', matches: {matches}")
            else:
                print("❌ No voxels found for patient!")
        
    except Exception as e:
        print(f"❌ Error during debugging: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_voxel_effects()
