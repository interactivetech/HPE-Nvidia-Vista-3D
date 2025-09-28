#!/usr/bin/env python3
"""
Demonstration Script for Enhanced Realistic Medical Effects

This script demonstrates how to use the new enhanced realistic medical
visualization effects to create ultra-realistic voxels similar to the
image shown. It processes a sample dataset with all three enhanced effects.

Usage:
    python demo_enhanced_realistic_effects.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3
"""

import argparse
import os
import sys
from pathlib import Path
import logging
import time

# Add the project root to the Python path
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent  # frontend/utils -> frontend -> project_root
sys.path.insert(0, str(project_root))

from utils.enhanced_realistic_medical import EnhancedRealisticMedicalProcessor

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def demo_enhanced_effects(patient_id: str, scan_name: str):
    """Demonstrate enhanced realistic effects on the specified patient and scan."""
    
    print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    Enhanced Realistic Voxel Effects Demo                    ║
║                                                                              ║
║  This demo will process your voxel data with three levels of enhanced       ║
║  realistic medical visualization effects to create ultra-realistic voxels   ║
║  similar to professional medical imaging software.                          ║
║                                                                              ║
║  Patient: {patient_id:<60} ║
║  Scan:    {scan_name:<60} ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Create processor
    processor = EnhancedRealisticMedicalProcessor()
    
    # Demo effects with descriptions
    demo_effects = [
        {
            'name': 'ultra_realistic_anatomy',
            'params': {
                'material_realism': 0.9,
                'lighting_quality': 0.8,
                'texture_detail': 0.7
            },
            'description': 'Ultra-Realistic Anatomy',
            'details': [
                '• Advanced material properties with anatomical accuracy',
                '• Photorealistic lighting with subsurface scattering',
                '• Sophisticated texture generation with organ-specific patterns',
                '• Medical-grade enhancement for professional visualization'
            ]
        },
        {
            'name': 'photorealistic_organs',
            'params': {
                'organ_detail': 0.8,
                'surface_quality': 0.9
            },
            'description': 'Photorealistic Organs',
            'details': [
                '• Specialized organ visualization with enhanced surface quality',
                '• Anatomically accurate organ-specific textures',
                '• Realistic material properties for different tissue types',
                '• Enhanced detail for organ-specific analysis'
            ]
        },
        {
            'name': 'medical_grade_rendering',
            'params': {
                'professional_quality': 1.0,
                'clinical_accuracy': 0.9
            },
            'description': 'Medical-Grade Rendering',
            'details': [
                '• Professional medical visualization with clinical accuracy',
                '• Diagnostic-quality enhancement for medical applications',
                '• Advanced image processing techniques',
                '• Suitable for clinical and research purposes'
            ]
        }
    ]
    
    total_start_time = time.time()
    results = []
    
    for i, effect in enumerate(demo_effects, 1):
        print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                          Effect {i}/3: {effect['description']:<30} ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║""")
        
        for detail in effect['details']:
            print(f"║  {detail:<76} ║")
        
        print(f"""║                                                                              ║
║  Processing with parameters:                                                ║""")
        
        for param, value in effect['params'].items():
            print(f"║    {param}: {value:<68} ║")
        
        print(f"""║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """)
        
        effect_start_time = time.time()
        
        try:
            logger.info(f"Starting {effect['name']} processing...")
            
            # Process files with this effect
            processed_files = processor.process_files(
                patient_id=patient_id,
                scan_name=scan_name,
                effect_name=effect['name'],
                effect_params=effect['params']
            )
            
            effect_end_time = time.time()
            processing_time = effect_end_time - effect_start_time
            
            if processed_files:
                print(f"✅ SUCCESS: {effect['description']}")
                print(f"   📁 Processed {len(processed_files)} files")
                print(f"   ⏱️  Processing time: {processing_time:.1f} seconds")
                print(f"   📂 Output directory: {processed_files[0].parent}")
                
                # Show some example files
                print(f"   📄 Example files:")
                for j, file_path in enumerate(processed_files[:3]):
                    print(f"      {j+1}. {file_path.name}")
                if len(processed_files) > 3:
                    print(f"      ... and {len(processed_files) - 3} more files")
                
                results.append({
                    'effect': effect['name'],
                    'description': effect['description'],
                    'status': 'success',
                    'files_processed': len(processed_files),
                    'processing_time': processing_time,
                    'output_dir': processed_files[0].parent
                })
                
            else:
                print(f"❌ NO FILES: {effect['description']}")
                print(f"   ⚠️  No voxel files found for processing")
                
                results.append({
                    'effect': effect['name'],
                    'description': effect['description'],
                    'status': 'no_files',
                    'files_processed': 0,
                    'processing_time': processing_time
                })
                
        except Exception as e:
            effect_end_time = time.time()
            processing_time = effect_end_time - effect_start_time
            
            print(f"❌ ERROR: {effect['description']}")
            print(f"   🚨 Error: {str(e)}")
            print(f"   ⏱️  Processing time: {processing_time:.1f} seconds")
            
            results.append({
                'effect': effect['name'],
                'description': effect['description'],
                'status': 'error',
                'files_processed': 0,
                'processing_time': processing_time,
                'error': str(e)
            })
        
        print()
    
    total_end_time = time.time()
    total_processing_time = total_end_time - total_start_time
    
    # Final summary
    print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                              DEMO COMPLETE                                 ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  Total processing time: {total_processing_time:.1f} seconds{' ' * (47 - len(f'{total_processing_time:.1f}'))} ║
║                                                                              ║""")
    
    successful_effects = [r for r in results if r['status'] == 'success']
    failed_effects = [r for r in results if r['status'] in ['error', 'no_files']]
    
    if successful_effects:
        print(f"""║  ✅ Successful effects: {len(successful_effects)}/3{' ' * (52 - len(str(len(successful_effects))))} ║
║                                                                              ║
║  Enhanced voxel files are now available in the following directories:       ║""")
        
        for result in successful_effects:
            print(f"║                                                                              ║")
            print(f"║  📁 {result['description']:<30} {' ' * (42 - len(result['description']))} ║")
            print(f"║     {str(result['output_dir']):<68} ║")
            print(f"║     {result['files_processed']} files processed in {result['processing_time']:.1f}s{' ' * (45 - len(f'{result['files_processed']} files processed in {result['processing_time']:.1f}s'))} ║")
    
    if failed_effects:
        print(f"""║                                                                              ║
║  ❌ Failed effects: {len(failed_effects)}/3{' ' * (56 - len(str(len(failed_effects))))} ║""")
        
        for result in failed_effects:
            error_msg = f" - {result['error']}" if 'error' in result else ""
            print(f"║     • {result['description']:<30} ({result['status']}){' ' * (35 - len(result['description']) - len(result['status']))} ║")
    
    print(f"""║                                                                              ║
║  🎯 Next steps:                                                             ║
║     1. Open Vista3D viewer                                                 ║
║     2. Select your patient and scan                                        ║
║     3. Choose an enhanced effect from the dropdown                         ║
║     4. View ultra-realistic voxel renderings!                              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    return results


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Demonstrate enhanced realistic medical visualization effects",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run demo with default settings
  python demo_enhanced_realistic_effects.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3
  
  # Run demo with verbose logging
  python demo_enhanced_realistic_effects.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 --verbose
        """
    )
    
    # Required arguments
    parser.add_argument("--patient", required=True, help="Patient ID (e.g., PA00000002)")
    parser.add_argument("--scan", required=True, help="Scan name (e.g., 2.5MM_ARTERIAL_3)")
    
    # Optional arguments
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        results = demo_enhanced_effects(args.patient, args.scan)
        
        # Exit with appropriate code
        successful_effects = [r for r in results if r['status'] == 'success']
        if successful_effects:
            print(f"\n🎉 Demo completed successfully! Enhanced realistic voxels are ready for viewing.")
            sys.exit(0)
        else:
            print(f"\n❌ Demo completed but no effects were successfully processed.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Demo failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
