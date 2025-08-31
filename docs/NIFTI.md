# DICOM to NIFTI Processor Documentation

## Overview

The `dicom2nifti_processor.py` script is a specialized tool for converting DICOM medical imaging files to NIFTI (Neuroimaging Informatics Technology Initiative) format, specifically designed for the Vista-3D pipeline. This processor follows the naming conventions and methods established in the demo notebook workflow.

## Features

- **Automatic DICOM to NIFTI conversion** with proper spatial information preservation
- **Environment-based configuration** using `.env` file
- **Intelligent file naming** based on DICOM Series Description metadata
- **Progress tracking** with detailed logging and progress bars
- **Error handling** with graceful fallbacks for corrupted slices
- **Force overwrite capability** for reprocessing existing data
- **Vista-3D label dictionary integration** for anatomical structure mapping

## Prerequisites

### Required Python Packages

```bash
pip install pydicom nibabel numpy tqdm python-dotenv
```

### Required Files

- `.env` file with environment variables
- `vista3d/label_dict.json` containing anatomical structure mappings
- DICOM data organized in patient-specific directories

## Configuration

### Environment Variables (.env)

Create a `.env` file in your project root with the following variables:

```env
PROJECT_ROOT="/home/hpadmin/NV"
DICOM_FOLDER="dicom"
```

- **PROJECT_ROOT**: Absolute path to your project directory
- **DICOM_FOLDER**: Path to DICOM data (relative to PROJECT_ROOT or absolute)

### Label Dictionary

The script automatically loads the Vista-3D label dictionary from `vista3d/label_dict.json`, which contains mappings for 124+ anatomical structures including:

- Background (0)
- Liver (1)
- Spleen (3)
- Pancreas (4)
- Aorta (6)
- Left iliac artery (58)
- Right iliac artery (59)
- And many more...

## Input Data Structure

Your DICOM data should be organized as follows:

```
dicom/
├── PA00000002/
│   ├── dicom_file_CT_001.dcm
│   ├── dicom_file_CT_002.dcm
│   └── ... (390 files)
├── PA00000014/
│   ├── dicom_file_CT_001.dcm
│   ├── dicom_file_CT_002.dcm
│   └── ... (1607 files)
├── PA00000015/
│   ├── dicom_file_CT_001.dcm
│   ├── dicom_file_CT_002.dcm
│   └── ... (488 files)
├── PA00000050/
│   ├── dicom_file_CT_001.dcm
│   ├── dicom_file_CT_002.dcm
│   └── ... (407 files)
└── PA00000058/
    ├── dicom_file_CT_001.dcm
    ├── dicom_file_CT_002.dcm
    └── ... (775 files)
```

## Usage

### Basic Execution

```bash
python utils/dicom2nifti_processor.py
```

### Force Overwrite Existing Files

```bash
python utils/dicom2nifti_processor.py --force
```

### Command Line Options

- **No flags**: Processes only new DICOM directories, skips existing NIFTI files
- **`--force` or `--overwrite`**: Reprocesses all directories, overwriting existing NIFTI files

## Output Structure

After successful conversion, the script creates the following directory structure:

```
outputs/
└── nifti/
    ├── PA00000002/
    │   ├── 01_2.5MM_ARTERIAL.nii.gz
    │   ├── 02_VENOUS_PHASE.nii.gz
    │   └── 03_PRE_CONTRAST.nii.gz
    ├── PA00000014/
    │   ├── 01_ARTERIAL_1.25MM.nii.gz
    │   ├── 02_CORONAL_REFORMAT.nii.gz
    │   └── 03_SAGITTAL_REFORMAT.nii.gz
    ├── PA00000015/
    │   ├── 01_ax_25x25.nii.gz
    │   └── 02_CORONAL_REFORMAT.nii.gz
    ├── PA00000050/
    │   ├── 01_ARTERIAL_PHASE_2.5MM.nii.gz
    │   └── 02_VENOUS_PHASE_2.5MM.nii.gz
    └── PA00000058/
        ├── 01_1.25_mm.nii.gz
        └── 02_CORONAL_REFORMAT.nii.gz
```

### Multiple NIFTI Files Per Patient

The script now intelligently detects different DICOM series within each patient directory and creates separate NIFTI files for each series:

- **Series Detection**: Automatically groups DICOM files by:
  - Series Description (e.g., "2.5MM ARTERIAL", "VENOUS PHASE")
  - Series Number
  - Acquisition Protocol
  - Slice Thickness
  - Other DICOM metadata

- **File Naming**: Each series gets a descriptive filename:
  - **Single series**: `ARTERIAL_PHASE_2.5MM.nii.gz`
  - **Multiple series**: `01_2.5MM_ARTERIAL.nii.gz`, `02_VENOUS_PHASE.nii.gz`

- **Series Separation**: Common series types include:
  - Arterial phase scans
  - Venous phase scans
  - Pre-contrast scans
  - Coronal reformats
  - Sagittal reformats
  - Different slice thicknesses
  - Different acquisition protocols

### File Naming Convention

NIFTI files are automatically named based on DICOM Series Description metadata:

- **Original DICOM Series Description**: `2.5MM ARTERIAL`
- **Generated NIFTI filename**: `2.5MM_ARTERIAL.nii.gz`

The script automatically:
- Replaces spaces with underscores
- Replaces hyphens with underscores  
- Replaces forward slashes with underscores
- Appends `.nii.gz` extension

## Technical Details

### Conversion Process

1. **Environment Loading**: Reads configuration from `.env` file
2. **Label Dictionary Loading**: Loads Vista-3D anatomical structure mappings
3. **DICOM Analysis**: Scans directories for valid DICOM files
4. **Series Detection**: Groups DICOM files by series using multiple metadata attributes
5. **Series Processing**: Processes each series separately to create multiple NIFTI files
6. **Slice Sorting**: Orders slices by position or instance number within each series
7. **Volume Creation**: Builds 3D volume from sorted slices for each series
8. **Affine Matrix**: Extracts spatial information from DICOM headers
9. **NIFTI Generation**: Creates properly formatted NIFTI files for each series
10. **File Naming**: Generates descriptive filenames with series numbering

### Series Detection Algorithm

The script uses intelligent series detection to separate different DICOM acquisitions:

- **Primary Key**: Series Description (most descriptive identifier)
- **Secondary Keys**: 
  - Series Number (sequential ordering)
  - Protocol Name (acquisition protocol)
  - Slice Thickness (spatial resolution)
- **Fallback**: Unknown series for unreadable files
- **Grouping**: Files with identical metadata are grouped together
- **Sorting**: Series are processed in consistent order

### Spatial Information Preservation

The script preserves critical spatial information:

- **Pixel Spacing**: X and Y dimensions from DICOM headers
- **Slice Thickness**: Z dimension spacing
- **Patient Position**: Origin coordinates in real-world space
- **Affine Transformation**: 4x4 transformation matrix for coordinate mapping

### Error Handling

- **Corrupted Slices**: Automatically skips slices with wrong dimensions
- **Missing Metadata**: Falls back to default values for spatial information
- **File I/O Errors**: Graceful handling with detailed error reporting
- **Directory Cleanup**: Removes failed output directories on errors

### Performance Features

- **Progress Bars**: Real-time progress tracking for both patients and slices
- **Memory Efficient**: Processes slices individually to minimize memory usage
- **Batch Processing**: Handles multiple patient directories efficiently
- **Skip Logic**: Avoids reprocessing existing files unless forced

## Example Output

### Successful Conversion

```
✅ Loaded label dictionary with 124 anatomical structures
Project Root: /home/hpadmin/NV
DICOM Source: /home/hpadmin/NV/dicom
NIFTI Destination: /home/hpadmin/NV/outputs/nifti
--------------------------------------------------
Found 5 DICOM directories to process
Progress bar will show below:
--------------------------------------------------
Processing patients:   0%|  | 0/5 [00:00<?, ?patient/s]

Processing: PA00000002
----------
Saving NIFTI files into directory /home/hpadmin/NV/outputs/nifti/PA00000002
📊 Found 390 valid DICOM files
Analyzing DICOM files for slice information...
✅ Sorted 390 slices
📊 Volume specifications:
   Width: 512 pixels
   Height: 512 pixels
   Slices: 390
   Total voxels: 102,236,160
🔄 Creating 3D volume...
✅ Successfully processed 388/390 slices
📐 Created affine matrix with spacing: 0.70 x 0.70 x 2.50 mm
💾 Successfully created: 2.5MM_ARTERIAL.nii.gz
📊 Final volume: (512, 512, 390)
📏 Data range: [-1133, 4423]
💾 File size: 93.8 MB
```

### File Specifications

| Patient ID | Series Description | Dimensions | Slices | File Size | Spacing (mm) |
|------------|-------------------|------------|---------|-----------|--------------|
| PA00000002 | 2.5MM ARTERIAL | 512×512×390 | 390 | 93.8 MB | 0.70×0.70×2.50 |
| PA00000014 | ARTERIAL 1.25MM | 512×512×1607 | 1607 | 436.7 MB | 0.88×0.88×0.62 |
| PA00000015 | ax 25x25 | 512×512×488 | 488 | 117.4 MB | 0.98×0.98×2.50 |
| PA00000050 | ARTERIAL PHASE 2.5MM | 512×512×407 | 407 | 95.6 MB | 0.70×0.70×2.50 |
| PA00000058 | 1.25 mm | 512×512×775 | 775 | 198.6 MB | 0.90×0.90×1.25 |

## Troubleshooting

### Common Issues

1. **Missing .env file**: Ensure `.env` file exists with required variables
2. **Invalid DICOM files**: Check that DICOM files are not corrupted
3. **Permission errors**: Verify write permissions for output directory
4. **Memory issues**: Large volumes may require sufficient RAM

### Debug Information

The script provides detailed logging including:
- File counts and dimensions
- Processing progress
- Error messages with context
- Final file specifications

### Performance Tips

- Use SSD storage for faster I/O
- Ensure sufficient RAM for large volumes
- Process during low system load
- Monitor disk space for large datasets

## Integration with Vista-3D

The generated NIFTI files are compatible with the Vista-3D segmentation model:

- **Format**: Standard NIFTI-1 format with `.nii.gz` compression
- **Dimensions**: Preserved from original DICOM data
- **Spatial Information**: Maintained through affine transformations
- **Data Type**: 16-bit integer (int16) for optimal memory usage

## Future Enhancements

Potential improvements for future versions:

- **Parallel Processing**: Multi-threaded conversion for large datasets
- **Quality Metrics**: Automated quality assessment of converted files
- **Batch Configuration**: Support for multiple DICOM source directories
- **Format Options**: Additional output formats (e.g., uncompressed NIFTI)
- **Validation Tools**: Built-in NIFTI file validation

## Support

For issues or questions:

1. Check the error messages in the console output
2. Verify your `.env` configuration
3. Ensure DICOM files are valid and accessible
4. Check available disk space for output files

## License

This script is part of the Vista-3D pipeline project and follows the project's licensing terms.
