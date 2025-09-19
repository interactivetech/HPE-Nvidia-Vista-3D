# External Directory Configuration

This document explains how to configure Vista-3D to use external directories for DICOM and output files.

## Overview

By default, Vista-3D uses local `dicom/` and `output/` directories within the project. However, you can configure it to use external directories by setting environment variables.

## Configuration

### 1. Create a `.env` file

Copy the template and modify it:
```bash
cp dot_env_template .env
```

Then edit the `.env` file with your directory paths:

```bash
# DICOM folder location (can be relative or absolute)
DICOM_FOLDER="../dicom"                    # Parent directory (recommended)
# DICOM_FOLDER="/absolute/path/to/dicom"   # Absolute path

# Output folder (can be relative or absolute)  
OUTPUT_FOLDER="../output"                  # Parent directory (recommended)
# OUTPUT_FOLDER="/absolute/path/to/output" # Absolute path

# Other configuration
IMAGE_SERVER="http://localhost:8888"
VISTA3D_SERVER="http://your-remote-vista3d-server:8000"
VESSELS_OF_INTEREST="all"
```

### 2. Directory Path Examples

**Relative paths** (relative to project root):
```bash
DICOM_FOLDER="dicom"
OUTPUT_FOLDER="output"
```

**Absolute paths** (recommended for external directories):
```bash
# macOS/Linux
DICOM_FOLDER="/Users/username/MedicalData/DICOM"
OUTPUT_FOLDER="/Users/username/MedicalData/Output"

# Windows
DICOM_FOLDER="C:\\MedicalData\\DICOM"
OUTPUT_FOLDER="C:\\MedicalData\\Output"
```

### 3. Docker Volume Mounting

The Docker Compose configuration automatically uses the environment variables for volume mounting:

```yaml
volumes:
  - ${OUTPUT_FOLDER:-./output}:/app/output
  - ${DICOM_FOLDER:-./dicom}:/app/dicom
```

This means:
- If `OUTPUT_FOLDER` is set, it mounts that directory
- If not set, it defaults to `./output`
- Same for `DICOM_FOLDER`

## Usage

1. **Set up your external directories** with the desired DICOM and output files
2. **Create a `.env` file** with the correct paths
3. **Start the containers** using `python3 start_gui.py`
4. **Access the image server** at `http://localhost:8888`

The image server will now show the contents of your external directories.

## Security Notes

- Ensure the external directories exist and are accessible
- The Docker containers run with appropriate permissions
- Only the configured directories are accessible through the web interface

## Troubleshooting

### Empty Directories
If directories appear empty:
1. Check that the paths in `.env` are correct
2. Verify the directories exist and contain files
3. Check Docker volume mounting with `docker inspect <container_name>`

### Permission Issues
If you get permission errors:
1. Ensure the directories are readable by the Docker user
2. Check file permissions: `ls -la /path/to/directory`
3. On macOS/Linux, you may need to adjust permissions

### Path Resolution
- Use absolute paths for external directories
- Avoid spaces in directory names (use underscores instead)
- On Windows, use forward slashes or double backslashes
