#!/usr/bin/env python3
"""
VISTA-3D API Query Script

This script queries the VISTA-3D API to get the complete list of supported labels
and compares them with the current label configuration files to identify missing labels.
"""

import json
import requests
import sys
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple
import argparse
from datetime import datetime

class Vista3DAPIAnalyzer:
    def __init__(self, api_url: str = "http://localhost:8000", config_dir: str = "conf"):
        self.api_url = api_url.rstrip('/')
        self.config_dir = Path(config_dir)
        self.labels_colors_file = self.config_dir / "vista3d_label_colors.json"
        self.labels_dict_file = self.config_dir / "vista3d_label_dict.json"
        self.labels_colors_backup = self.config_dir / "vista3d_label_colors.json.bak"
        
    def query_vista3d_api(self) -> Dict:
        """Query VISTA-3D API for model information and supported labels."""
        try:
            print(f"Querying VISTA-3D API at {self.api_url}/v1/vista3d/info...")
            response = requests.get(f"{self.api_url}/v1/vista3d/info", timeout=30)
            response.raise_for_status()
            
            api_data = response.json()
            print("✅ Successfully retrieved VISTA-3D API data")
            return api_data
            
        except requests.exceptions.ConnectionError:
            print("❌ Error: Could not connect to VISTA-3D API")
            print(f"   Make sure VISTA-3D is running at {self.api_url}")
            return None
        except requests.exceptions.Timeout:
            print("❌ Error: Request timed out")
            return None
        except requests.exceptions.RequestException as e:
            print(f"❌ Error: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ Error: Invalid JSON response - {e}")
            return None
    
    def load_label_files(self) -> Tuple[Dict, Dict, Dict]:
        """Load existing label configuration files."""
        files_data = {}
        
        for file_path, name in [
            (self.labels_colors_file, "colors"),
            (self.labels_dict_file, "dict"),
            (self.labels_colors_backup, "colors_backup")
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
        
        return files_data.get("colors", {}), files_data.get("dict", {}), files_data.get("colors_backup", {})
    
    def extract_label_ids_from_api(self, api_data: Dict) -> Set[int]:
        """Extract label IDs from VISTA-3D API response."""
        label_ids = set()
        
        # Try different possible structures in the API response
        if 'labels' in api_data:
            labels = api_data['labels']
        elif 'supported_labels' in api_data:
            labels = api_data['supported_labels']
        elif 'model_info' in api_data and 'labels' in api_data['model_info']:
            labels = api_data['model_info']['labels']
        else:
            # If we can't find labels in expected structure, print the response structure
            print("🔍 API Response Structure:")
            self._print_dict_structure(api_data, max_depth=3)
            return label_ids
        
        # Extract IDs from labels
        if isinstance(labels, list):
            for label in labels:
                if isinstance(label, dict) and 'id' in label:
                    label_ids.add(label['id'])
                elif isinstance(label, (int, str)):
                    try:
                        label_ids.add(int(label))
                    except ValueError:
                        pass
        elif isinstance(labels, dict):
            # If labels is a dict, keys are the IDs (as strings) and values are names
            for key in labels.keys():
                try:
                    label_ids.add(int(key))
                except (ValueError, TypeError):
                    pass
        
        return label_ids
    
    def extract_label_ids_from_files(self, colors_data: List, dict_data: Dict) -> Set[int]:
        """Extract label IDs from existing configuration files."""
        label_ids = set()
        
        # From colors file (list of dicts with 'id' field)
        if isinstance(colors_data, list):
            for item in colors_data:
                if isinstance(item, dict) and 'id' in item:
                    label_ids.add(item['id'])
        
        # From dict file (dict with name -> id mapping)
        if isinstance(dict_data, dict):
            for value in dict_data.values():
                try:
                    label_ids.add(int(value))
                except (ValueError, TypeError):
                    pass
        
        return label_ids
    
    def _print_dict_structure(self, d: Dict, prefix="", max_depth=3, current_depth=0):
        """Print dictionary structure for debugging."""
        if current_depth >= max_depth:
            print(f"{prefix}...")
            return
        
        for key, value in d.items():
            if isinstance(value, dict):
                print(f"{prefix}{key}: {{")
                self._print_dict_structure(value, prefix + "  ", max_depth, current_depth + 1)
                print(f"{prefix}}}")
            elif isinstance(value, list):
                print(f"{prefix}{key}: [list with {len(value)} items]")
                if value and isinstance(value[0], dict):
                    print(f"{prefix}  First item keys: {list(value[0].keys())}")
            else:
                print(f"{prefix}{key}: {type(value).__name__}")
    
    def analyze_missing_labels(self, api_label_ids: Set[int], file_label_ids: Set[int]) -> Dict:
        """Analyze missing and extra labels."""
        missing_in_files = api_label_ids - file_label_ids
        extra_in_files = file_label_ids - api_label_ids
        common_labels = api_label_ids & file_label_ids
        
        return {
            'missing_in_files': sorted(missing_in_files),
            'extra_in_files': sorted(extra_in_files),
            'common_labels': sorted(common_labels),
            'api_total': len(api_label_ids),
            'files_total': len(file_label_ids)
        }
    
    def generate_missing_labels_config(self, missing_ids: List[int], api_data: Dict) -> Dict:
        """Generate configuration for missing labels."""
        missing_config = {
            'colors': [],
            'dict': {}
        }
        
        # Try to find label names from API data
        label_names = {}
        if 'labels' in api_data:
            labels = api_data['labels']
            if isinstance(labels, list):
                for label in labels:
                    if isinstance(label, dict) and 'id' in label and 'name' in label:
                        label_names[label['id']] = label['name']
            elif isinstance(labels, dict):
                # If labels is a dict, keys are IDs (as strings) and values are names
                for key, name in labels.items():
                    try:
                        label_names[int(key)] = name
                    except (ValueError, TypeError):
                        pass
        
        # Generate default colors (cycling through a color palette)
        color_palette = [
            [255, 0, 0],      # Red
            [0, 255, 0],      # Green
            [0, 0, 255],      # Blue
            [255, 255, 0],    # Yellow
            [255, 0, 255],    # Magenta
            [0, 255, 255],    # Cyan
            [255, 165, 0],    # Orange
            [128, 0, 128],    # Purple
            [255, 192, 203],  # Pink
            [0, 128, 0],      # Dark Green
        ]
        
        for i, label_id in enumerate(missing_ids):
            # Get name from API or generate default
            name = label_names.get(label_id, f"unknown_label_{label_id}")
            
            # Generate color
            color = color_palette[i % len(color_palette)]
            
            # Add to colors config
            missing_config['colors'].append({
                "id": label_id,
                "name": name,
                "color": color
            })
            
            # Add to dict config
            missing_config['dict'][name] = label_id
        
        return missing_config
    
    def save_analysis_report(self, analysis: Dict, missing_config: Dict, output_file: str = None):
        """Save analysis report to file."""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"vista3d_analysis_report_{timestamp}.json"
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'analysis': analysis,
            'missing_labels_config': missing_config,
            'summary': {
                'total_api_labels': analysis['api_total'],
                'total_file_labels': analysis['files_total'],
                'missing_labels_count': len(analysis['missing_in_files']),
                'extra_labels_count': len(analysis['extra_in_files']),
                'missing_label_ids': analysis['missing_in_files']
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Analysis report saved to: {output_file}")
        return output_file
    
    def run_analysis(self, save_report: bool = True) -> Dict:
        """Run complete analysis."""
        print("🔍 VISTA-3D Label Analysis")
        print("=" * 50)
        
        # Query API
        api_data = self.query_vista3d_api()
        if not api_data:
            return None
        
        # Load existing files
        colors_data, dict_data, backup_data = self.load_label_files()
        
        # Extract label IDs
        api_label_ids = self.extract_label_ids_from_api(api_data)
        file_label_ids = self.extract_label_ids_from_files(colors_data, dict_data)
        
        if not api_label_ids:
            print("❌ No label IDs found in API response")
            print("API Response:")
            print(json.dumps(api_data, indent=2))
            return None
        
        # Analyze differences
        analysis = self.analyze_missing_labels(api_label_ids, file_label_ids)
        
        # Print results
        print("\n📊 Analysis Results:")
        print(f"   API Labels: {analysis['api_total']}")
        print(f"   File Labels: {analysis['files_total']}")
        print(f"   Missing in Files: {len(analysis['missing_in_files'])}")
        print(f"   Extra in Files: {len(analysis['extra_in_files'])}")
        
        if analysis['missing_in_files']:
            print(f"\n❌ Missing Label IDs: {analysis['missing_in_files']}")
        else:
            print("\n✅ No missing labels found!")
        
        if analysis['extra_in_files']:
            print(f"\n⚠️  Extra Label IDs in files: {analysis['extra_in_files']}")
        
        # Generate missing labels configuration
        if analysis['missing_in_files']:
            missing_config = self.generate_missing_labels_config(analysis['missing_in_files'], api_data)
            print(f"\n🔧 Generated configuration for {len(analysis['missing_in_files'])} missing labels")
        else:
            missing_config = {'colors': [], 'dict': {}}
        
        # Save report
        if save_report:
            report_file = self.save_analysis_report(analysis, missing_config)
            print(f"\n📄 Complete analysis saved to: {report_file}")
        
        return {
            'analysis': analysis,
            'missing_config': missing_config,
            'api_data': api_data
        }

def main():
    parser = argparse.ArgumentParser(description='Query VISTA-3D API and analyze label configuration')
    parser.add_argument('--api-url', default='http://localhost:8000', 
                       help='VISTA-3D API URL (default: http://localhost:8000)')
    parser.add_argument('--config-dir', default='conf', 
                       help='Configuration directory (default: conf)')
    parser.add_argument('--no-report', action='store_true', 
                       help='Do not save analysis report')
    
    args = parser.parse_args()
    
    analyzer = Vista3DAPIAnalyzer(args.api_url, args.config_dir)
    result = analyzer.run_analysis(save_report=not args.no_report)
    
    if result:
        print("\n✅ Analysis completed successfully!")
        if result['analysis']['missing_in_files']:
            print("\n💡 Next steps:")
            print("   1. Review the missing labels in the analysis report")
            print("   2. Update your label configuration files")
            print("   3. Test the updated configuration")
    else:
        print("\n❌ Analysis failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
