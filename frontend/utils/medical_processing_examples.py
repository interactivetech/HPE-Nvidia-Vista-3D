#!/usr/bin/env python3
"""
Comprehensive examples for realistic medical post-processing.

This script demonstrates various ways to use the realistic medical post-processor
to create different types of medical visualizations.

Usage:
    python medical_processing_examples.py
"""

import sys
from pathlib import Path
from realistic_medical_postprocessor import RealisticMedicalPostProcessor
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def example_1_realistic_medical_visualization():
    """Example 1: Complete realistic medical visualization like the reference image."""
    print("🎨 Example 1: Realistic Medical Visualization")
    print("-" * 50)
    
    processor = RealisticMedicalPostProcessor()
    
    # Process with realistic medical effect - similar to the reference image
    processed_files = processor.process_files(
        patient_id="PA00000002",
        scan_name="2.5MM_ARTERIAL_3",
        effect_name="realistic_medical",
        effect_params={
            "translucency": 0.8,        # Semi-transparent for layered view
            "texture_strength": 1.0,    # Full texture enhancement
            "color_enhancement": True   # Apply anatomical coloring
        }
    )
    
    print(f"✅ Processed {len(processed_files)} files with realistic medical visualization")
    return processed_files


def example_2_anatomical_enhancement():
    """Example 2: Focus on anatomical structure enhancement."""
    print("\n🔬 Example 2: Anatomical Structure Enhancement")
    print("-" * 50)
    
    processor = RealisticMedicalPostProcessor()
    
    # Process with anatomical enhancement
    processed_files = processor.process_files(
        patient_id="PA00000002",
        scan_name="2.5MM_ARTERIAL_3",
        effect_name="anatomical_enhancement",
        effect_params={
            "structure_preservation": 0.9,  # Preserve original structure
            "detail_enhancement": 1.2       # Enhance details
        }
    )
    
    print(f"✅ Processed {len(processed_files)} files with anatomical enhancement")
    return processed_files


def example_3_vessel_enhancement():
    """Example 3: Specialized vessel enhancement for vascular structures."""
    print("\n🩸 Example 3: Vascular Structure Enhancement")
    print("-" * 50)
    
    processor = RealisticMedicalPostProcessor()
    
    # Process with vessel enhancement
    processed_files = processor.process_files(
        patient_id="PA00000002",
        scan_name="2.5MM_ARTERIAL_3",
        effect_name="vessel_enhancement",
        effect_params={
            "vessel_contrast": 1.5,     # Enhanced contrast for vessels
            "wall_thickness": 1.2       # Simulated wall thickness
        }
    )
    
    print(f"✅ Processed {len(processed_files)} files with vessel enhancement")
    return processed_files


def example_4_custom_processing():
    """Example 4: Custom processing with different parameters."""
    print("\n⚙️ Example 4: Custom Processing Parameters")
    print("-" * 50)
    
    processor = RealisticMedicalPostProcessor()
    
    # Custom realistic medical processing with different settings
    processed_files = processor.process_files(
        patient_id="PA00000002",
        scan_name="2.5MM_ARTERIAL_3",
        effect_name="realistic_medical",
        effect_params={
            "translucency": 0.6,        # More opaque
            "texture_strength": 1.5,    # Enhanced texture
            "color_enhancement": True   # Keep anatomical coloring
        }
    )
    
    print(f"✅ Processed {len(processed_files)} files with custom parameters")
    return processed_files


def example_5_batch_processing():
    """Example 5: Batch processing multiple effects."""
    print("\n📦 Example 5: Batch Processing Multiple Effects")
    print("-" * 50)
    
    processor = RealisticMedicalPostProcessor()
    
    effects = [
        {
            "name": "realistic_medical",
            "params": {"translucency": 0.8, "texture_strength": 1.0, "color_enhancement": True},
            "description": "Realistic medical visualization"
        },
        {
            "name": "anatomical_enhancement", 
            "params": {"structure_preservation": 0.9, "detail_enhancement": 1.2},
            "description": "Anatomical structure enhancement"
        },
        {
            "name": "vessel_enhancement",
            "params": {"vessel_contrast": 1.5, "wall_thickness": 1.0},
            "description": "Vascular enhancement"
        }
    ]
    
    all_processed_files = []
    
    for effect in effects:
        print(f"\n🔄 Processing with {effect['description']}...")
        processed_files = processor.process_files(
            patient_id="PA00000002",
            scan_name="2.5MM_ARTERIAL_3",
            effect_name=effect["name"],
            effect_params=effect["params"]
        )
        all_processed_files.extend(processed_files)
        print(f"   ✅ {len(processed_files)} files processed")
    
    print(f"\n📊 Total files processed across all effects: {len(all_processed_files)}")
    return all_processed_files


def show_anatomical_mappings():
    """Show the anatomical color and texture mappings."""
    print("\n🎨 Anatomical Color and Texture Mappings")
    print("-" * 50)
    
    processor = RealisticMedicalPostProcessor()
    
    print("Organ Structures:")
    organ_structures = ['liver', 'gallbladder', 'heart', 'kidney', 'lung']
    for structure in organ_structures:
        color_config = processor.anatomical_colors.get(structure, processor.anatomical_colors['default'])
        color_rgb = [int(c * 255) for c in color_config['base_color']]
        print(f"   • {structure.title()}: RGB{color_rgb} - {color_config['texture_strength']:.1f} texture strength")
    
    print("\nVascular Structures:")
    vascular_structures = ['aorta', 'inferior_vena_cava', 'iliac_artery', 'iliac_vena']
    for structure in vascular_structures:
        color_config = processor.anatomical_colors.get(structure, processor.anatomical_colors['default'])
        color_rgb = [int(c * 255) for c in color_config['base_color']]
        print(f"   • {structure.replace('_', ' ').title()}: RGB{color_rgb} - {color_config['texture_strength']:.1f} texture strength")
    
    print("\nSkeletal Structures:")
    skeletal_structures = ['rib', 'hip', 'femur', 'vertebrae', 'sacrum', 'sternum', 'skull']
    for structure in skeletal_structures:
        color_config = processor.anatomical_colors.get(structure, processor.anatomical_colors['default'])
        color_rgb = [int(c * 255) for c in color_config['base_color']]
        print(f"   • {structure.title()}: RGB{color_rgb} - {color_config['texture_strength']:.1f} texture strength")


def main():
    """Run all examples."""
    print("🏥 Vista3D Medical Post-Processing Examples")
    print("=" * 60)
    print("This script demonstrates various ways to create realistic medical visualizations")
    print("similar to the reference image you provided.")
    print()
    
    try:
        # Show anatomical mappings
        show_anatomical_mappings()
        
        # Run examples
        print("\n🚀 Running Processing Examples...")
        print("=" * 60)
        
        # Example 1: Realistic medical visualization (like the reference image)
        example_1_realistic_medical_visualization()
        
        # Example 2: Anatomical enhancement
        example_2_anatomical_enhancement()
        
        # Example 3: Vessel enhancement
        example_3_vessel_enhancement()
        
        # Example 4: Custom processing
        example_4_custom_processing()
        
        # Example 5: Batch processing
        example_5_batch_processing()
        
        print("\n🎉 All examples completed successfully!")
        print("\n📁 Check the output directories for processed files:")
        print("   • output/PA00000002/voxels/2.5MM_ARTERIAL_3_realistic_medical/")
        print("   • output/PA00000002/voxels/2.5MM_ARTERIAL_3_anatomical_enhancement/")
        print("   • output/PA00000002/voxels/2.5MM_ARTERIAL_3_vessel_enhancement/")
        
        print("\n💡 Tips for best results:")
        print("   • Use 'realistic_medical' for comprehensive visualization like the reference image")
        print("   • Use 'anatomical_enhancement' for structure-focused visualization")
        print("   • Use 'vessel_enhancement' for vascular structure analysis")
        print("   • Adjust translucency (0.6-0.9) for different transparency levels")
        print("   • Increase texture_strength (1.0-1.5) for more pronounced textures")
        
    except Exception as e:
        logger.error(f"Error during examples: {e}")
        print(f"\n❌ Error: {e}")
        print("\n🔧 Troubleshooting:")
        print("   • Ensure the output directory exists and contains voxel files")
        print("   • Check that all required dependencies are installed")
        print("   • Verify file permissions")
        sys.exit(1)


if __name__ == "__main__":
    main()
