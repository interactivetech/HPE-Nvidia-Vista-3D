#!/usr/bin/env python3
"""
Create a sample NIfTI file for testing the 3D viewer
"""
import numpy as np
import nibabel as nib
import os

def create_sample_nifti():
    """Create a simple 3D NIfTI file with a sphere for testing"""
    
    # Create a 64x64x64 volume
    size = 64
    data = np.zeros((size, size, size), dtype=np.float32)
    
    # Create a sphere in the center
    center = size // 2
    radius = 20
    
    for x in range(size):
        for y in range(size):
            for z in range(size):
                dist = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
                if dist <= radius:
                    # Create intensity gradient from center to edge
                    intensity = 1.0 - (dist / radius) * 0.5
                    data[x, y, z] = intensity
    
    # Add some noise
    data += np.random.normal(0, 0.1, data.shape)
    data = np.clip(data, 0, 1)
    
    # Create proper affine transformation matrix
    affine = np.eye(4)
    affine[:3, :3] = np.eye(3) * 2.0  # 2mm voxel size
    affine[:3, 3] = [-size, -size, -size]  # Center the volume
    
    # Create NIfTI image with proper header
    nii_img = nib.Nifti1Image(data, affine)
    
    # Set proper header information
    header = nii_img.header
    header.set_data_dtype(np.float32)
    header['cal_min'] = 0.0
    header['cal_max'] = 1.0
    header['descrip'] = b'Test brain volume for 3D viewer'
    
    # Save to assets folder
    os.makedirs('assets', exist_ok=True)
    output_path = 'assets/sample_brain.nii.gz'
    nib.save(nii_img, output_path)
    
    print(f"✅ Sample NIfTI file created: {output_path}")
    print(f"   Shape: {data.shape}")
    print(f"   Data range: {data.min():.3f} to {data.max():.3f}")
    print(f"   File size: {os.path.getsize(output_path) / 1024:.1f} KB")
    
    return output_path

if __name__ == "__main__":
    create_sample_nifti()
