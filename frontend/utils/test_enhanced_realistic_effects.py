#!/usr/bin/env python3
"""
Test Script for Enhanced Realistic Medical Effects

This script tests the new enhanced realistic medical visualization effects
to ensure they produce high-quality, realistic-looking voxels similar to
professional medical imaging software.

Usage:
    python test_enhanced_realistic_effects.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3
"""

import argparse
import os
import sys
from pathlib import Path
import logging

# Add the project root to the Python path
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent  # frontend/utils -> frontend -> project_root
sys.path.insert(0, str(project_root))

from utils.enhanced_realistic_medical import EnhancedRealisticMedicalProcessor

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_enhanced_effects(patient_id: str, scan_name: str):
    """Test all enhanced realistic effects on the specified patient and scan."""
    
    logger.info(f"Testing enhanced realistic effects for {patient_id}/{scan_name}")
    
    # Create processor
    processor = EnhancedRealisticMedicalProcessor()
    
    # Test effects
    effects_to_test = [
        {
            'name': 'ultra_realistic_anatomy',
            'params': {
                'material_realism': 0.9,
                'lighting_quality': 0.8,
                'texture_detail': 0.7
            },
            'description': 'Ultra-realistic anatomical visualization with advanced material properties'
        },
        {
            'name': 'photorealistic_organs',
            'params': {
                'organ_detail': 0.8,
                'surface_quality': 0.9
            },
            'description': 'Photorealistic organ rendering with enhanced surface quality'
        },
        {
            'name': 'medical_grade_rendering',
            'params': {
                'professional_quality': 1.0,
                'clinical_accuracy': 0.9
            },
            'description': 'Medical-grade professional rendering with clinical accuracy'
        }
    ]
    
    results = []
    
    for effect in effects_to_test:
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing effect: {effect['name']}")
        logger.info(f"Description: {effect['description']}")
        logger.info(f"{'='*60}")
        
        try:
            # Process files with this effect
            processed_files = processor.process_files(
                patient_id=patient_id,
                scan_name=scan_name,
                effect_name=effect['name'],
                effect_params=effect['params']
            )
            
            if processed_files:
                logger.info(f"✅ Successfully processed {len(processed_files)} files with {effect['name']}")
                results.append({
                    'effect': effect['name'],
                    'status': 'success',
                    'files_processed': len(processed_files),
                    'files': processed_files
                })
                
                # Log some example files
                for i, file_path in enumerate(processed_files[:3]):  # Show first 3 files
                    logger.info(f"  - {file_path}")
                if len(processed_files) > 3:
                    logger.info(f"  ... and {len(processed_files) - 3} more files")
            else:
                logger.warning(f"❌ No files were processed for {effect['name']}")
                results.append({
                    'effect': effect['name'],
                    'status': 'no_files',
                    'files_processed': 0,
                    'files': []
                })
                
        except Exception as e:
            logger.error(f"❌ Error testing {effect['name']}: {e}")
            results.append({
                'effect': effect['name'],
                'status': 'error',
                'files_processed': 0,
                'files': [],
                'error': str(e)
            })
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*60}")
    
    successful_tests = [r for r in results if r['status'] == 'success']
    failed_tests = [r for r in results if r['status'] in ['error', 'no_files']]
    
    logger.info(f"✅ Successful tests: {len(successful_tests)}")
    for result in successful_tests:
        logger.info(f"  - {result['effect']}: {result['files_processed']} files processed")
    
    if failed_tests:
        logger.info(f"❌ Failed tests: {len(failed_tests)}")
        for result in failed_tests:
            error_msg = f" - {result['error']}" if 'error' in result else ""
            logger.info(f"  - {result['effect']}: {result['status']}{error_msg}")
    
    total_files = sum(r['files_processed'] for r in results)
    logger.info(f"\nTotal files processed across all effects: {total_files}")
    
    if successful_tests:
        logger.info(f"\n🎉 Enhanced realistic effects are working! Check the output directories:")
        for result in successful_tests:
            if result['files']:
                output_dir = result['files'][0].parent
                logger.info(f"  - {result['effect']}: {output_dir}")
    
    return results


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Test enhanced realistic medical visualization effects",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test all enhanced effects on a specific patient/scan
  python test_enhanced_realistic_effects.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3
  
  # Test with verbose logging
  python test_enhanced_realistic_effects.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 --verbose
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
        results = test_enhanced_effects(args.patient, args.scan)
        
        # Exit with appropriate code
        successful_tests = [r for r in results if r['status'] == 'success']
        if successful_tests:
            logger.info(f"\n✅ Test completed successfully!")
            sys.exit(0)
        else:
            logger.error(f"\n❌ All tests failed!")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
