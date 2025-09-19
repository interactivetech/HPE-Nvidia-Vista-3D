# NIfTI to PLY Conversion Script

## Overview

The `nifti2ply.py` script is an enhanced NIfTI to PLY (Polygon File Format) converter designed specifically for the Vista-3D pipeline. It converts medical imaging files to 3D mesh format using high-quality marching cubes algorithm, supporting both single file conversion and batch processing of voxels folders from the Vista-3D output structure.

## Features

- **High-Quality Mesh Generation**: Uses marching cubes algorithm with multiple fallback strategies
- **Batch Processing**: Processes all voxels folders in the Vista-3D output structure
- **Single File Conversion**: Command-line interface for individual file conversion
- **Automatic Voxel Spacing**: Preserves original voxel dimensions for accurate 3D representation
- **Gaussian Smoothing**: Optional smoothing for improved mesh quality
- **Label Extraction**: Support for extracting specific anatomical labels
- **Progress Tracking**: Real-time progress bars and detailed logging
- **Error Handling**: Comprehensive error handling with multiple fallback strategies
- **Binary/ASCII Output**: Choice between efficient binary and human-readable ASCII PLY format

## Prerequisites

### Required Software

1. **Python Dependencies**:
   ```bash
   pip install nibabel numpy scikit-image plyfile tqdm python-dotenv
   ```

2. **Optional Dependencies** (for enhanced smoothing):
   ```bash
   pip install scipy
   ```

### Environment Setup

The script requires a `.env` file with the following variables:

```env
# PROJECT_ROOT is now auto-detected
# Use absolute path for OUTPUT_FOLDER
OUTPUT_FOLDER=/path/to/your/output
```

## Directory Structure

The script works with the Vista-3D output structure:

```
project_root/
├── output/                      # Vista-3D output directory
│   ├── PA00000002/             # Patient 1
│   │   ├── voxels/             # Source NIfTI files
│   │   │   ├── 2.5MM_ARTERIAL_3/
│   │   │   │   ├── file1.nii.gz
│   │   │   │   └── file2.nii.gz
│   │   │   └── CORONAL_ABDOMEN_601_i00002/
│   │   │       └── file3.nii.gz
│   │   └── ply/                # Generated PLY files (created automatically)
│   │       ├── 2.5MM_ARTERIAL_3/
│   │       │   ├── file1.ply
│   │       │   └── file2.ply
│   │       └── CORONAL_ABDOMEN_601_i00002/
│   │           └── file3.ply
│   ├── PA00000014/             # Patient 2
│   │   ├── voxels/
│   │   └── ply/
│   └── ...
└── .env                        # Environment configuration
```

## Usage

### Single File Conversion

```bash
# Basic conversion (creates input.ply)
python utils/nifti2ply.py input.nii.gz

# Specify output file
python utils/nifti2ply.py input.nii.gz output.ply

# With custom parameters
python utils/nifti2ply.py input.nii.gz --threshold 0.5 --smooth 1.0 --verbose

# Extract specific label
python utils/nifti2ply.py input.nii.gz --label 1 --smooth 2.0

# ASCII format output
python utils/nifti2ply.py input.nii.gz --ascii --verbose
```

### Batch Processing

```bash
# Process all voxels folders
python utils/nifti2ply.py --batch

# Process specific patient
python utils/nifti2ply.py --batch --patient PA00000002

# Force overwrite existing PLY files
python utils/nifti2ply.py --batch --force

# Custom parameters for batch processing
python utils/nifti2ply.py --batch --threshold 0.2 --smooth 1.5 --verbose
```

### Command Line Options

| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `input` | Input NIfTI file (.nii or .nii.gz) | Required for single file | `input.nii.gz` |
| `output` | Output PLY file (.ply) | Auto-generated from input | `output.ply` |
| `--batch` | Process all voxels folders | False | `--batch` |
| `--patient` | Process specific patient ID | None | `--patient PA00000002` |
| `--force` | Force overwrite existing PLY files | False | `--force` |
| `--threshold` | Threshold value for binary mask | 0.1 | `--threshold 0.5` |
| `--label` | Extract specific label value | None | `--label 1` |
| `--smooth` | Smoothing factor for mesh | 1.0 | `--smooth 2.0` |
| `--ascii` | Write ASCII PLY format | Binary | `--ascii` |
| `--verbose`, `-v` | Enable verbose output | False | `--verbose` |

## Core Functions

### `load_environment()`

Loads environment variables from the `.env` file.

**Returns**: `str` - Project root path (auto-detected)

**Raises**: `RuntimeError` if project root cannot be determined

### `check_voxels_folders_exist(output_path: Path)`

Validates that the output directory contains voxels folders.

**Parameters**:
- `output_path` (Path): Path to output directory

**Returns**: `bool` - True if voxels folders exist

### `get_patient_directories(output_path: Path, specific_patient=None)`

Gets list of patient directories that have voxels folders.

**Parameters**:
- `output_path` (Path): Path to output directory
- `specific_patient` (str, optional): Specific patient ID to process

**Returns**: `list` - List of patient directory paths

### `load_nifti(filepath)`

Loads NIfTI file and returns image data and affine transformation.

**Parameters**:
- `filepath` (str): Path to NIfTI file

**Returns**: `tuple` - (image_data, affine_matrix)

**Raises**: `SystemExit` on loading error

### `generate_mesh(data, threshold=0.1, label_value=None, smooth=1.0, spacing=None)`

Generates mesh from 3D data using marching cubes with multiple fallback strategies.

**Parameters**:
- `data` (numpy.ndarray): 3D image data
- `threshold` (float): Threshold for binary mask (default: 0.1)
- `label_value` (int, optional): Specific label value to extract
- `smooth` (float): Smoothing factor for mesh (default: 1.0)
- `spacing` (tuple, optional): Voxel spacing (x, y, z)

**Returns**: `tuple` - (vertices, faces, normals) or (None, None, None) on failure

**Features**:
- Automatic threshold adjustment based on data range
- Multiple level values for marching cubes
- Different gradient directions
- Gaussian smoothing with scipy (if available)
- Sparse threshold fallback

### `write_ply(vertices, faces, normals, output_path, binary=True)`

Writes mesh data to PLY file with vertex normals.

**Parameters**:
- `vertices` (numpy.ndarray): Vertex coordinates
- `faces` (numpy.ndarray): Face indices
- `normals` (numpy.ndarray): Vertex normals
- `output_path` (str): Output file path
- `binary` (bool): Whether to write binary PLY format

**Features**:
- Includes vertex normals for proper lighting
- Binary format for efficiency (default)
- ASCII format for human readability
- Comprehensive error handling

### `convert_single_file(input_file, output_file, threshold=0.1, label_value=None, smooth=1.0, ascii=False, verbose=False)`

Converts a single NIfTI file to PLY format.

**Parameters**:
- `input_file` (str): Input NIfTI file path
- `output_file` (str): Output PLY file path
- `threshold` (float): Threshold value for binary mask
- `label_value` (int, optional): Specific label value to extract
- `smooth` (float): Smoothing factor for mesh
- `ascii` (bool): Whether to write ASCII PLY format
- `verbose` (bool): Enable verbose output

**Returns**: `bool` - True if conversion successful

### `convert_voxels_to_ply(force_overwrite=False, threshold=0.1, label_value=None, smooth=1.0, ascii=False, specific_patient=None, verbose=False)`

Main batch conversion function that processes all voxels folders.

**Parameters**:
- `force_overwrite` (bool): Overwrite existing PLY files
- `threshold` (float): Threshold value for binary mask
- `label_value` (int, optional): Specific label value to extract
- `smooth` (float): Smoothing factor for mesh
- `ascii` (bool): Whether to write ASCII PLY format
- `specific_patient` (str, optional): Process only specific patient ID
- `verbose` (bool): Enable verbose output

**Features**:
- Progress tracking with tqdm
- Automatic PLY directory creation
- Organized output structure matching voxels folders
- Comprehensive error handling and cleanup
- Detailed success/failure reporting

## Mesh Generation Algorithm

### Marching Cubes Implementation

The script uses scikit-image's marching cubes algorithm with the following features:

1. **Automatic Threshold Adjustment**: Adjusts threshold based on data range
2. **Multiple Level Values**: Tries different level values if default fails
3. **Gradient Direction Options**: Tests both 'descent' and 'ascent' directions
4. **Smoothing Integration**: Optional Gaussian smoothing for better mesh quality
5. **Sparse Threshold Fallback**: Uses 1% of max value as last resort

### Quality Settings

- **Default Threshold**: 0.1 (high quality, captures more detail)
- **Default Smoothing**: 1.0 (balanced quality vs. performance)
- **Voxel Spacing**: Automatically extracted from NIfTI affine matrix
- **Binary Format**: Default for efficiency and smaller file sizes

## Output Files

### PLY File Format

The generated PLY files include:

1. **Vertex Data**: 3D coordinates (x, y, z)
2. **Face Data**: Triangular face indices
3. **Normal Data**: Vertex normals for proper lighting
4. **Format**: Binary (default) or ASCII

### File Structure

```
ply/
├── patient_id/
│   ├── series_name_1/
│   │   ├── file1.ply
│   │   └── file2.ply
│   └── series_name_2/
│       └── file3.ply
```

## Error Handling

### Comprehensive Fallback Strategies

1. **Threshold Adjustment**: Automatically adjusts if outside data range
2. **Multiple Level Values**: Tries 10 different level values
3. **Gradient Directions**: Tests both descent and ascent
4. **Smoothing Fallback**: Falls back to unsmoothed data if smoothing fails
5. **Sparse Threshold**: Uses 1% of max value as last resort

### Error Messages

- **No voxels found**: Suggests adjusting threshold or label value
- **Threshold adjusted**: Warns when threshold is automatically adjusted
- **Level value used**: Reports which level value worked
- **Smoothing unavailable**: Warns if scipy not available for smoothing

## Performance Considerations

### Memory Usage

- Processes one file at a time to minimize memory usage
- Uses efficient numpy operations
- Optional smoothing with scipy for better quality

### Processing Time

Typical processing times:
- Small files (< 50 MB): 10-30 seconds per file
- Medium files (50-200 MB): 30 seconds - 2 minutes per file
- Large files (> 200 MB): 2-5 minutes per file

### File Size

PLY file sizes are typically:
- 10-50% of original NIfTI file size
- Binary format: ~30% smaller than ASCII
- Quality depends on threshold and smoothing settings

## Troubleshooting

### Common Issues

1. **No voxels found above threshold**
   ```
   Warning: No voxels found above threshold. Try adjusting threshold or label value.
   ```
   **Solution**: Lower the threshold value or check if label value is correct

2. **Threshold adjusted**
   ```
   Warning: Threshold adjusted to 0.900 (data range: 0.000 to 1.000)
   ```
   **Solution**: This is normal - the script automatically adjusts thresholds

3. **Could not generate mesh with any method**
   ```
   Error: Could not generate mesh with any method
   ```
   **Solution**: Check if the NIfTI file contains valid 3D data

4. **scipy not available for smoothing**
   ```
   Warning: scipy not available for smoothing. Install scipy for better mesh quality.
   ```
   **Solution**: Install scipy for enhanced smoothing: `pip install scipy`

### Debug Mode

Use `--verbose` flag for detailed debugging information:
- Data range and statistics
- Voxel spacing information
- Mesh generation attempts
- File conversion progress

## Integration with Vista-3D Pipeline

This script is designed to work seamlessly with the Vista-3D pipeline:

1. **Input**: NIfTI files from voxels folders (generated by segmentation)
2. **Processing**: High-quality mesh generation with medical imaging optimizations
3. **Output**: PLY files organized in matching folder structure
4. **Quality**: Preserves voxel spacing and anatomical accuracy

## Examples

### Basic Batch Processing

```bash
# Process all patients with default settings
python utils/nifti2ply.py --batch

# Process with custom quality settings
python utils/nifti2ply.py --batch --threshold 0.2 --smooth 1.5 --verbose
```

### Single File with Label Extraction

```bash
# Extract specific anatomical structure (label 1)
python utils/nifti2ply.py input.nii.gz --label 1 --smooth 2.0 --verbose

# High-quality conversion with ASCII output
python utils/nifti2ply.py input.nii.gz --threshold 0.05 --smooth 1.0 --ascii
```

### Programmatic Usage

```python
from utils.nifti2ply import convert_single_file, convert_voxels_to_ply

# Single file conversion
success = convert_single_file(
    input_file="input.nii.gz",
    output_file="output.ply",
    threshold=0.1,
    smooth=1.0,
    verbose=True
)

# Batch processing
convert_voxels_to_ply(
    force_overwrite=True,
    threshold=0.2,
    smooth=1.5,
    verbose=True
)
```

## References

- [PLY File Format Specification](http://paulbourke.net/dataformats/ply/)
- [Marching Cubes Algorithm](https://en.wikipedia.org/wiki/Marching_cubes)
- [scikit-image marching_cubes](https://scikit-image.org/docs/stable/api/skimage.measure.html#marching-cubes)
- [NIfTI Format Specification](https://nifti.nimh.nih.gov/nifti-1/)
- [plyfile Python Library](https://github.com/dranjan/python-plyfile)

## License

This script is part of the Vista-3D segmentation pipeline and follows the same licensing terms as the parent project.
