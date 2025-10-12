#!/bin/bash
# Script to run nifti2obj.py on all patients and scans

# Set the OUTPUT_FOLDER environment variable
export OUTPUT_FOLDER="/Users/dave/AI/HPE/HPE-Nvidia-Vista-3D/output"

# Array of patient:scan combinations
conversions=(
    "PA00000002:2.5MM_ARTERIAL_3"
    "PA00000002:CORONAL_ABDOMEN_601_i00002"
    "PA00000002:SAGITTAL_ABDOMEN_602_i00002"
    "PA00000014:ARTERIAL_1.25MM_102"
    "PA00000014:ARTERIAL_1.25MM_2"
    "PA00000014:ARTERIAL_2.5MM_3"
    "PA00000014:Reformatted_201_i00002"
    "PA00000014:Reformatted_202_i00002"
    "PA00000015:ax_25x25_601_i00002"
    "PA00000015:cor_3x3_602_i00002"
    "PA00000015:sag_3x3_603_i00002"
    "PA00000050:ARTERIAL_PHASE_2.5MM_3"
    "PA00000050:COR_3_601_i00002"
    "PA00000050:SAG_3_602_i00002"
    "PA00000058:1.25_mm_4"
    "PA00000058:2.5_mm_STD_-_30%_ASIR_2"
    "PA00000058:cor_1_3mm_601_i00002"
    "PA00000058:sag_1_3mm_602_i00002"
    "SAMPLE_DATA_001:2.5MM_ARTERIAL_3"
    "SAMPLE_DATA_001:CORONAL_ABDOMEN_601_i00002"
    "SAMPLE_DATA_001:SAGITTAL_ABDOMEN_602_i00002"
)

total_count=${#conversions[@]}
success_count=0
fail_count=0

echo "========================================"
echo "NIfTI to OBJ Batch Conversion"
echo "========================================"
echo "Total conversions to process: $total_count"
echo ""

current=0

# Process each conversion
for conversion in "${conversions[@]}"; do
    current=$((current + 1))
    
    # Split patient:scan
    patient="${conversion%%:*}"
    scan="${conversion#*:}"
    
    echo "----------------------------------------"
    echo "[$current/$total_count] Processing: $patient / $scan"
    echo "----------------------------------------"
    
    # Run nifti2obj.py with verbose output
    if python3 frontend/utils/nifti2obj.py --patient "$patient" --scan "$scan" -v; then
        success_count=$((success_count + 1))
        echo "[✓] Successfully processed: $patient / $scan"
    else
        fail_count=$((fail_count + 1))
        echo "[✗] Failed to process: $patient / $scan"
    fi
    echo ""
done

echo "========================================"
echo "Batch Conversion Complete"
echo "========================================"
echo "Total: $total_count"
echo "Success: $success_count"
echo "Failed: $fail_count"
echo "========================================"
