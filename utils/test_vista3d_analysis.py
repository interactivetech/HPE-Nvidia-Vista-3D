#!/usr/bin/env python3
"""
Test script for VISTA-3D API analysis.
This tests the analysis functionality with real API data.
"""

import json
import sys
import os
from pathlib import Path

# Add the utils directory to the path so we can import the main script
sys.path.append(str(Path(__file__).parent))

from query_vista3d_api import Vista3DAPIAnalyzer

def test_analysis():
    """Test the analysis functionality with real API data."""
    print("🧪 Testing VISTA-3D Analysis Script")
    print("=" * 50)
    
    # Create analyzer
    analyzer = Vista3DAPIAnalyzer()
    
    # Query real API
    print("📡 Querying VISTA-3D API...")
    api_data = analyzer.query_vista3d_api()
    
    if not api_data:
        print("❌ Failed to query VISTA-3D API")
        return None
    
    # Load existing files
    colors_data, dict_data, backup_data = analyzer.load_label_files()
    
    # Extract label IDs
    api_label_ids = analyzer.extract_label_ids_from_api(api_data)
    file_label_ids = analyzer.extract_label_ids_from_files(colors_data, dict_data)
    
    print(f"API Labels: {len(api_label_ids)}")
    print(f"File Labels: {len(file_label_ids)}")
    
    # Analyze differences
    analysis = analyzer.analyze_missing_labels(api_label_ids, file_label_ids)
    
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
        missing_config = analyzer.generate_missing_labels_config(analysis['missing_in_files'], api_data)
        print(f"\n🔧 Generated configuration for {len(analysis['missing_in_files'])} missing labels")
        
        # Show sample of missing labels configuration
        print("\n📋 Sample Missing Labels Configuration:")
        for i, label in enumerate(missing_config['colors'][:3]):  # Show first 3
            print(f"   ID {label['id']}: {label['name']} - Color: {label['color']}")
        if len(missing_config['colors']) > 3:
            print(f"   ... and {len(missing_config['colors']) - 3} more")
    
    print("\n✅ Test completed successfully!")
    return analysis

if __name__ == "__main__":
    test_analysis()
