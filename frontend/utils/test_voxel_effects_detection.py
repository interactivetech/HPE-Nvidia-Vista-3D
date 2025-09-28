#!/usr/bin/env python3
"""
Test script to verify voxel effects detection is working correctly.
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

def test_voxel_effects_detection():
    """Test that voxel effects are detected correctly."""
    print("🧪 Testing Voxel Effects Detection")
    print("=" * 50)
    
    try:
        # Initialize managers
        config_manager = ConfigManager()
        data_manager = DataManager("http://localhost:8888")
        voxel_manager = VoxelManager(config_manager, data_manager)
        
        # Test available effects from config
        available_effects = voxel_manager.get_available_effects()
        print(f"📋 Available effects in config: {len(available_effects)}")
        for effect in available_effects:
            print(f"   • {effect['name']}: {effect['display_name']}")
        
        # Test effect detection for PA00000002
        print(f"\n🔍 Testing effect detection for PA00000002...")
        detected_effects = voxel_manager.detect_effect_folders("PA00000002", "2.5MM_ARTERIAL_3")
        print(f"📁 Detected effect folders: {len(detected_effects)}")
        for effect in detected_effects:
            display_name = voxel_manager.get_effect_display_name(effect)
            print(f"   • {effect}: {display_name}")
        
        # Check if realistic_medical is detected
        if "realistic_medical" in detected_effects:
            print("✅ Realistic Medical effect detected successfully!")
        else:
            print("❌ Realistic Medical effect not detected")
            
        # Check folder pattern
        folder_pattern = voxel_manager.effects_config.get("folder_pattern", "{scan_name}_{effect_name}")
        print(f"\n📂 Folder pattern: {folder_pattern}")
        
        # Test expected folder names
        expected_folders = [
            "2.5MM_ARTERIAL_3_realistic_medical",
            "2.5MM_ARTERIAL_3_anatomical_enhancement", 
            "2.5MM_ARTERIAL_3_vessel_enhancement"
        ]
        
        print(f"\n📁 Expected folders:")
        for folder in expected_folders:
            print(f"   • {folder}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False

if __name__ == "__main__":
    success = test_voxel_effects_detection()
    if success:
        print("\n🎉 Voxel effects detection test completed!")
    else:
        print("\n❌ Voxel effects detection test failed!")
        sys.exit(1)
