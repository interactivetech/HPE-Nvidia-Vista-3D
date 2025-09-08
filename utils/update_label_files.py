#!/usr/bin/env python3
"""
Update VISTA-3D Label Configuration Files

This script updates the label configuration files with missing labels identified
by the VISTA-3D API analysis.
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List
import argparse
from datetime import datetime

class LabelFileUpdater:
    def __init__(self, config_dir: str = "conf"):
        self.config_dir = Path(config_dir)
        self.labels_colors_file = self.config_dir / "vista3d_label_colors.json"
        self.labels_dict_file = self.config_dir / "vista3d_label_colors.json.bak"
        self.labels_dict_file = self.config_dir / "vista3d_label_dict.json"
        
    def load_missing_labels_from_report(self, report_file: str) -> Dict:
        """Load missing labels configuration from analysis report."""
        try:
            with open(report_file, 'r') as f:
                report = json.load(f)
            
            missing_config = report.get('missing_labels_config', {})
            print(f"✅ Loaded missing labels from: {report_file}")
            return missing_config
            
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"❌ Error loading report file: {e}")
            return None
    
    def load_existing_files(self) -> tuple:
        """Load existing label configuration files."""
        files_data = {}
        
        for file_path, name in [
            (self.labels_colors_file, "colors"),
            (self.labels_dict_file, "dict")
        ]:
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        files_data[name] = json.load(f)
                    print(f"✅ Loaded {name} file: {file_path}")
                except (json.JSONDecodeError, FileNotFoundError) as e:
                    print(f"❌ Error loading {name} file: {e}")
                    files_data[name] = None
            else:
                print(f"⚠️  File not found: {file_path}")
                files_data[name] = None
        
        return files_data.get("colors", []), files_data.get("dict", {})
    
    def update_colors_file(self, existing_colors: List, missing_colors: List) -> List:
        """Update the colors file with missing labels."""
        # Create a set of existing IDs for quick lookup
        existing_ids = {item['id'] for item in existing_colors if 'id' in item}
        
        # Add missing labels
        updated_colors = existing_colors.copy()
        added_count = 0
        
        for missing_label in missing_colors:
            if missing_label['id'] not in existing_ids:
                updated_colors.append(missing_label)
                added_count += 1
                print(f"   Added: ID {missing_label['id']} - {missing_label['name']}")
            else:
                print(f"   Skipped: ID {missing_label['id']} - {missing_label['name']} (already exists)")
        
        print(f"✅ Added {added_count} new labels to colors file")
        return updated_colors
    
    def update_dict_file(self, existing_dict: Dict, missing_dict: Dict) -> Dict:
        """Update the dict file with missing labels."""
        updated_dict = existing_dict.copy()
        added_count = 0
        
        for name, label_id in missing_dict.items():
            if name not in updated_dict:
                updated_dict[name] = label_id
                added_count += 1
                print(f"   Added: {name} -> {label_id}")
            else:
                print(f"   Skipped: {name} -> {label_id} (already exists)")
        
        print(f"✅ Added {added_count} new labels to dict file")
        return updated_dict
    
    def create_backup(self) -> str:
        """Create backup of existing files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.config_dir / f"backup_{timestamp}"
        backup_dir.mkdir(exist_ok=True)
        
        files_to_backup = [
            (self.labels_colors_file, "vista3d_label_colors.json"),
            (self.labels_dict_file, "vista3d_label_dict.json")
        ]
        
        for source_file, backup_name in files_to_backup:
            if source_file.exists():
                backup_file = backup_dir / backup_name
                backup_file.write_text(source_file.read_text())
                print(f"📁 Backed up: {source_file} -> {backup_file}")
        
        return str(backup_dir)
    
    def save_updated_files(self, updated_colors: List, updated_dict: Dict):
        """Save updated files."""
        # Save colors file
        with open(self.labels_colors_file, 'w') as f:
            json.dump(updated_colors, f, indent=4)
        print(f"💾 Saved updated colors file: {self.labels_colors_file}")
        
        # Save dict file
        with open(self.labels_dict_file, 'w') as f:
            json.dump(updated_dict, f, indent=4)
        print(f"💾 Saved updated dict file: {self.labels_dict_file}")
    
    def update_files(self, report_file: str, create_backup: bool = True) -> bool:
        """Update label files with missing labels."""
        print("🔄 Updating VISTA-3D Label Configuration Files")
        print("=" * 60)
        
        # Load missing labels from report
        missing_config = self.load_missing_labels_from_report(report_file)
        if not missing_config:
            return False
        
        missing_colors = missing_config.get('colors', [])
        missing_dict = missing_config.get('dict', {})
        
        if not missing_colors and not missing_dict:
            print("ℹ️  No missing labels to add")
            return True
        
        # Create backup if requested
        if create_backup:
            backup_dir = self.create_backup()
            print(f"📁 Backup created in: {backup_dir}")
        
        # Load existing files
        existing_colors, existing_dict = self.load_existing_files()
        
        # Update files
        print(f"\n🔧 Updating colors file with {len(missing_colors)} missing labels...")
        updated_colors = self.update_colors_file(existing_colors, missing_colors)
        
        print(f"\n🔧 Updating dict file with {len(missing_dict)} missing labels...")
        updated_dict = self.update_dict_file(existing_dict, missing_dict)
        
        # Save updated files
        print(f"\n💾 Saving updated files...")
        self.save_updated_files(updated_colors, updated_dict)
        
        print(f"\n✅ Successfully updated label configuration files!")
        print(f"   Added {len(missing_colors)} labels to colors file")
        print(f"   Added {len(missing_dict)} labels to dict file")
        
        return True

def main():
    parser = argparse.ArgumentParser(description='Update VISTA-3D label configuration files')
    parser.add_argument('--report-file', required=True,
                       help='Path to the analysis report JSON file')
    parser.add_argument('--config-dir', default='conf',
                       help='Configuration directory (default: conf)')
    parser.add_argument('--no-backup', action='store_true',
                       help='Do not create backup files')
    
    args = parser.parse_args()
    
    updater = LabelFileUpdater(args.config_dir)
    success = updater.update_files(args.report_file, create_backup=not args.no_backup)
    
    if success:
        print("\n🎉 Label files updated successfully!")
        print("\n💡 Next steps:")
        print("   1. Test the updated configuration with VISTA-3D")
        print("   2. Verify all labels are working correctly")
        print("   3. Update your application if needed")
    else:
        print("\n❌ Failed to update label files!")
        sys.exit(1)

if __name__ == "__main__":
    main()
