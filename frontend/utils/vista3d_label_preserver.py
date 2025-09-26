#!/usr/bin/env python3
"""
Vista3D Label ID Preserver

This utility ensures that MONAI post-processing preserves the correct Vista3D label IDs
for each anatomical structure, maintaining proper color mapping.
"""

import os
import json
import numpy as np
import nibabel as nib
from typing import Dict, List, Tuple, Optional


class Vista3DLabelPreserver:
    """Preserves Vista3D label IDs during MONAI post-processing."""
    
    def __init__(self, label_colors_path: str = "conf/vista3d_label_colors.json"):
        """Initialize with Vista3D label colors configuration."""
        self.label_colors_path = label_colors_path
        self.label_colors = self._load_label_colors()
        self.id_to_color = self._create_id_to_color_mapping()
        self.name_to_id = self._create_name_to_id_mapping()
    
    def _load_label_colors(self) -> List[Dict]:
        """Load Vista3D label colors from JSON file."""
        try:
            with open(self.label_colors_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: {self.label_colors_path} not found. Using empty mapping.")
            return []
    
    def _create_id_to_color_mapping(self) -> Dict[int, Tuple[int, int, int]]:
        """Create mapping from label ID to RGB color."""
        mapping = {}
        for item in self.label_colors:
            id_val = item['id']
            color = tuple(item['color'])
            mapping[id_val] = color
        return mapping
    
    def _create_name_to_id_mapping(self) -> Dict[str, int]:
        """Create mapping from filename to Vista3D label ID."""
        mapping = {}
        
        # Create mappings for all Vista3D structures
        for item in self.label_colors:
            name = item['name']
            id_val = item['id']
            
            # Create multiple variations of the name for matching
            variations = [
                name.lower().replace(' ', '_'),
                name.lower().replace(' ', ''),
                name.lower(),
                name.replace(' ', '_'),
                name.replace(' ', '')
            ]
            
            for variation in variations:
                mapping[variation] = id_val
        
        # Add specific mappings for common variations
        specific_mappings = {
            'right_lung_lower_lobe': 32,  # Vista3D specific ID
            'left_lung_lower_lobe': 29,  # Vista3D specific ID
            'left_lung_upper_lobe': 28,  # Vista3D specific ID
            'right_lung_middle_lobe': 31,  # Vista3D specific ID
            'right_lung_upper_lobe': 30,  # Vista3D specific ID
            'right_kidney': 5,  # Vista3D specific ID
            'left_kidney': 14,  # Vista3D specific ID
            'left_kidney_cyst': 116,  # Vista3D specific ID
            'right_kidney_cyst': 117,  # Vista3D specific ID
            'prostate': 118,  # Vista3D specific ID
            'left_rib_3': 65,  # Vista3D specific ID
            'vertebrae_t12': 38,  # Vista3D specific ID
            'left_gluteus_maximus': 98,  # Vista3D specific ID
            'left_rib_10': 72,  # Vista3D specific ID
            'skull': 120,  # Vista3D specific ID
            'right_gluteus_maximus': 99,  # Vista3D specific ID
            'right_hip': 96,  # Vista3D specific ID
            'portal_vein_and_splenic_vein': 17,  # Vista3D specific ID
            'aorta': 6,  # Vista3D specific ID
            'vertebrae_l4': 34,  # Vista3D specific ID
            'left_rib_12': 74,  # Vista3D specific ID
            'right_adrenal_gland': 8,  # Vista3D specific ID
            'right_femur': 94,  # Vista3D specific ID
            'right_rib_11': 85,  # Vista3D specific ID
            'vertebrae_t10': 40,  # Vista3D specific ID
            'stomach': 12,  # Vista3D specific ID
            'left_hip': 95,  # Vista3D specific ID
            'sternum': 122,  # Vista3D specific ID
            'left_iliac_artery': 58,  # Vista3D specific ID
            'right_rib_6': 80,  # Vista3D specific ID
            'gallbladder': 10,  # Vista3D specific ID
            'duodenum': 13,  # Vista3D specific ID
            'left_iliopsoas': 106,  # Vista3D specific ID
            'left_iliac_vena': 60,  # Vista3D specific ID
            'left_rib_5': 67,  # Vista3D specific ID
            'left_gluteus_medius': 100,  # Vista3D specific ID
            'left_rib_9': 71,  # Vista3D specific ID
            'left_autochthon': 104,  # Vista3D specific ID
            'inferior_vena_cava': 7,  # Vista3D specific ID
            'vertebrae_t9': 41,  # Vista3D specific ID
            'left_rib_7': 69,  # Vista3D specific ID
            'costal_cartilages': 114,  # Vista3D specific ID
            'left_humerus': 87,  # Vista3D specific ID
            'small_bowel': 19,  # Vista3D specific ID
            'bladder': 15,  # Vista3D specific ID
            'superior_vena_cava': 125,  # Vista3D specific ID
            'colon': 62,  # Vista3D specific ID
            'right_rib_8': 82,  # Vista3D specific ID
            'vertebrae_l2': 36,  # Vista3D specific ID
            'pulmonary_vein': 119,  # Vista3D specific ID
            'left_rib_11': 73,  # Vista3D specific ID
            'sacrum': 97,  # Vista3D specific ID
            'left_femur': 93,  # Vista3D specific ID
            'spleen': 3,  # Vista3D specific ID
            'vertebrae_s1': 127,  # Vista3D specific ID
            'left_gluteus_minimus': 102,  # Vista3D specific ID
            'left_adrenal_gland': 9,  # Vista3D specific ID
            'right_gluteus_minimus': 103,  # Vista3D specific ID
            'right_iliac_vena': 61,  # Vista3D specific ID
            'right_autochthon': 105,  # Vista3D specific ID
            'right_rib_12': 86,  # Vista3D specific ID
            'right_iliopsoas': 107,  # Vista3D specific ID
            'vertebrae_t11': 39,  # Vista3D specific ID
            'vertebrae_t2': 48,  # Vista3D specific ID
            'esophagus': 11,  # Vista3D specific ID
            'right_rib_10': 84,  # Vista3D specific ID
            'heart': 115,  # Vista3D specific ID
            'vertebrae_l5': 33,  # Vista3D specific ID
            'pancreas': 4,  # Vista3D specific ID
            'left_rib_4': 66,  # Vista3D specific ID
            'right_iliac_artery': 59,  # Vista3D specific ID
            'liver': 1,  # Vista3D specific ID
            'left_rib_8': 70,  # Vista3D specific ID
            'vertebrae_l1': 37,  # Vista3D specific ID
            'right_rib_7': 81,  # Vista3D specific ID
            'spinal_cord': 121,  # Vista3D specific ID
            'vertebrae_l3': 35,  # Vista3D specific ID
            'right_rib_9': 83,  # Vista3D specific ID
            'right_gluteus_medius': 101,  # Vista3D specific ID
            'vertebrae_t8': 42,  # Vista3D specific ID
            'left_rib_6': 68,  # Vista3D specific ID
        }
        
        mapping.update(specific_mappings)
        return mapping
    
    def get_correct_label_id(self, filename: str) -> Optional[int]:
        """Get the correct Vista3D label ID for a given filename."""
        base_name = filename.replace('.nii.gz', '').replace('.nii', '')
        normalized_name = base_name.lower()
        
        return self.name_to_id.get(normalized_name)
    
    def get_color_for_id(self, label_id: int) -> Tuple[int, int, int]:
        """Get RGB color for a given label ID."""
        return self.id_to_color.get(label_id, (128, 128, 128))  # Gray fallback
    
    def restore_correct_labels(self, voxel_dir: str) -> Dict:
        """Restore correct Vista3D label IDs for all voxel files."""
        results = {
            'directory': voxel_dir,
            'files_processed': 0,
            'files_restored': 0,
            'files_skipped': 0,
            'restorations': []
        }
        
        if not os.path.exists(voxel_dir):
            results['error'] = f"Directory not found: {voxel_dir}"
            return results
        
        nifti_files = [f for f in os.listdir(voxel_dir) if f.endswith('.nii.gz')]
        
        for filename in nifti_files:
            file_path = os.path.join(voxel_dir, filename)
            correct_id = self.get_correct_label_id(filename)
            
            if correct_id is None:
                print(f"Warning: Could not determine correct ID for {filename}")
                results['files_skipped'] += 1
                continue
            
            try:
                # Load the file
                img = nib.load(file_path)
                data = img.get_fdata()
                
                # Check current non-zero values
                non_zero_mask = data > 0
                if not np.any(non_zero_mask):
                    print(f"Warning: No non-zero values found in {filename}")
                    results['files_skipped'] += 1
                    continue
                
                current_values = np.unique(data[non_zero_mask])
                
                # Only restore if the current value is different from the correct ID
                if len(current_values) == 1 and current_values[0] != correct_id:
                    # Restore the correct label ID
                    data[non_zero_mask] = correct_id
                    
                    # Save the corrected file
                    img_corrected = nib.Nifti1Image(data, img.affine)
                    nib.save(img_corrected, file_path)
                    
                    color = self.get_color_for_id(correct_id)
                    print(f"Restored {filename}: {current_values[0]} -> {correct_id} (RGB{color})")
                    
                    results['files_restored'] += 1
                    results['restorations'].append({
                        'file': filename,
                        'old_id': int(current_values[0]),
                        'new_id': correct_id,
                        'color': color
                    })
                else:
                    print(f"Skipped {filename}: already has correct ID {correct_id}")
                    results['files_skipped'] += 1
                
                results['files_processed'] += 1
                
            except Exception as e:
                print(f"Error processing {filename}: {e}")
                results['files_skipped'] += 1
        
        return results
    
    def generate_color_report(self, voxel_dir: str) -> str:
        """Generate a detailed color mapping report."""
        if not os.path.exists(voxel_dir):
            return f"Error: Directory not found: {voxel_dir}"
        
        nifti_files = [f for f in os.listdir(voxel_dir) if f.endswith('.nii.gz')]
        
        report = []
        report.append("=" * 80)
        report.append("VISTA3D COLOR MAPPING REPORT")
        report.append("=" * 80)
        report.append(f"Directory: {voxel_dir}")
        report.append(f"Total files: {len(nifti_files)}")
        report.append("")
        
        for filename in sorted(nifti_files):
            file_path = os.path.join(voxel_dir, filename)
            correct_id = self.get_correct_label_id(filename)
            
            try:
                img = nib.load(file_path)
                data = img.get_fdata()
                unique_vals = np.unique(data)
                non_zero_vals = unique_vals[unique_vals > 0]
                
                report.append(f"File: {filename}")
                if correct_id:
                    color = self.get_color_for_id(correct_id)
                    report.append(f"  Correct ID: {correct_id}")
                    report.append(f"  Color: RGB{color} (#{color[0]:02x}{color[1]:02x}{color[2]:02x})")
                else:
                    report.append(f"  Correct ID: Unknown")
                
                if len(non_zero_vals) > 0:
                    actual_id = int(non_zero_vals[0])
                    actual_color = self.get_color_for_id(actual_id)
                    report.append(f"  Actual ID: {actual_id}")
                    report.append(f"  Actual Color: RGB{actual_color} (#{actual_color[0]:02x}{actual_color[1]:02x}{actual_color[2]:02x})")
                    
                    if correct_id and actual_id != correct_id:
                        report.append(f"  Status: ❌ MISMATCH")
                    else:
                        report.append(f"  Status: ✅ CORRECT")
                else:
                    report.append(f"  Actual ID: None (no non-zero values)")
                    report.append(f"  Status: ⚠️ EMPTY")
                
                report.append("")
                
            except Exception as e:
                report.append(f"File: {filename}")
                report.append(f"  Error: {e}")
                report.append("")
        
        return "\n".join(report)


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Vista3D Label ID Preserver")
    parser.add_argument("voxel_dir", help="Path to voxel directory")
    parser.add_argument("--restore", action="store_true", help="Restore correct label IDs")
    parser.add_argument("--report", action="store_true", help="Generate detailed report")
    
    args = parser.parse_args()
    
    preserver = Vista3DLabelPreserver()
    
    if args.report:
        report = preserver.generate_color_report(args.voxel_dir)
        print(report)
    
    if args.restore:
        print("Restoring correct Vista3D label IDs...")
        results = preserver.restore_correct_labels(args.voxel_dir)
        print(f"Files processed: {results['files_processed']}")
        print(f"Files restored: {results['files_restored']}")
        print(f"Files skipped: {results['files_skipped']}")
        
        if results['restorations']:
            print("\nRestorations made:")
            for restoration in results['restorations']:
                print(f"  {restoration['file']}: {restoration['old_id']} -> {restoration['new_id']} (RGB{restoration['color']})")


if __name__ == "__main__":
    main()
