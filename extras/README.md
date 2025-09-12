# Extras: Voxel2Mesh and Mesh2STL Pipeline

This directory contains utilities for converting medical imaging data (NIfTI files) to 3D printable STL files.

## Overview

The pipeline consists of two main modules that work together:

1. **`voxel2mesh.py`** - Converts NIfTI medical imaging files to 3D meshes
2. **`mesh2stl.py`** - Converts 3D meshes to STL files for 3D printing
3. **`example_usage.py`** - Comprehensive examples showing how to use both modules

## Quick Start

### Option 1: Run Scripts Directly

```bash
# Convert NIfTI files to meshes
python extras/voxel2mesh.py

# Convert meshes to STL files
python extras/mesh2stl.py
```

### Option 2: Use as Modules (Recommended)

```python
from voxel2mesh import process_voxels_directory
from mesh2stl import export_meshes_to_stl_files

# Step 1: Convert NIfTI files to meshes
meshes = process_voxels_directory("/path/to/voxels", threshold=0.5)

# Step 2: Export to STL files
export_meshes_to_stl_files(meshes, "/path/to/output")
```

## Dependencies

Install required packages:

```bash
pip install open3d nibabel trimesh numpy
```

## Module Documentation

### voxel2mesh.py

Converts NIfTI medical imaging files to 3D meshes using Open3D's marching cubes algorithm.

**Key Functions:**
- `nifti_to_mesh(nifti_path, threshold=0.5)` - Convert single NIfTI file to mesh
- `process_voxels_directory(voxels_dir, threshold=0.5)` - Process entire directory

**Parameters:**
- `threshold`: Controls which voxels are included in the mesh (0.0-1.0)
- Lower values = more detailed meshes, higher values = simpler meshes

### mesh2stl.py

Converts 3D mesh data to STL (STereoLithography) files for 3D printing.

**Key Functions:**
- `export_mesh_to_stl_bytes(o3d_mesh)` - Convert single mesh to STL bytes
- `export_meshes_to_stl_files(combined_meshes, output_dir)` - Export multiple meshes to individual STL files

## Usage Examples

### Basic Pipeline

```python
from voxel2mesh import process_voxels_directory
from mesh2stl import export_meshes_to_stl_files

# Convert all NIfTI files in directory
meshes = process_voxels_directory("/path/to/voxels", threshold=0.5)

# Export to STL files
export_meshes_to_stl_files(meshes, "/path/to/output")
```

### Individual File Processing

```python
from voxel2mesh import nifti_to_mesh
from mesh2stl import export_mesh_to_stl_bytes

# Process single file
mesh_data = nifti_to_mesh("/path/to/file.nii.gz", threshold=0.3)

# Convert to STL
stl_data = export_mesh_to_stl_bytes(mesh_data)
with open("output.stl", "wb") as f:
    f.write(stl_data)
```

### Custom Mesh Data

```python
from mesh2stl import export_meshes_to_stl_files

# Work with custom mesh data
custom_meshes = {
    "heart": {"vertices": vertices_array, "triangles": triangles_array},
    "liver": {"vertices": vertices_array, "triangles": triangles_array}
}

export_meshes_to_stl_files(custom_meshes, "/output/path")
```

### Different Thresholds

```python
# Process with different detail levels
for threshold in [0.3, 0.5, 0.7]:
    meshes = process_voxels_directory("/path/to/voxels", threshold=threshold)
    export_meshes_to_stl_files(meshes, f"/output/threshold_{threshold}")
```

## File Structure

```
extras/
├── voxel2mesh.py      # NIfTI to mesh conversion
├── mesh2stl.py        # Mesh to STL conversion  
├── example_usage.py   # Comprehensive usage examples
└── README.md          # This documentation
```

## Input/Output Formats

### Input
- **NIfTI files** (`.nii.gz`) - Medical imaging format
- Directory structure: `voxels/subdir/*.nii.gz`

### Output
- **STL files** (`.stl`) - 3D printing format
- Mesh data dictionaries for programmatic use

## Troubleshooting

### Common Issues

1. **Empty meshes**: Try adjusting the threshold parameter
2. **Import errors**: Ensure all dependencies are installed
3. **Memory issues**: Process files in smaller batches

### Threshold Guidelines

- **0.1-0.3**: Very detailed meshes (may be noisy)
- **0.4-0.6**: Balanced detail and smoothness (recommended)
- **0.7-0.9**: Smooth, simplified meshes

### Performance Tips

- Use appropriate threshold values for your data
- Process files in batches for large datasets
- Consider mesh simplification for very detailed models

## Integration with HPE-Nvidia-Vista-3D

These utilities are designed to work with the output from the Vista3D analysis pipeline:

1. Vista3D processes DICOM files and creates NIfTI segments
2. `voxel2mesh.py` converts the segments to 3D meshes
3. `mesh2stl.py` creates 3D printable STL files

The typical workflow is:
```
DICOM → Vista3D → NIfTI segments → voxel2mesh → STL files
```

## License

Part of the HPE-Nvidia-Vista-3D project.
