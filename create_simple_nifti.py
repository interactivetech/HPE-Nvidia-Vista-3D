#!/usr/bin/env python3
"""
Create a simple NIfTI file for testing NiiVue viewer
"""

import numpy as np
import nibabel as nib
import os

def create_simple_nifti():
    """Create a simple 3D NIfTI file with a sphere"""
    
    # Create a 32x32x32 volume
    size = 32
    data = np.zeros((size, size, size), dtype=np.float32)
    
    # Create a sphere in the center
    center = size // 2
    radius = 12
    
    for x in range(size):
        for y in range(size):
            for z in range(size):
                dx = x - center
                dy = y - center
                dz = z - center
                dist = np.sqrt(dx*dx + dy*dy + dz*dz)
                
                if dist <= radius:
                    # Create a gradient from center to edge
                    intensity = 1.0 - (dist / radius) * 0.3
                    data[x, y, z] = intensity
    
    # Create affine transformation matrix (identity)
    affine = np.eye(4)
    
    # Create NIfTI image
    nii_img = nib.Nifti1Image(data, affine)
    
    # Set proper header information
    header = nii_img.header
    header.set_data_dtype(np.float32)
    header['cal_min'] = 0.0
    header['cal_max'] = 1.0
    header['descrip'] = b'Simple test volume for NiiVue'
    
    # Ensure proper NIfTI format
    header['dim'] = [3, size, size, size, 1, 1, 1, 1]
    header['pixdim'] = [0, 1, 1, 1, 1, 1, 1, 1]
    header['datatype'] = 16  # Float32
    header['bitpix'] = 32
    
    # Save to assets folder
    os.makedirs('assets', exist_ok=True)
    output_path = 'assets/simple_test.nii.gz'
    nib.save(nii_img, output_path)
    
    print(f"✅ Created simple NIfTI file: {output_path}")
    print(f"   Dimensions: {data.shape}")
    print(f"   Data range: {data.min():.3f} to {data.max():.3f}")
    print(f"   File size: {os.path.getsize(output_path)} bytes")
    
    return output_path

if __name__ == "__main__":
    create_simple_nifti()
