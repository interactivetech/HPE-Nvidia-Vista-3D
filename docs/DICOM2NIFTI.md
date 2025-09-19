# DICOM to NIFTI Conversion Script

## Overview

The `dicom2nifti.py` script is an enhanced DICOM to NIFTI conversion tool designed specifically for the Vista-3D pipeline. It uses `dcm2niix` for robust conversion and incorporates NiiVue best practices to ensure optimal compatibility with web-based medical image viewers.

## Features

- **Robust Conversion**: Uses `dcm2niix` for industry-standard DICOM to NIFTI conversion
- **NiiVue Optimization**: Enhanced for optimal compatibility with NiiVue web viewers
- **BIDS Compliance**: Generates BIDS-compliant JSON sidecar metadata
- **Quality Reports**: Comprehensive quality analysis for each converted file
- **Size Filtering**: Optional filtering of small files to reduce storage
- **Progress Tracking**: Real-time progress bars and detailed logging
- **Error Handling**: Robust error handling with cleanup of failed conversions

## Prerequisites

### Required Software

1. **dcm2niix**: The core conversion tool
   ```bash
   # Install via conda
   conda install -c conda-forge dcm2niix
   
   # Or install via pip
   pip install dcm2niix
   
   # Or download from GitHub
   # https://github.com/rordenlab/dcm2niix
   ```

2. **Python Dependencies**:
   ```bash
   pip install nibabel numpy tqdm python-dotenv
   ```

### Environment Setup

The script requires a `.env` file with the following variables:

```env
# PROJECT_ROOT is now auto-detected
DICOM_FOLDER=dicom
```

## Directory Structure

The script expects the following directory structure:

```
project_root/
├── dicom/                    # Source DICOM files
│   ├── PA00000002/          # Patient 1 DICOM files
│   ├── PA00000014/          # Patient 2 DICOM files
│   └── ...
├── output/                   # Generated NIFTI files
│   ├── PA00000002/
│   │   └── nifti/           # Patient 1 NIFTI files
│   ├── PA00000014/
│   │   └── nifti/           # Patient 2 NIFTI files
│   └── ...
└── conf/
    └── vista3d_label_dict.json  # Label dictionary (optional)
```

## Usage

### Basic Usage

```bash
python utils/dicom2nifti.py
```

### Command Line Options

```bash
# Force overwrite existing NIFTI directories
python utils/dicom2nifti.py --force

# Filter out small files (e.g., files smaller than 10 MB)
python utils/dicom2nifti.py --min-size-mb 10

# Combine options
python utils/dicom2nifti.py --force --min-size-mb 20
```

### Programmatic Usage

```python
from utils.dicom2nifti import convert_dicom_to_nifti

# Basic conversion
convert_dicom_to_nifti()

# With options
convert_dicom_to_nifti(
    force_overwrite=True,
    min_size_mb=15
)
```

## Core Functions

### `check_dcm2niix_installation()`

Verifies that `dcm2niix` is installed and accessible in the system PATH.

**Returns**: `bool` - True if dcm2niix is available, False otherwise

### `load_environment()`

Loads environment variables from the `.env` file.

**Returns**: `tuple` - (project_root, dicom_folder)

**Raises**: `ValueError` if required environment variables are missing

### `load_label_dictionary()`

Loads the Vista-3D label dictionary from JSON configuration.

**Returns**: `dict` - Label mapping dictionary

**Fallback**: Returns basic anatomical structure mapping if file not found

### `check_patient_folders_exist(dicom_path: Path)`

Validates that the DICOM directory contains patient subdirectories.

**Parameters**:
- `dicom_path` (Path): Path to DICOM directory

**Returns**: `bool` - True if patient folders exist

### `run_dcm2niix_conversion(input_dir, output_dir, filename_format="%d_%s")`

Executes dcm2niix conversion with NiiVue-optimized settings.

**Parameters**:
- `input_dir`: Input DICOM directory
- `output_dir`: Output directory for NIFTI files
- `filename_format`: Output filename format (dcm2niix -f option)

**Returns**: `dict` - Conversion results with status and file lists

**dcm2niix Options Used**:
- `-z y`: Compress output (.nii.gz)
- `-b y`: Generate BIDS sidecar JSON
- `-ba y`: Anonymize BIDS sidecar
- `-f %d_%s`: Filename format
- `-v 2`: Verbose output
- `-x y`: Crop 3D acquisitions

### `enhance_nifti_for_niivue(nifti_file, json_file=None)`

Enhances NIFTI files for optimal NiiVue compatibility and generates quality reports.

**Parameters**:
- `nifti_file`: Path to NIFTI file
- `json_file`: Path to associated JSON sidecar (optional)

**Returns**: `dict` - Enhancement results with quality information

**Quality Report Includes**:
- File information (size, compression)
- Volume information (dimensions, data type, memory usage)
- Data quality metrics (min/max/mean/std values, dynamic range)
- Spatial information (voxel spacing, volume dimensions)
- DICOM metadata (if JSON sidecar available)

### `convert_dicom_to_nifti(force_overwrite=False, min_size_mb=35)`

Main conversion function that processes all DICOM directories.

**Parameters**:
- `force_overwrite` (bool): Overwrite existing NIFTI directories
- `min_size_mb` (int): Delete NIFTI files smaller than this size in MB

## Output Files

For each converted NIFTI file, the script generates:

1. **NIFTI File** (`.nii.gz`): Compressed NIFTI format
2. **JSON Sidecar** (`.json`): BIDS-compliant metadata
3. **Quality Report** (`.quality.json`): Detailed quality analysis

### Quality Report Structure

```json
{
  "file_info": {
    "filename": "example.nii.gz",
    "file_size_mb": 45.2,
    "compression": true
  },
  "volume_info": {
    "dimensions": [512, 512, 100],
    "data_type": "float32",
    "total_voxels": 26214400,
    "memory_usage_mb": 100.0
  },
  "data_quality": {
    "min_value": 0.0,
    "max_value": 4095.0,
    "mean_value": 1024.5,
    "std_value": 512.3,
    "dynamic_range": 4095.0
  },
  "spatial_info": {
    "voxel_spacing_mm": [0.5, 0.5, 1.0],
    "volume_dimensions_mm": [256.0, 256.0, 100.0]
  },
  "dicom_metadata": {
    // BIDS-compliant DICOM metadata
  }
}
```

## Error Handling

The script includes comprehensive error handling:

- **dcm2niix Installation Check**: Verifies tool availability before processing
- **Directory Validation**: Ensures source and destination directories exist
- **Conversion Timeout**: 5-minute timeout for individual conversions
- **Cleanup on Failure**: Removes partial output directories on conversion failure
- **Progress Tracking**: Continues processing other patients if one fails

## Performance Considerations

### File Size Filtering

Use the `--min-size-mb` option to filter out small files that may be:
- Corrupted or incomplete
- Low-quality preview images
- Unnecessary for analysis

### Memory Usage

The script processes one patient at a time to minimize memory usage. Large datasets are handled efficiently through:
- Streaming processing
- Compressed output format
- Quality report generation without loading full datasets into memory

### Processing Time

Typical processing times:
- Small datasets (< 100 MB): 1-2 minutes per patient
- Medium datasets (100-500 MB): 3-5 minutes per patient
- Large datasets (> 500 MB): 5-10 minutes per patient

## Troubleshooting

### Common Issues

1. **dcm2niix not found**
   ```
   ❌ dcm2niix not found in PATH
   ```
   **Solution**: Install dcm2niix and ensure it's in your PATH

2. **Missing environment variables**
   ```
   RuntimeError: Could not determine project root
   ```
   **Solution**: Ensure you're running from within the Vista3D project directory

3. **No patient folders found**
   ```
   FileNotFoundError: No patient folders (subdirectories) found
   ```
   **Solution**: Ensure DICOM files are organized in patient subdirectories

4. **Conversion timeout**
   ```
   ❌ dcm2niix conversion timed out
   ```
   **Solution**: Check for corrupted DICOM files or increase timeout

### Debug Mode

For detailed debugging, the script provides verbose output including:
- dcm2niix command execution details
- File creation logs
- Quality report summaries
- Error messages with context

## Integration with Vista-3D Pipeline

This script is designed to work seamlessly with the Vista-3D pipeline:

1. **Input**: DICOM files organized by patient ID
2. **Processing**: Robust conversion with quality validation
3. **Output**: NiiVue-optimized NIFTI files ready for web viewing
4. **Metadata**: BIDS-compliant sidecar files for downstream processing

## References

- [dcm2niix Documentation](https://github.com/rordenlab/dcm2niix)
- [NiiVue Best Practices](https://github.com/niivue/niivue-dcm2niix)
- [BIDS Specification](https://bids.neuroimaging.io/)
- [NIFTI Format Specification](https://nifti.nimh.nih.gov/nifti-1/)

## License

This script is part of the Vista-3D segmentation pipeline and follows the same licensing terms as the parent project.
