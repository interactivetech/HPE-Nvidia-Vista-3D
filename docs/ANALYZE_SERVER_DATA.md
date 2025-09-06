# Image Server Data Analysis Script

## Overview

The `analyze_server_data.py` script provides comprehensive analysis of the medical imaging server data, scanning both the `output/nifti` and `output/segments` folders to generate detailed reports on patients, CT scans, and voxel data.

## Features

- **Patient Detection**: Automatically identifies patient folders using the PA00000002 format
- **CT Scan Counting**: Counts all `.nii.gz` files in each patient's nifti folder
- **Voxel Analysis**: Analyzes segmentation files and voxel folders for each CT scan
- **Comprehensive Reporting**: Generates detailed reports with statistics and breakdowns
- **Multiple Output Formats**: Console output and optional file export

## Usage

### Basic Usage
```bash
python utils/analyze_server_data.py
```

### Advanced Options
```bash
# Use custom server URL
python utils/analyze_server_data.py --url https://your-server:8888

# Enable SSL verification (for production certificates)
python utils/analyze_server_data.py --verify-ssl

# Save report to file
python utils/analyze_server_data.py --output report.txt

# Quiet mode (minimal output)
python utils/analyze_server_data.py --quiet
```

## Command Line Options

- `--verify-ssl`: Enable SSL certificate verification (disabled by default for self-signed certs)
- `--url URL`: Override the IMAGE_SERVER URL from environment variables
- `--output OUTPUT, -o OUTPUT`: Save the report to a specified file
- `--quiet, -q`: Suppress progress output and only show the final report

## Report Contents

The generated report includes:

### Summary Statistics
- Total number of patients found
- Number of patients with CT scans
- Number of patients with voxel data
- Total CT scans across all patients
- Total voxel files across all patients

### Detailed Patient Breakdown
For each patient:
- Patient ID
- Number of CT scans
- Number of voxel files
- Detailed CT scan listing with voxel data status

### File Structure Overview
Visual representation of the expected folder structure

## Expected Folder Structure

```
output/
├── nifti/                    # CT scan data
│   ├── PA00000002/          # Patient folder
│   │   ├── scan1.nii.gz     # CT scan files
│   │   └── scan2.nii.gz
│   └── PA00000014/
│       └── scan1.nii.gz
└── segments/                 # Segmentation data
    ├── PA00000002/
    │   ├── scan1.nii.gz     # Segmentation files
    │   ├── scan1_voxel/     # Voxel folders
    │   │   ├── voxel1.nii.gz
    │   │   └── voxel2.nii.gz
    │   └── scan2.nii.gz
    └── PA00000014/
        └── scan1.nii.gz
```

## Requirements

- Python 3.7+
- requests
- beautifulsoup4
- python-dotenv
- urllib3

## Dependencies

The script automatically loads configuration from the `.env` file and uses the same environment variables as other scripts in the project:

- `IMAGE_SERVER`: URL of the image server (default: https://localhost:8888)
- `PROJECT_ROOT`: Root directory of the project

## Error Handling

The script includes comprehensive error handling for:
- Server connection issues
- SSL certificate problems
- Missing folders or files
- Network timeouts
- Invalid folder structures

## Example Output

```
================================================================================
🏥 MEDICAL IMAGING SERVER DATA ANALYSIS REPORT
================================================================================
📅 Generated: 2025-09-06 11:30:49

📊 SUMMARY STATISTICS
----------------------------------------
Total Patients Found: 5
Patients with CT Scans: 5
Patients with Voxel Data: 5
Total CT Scans: 9
Total Voxel Files: 9

👥 DETAILED PATIENT BREAKDOWN
----------------------------------------

🏷️  Patient ID: PA00000002
   📊 CT Scans: 1
   🧬 Voxel Files: 1
   📋 CT Scan Details:
      ✅ 2.5MM_ARTERIAL_3.nii.gz (segmentation file)
```

## Integration

This script integrates seamlessly with the existing medical imaging workflow:
- Uses the same image server as other tools
- Follows the same folder structure conventions
- Compatible with Vista3D segmentation pipeline
- Works with both HTTP and HTTPS servers
