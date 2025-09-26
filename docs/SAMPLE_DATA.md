# 📁 Sample Data Setup Guide

This guide explains how to extract and use the sample data provided with the HPE NVIDIA Vista3D project.

## 📦 What's Included

The `sample_data.tgz` file contains sample medical imaging data for patient **PA00000002**:

- **DICOM Files**: 391 CT scan files in DICOM format
- **Processed Output**: 262 processed files including NIFTI volumes and segmentation results
- **Total Files**: 656 files across both DICOM and output directories

## 🚀 Quick Setup

### Option 1: Extract to Existing Directories (Recommended)

If you already have `dicom/` and `output/` directories in your project:

```bash
# Navigate to the project root
cd HPE-Nvidia-Vista-3D

# Extract the sample data
tar -xzf sample_data.tgz

# Move the extracted data to the correct locations
mv sample_data/dicom/PA00000002 dicom/
mv sample_data/output/PA00000002 output/

# Clean up the temporary extraction directory
rm -rf sample_data
```

### Option 2: Extract and Copy Manually

```bash
# Navigate to the project root
cd HPE-Nvidia-Vista-3D

# Extract to a temporary location
tar -xzf sample_data.tgz

# Copy DICOM files
cp -r sample_data/dicom/PA00000002 dicom/

# Copy processed output
cp -r sample_data/output/PA00000002 output/

# Clean up
rm -rf sample_data
```

### Option 3: Extract with Custom Location

If you want to extract to a different location:

```bash
# Extract to a specific directory
tar -xzf sample_data.tgz -C /path/to/your/project/

# Then move the files as needed
mv /path/to/your/project/sample_data/dicom/PA00000002 dicom/
mv /path/to/your/project/sample_data/output/PA00000002 output/
```

## 📋 Verification

After extraction, verify the data is in the correct location:

```bash
# Check DICOM files
ls -la dicom/PA00000002/ | head -10

# Check output files
ls -la output/PA00000002/

# Count files to verify
echo "DICOM files: $(find dicom/PA00000002 -type f | wc -l)"
echo "Output files: $(find output/PA00000002 -type f | wc -l)"
```

Expected output:
- DICOM files: ~391 files
- Output files: ~262 files

## 🎯 Using the Sample Data

Once extracted, you can use the sample data with the Vista3D system:

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
│   ├── SAGITTAL_ABDOMEN_602_i00002.nii.gz
│   ├── 2.5MM_ARTERIAL_3.nii.gz
│   ├── CORONAL_ABDOMEN_601_i00002.nii.gz
│   └── ... (processed files)
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
If the `PA00000002` directory already exists:

```bash
# Backup existing data (optional)
mv dicom/PA00000002 dicom/PA00000002_backup
mv output/PA00000002 output/PA00000002_backup

# Then extract the sample data
tar -xzf sample_data.tgz
mv sample_data/dicom/PA00000002 dicom/
mv sample_data/output/PA00000002 output/
rm -rf sample_data
```

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

## 🆘 Need Help?

If you encounter issues with the sample data:

1. Check the [QUICK_START.md](../QUICK_START.md) for general setup instructions
2. Verify your Docker services are running correctly
3. Check the troubleshooting section in [QUICK_START.md](../QUICK_START.md)
4. Ensure you have sufficient disk space and proper permissions

---

**Ready to explore?** Extract the sample data and start exploring the Vista3D medical AI platform! 🚀
