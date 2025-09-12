# Extras: Voxel2Mesh and Mesh2STL Pipeline

This directory contains utilities for converting medical imaging data (NIfTI files) to 3D printable STL files.

## Overview

The pipeline consists of several modules that work together:

1. **`voxel2mesh.py`** - Converts NIfTI medical imaging files to 3D meshes
2. **`mesh2stl.py`** - Converts 3D meshes to STL files for 3D printing
3. **`nifti_viewer.py`** - Interactive Streamlit web app for viewing and analyzing NIfTI files
4. **`stl_viewer.py`** - Interactive Streamlit web app for viewing and analyzing STL files
5. **`ply_viewer.py`** - Interactive Streamlit web app for viewing and analyzing PLY files
6. **`example_usage.py`** - Comprehensive examples showing how to use both modules

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

### Option 3: Interactive Viewers

```bash
# Install viewer dependencies
pip install -r requirements_stl_viewer.txt

# Launch the NIfTI viewer
streamlit run nifti_viewer.py

# Launch the STL viewer (in another terminal)
streamlit run stl_viewer.py

# Launch the PLY viewer (in another terminal)
streamlit run ply_viewer.py
```

## Dependencies

### Core Pipeline Dependencies
Install required packages for the voxel2mesh and mesh2stl pipeline:

```bash
pip install open3d nibabel trimesh numpy
```

### Viewer Dependencies
For the interactive NIfTI, STL, and PLY viewers, install additional packages:

```bash
pip install -r requirements_stl_viewer.txt
```

Or install individually:
```bash
pip install streamlit plotly trimesh numpy pandas open3d nibabel scipy matplotlib opencv-python
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

### stl_viewer.py

Interactive Streamlit web application for viewing and analyzing STL files with 3D visualization.

**Features:**
- Upload and view STL files with interactive 3D visualization
- Display comprehensive mesh statistics and properties
- Multiple view modes (solid, wireframe, both)
- Export to different formats (STL, PLY, OBJ)
- Advanced analysis tools (bounding box, center of mass)
- Batch processing of multiple STL files

**Usage:**
```bash
streamlit run stl_viewer.py
```

**Key Functions:**
- `load_stl_file(file_path)` - Load STL file and return trimesh object
- `get_mesh_info(mesh)` - Extract comprehensive mesh statistics
- `create_3d_plot(mesh)` - Create interactive 3D visualization
- `export_mesh_data(mesh, format)` - Export mesh in various formats

### ply_viewer.py

Interactive Streamlit web application for viewing and analyzing PLY (Polygon File Format) files with 3D visualization and color support.

**Features:**
- Upload and view PLY files with interactive 3D visualization
- Support for vertex colors and textures
- Multiple view modes (solid, wireframe, point cloud, all)
- Display comprehensive mesh statistics and properties
- Export to different formats (PLY, STL, OBJ, OFF)
- Advanced analysis tools (bounding box, center of mass, color analysis)
- Mesh quality analysis and validation
- Batch processing of multiple PLY files

**Usage:**
```bash
streamlit run ply_viewer.py
```

**Key Functions:**
- `load_ply_file(file_path)` - Load PLY file and return trimesh object
- `get_ply_mesh_info(mesh)` - Extract comprehensive PLY mesh statistics
- `create_ply_3d_plot(mesh)` - Create interactive 3D visualization with color support
- `analyze_ply_quality(mesh)` - Analyze mesh quality and detect issues
- `export_ply_mesh_data(mesh, format)` - Export mesh in various formats

### nifti_viewer.py

Interactive Streamlit web application for viewing and analyzing NIfTI medical imaging files with 3D volume rendering and 2D slice viewing.

**Features:**
- Upload and view NIfTI files with interactive 3D volume rendering
- 2D slice viewer for axial, sagittal, and coronal orientations
- Window/level controls for intensity adjustment
- Display comprehensive volume statistics and properties
- Export to different formats (NIfTI, NumPy)
- Integration with voxel2mesh pipeline
- Intensity histogram analysis
- Advanced volume statistics

**Usage:**
```bash
streamlit run nifti_viewer.py
```

**Key Functions:**
- `load_nifti_file(file_path)` - Load NIfTI file and return nibabel image object
- `get_nifti_info(img)` - Extract comprehensive NIfTI image statistics
- `create_3d_volume_plot(data)` - Create interactive 3D volume rendering
- `create_slice_plot(data, slice_idx, orientation)` - Create 2D slice visualization
- `calculate_window_level(data)` - Calculate appropriate window/level for display
- `export_nifti_data(img, format)` - Export image in various formats

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
├── voxel2mesh.py              # NIfTI to mesh conversion
├── mesh2stl.py                # Mesh to STL conversion  
├── nifti_viewer.py            # Interactive NIfTI viewer (Streamlit)
├── stl_viewer.py              # Interactive STL viewer (Streamlit)
├── ply_viewer.py              # Interactive PLY viewer (Streamlit)
├── requirements_stl_viewer.txt # Viewer dependencies
├── example_usage.py           # Comprehensive usage examples
└── README.md                  # This documentation
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
DICOM → Vista3D → NIfTI segments → nifti_viewer → voxel2mesh → STL/PLY files → viewers
```

### Interactive Viewers Workflow

The NIfTI, STL, and PLY viewers provide interactive interfaces for different stages of the pipeline:

#### NIfTI Viewer
1. **Load NIfTI Files**: Upload new NIfTI files or select from existing ones
2. **3D Volume Rendering**: Interactive 3D volume visualization with threshold controls
3. **2D Slice Viewing**: Navigate through axial, sagittal, and coronal slices
4. **Window/Level Controls**: Adjust intensity display for optimal visualization
5. **Volume Analysis**: View comprehensive statistics and properties
6. **Export**: Convert to different formats or prepare for mesh conversion

#### STL Viewer
1. **Load STL Files**: Upload new STL files or select from existing ones
2. **3D Visualization**: Interactive 3D viewing with rotation, zoom, and pan
3. **Analysis**: View mesh statistics, properties, and geometric information
4. **Export**: Convert to different formats or download processed files
5. **Advanced Features**: Bounding box analysis, center of mass calculation

#### PLY Viewer
1. **Load PLY Files**: Upload new PLY files or select from existing ones
2. **3D Visualization**: Interactive 3D viewing with support for vertex colors and textures
3. **Multiple View Modes**: Solid, wireframe, point cloud, or all combined
4. **Color Analysis**: Analyze vertex colors and create color histograms
5. **Quality Analysis**: Detect degenerate faces, duplicate vertices, and mesh issues
6. **Export**: Convert to different formats (PLY, STL, OBJ, OFF)

Both viewers automatically scan common output directories for existing files and provide user-friendly interfaces for exploring the 3D models created by the pipeline.

## License

Part of the HPE-Nvidia-Vista-3D project.
