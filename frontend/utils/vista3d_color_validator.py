#!/usr/bin/env python3
"""
Vista3D Color Mapping Validator and Corrector

This utility ensures that voxel files maintain proper Vista3D label ID to color mapping
after MONAI post-processing. It validates and corrects any inconsistencies.
"""

import os
import json
import numpy as np
import nibabel as nib
from typing import Dict, List, Tuple, Optional


class Vista3DColorValidator:
    """Validates and corrects Vista3D color mapping for voxel files."""
    
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
            color = tuple(item['color'])  # Convert to tuple for immutability
            mapping[id_val] = color
        return mapping
    
    def _create_name_to_id_mapping(self) -> Dict[str, int]:
        """Create mapping from normalized name to label ID."""
        mapping = {}
        for item in self.label_colors:
            name = item['name'].replace(' ', '_').lower()
            id_val = item['id']
            mapping[name] = id_val
        return mapping
    
    def get_expected_label_id(self, filename: str) -> Optional[int]:
        """Get expected label ID for a given filename."""
        # Remove file extension and normalize name
        base_name = filename.replace('.nii.gz', '').replace('.nii', '')
        normalized_name = base_name.replace('_', ' ').lower()
        
        # Try exact match first
        if normalized_name in self.name_to_id:
            return self.name_to_id[normalized_name]
        
        # Try partial matches for complex names
        for name, id_val in self.name_to_id.items():
            if name in normalized_name or normalized_name in name:
                return id_val
        
        return None
    
    def get_color_for_id(self, label_id: int) -> Tuple[int, int, int]:
        """Get RGB color for a given label ID."""
        return self.id_to_color.get(label_id, (128, 128, 128))  # Gray fallback
    
    def validate_voxel_file(self, file_path: str) -> Dict:
        """Validate a single voxel file for proper Vista3D color mapping."""
        try:
            img = nib.load(file_path)
            data = img.get_fdata()
            unique_vals = np.unique(data)
            
            # Remove zero values (background)
            non_zero_vals = unique_vals[unique_vals > 0]
            
            filename = os.path.basename(file_path)
            expected_id = self.get_expected_label_id(filename)
            
            result = {
                'file': filename,
                'path': file_path,
                'unique_values': unique_vals.tolist(),
                'non_zero_values': non_zero_vals.tolist(),
                'expected_id': expected_id,
                'is_valid': True,
                'issues': []
            }
            
            if len(non_zero_vals) == 0:
                result['issues'].append("No non-zero values found")
                result['is_valid'] = False
            elif len(non_zero_vals) > 1:
                result['issues'].append(f"Multiple non-zero values: {non_zero_vals}")
                result['is_valid'] = False
            elif expected_id is not None and non_zero_vals[0] != expected_id:
                result['issues'].append(f"Expected ID {expected_id}, found {non_zero_vals[0]}")
                result['is_valid'] = False
            
            # Add color information
            if len(non_zero_vals) > 0:
                actual_id = int(non_zero_vals[0])
                result['actual_id'] = actual_id
                result['color'] = self.get_color_for_id(actual_id)
                result['color_hex'] = f"#{result['color'][0]:02x}{result['color'][1]:02x}{result['color'][2]:02x}"
            
            return result
            
        except Exception as e:
            return {
                'file': os.path.basename(file_path),
                'path': file_path,
                'is_valid': False,
                'error': str(e)
            }
    
    def validate_voxel_directory(self, voxel_dir: str) -> Dict:
        """Validate all voxel files in a directory."""
        results = {
            'directory': voxel_dir,
            'total_files': 0,
            'valid_files': 0,
            'invalid_files': 0,
            'files': []
        }
        
        if not os.path.exists(voxel_dir):
            results['error'] = f"Directory not found: {voxel_dir}"
            return results
        
        nifti_files = [f for f in os.listdir(voxel_dir) if f.endswith('.nii.gz')]
        results['total_files'] = len(nifti_files)
        
        for filename in nifti_files:
            file_path = os.path.join(voxel_dir, filename)
            file_result = self.validate_voxel_file(file_path)
            results['files'].append(file_result)
            
            if file_result['is_valid']:
                results['valid_files'] += 1
            else:
                results['invalid_files'] += 1
        
        return results
    
    def fix_voxel_file(self, file_path: str, target_id: Optional[int] = None) -> bool:
        """Fix a voxel file to have the correct label ID."""
        try:
            img = nib.load(file_path)
            data = img.get_fdata()
            
            filename = os.path.basename(file_path)
            if target_id is None:
                target_id = self.get_expected_label_id(filename)
            
            if target_id is None:
                print(f"Warning: Could not determine target ID for {filename}")
                return False
            
            # Find current non-zero values
            non_zero_mask = data > 0
            if not np.any(non_zero_mask):
                print(f"Warning: No non-zero values found in {filename}")
                return False
            
            # Replace all non-zero values with target ID
            data[non_zero_mask] = target_id
            
            # Save the corrected file
            img_corrected = nib.Nifti1Image(data, img.affine)
            nib.save(img_corrected, file_path)
            
            print(f"Fixed {filename}: set all non-zero values to ID {target_id}")
            return True
            
        except Exception as e:
            print(f"Error fixing {file_path}: {e}")
            return False
    
    def fix_voxel_directory(self, voxel_dir: str) -> Dict:
        """Fix all voxel files in a directory."""
        results = {
            'directory': voxel_dir,
            'files_fixed': 0,
            'files_failed': 0,
            'fixes': []
        }
        
        if not os.path.exists(voxel_dir):
            results['error'] = f"Directory not found: {voxel_dir}"
            return results
        
        nifti_files = [f for f in os.listdir(voxel_dir) if f.endswith('.nii.gz')]
        
        for filename in nifti_files:
            file_path = os.path.join(voxel_dir, filename)
            target_id = self.get_expected_label_id(filename)
            
            if target_id is not None:
                if self.fix_voxel_file(file_path, target_id):
                    results['files_fixed'] += 1
                    results['fixes'].append(f"{filename} -> ID {target_id}")
                else:
                    results['files_failed'] += 1
            else:
                print(f"Warning: Could not determine target ID for {filename}")
                results['files_failed'] += 1
        
        return results
    
    def generate_color_report(self, voxel_dir: str) -> str:
        """Generate a detailed color mapping report."""
        validation = self.validate_voxel_directory(voxel_dir)
        
        report = []
        report.append("=" * 80)
        report.append("VISTA3D COLOR MAPPING REPORT")
        report.append("=" * 80)
        report.append(f"Directory: {voxel_dir}")
        report.append(f"Total files: {validation['total_files']}")
        report.append(f"Valid files: {validation['valid_files']}")
        report.append(f"Invalid files: {validation['invalid_files']}")
        report.append("")
        
        if validation['invalid_files'] > 0:
            report.append("INVALID FILES:")
            report.append("-" * 40)
            for file_result in validation['files']:
                if not file_result['is_valid']:
                    report.append(f"File: {file_result['file']}")
                    if 'error' in file_result:
                        report.append(f"  Error: {file_result['error']}")
                    else:
                        report.append(f"  Issues: {', '.join(file_result['issues'])}")
                    if 'expected_id' in file_result and file_result['expected_id']:
                        expected_color = self.get_color_for_id(file_result['expected_id'])
                        report.append(f"  Expected: ID {file_result['expected_id']}, Color RGB{expected_color}")
                    report.append("")
        
        report.append("VALID FILES:")
        report.append("-" * 40)
        for file_result in validation['files']:
            if file_result['is_valid'] and 'actual_id' in file_result:
                report.append(f"File: {file_result['file']}")
                report.append(f"  ID: {file_result['actual_id']}")
                report.append(f"  Color: RGB{file_result['color']} ({file_result['color_hex']})")
                report.append("")
        
        return "\n".join(report)


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Vista3D Color Mapping Validator")
    parser.add_argument("voxel_dir", help="Path to voxel directory")
    parser.add_argument("--fix", action="store_true", help="Fix invalid files")
    parser.add_argument("--report", action="store_true", help="Generate detailed report")
    
    args = parser.parse_args()
    
    validator = Vista3DColorValidator()
    
    if args.report:
        report = validator.generate_color_report(args.voxel_dir)
        print(report)
    
    if args.fix:
        print("Fixing voxel files...")
        results = validator.fix_voxel_directory(args.voxel_dir)
        print(f"Files fixed: {results['files_fixed']}")
        print(f"Files failed: {results['files_failed']}")
        for fix in results['fixes']:
            print(f"  {fix}")


if __name__ == "__main__":
    main()
