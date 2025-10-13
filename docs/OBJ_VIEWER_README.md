# OBJ Viewer - Quick Start

## What Was Created

A new Streamlit-based 3D OBJ mesh viewer that follows the same navigation pattern as the NiiVue Viewer.

### Files Created/Modified:

1. **`OBJ_Viewer.py`** - Main viewer application with Three.js integration
2. **`utils/data_manager.py`** - Added OBJ-specific methods:
   - `get_obj_scans(patient_id)` - Get scan folders containing OBJ files
   - `get_obj_files(patient_id, scan_name)` - Get OBJ files for a scan
   - `get_obj_directory_url(patient_id, scan_name)` - Get OBJ directory URL

3. **`conf/navigation_config.json`** - Added OBJ Viewer to navigation menu
4. **`app.py`** - Added route handler for OBJ viewer page
5. **`docs/OBJ_VIEWER_GUIDE.md`** - Complete user documentation

## How to Access

1. Open the application in your browser (usually http://localhost:8501)
2. Click **🫁 OBJ Viewer** in the sidebar navigation
3. Select a patient, scan, and objects to view

## Expected Folder Structure

```
OUTPUT_FOLDER/
└── PATIENT_ID/
    └── obj/
        └── SCAN_NAME/
            ├── organ1.obj
            ├── organ2.obj
            └── ...
```

Example with real data:
```
/output/
└── PA00000002/
    └── obj/
        └── 2.5MM_ARTERIAL_3/
            ├── liver.obj
            ├── heart.obj
            ├── spleen.obj
            └── ... (80 OBJ files)
```

## Features

✅ Patient/Scan/File navigation matching NiiVue Viewer
✅ Multi-select for viewing multiple objects simultaneously
✅ Interactive 3D controls (rotate, pan, zoom)
✅ Auto-coloring based on Vista3D label colors
✅ Customizable settings:
  - Wireframe overlay
  - Object opacity
  - Auto-rotation
  - Lighting controls

## Generating OBJ Files

If you need to create OBJ files from voxel data:

```bash
cd /Users/dave/AI/HPE/HPE-Nvidia-Vista-3D/frontend

# Generate OBJ files for a specific patient and scan
python utils/voxel2obj.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 -v

# Options:
# -t, --threshold: Iso-surface threshold (default: 0.1)
# -s, --smoothing: Smoothing iterations (default: 10)
# -d, --decimation: Mesh simplification (0.0-1.0, default: 0.5)
# -v, --verbose: Detailed output
# --close-boundaries: Fill holes in meshes (default: True)
# --hole-filling: Method - 'convex' or 'planar' (default: convex)
```

## Troubleshooting

### Container Restart (if changes aren't reflected)
```bash
cd /Users/dave/AI/HPE/HPE-Nvidia-Vista-3D/frontend
docker compose restart vista3d-frontend
```

### No Patient Folders Found
- Verify image server is running
- Check OUTPUT_FOLDER in .env file
- Ensure patient directories have obj/ folders with OBJ files

### Objects Not Displaying
- Check browser console (F12) for errors
- Verify OBJ file URLs are accessible: `http://localhost:8888/output/PATIENT_ID/obj/SCAN_NAME/`
- Ensure files are valid OBJ format

### Performance Issues
- View fewer objects simultaneously
- Enable browser hardware acceleration
- Try reducing mesh complexity during OBJ generation (higher decimation value)

## Browser Support

Requires a modern browser with WebGL support:
- Chrome 56+
- Firefox 51+
- Safari 11+
- Edge 15+

## Technical Stack

- **Frontend**: Streamlit + Three.js (v0.150.0)
- **3D Rendering**: WebGL via Three.js
- **Controls**: OrbitControls for camera manipulation
- **File Format**: Wavefront OBJ (.obj)
- **Lighting**: Ambient + Dual directional lights
- **Materials**: Phong shading with vertex colors

## Integration with Existing Workflow

The OBJ Viewer completes the medical imaging visualization pipeline:

1. **DICOM → NIfTI**: Convert medical images (Image Data page)
2. **NIfTI → Segmentation**: Run Vista3D segmentation (Tools page)
3. **Voxels → OBJ**: Convert to 3D meshes (`voxel2obj.py`)
4. **Visualization**: View in OBJ Viewer 🫁

## Next Steps

1. Test the viewer by navigating to **🫁 OBJ Viewer** in the app
2. If you already have OBJ files, select a patient and scan to view them
3. If you need to generate OBJ files, use the `voxel2obj.py` utility
4. Customize the viewer settings to your preference

For detailed documentation, see: `docs/OBJ_VIEWER_GUIDE.md`

