import os
import nibabel as nib
import numpy as np
from pathlib import Path

def create_overlay(original_path: Path, segment_path: Path):
    """Creates an overlay of a colored segmentation on top of an original NIfTI image."""
    try:
        # Load the original and segmented images
        original_nii = nib.load(original_path)
        segment_nii = nib.load(segment_path)

        original_data = original_nii.get_fdata()
        segment_data = segment_nii.get_fdata()

        # Normalize original data to 0-255 range for grayscale conversion
        original_data = (original_data - original_data.min()) / (original_data.max() - original_data.min()) * 255
        original_data = original_data.astype(np.uint8)

        # Convert grayscale original image to a 3-channel RGB image
        original_rgb = np.stack([original_data]*3, axis=-1)

        # Ensure segment_data is also uint8
        segment_data = segment_data.astype(np.uint8)

        # Create a mask where the segmentation is not black
        mask = np.any(segment_data > [0, 0, 0], axis=-1)

        # Create the overlay image
        overlay_data = original_rgb.copy()
        
        # Where the mask is true, blend the images
        # You can adjust the alpha value to change the transparency of the overlay
        alpha = 0.6
        overlay_data[mask] = (alpha * segment_data[mask] + (1 - alpha) * original_rgb[mask]).astype(np.uint8)

        # Create a new NIfTI image for the overlay
        overlay_nii = nib.Nifti1Image(overlay_data, original_nii.affine, original_nii.header)
        return overlay_nii

    except Exception as e:
        print(f"Error creating overlay for {original_path.name}: {e}")
        return None

def main():
    """
    Main function to find all NIfTI files in outputs/nifti, 
    create overlays with corresponding segmentations, and save them in outputs/overlay.
    """
    project_root = Path(__file__).resolve().parent.parent
    nifti_dir = project_root / 'outputs' / 'nifti'
    segments_dir = project_root / 'outputs' / 'segments'
    overlay_dir = project_root / 'outputs' / 'overlay'

    if not nifti_dir.exists():
        print(f"Error: Input directory not found at {nifti_dir}")
        return

    if not segments_dir.exists():
        print(f"Error: Segments directory not found at {segments_dir}")
        return

    print(f"Searching for NIfTI files in {nifti_dir}...")
    
    nifti_files = list(nifti_dir.glob('**/*.nii')) + list(nifti_dir.glob('**/*.nii.gz'))

    if not nifti_files:
        print("No NIfTI files found.")
        return

    print(f"Found {len(nifti_files)} potential images to process.")

    for original_file in nifti_files:
        print(f"--- Processing file: {original_file.name} ---")
        
        # Determine corresponding segment and output paths
        relative_path = original_file.relative_to(nifti_dir)
        
        # The segment file has a `_colored_seg` suffix
        segment_filename = original_file.stem.replace('.nii', '') + '_colored_seg.nii.gz'
        segment_file = segments_dir / relative_path.parent / segment_filename

        output_path = overlay_dir / relative_path

        if not segment_file.exists():
            print(f"Segment file not found, skipping: {segment_file}")
            continue

        if output_path.exists():
            print(f"Output file already exists, skipping: {output_path}")
            continue

        # Create the overlay
        overlay_nii = create_overlay(original_file, segment_file)

        if overlay_nii:
            # Create output directory
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            print(f"Saving overlay to {output_path}")
            nib.save(overlay_nii, output_path)
            print("Done.")
        print("-" * (len(str(original_file.name)) + 20))

if __name__ == "__main__":
    main()
