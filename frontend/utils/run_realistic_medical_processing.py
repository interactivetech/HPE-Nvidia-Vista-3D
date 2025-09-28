#!/usr/bin/env python3
"""
Simple script to run realistic medical processing on voxel files.

This script provides an easy way to apply realistic medical visualization effects
to your voxel files, creating professional-quality 3D medical renderings.

Usage:
    python run_realistic_medical_processing.py
"""

import sys
from pathlib import Path
from realistic_medical_postprocessor import RealisticMedicalPostProcessor
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Run realistic medical processing with default settings."""
    
    # Configuration
    patient_id = "PA00000002"
    scan_name = "2.5MM_ARTERIAL_3"
    
    print("🏥 Vista3D Realistic Medical Post-Processing")
    print("=" * 50)
    print(f"Patient: {patient_id}")
    print(f"Scan: {scan_name}")
    print()
    
    try:
        # Create processor
        processor = RealisticMedicalPostProcessor()
        
        # Process with realistic medical effect
        print("🎨 Applying Realistic Medical Visualization...")
        processed_files = processor.process_files(
            patient_id=patient_id,
            scan_name=scan_name,
            effect_name="realistic_medical",
            effect_params={
                "translucency": 0.8,
                "texture_strength": 1.0,
                "color_enhancement": True
            }
        )
        
        if processed_files:
            print(f"\n✅ Successfully processed {len(processed_files)} files with realistic medical visualization!")
            print("\n📁 Output directory:")
            output_dir = Path(processed_files[0]).parent
            print(f"   {output_dir}")
            
            print("\n📋 Processed files:")
            for file_path in processed_files[:10]:  # Show first 10 files
                print(f"   - {file_path.name}")
            if len(processed_files) > 10:
                print(f"   ... and {len(processed_files) - 10} more files")
            
            print("\n🎯 Key Features Applied:")
            print("   • Anatomical coloring (liver=reddish-brown, vessels=red/blue, bones=beige)")
            print("   • Realistic texture enhancement (organic, vascular, bone patterns)")
            print("   • Surface refinement with edge-preserving smoothing")
            print("   • Volume rendering enhancement with contrast and gamma correction")
            print("   • Translucent rendering for layered visualization")
            
            print("\n🔬 Anatomical Structures Enhanced:")
            anatomical_types = set()
            for file_path in processed_files:
                filename = file_path.name.lower()
                if 'liver' in filename:
                    anatomical_types.add('Liver (reddish-brown)')
                elif 'aorta' in filename:
                    anatomical_types.add('Aorta (bright red)')
                elif 'vena_cava' in filename or 'cava' in filename:
                    anatomical_types.add('Inferior Vena Cava (blue)')
                elif 'iliac_artery' in filename:
                    anatomical_types.add('Iliac Arteries (red)')
                elif 'iliac_vena' in filename:
                    anatomical_types.add('Iliac Veins (blue)')
                elif 'rib' in filename:
                    anatomical_types.add('Ribs (bone beige)')
                elif 'hip' in filename:
                    anatomical_types.add('Hip Bones (bone beige)')
                elif 'femur' in filename:
                    anatomical_types.add('Femur (bone beige)')
                elif 'vertebrae' in filename:
                    anatomical_types.add('Vertebrae (bone beige)')
                elif 'heart' in filename:
                    anatomical_types.add('Heart (red)')
                elif 'kidney' in filename:
                    anatomical_types.add('Kidney (green)')
                elif 'lung' in filename:
                    anatomical_types.add('Lung (light blue-gray)')
            
            for structure in sorted(anatomical_types):
                print(f"   • {structure}")
            
            print(f"\n🚀 Ready for visualization! Load the processed files in your 3D viewer.")
            
        else:
            print("\n❌ No files were processed. Please check:")
            print(f"   • Patient directory exists: output/{patient_id}/voxels/{scan_name}/")
            print(f"   • Voxel files are present in the directory")
            print(f"   • File permissions allow reading/writing")
            
    except Exception as e:
        logger.error(f"Error during processing: {e}")
        print(f"\n❌ Error: {e}")
        print("\n🔧 Troubleshooting:")
        print("   • Ensure the output directory exists and contains voxel files")
        print("   • Check that all required dependencies are installed")
        print("   • Verify file permissions")
        sys.exit(1)


if __name__ == "__main__":
    main()
