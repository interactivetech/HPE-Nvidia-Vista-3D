# OBJ Viewer Guide

## Overview

The OBJ Viewer is an interactive 3D mesh viewer for anatomical structures extracted from medical imaging data. It provides real-time 3D visualization of anatomical structures exported as OBJ mesh files.

## Features

- **Patient & Scan Navigation**: Navigate through patient folders and select specific scan sessions
- **Multiple Object Selection**: Display multiple anatomical structures simultaneously
- **Interactive 3D Controls**: 
  - Left-click drag: Rotate view
  - Right-click drag: Pan view
  - Mouse wheel: Zoom in/out
- **Customization Options**:
  - Background color selection
  - Wireframe overlay toggle
  - Object opacity adjustment
  - Auto-rotation mode
  - Adjustable ambient and directional lighting

## File Structure

The OBJ viewer expects files to be organized in the following structure:

```
OUTPUT_FOLDER/
├── PATIENT_ID/
│   ├── obj/
│   │   ├── SCAN_NAME/
│   │   │   ├── organ1.obj
│   │   │   ├── organ2.obj
│   │   │   └── ...
```

For example:
```
/output/
├── PA00000002/
│   ├── obj/
│   │   ├── 2.5MM_ARTERIAL_3/
│   │   │   ├── liver.obj
│   │   │   ├── heart.obj
│   │   │   ├── spleen.obj
│   │   │   └── ...
```

## Accessing the OBJ Viewer

1. Start the application: `streamlit run app.py`
2. In the sidebar navigation menu, click **🫁 OBJ Viewer**
3. Select a patient from the dropdown
4. Choose a scan session
5. Select one or more objects to display

## Quick Selection Buttons

- **Select All**: Quickly select all available OBJ files for viewing
- **Clear All**: Deselect all objects

## Viewer Settings

### Show Wireframe
Enable wireframe overlay on top of solid meshes to see the mesh structure.

### Object Opacity
Adjust the transparency of all displayed objects (0.0 = fully transparent, 1.0 = fully opaque).

### Auto Rotate
Enable automatic rotation of the 3D view for presentation mode.

### Lighting Settings
- **Ambient Light**: Overall scene illumination (0.0 - 2.0)
- **Directional Light**: Focused lighting intensity (0.0 - 2.0)

## Color Mapping

Objects are automatically colored based on the Vista3D label color configuration (`conf/vista3d_label_colors.json`). Each anatomical structure is assigned a specific color for consistency across visualizations.

## Browser Compatibility

The OBJ viewer uses Three.js for 3D rendering and requires a modern web browser with WebGL support:
- Chrome 56+
- Firefox 51+
- Safari 11+
- Edge 15+

## Performance Tips

1. **Large File Sets**: When viewing many objects simultaneously, consider:
   - Reducing object opacity to improve visibility
   - Selecting fewer objects for better performance
   
2. **Slow Loading**: If objects take time to load:
   - Check your network connection to the image server
   - Verify OBJ files are not corrupted
   - Monitor the loading progress in the viewer

3. **Rendering Issues**: If you experience visual artifacts:
   - Try adjusting lighting settings
   - Toggle wireframe mode off
   - Reduce the number of displayed objects

## Generating OBJ Files

OBJ files can be generated from NIfTI voxel data using the `voxel2obj.py` utility:

```bash
python utils/voxel2obj.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 -v
```

This will convert all voxel files from:
```
OUTPUT_FOLDER/PA00000002/voxels/2.5MM_ARTERIAL_3/
```

To OBJ meshes in:
```
OUTPUT_FOLDER/PA00000002/obj/2.5MM_ARTERIAL_3/
```

## Troubleshooting

### No Patient Folders Found
- Verify the image server is running
- Check OUTPUT_FOLDER path in `.env` file
- Ensure patient directories contain `obj/` folders

### Objects Not Loading
- Check browser console for JavaScript errors
- Verify OBJ file URLs are accessible
- Ensure image server is serving files correctly

### Performance Issues
- Try viewing fewer objects at once
- Check browser hardware acceleration is enabled
- Close other resource-intensive browser tabs

## Technical Details

- **3D Engine**: Three.js (v0.150.0)
- **File Format**: Wavefront OBJ (.obj)
- **Controls**: OrbitControls for camera manipulation
- **Lighting**: Ambient + Dual directional lights
- **Materials**: Phong shading with per-vertex colors

## Integration with Workflow

The OBJ Viewer integrates with the complete Vista3D workflow:

1. **DICOM → NIfTI**: Convert medical images using Image Data tools
2. **NIfTI → Segmentation**: Run Vista3D segmentation
3. **Voxels → OBJ**: Convert voxel data to 3D meshes with `voxel2obj.py`
4. **Visualization**: View and analyze 3D anatomy in the OBJ Viewer

## API Usage

The OBJ Viewer uses the DataManager API for file access:

```python
# Get available scans for a patient
scans = data_manager.get_obj_scans(patient_id)

# Get OBJ files for a specific scan
obj_files = data_manager.get_obj_files(patient_id, scan_name)

# Get URL for OBJ directory
url = data_manager.get_obj_directory_url(patient_id, scan_name)
```

## Related Documentation

- [SETUP_GUIDE.md](SETUP_GUIDE.md) - General setup instructions
- [NIIVUE_VIEWER.md](NIIVUE_VIEWER.md) - NIfTI viewer documentation
- See `utils/voxel2obj.py` for OBJ generation options

