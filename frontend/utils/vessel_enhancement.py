#!/usr/bin/env python3
"""
Vessel Enhancement Script for Vista3D

This script applies specialized vessel enhancement effects to create realistic
vascular visualization similar to professional medical imaging software.

Usage:
    python vessel_enhancement.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3
    python vessel_enhancement.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 --thickness 2.5 --contrast 1.5
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

# Import the voxel effects processor
from frontend.utils.voxel_effects import VoxelEffectsProcessor

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Main command-line interface for vessel enhancement."""
    parser = argparse.ArgumentParser(
        description="Apply vessel enhancement effects to create realistic vascular visualization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Apply standard vessel enhancement
  python vessel_enhancement.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3
  
  # Apply enhanced vessel thickness and contrast
  python vessel_enhancement.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 --thickness 2.5 --contrast 1.5
  
  # Apply maximum vessel enhancement for high-quality visualization
  python vessel_enhancement.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 --thickness 3.0 --wall-enhancement 2.0 --texture 1.2 --contrast 1.8
        """
    )
    
    # Required arguments
    parser.add_argument("--patient", required=True, help="Patient ID (e.g., PA00000002)")
    parser.add_argument("--scan", required=True, help="Scan name (e.g., 2.5MM_ARTERIAL_3)")
    
    # Vessel enhancement parameters
    parser.add_argument("--thickness", type=float, default=2.0, 
                       help="Vessel wall thickness multiplier (1.0-4.0, default: 2.0)")
    parser.add_argument("--wall-enhancement", type=float, default=1.5,
                       help="Vessel wall enhancement factor (1.0-3.0, default: 1.5)")
    parser.add_argument("--texture", type=float, default=0.8,
                       help="Vessel texture granularity level (0.0-2.0, default: 0.8)")
    parser.add_argument("--contrast", type=float, default=1.3,
                       help="Vessel contrast boost factor (1.0-2.0, default: 1.3)")
    
    # Optional arguments
    parser.add_argument("--output-dir", type=Path, help="Custom output directory")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Create processor
        processor = VoxelEffectsProcessor()
        
        # Prepare vessel enhancement parameters
        effect_params = {
            "vessel_thickness": args.thickness,
            "wall_enhancement": args.wall_enhancement,
            "texture_granularity": args.texture,
            "contrast_boost": args.contrast
        }
        
        logger.info(f"Applying vessel enhancement to {args.patient}/{args.scan}")
        logger.info(f"Parameters: thickness={args.thickness}, wall={args.wall_enhancement}, texture={args.texture}, contrast={args.contrast}")
        
        # Process files with vessel enhancement
        processed_files = processor.process_files(
            patient_id=args.patient,
            scan_name=args.scan,
            effect_name="vessel_enhancement",
            effect_params=effect_params,
            output_dir=args.output_dir
        )
        
        if processed_files:
            print(f"\n✅ Successfully processed {len(processed_files)} vessel files:")
            for file_path in processed_files:
                print(f"  - {file_path}")
            print(f"\n🎨 Vessel enhancement complete! Use the 'realistic_arteries' or 'realistic_veins' colormaps for best results.")
        else:
            print("\n❌ No vessel files were processed.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
