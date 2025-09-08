# VISTA-3D API Analysis Scripts

This directory contains scripts to query the VISTA-3D API and analyze label configuration files.

## Files

- `query_vista3d_api.py` - Main Python script for API analysis
- `run_vista3d_analysis.sh` - Bash script to automatically find and run analysis
- `README_vista3d_analysis.md` - This documentation

## Quick Start

### Option 1: Automatic Detection
```bash
./utils/run_vista3d_analysis.sh
```

### Option 2: Manual Execution
```bash
# Basic usage (assumes VISTA-3D on localhost:8000)
python utils/query_vista3d_api.py

# Specify custom API URL
python utils/query_vista3d_api.py --api-url http://your-server:port

# Specify custom config directory
python utils/query_vista3d_api.py --config-dir /path/to/conf

# Don't save analysis report
python utils/query_vista3d_api.py --no-report
```

## What the Script Does

1. **Queries VISTA-3D API** - Gets the complete list of supported labels from `/v1/vista3d/info`
2. **Loads Current Configuration** - Reads your existing label files:
   - `conf/vista3d_label_colors.json`
   - `conf/vista3d_label_dict.json`
   - `conf/vista3d_label_colors.json.bak`
3. **Compares Labels** - Identifies missing and extra labels
4. **Generates Report** - Creates a detailed analysis report with missing label configurations

## Output

The script generates:
- **Console Output** - Real-time analysis results
- **Analysis Report** - JSON file with complete analysis (`vista3d_analysis_report_YYYYMMDD_HHMMSS.json`)

## Example Output

```
🔍 VISTA-3D Label Analysis
==================================================
Querying VISTA-3D API at http://localhost:8000/v1/vista3d/info...
✅ Successfully retrieved VISTA-3D API data
✅ Loaded colors file: conf/vista3d_label_colors.json
✅ Loaded dict file: conf/vista3d_label_dict.json
✅ Loaded colors_backup file: conf/vista3d_label_colors.json.bak

📊 Analysis Results:
   API Labels: 128
   File Labels: 124
   Missing in Files: 4
   Extra in Files: 0

❌ Missing Label IDs: [2, 16, 18, 20]

🔧 Generated configuration for 4 missing labels
📄 Analysis report saved to: vista3d_analysis_report_20241209_143022.json
```

## Prerequisites

- Python 3.6+
- `requests` library: `pip install requests`
- VISTA-3D running and accessible via HTTP

## Troubleshooting

### Connection Issues
- Ensure VISTA-3D is running
- Check the API URL and port
- Verify network connectivity

### Missing Dependencies
```bash
pip install requests
```

### Permission Issues
```bash
chmod +x utils/query_vista3d_api.py
chmod +x utils/run_vista3d_analysis.sh
```

## Next Steps

After running the analysis:

1. **Review the Report** - Check the generated JSON report for missing labels
2. **Update Configuration** - Add missing labels to your configuration files
3. **Test Changes** - Verify the updated configuration works with VISTA-3D
4. **Backup** - Keep backups of your original configuration files

## API Response Structure

The script handles various possible API response structures:
- `{ "labels": [...] }`
- `{ "supported_labels": [...] }`
- `{ "model_info": { "labels": [...] } }`

If the structure is different, the script will print the response structure for debugging.
