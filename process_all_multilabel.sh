#!/bin/bash
# Script to process all.nii.gz files to create all_*.obj files

# Set the OUTPUT_FOLDER environment variable
export OUTPUT_FOLDER="/Users/dave/AI/HPE/HPE-Nvidia-Vista-3D/output"

echo "========================================"
echo "Processing Multi-Label Files (all.nii.gz)"
echo "========================================"
echo ""

# Find all all.nii.gz files and extract patient/scan info
all_files=$(find "$OUTPUT_FOLDER" -path "*/voxels/*/all.nii.gz")

# Count total files
total_count=$(echo "$all_files" | wc -l | tr -d ' ')
success_count=0
fail_count=0
current=0

echo "Found $total_count all.nii.gz files to process"
echo ""

# Process each all.nii.gz file
for filepath in $all_files; do
    current=$((current + 1))
    
    # Extract patient and scan from path
    # Path format: .../output/PATIENT/voxels/SCAN/all.nii.gz
    patient=$(echo "$filepath" | sed -E 's|.*/output/([^/]+)/voxels/.*|\1|')
    scan=$(echo "$filepath" | sed -E 's|.*/voxels/([^/]+)/all\.nii\.gz|\1|')
    
    echo "----------------------------------------"
    echo "[$current/$total_count] Processing: $patient / $scan"
    echo "----------------------------------------"
    
    # Remove existing all_*.obj files to force regeneration
    rm -f "$OUTPUT_FOLDER/$patient/obj/$scan/all_"*.obj 2>/dev/null
    
    # Run nifti2obj.py for just this scan (will process all .nii.gz files including all.nii.gz)
    if python3 frontend/utils/nifti2obj.py --patient "$patient" --scan "$scan" -v 2>&1 | grep -q "Converting multi-label"; then
        # Check if all_*.obj files were created
        all_obj_count=$(find "$OUTPUT_FOLDER/$patient/obj/$scan/" -name "all_*.obj" 2>/dev/null | wc -l | tr -d ' ')
        if [ "$all_obj_count" -gt 0 ]; then
            success_count=$((success_count + 1))
            echo "[✓] Successfully created $all_obj_count all_*.obj files"
        else
            fail_count=$((fail_count + 1))
            echo "[✗] Failed to create all_*.obj files"
        fi
    else
        fail_count=$((fail_count + 1))
        echo "[✗] Failed to process multi-label file"
    fi
    echo ""
done

echo "========================================"
echo "Multi-Label Processing Complete"
echo "========================================"
echo "Total: $total_count"
echo "Success: $success_count"
echo "Failed: $fail_count"
echo "========================================"

