# 📁 Sample Data Setup Guide

This guide explains how sample data is automatically installed and used in the HPE NVIDIA Vista3D project.

## 📦 What's Included

The `sample_data.tgz` file contains sample medical imaging data for patient **SAMPLE_DATA_001**:

- **DICOM Files**: CT scan files in DICOM format
- **Processed Output**: Processed files including NIFTI volumes and segmentation results
- **Total Files**: Multiple files across both DICOM and output directories

## 🚀 Automatic Installation

**Sample data is automatically installed during the setup process!**

When you run the setup script (`python3 setup.py`), it will:

1. **Detect the sample data archive** (`sample_data.tgz`) in the project root
2. **Prompt you to install it** with a clear description of what's included
3. **Automatically extract and install** the data to the correct directories
4. **Set up the proper directory structure** for immediate use

### What Happens During Setup

```bash
# When you run the setup script
python3 setup.py

# The script will:
# 1. Check for sample_data.tgz in the project root
# 2. Ask: "Install sample data? (Y/n):"
# 3. If you choose Yes, it automatically:
#    - Extracts the archive to a temporary location
#    - Moves DICOM files to dicom/SAMPLE_DATA_001/
#    - Moves output files to output/SAMPLE_DATA_001/
#    - Cleans up temporary files
#    - Reports success
```

### Manual Installation (If Needed)

If you need to install sample data manually or the automatic installation failed:

```bash
# Navigate to the project root
cd HPE-Nvidia-Vista-3D

# Extract the sample data
tar -xzf sample_data.tgz

# Move the extracted data to the correct locations
mv sample_data/dicom/SAMPLE_DATA_001 dicom/
mv sample_data/output/SAMPLE_DATA_001 output/

# Clean up the temporary extraction directory
rm -rf sample_data
```

## 📋 Verification

After automatic installation (or manual extraction), verify the data is in the correct location:

```bash
# Check DICOM files
ls -la dicom/SAMPLE_DATA_001/ | head -10

# Check output files
ls -la output/SAMPLE_DATA_001/

# Count files to verify
echo "DICOM files: $(find dicom/SAMPLE_DATA_001 -type f | wc -l)"
echo "Output files: $(find output/SAMPLE_DATA_001 -type f | wc -l)"
```

Expected output:
- DICOM files: ~391 files
- Output files: ~262 files

## 🎯 Using the Sample Data

Once automatically installed (or manually extracted), you can use the sample data with the Vista3D system:

### 1. Start the Services

```bash
# Start the frontend (if not already running)
cd frontend
docker-compose up -d

# Start the image server (if not already running)
cd ../image_server
docker-compose up -d
```

### 2. Access the Web Interface

Open your browser to: http://localhost:8501

### 3. View the Sample Data

- Navigate to the **Tools** page
- The patient **PA00000002** should appear in the patient list
- You can:
  - View the DICOM images
  - Convert DICOM to NIFTI (if not already done)
  - Run AI segmentation
  - View 3D visualizations

## 📊 Sample Data Contents

### DICOM Directory Structure
```
dicom/PA00000002/
├── deid_CT.1.2.840.113619.2.55.3.3859472014.238.1551439919.146.35
├── deid_CT.1.2.840.113619.2.5.83425804.19836.1551442938.271
├── deid_CT.1.2.840.113619.2.5.83425804.19836.1551442938.285
└── ... (391 total DICOM files)
```

### Output Directory Structure
```
output/PA00000002/
├── nifti/                    # NIFTI format files
├── voxels/                   # Processed voxel data
│   ├── 2.5MM_ARTERIAL_3/
│   │   └── original/         # Original segmented voxel files
│   │       ├── aorta.nii.gz
│   │       ├── liver.nii.gz
│   │       └── ... (81 individual structure files)
│   ├── CORONAL_ABDOMEN_601_i00002/
│   │   └── original/         # Original segmented voxel files
│   │       └── ... (83 individual structure files)
│   └── SAGITTAL_ABDOMEN_602_i00002/
│       └── original/         # Original segmented voxel files
│           └── ... (81 individual structure files)
└── .DS_Store                 # System file (can be ignored)
```

## 🔧 Troubleshooting

### Permission Issues
If you encounter permission issues during extraction:

```bash
# Fix permissions
sudo chown -R $USER:$USER dicom/PA00000002/
sudo chown -R $USER:$USER output/PA00000002/
sudo chmod -R 755 dicom/PA00000002/
sudo chmod -R 755 output/PA00000002/
```

### Directory Already Exists
If the `PA00000002` directory already exists during automatic installation:

- The setup script will **skip installation** if the directory already exists
- You can manually remove the existing directory and re-run setup if needed
- Or use the manual installation method above to overwrite existing data

### Insufficient Disk Space
Check available space before extraction:

```bash
# Check available disk space
df -h .

# Check size of the archive
ls -lh sample_data.tgz
```

## 📝 Notes

- The sample data is for **patient PA00000002** and contains CT scan data
- DICOM files are the original medical imaging format
- Output files include processed NIFTI volumes and segmentation results
- This data is suitable for testing the Vista3D system functionality
- The data has been de-identified for privacy and research purposes
- **Automatic installation** happens during setup - no manual extraction needed!

## 🆘 Need Help?

If you encounter issues with the sample data:

1. Check the [QUICK_START.md](../QUICK_START.md) for general setup instructions
2. Verify your Docker services are running correctly
3. Check the troubleshooting section in [QUICK_START.md](../QUICK_START.md)
4. Ensure you have sufficient disk space and proper permissions

---

**Ready to explore?** Run the setup script and the sample data will be automatically installed for you to start exploring the Vista3D medical AI platform! 🚀
