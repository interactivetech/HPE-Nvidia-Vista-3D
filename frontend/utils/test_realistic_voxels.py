#!/usr/bin/env python3
"""
Test script for realistic voxel effects

This script demonstrates the new realistic voxel effects that create
medical visualizations similar to the provided image.
"""

import argparse
import sys
from pathlib import Path

# Add the project root to the Python path
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent  # frontend/utils -> frontend -> project_root
sys.path.insert(0, str(project_root))

from enhanced_realistic_medical import EnhancedRealisticMedicalProcessor
from voxel_effects import VoxelEffectsProcessor

def test_realistic_effects(patient_id: str, scan_name: str):
    """Test all realistic voxel effects."""
    print(f"Testing realistic voxel effects for {patient_id}/{scan_name}")
    print("=" * 60)
    
    # Test enhanced realistic medical effects
    print("\n1. Testing Enhanced Realistic Medical Effects:")
    print("-" * 40)
    
    enhanced_processor = EnhancedRealisticMedicalProcessor()
    
    effects_to_test = [
        ("ultra_realistic_anatomy", "Ultra-Realistic Anatomy"),
        ("photorealistic_organs", "Photorealistic Organs"),
        ("medical_grade_rendering", "Medical-Grade Rendering"),
        ("medical_visualization", "Medical Visualization (New)")
    ]
    
    for effect_name, display_name in effects_to_test:
        print(f"\nTesting {display_name}...")
        try:
            processed_files = enhanced_processor.process_files(
                patient_id=patient_id,
                scan_name=scan_name,
                effect_name=effect_name,
                effect_params={}
            )
            print(f"✅ {display_name}: {len(processed_files)} files processed")
            for file_path in processed_files:
                print(f"   - {file_path}")
        except Exception as e:
            print(f"❌ {display_name}: Error - {e}")
    
    # Test voxel effects processor
    print("\n2. Testing Voxel Effects Processor:")
    print("-" * 40)
    
    voxel_processor = VoxelEffectsProcessor()
    
    voxel_effects_to_test = [
        ("medical_visualization", "Medical Visualization"),
        ("ultra_realistic_anatomy", "Ultra-Realistic Anatomy"),
        ("photorealistic_organs", "Photorealistic Organs"),
        ("medical_grade_rendering", "Medical-Grade Rendering")
    ]
    
    for effect_name, display_name in voxel_effects_to_test:
        print(f"\nTesting {display_name}...")
        try:
            processed_files = voxel_processor.process_files(
                patient_id=patient_id,
                scan_name=scan_name,
                effect_name=effect_name,
                effect_params={}
            )
            print(f"✅ {display_name}: {len(processed_files)} files processed")
            for file_path in processed_files:
                print(f"   - {file_path}")
        except Exception as e:
            print(f"❌ {display_name}: Error - {e}")
    
    print("\n" + "=" * 60)
    print("Realistic voxel effects testing completed!")
    print("\nTo use these effects in the web interface:")
    print("1. Select a patient and scan")
    print("2. Choose 'Individual Voxels' or 'All Voxels' mode")
    print("3. Select one of the new realistic effects:")
    print("   - Ultra-Realistic Anatomy")
    print("   - Photorealistic Organs")
    print("   - Medical-Grade Rendering")
    print("   - Medical Visualization (New - Best for medical image style)")
    print("4. View the enhanced 3D visualization")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Test realistic voxel effects",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with default patient and scan
  python test_realistic_voxels.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3
  
  # Test with different patient
  python test_realistic_voxels.py --patient PA00000014 --scan 2.5MM_ARTERIAL_3
        """
    )
    
    parser.add_argument("--patient", required=True, help="Patient ID (e.g., PA00000002)")
    parser.add_argument("--scan", required=True, help="Scan name (e.g., 2.5MM_ARTERIAL_3)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    try:
        test_realistic_effects(args.patient, args.scan)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
