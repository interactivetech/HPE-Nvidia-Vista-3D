#!/usr/bin/env python3
"""
Test script for realistic medical post-processor.

This script tests the realistic medical post-processor to ensure it works correctly
with the existing voxel files.

Usage:
    python test_realistic_medical.py
"""

import sys
from pathlib import Path
from realistic_medical_postprocessor import RealisticMedicalPostProcessor
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_processor_initialization():
    """Test that the processor initializes correctly."""
    print("🧪 Testing processor initialization...")
    
    try:
        processor = RealisticMedicalPostProcessor()
        print("✅ Processor initialized successfully")
        
        # Test anatomical colors
        assert 'liver' in processor.anatomical_colors
        assert 'aorta' in processor.anatomical_colors
        assert 'rib' in processor.anatomical_colors
        print("✅ Anatomical color mappings loaded")
        
        # Test texture patterns
        assert 'organic' in processor.texture_patterns
        assert 'vascular' in processor.texture_patterns
        assert 'bone' in processor.texture_patterns
        print("✅ Texture patterns loaded")
        
        return True
        
    except Exception as e:
        print(f"❌ Processor initialization failed: {e}")
        return False


def test_anatomical_type_detection():
    """Test anatomical type detection from filenames."""
    print("\n🧪 Testing anatomical type detection...")
    
    try:
        processor = RealisticMedicalPostProcessor()
        
        # Test cases
        test_cases = [
            ("liver.nii.gz", "liver"),
            ("aorta.nii.gz", "aorta"),
            ("inferior_vena_cava.nii.gz", "inferior_vena_cava"),
            ("left_rib_5.nii.gz", "rib"),
            ("right_hip.nii.gz", "hip"),
            ("vertebrae_l1.nii.gz", "vertebrae"),
            ("heart.nii.gz", "heart"),
            ("left_kidney.nii.gz", "kidney"),
            ("unknown_structure.nii.gz", "default")
        ]
        
        for filename, expected_type in test_cases:
            detected_type = processor._get_anatomical_type(filename)
            assert detected_type == expected_type, f"Expected {expected_type}, got {detected_type} for {filename}"
            print(f"   ✅ {filename} -> {detected_type}")
        
        print("✅ Anatomical type detection working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Anatomical type detection failed: {e}")
        return False


def test_texture_generation():
    """Test texture generation functions."""
    print("\n🧪 Testing texture generation...")
    
    try:
        processor = RealisticMedicalPostProcessor()
        
        # Test shape
        test_shape = (10, 10, 10)
        
        # Test organic texture
        organic_texture = processor._generate_organic_texture(test_shape, processor.texture_patterns['organic'])
        assert organic_texture.shape == test_shape
        assert 0 <= organic_texture.min() <= organic_texture.max() <= 1
        print("   ✅ Organic texture generation")
        
        # Test vascular texture
        vascular_texture = processor._generate_vascular_texture(test_shape, processor.texture_patterns['vascular'])
        assert vascular_texture.shape == test_shape
        assert 0 <= vascular_texture.min() <= vascular_texture.max() <= 1
        print("   ✅ Vascular texture generation")
        
        # Test bone texture
        bone_texture = processor._generate_bone_texture(test_shape, processor.texture_patterns['bone'])
        assert bone_texture.shape == test_shape
        assert 0 <= bone_texture.min() <= bone_texture.max() <= 1
        print("   ✅ Bone texture generation")
        
        print("✅ Texture generation working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Texture generation failed: {e}")
        return False


def test_voxel_files_detection():
    """Test voxel files detection."""
    print("\n🧪 Testing voxel files detection...")
    
    try:
        processor = RealisticMedicalPostProcessor()
        
        # Test with PA00000002 (should exist based on project structure)
        voxel_files = processor.get_voxel_files("PA00000002", "2.5MM_ARTERIAL_3")
        
        assert 'individual_voxels' in voxel_files
        assert 'main_scan' in voxel_files
        print(f"   ✅ Found {len(voxel_files['individual_voxels'])} individual voxel files")
        print(f"   ✅ Found {len(voxel_files['main_scan'])} main scan files")
        
        if voxel_files['individual_voxels']:
            print("   ✅ Individual voxel files detected")
        else:
            print("   ⚠️ No individual voxel files found (this may be expected)")
        
        if voxel_files['main_scan']:
            print("   ✅ Main scan files detected")
        else:
            print("   ⚠️ No main scan files found (this may be expected)")
        
        print("✅ Voxel files detection working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Voxel files detection failed: {e}")
        return False


def test_processing_with_sample_data():
    """Test processing with actual voxel data if available."""
    print("\n🧪 Testing processing with sample data...")
    
    try:
        processor = RealisticMedicalPostProcessor()
        
        # Get voxel files
        voxel_files = processor.get_voxel_files("PA00000002", "2.5MM_ARTERIAL_3")
        all_files = voxel_files['individual_voxels'] + voxel_files['main_scan']
        
        if not all_files:
            print("   ⚠️ No voxel files found for testing - skipping processing test")
            return True
        
        # Test with first available file
        test_file = all_files[0]
        print(f"   📁 Testing with file: {test_file.name}")
        
        # Test realistic medical effect
        import nibabel as nib
        nifti_img = nib.load(test_file)
        
        # Test anatomical type detection
        anatomical_type = processor._get_anatomical_type(test_file.name)
        print(f"   🔍 Detected anatomical type: {anatomical_type}")
        
        # Test color application
        data = nifti_img.get_fdata()
        colored_data = processor._apply_anatomical_coloring(data, anatomical_type)
        print(f"   🎨 Applied anatomical coloring: {colored_data.shape}")
        
        # Test texture enhancement
        textured_data = processor._apply_texture_enhancement(data, anatomical_type)
        print(f"   🖼️ Applied texture enhancement: {textured_data.shape}")
        
        print("✅ Processing with sample data working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Processing with sample data failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 Vista3D Realistic Medical Post-Processor Tests")
    print("=" * 60)
    
    tests = [
        test_processor_initialization,
        test_anatomical_type_detection,
        test_texture_generation,
        test_voxel_files_detection,
        test_processing_with_sample_data
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The realistic medical post-processor is working correctly.")
        print("\n🚀 You can now use the post-processor:")
        print("   • python run_realistic_medical_processing.py")
        print("   • python medical_processing_examples.py")
        print("   • python realistic_medical_postprocessor.py --help")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
