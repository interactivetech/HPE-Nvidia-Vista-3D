# NiiVue Viewer Documentation

## Overview

The NiiVue Viewer is a sophisticated Streamlit-based medical imaging application that provides interactive visualization of NIFTI files with advanced overlay capabilities. Built on the NiiVue JavaScript library, it offers comprehensive tools for viewing medical scans with anatomical segmentation overlays, making it ideal for medical professionals, researchers, and imaging specialists.

## 🎯 Key Features

### 📊 Advanced Medical Imaging Visualization
- **NIFTI File Support**: Native support for .nii and .nii.gz medical imaging files
- **Interactive 3D Viewer**: Full multiplanar reconstruction with axial, coronal, sagittal, and 3D rendering
- **Real-time Windowing**: Adjustable window center and width for optimal tissue contrast
- **Color Mapping**: Multiple medical imaging color maps including grayscale, viridis, plasma, and more

### 🎭 Anatomical Segmentation Overlays
- **Vista3D Integration**: Seamless integration with Vista3D segmentation outputs
- **Individual Voxel Selection**: Choose specific anatomical structures to display
- **Smart Overlay Management**: Automatic color assignment and opacity control
- **Dynamic Label Loading**: Real-time loading of anatomical structure names

### 🎮 Interactive Controls
- **Patient Selection**: Browse and select from available patient datasets
- **Scan Selection**: Choose from multiple scans per patient with clean display names
- **Voxel Mode Selection**: Toggle between "All" and "Individual Voxels" display modes
- **Real-time Settings**: Adjust opacity, gamma, and visualization parameters on-the-fly

### 🔧 Technical Architecture
- **Modular Design**: Clean separation of concerns with specialized utility modules
- **Server Integration**: Connects to dedicated image server for efficient file serving
- **Configuration Management**: Centralized configuration with caching for optimal performance
- **Template Rendering**: Dynamic HTML template generation with Jinja2

## 📁 Application Structure

### Main Components

#### 1. **Core Application** (`NiiVue_Viewer.py`)
The main Streamlit application that orchestrates the entire viewing experience.

**Key Functions:**
- `main()`: Application entry point and page setup
- `render_sidebar()`: Creates the patient/file selection interface
- `render_voxel_selection()`: Manages voxel overlay selection
- `render_viewer()`: Renders the main NiiVue visualization

#### 2. **Utility Modules**

##### **ConfigManager** (`utils/config_manager.py`)
Centralized configuration management with caching capabilities.
- Loads Vista3D label colors, dictionaries, and sets
- Caches JSON configuration files to avoid repeated I/O
- Provides clean interface for accessing anatomical structure metadata

##### **DataManager** (`utils/data_manager.py`)
Handles all server interactions and data fetching operations.
- Communicates with the image server for file listings
- Parses HTML directory structures
- Manages patient and scan file discovery
- Constructs proper URLs for NIFTI and voxel files

##### **VoxelManager** (`utils/voxel_manager.py`)
Manages voxel selection and overlay configuration.
- Discovers available anatomical structures
- Creates overlay configurations for NiiVue
- Handles individual voxel selection logic
- Generates custom color maps for anatomical structures

##### **ViewerConfig** (`utils/viewer_config.py`)
Manages viewer settings, state, and UI configuration.
- Maintains viewer settings (slice type, opacity, windowing)
- Handles Streamlit session state management
- Provides UI components for settings adjustment
- Manages window presets for different tissue types

##### **TemplateRenderer** (`utils/template_renderer.py`)
Handles rendering of HTML templates with dynamic data injection.
- Uses Jinja2 for template processing
- Injects JavaScript data for NiiVue initialization
- Manages template loading and caching

## 🚀 Usage Guide

### Prerequisites

1. **Environment Setup**:
   ```bash
   # Set up environment variables
   cp dot_env_template .env
   # Edit .env to configure IMAGE_SERVER and OUTPUT_FOLDER
   ```

2. **Image Server**: Ensure the image server is running:
   ```bash
   python utils/image_server.py
   ```

3. **Data Structure**: Organize your data in the expected format:
   ```
   output/
   ├── PATIENT_ID/
   │   ├── nifti/
   │   │   └── scan_files.nii.gz
   │   ├── segments/
   │   │   └── segmentation_files.nii.gz
   │   └── voxels/
   │       └── SCAN_NAME/
   │           └── individual_structure_files.nii.gz
   ```

### Starting the Application

1. **Launch the Viewer**:
   ```bash
   streamlit run NiiVue_Viewer.py
   ```

2. **Access the Interface**:
   - Open your browser to `http://localhost:8501`
   - The application loads with an empty viewer awaiting selection

### Basic Workflow

#### Step 1: Patient Selection
1. Use the **"Select Patient"** dropdown in the sidebar
2. Choose from available patient folders in your output directory
3. Patient selection automatically triggers scan discovery

#### Step 2: Scan Selection
1. The **"Select Scan"** dropdown populates with available NIFTI files
2. Scan names are cleaned (removing .nii.gz extensions) for better readability
3. Select the desired scan for visualization

#### Step 3: Viewer Configuration
1. **Slice Type**: Choose viewing mode (Axial, Coronal, Sagittal, Multiplanar, 3D Render)
2. **Window Settings**: 
   - Use presets (Brain, Abdomen, Lung, Bone) or custom values
   - Adjust window center and width for optimal contrast
3. **Display Options**:
   - Toggle NIFTI base image display
   - Enable/disable overlay visualization
   - Adjust opacity and gamma settings

#### Step 4: Overlay Management (Optional)
1. **Enable Overlays**: Check "Show Overlay" in the sidebar
2. **Select Voxel Mode**:
   - **"All"**: Display the complete segmentation file
   - **"Individual Voxels"**: Choose specific anatomical structures
3. **Structure Selection**: 
   - Browse available anatomical structures
   - Multi-select desired structures for overlay
4. **Overlay Settings**:
   - Adjust segment opacity for optimal visualization
   - Structures automatically receive distinct colors

### Advanced Features

#### Voxel Legend
- Displays selected anatomical structures with their assigned colors
- Provides visual reference for overlay interpretation
- Updates dynamically based on voxel selection

#### Status Messages
- Real-time feedback on current selection state
- Guidance messages for next steps
- Error notifications for missing data

#### Custom Color Mapping
- Automatic color assignment for anatomical structures
- Vista3D label configuration integration
- Consistent color mapping across sessions

## 🛠️ Technical Implementation

### Architecture Patterns

#### **Separation of Concerns**
Each utility module handles a specific aspect of functionality:
- Configuration management is isolated in ConfigManager
- Server communication is centralized in DataManager  
- UI state management is handled by ViewerConfig
- Voxel logic is contained in VoxelManager

#### **Caching Strategy**
- Configuration files are loaded once and cached
- Server responses are minimized through smart data fetching
- Template rendering includes caching for performance

#### **State Management**
- Streamlit session state is used for persistent viewer settings
- Configuration changes trigger automatic UI updates
- Voxel selections are maintained across navigation

### Integration Points

#### **Image Server Communication**
```python
# Example: Fetching patient folders
patient_folders = data_manager.get_server_data('', 'folders', ('',))

# Example: Getting scan files
filenames = data_manager.get_server_data(f"{patient}/nifti", 'files', IMAGE_EXTENSIONS)
```

#### **NiiVue Integration**
```javascript
// Dynamic volume list creation
const volumeList = {{ volume_list_js|safe }};
const overlayColors = {{ overlay_colors_js|safe }};

// NiiVue initialization with medical imaging settings
const nv = new niivue.Niivue({
    isColorbar: false,
    loadingText: 'loading ...',
    dragAndDropEnabled: false
});
```

#### **Vista3D Configuration**
```python
# Anatomical structure mapping
label_colors = config_manager.label_colors
label_dict = config_manager.label_dict
id_to_name_map = config_manager.get_id_to_name_map()
```

## 🔧 Configuration

### Environment Variables
- `IMAGE_SERVER`: URL of the image server (default: http://localhost:8888)
- `OUTPUT_FOLDER`: Directory containing patient data (default: output)

### Configuration Files
- `conf/vista3d_label_colors.json`: Anatomical structure color definitions
- `conf/vista3d_label_dict.json`: Structure name to ID mappings
- `conf/vista3d_label_sets.json`: Grouped structure definitions

### Viewer Settings
Default settings can be modified in `utils/constants.py`:
```python
DEFAULT_VIEWER_SETTINGS = {
    'slice_type': 'Multiplanar',
    'orientation': 'Axial',
    'color_map': 'gray',
    'nifti_opacity': 0.5,
    'nifti_gamma': 1.0,
    'show_nifti': True,
    'show_overlay': False,
    'segment_opacity': 0.5,
    'segment_gamma': 1.0,
    'window_center': 0,
    'window_width': 1000,
}
```

## 🔍 Troubleshooting

### Common Issues

#### **No Patients Available**
- Verify the image server is running on the configured port
- Check that the OUTPUT_FOLDER contains patient directories
- Ensure patient directories contain nifti subdirectories

#### **Scans Not Loading**
- Confirm NIFTI files exist in the patient's nifti directory
- Verify file extensions are .nii or .nii.gz
- Check image server logs for file serving errors

#### **Overlays Not Displaying**
- Ensure segments directory exists with corresponding .nii.gz files
- Verify voxels directory structure matches the scan name
- Check Vista3D configuration files for label definitions

#### **Viewer Performance Issues**
- Large NIFTI files may require streaming optimization
- Consider reducing image resolution for better performance
- Monitor browser memory usage for very large datasets

### Debug Information
Enable debug mode by uncommenting the debug checkbox in the code:
```python
st.checkbox("Show Debug Info", value=False, key="debug_info")
```

## 🔮 Future Enhancements

### Planned Features
- **Multi-timepoint Support**: Visualization of temporal imaging series
- **Measurement Tools**: Distance, angle, and area measurement capabilities
- **Export Functionality**: Save views as images or generate reports
- **Collaborative Features**: Share views with team members
- **Advanced Windowing**: Histogram-based windowing controls

### Performance Optimizations
- **Lazy Loading**: Load voxel data only when needed
- **Compression**: Implement client-side image compression
- **Caching**: Browser-based caching for frequently accessed data
- **Streaming**: Progressive loading for large datasets

## 📚 Related Documentation

- [DICOM Inspector](DICOM_INSPECTOR.md): Raw DICOM file inspection and analysis
- [Image Server](IMAGE_SERVER.md): HTTP server for medical imaging files
- [Vista3D Setup](VISTA3D_SETUP.md): AI segmentation pipeline configuration
- [DICOM to NIFTI](DICOM2NIFTI.md): Medical image format conversion

## 🤝 Contributing

When extending the NiiVue Viewer:

1. **Follow the modular architecture**: Add new functionality to appropriate utility modules
2. **Maintain state consistency**: Use ViewerConfig for all UI state management
3. **Add configuration options**: Extend constants.py for new settings
4. **Test with real data**: Verify functionality with actual medical imaging datasets
5. **Document changes**: Update this documentation for any new features

---

*The NiiVue Viewer represents a sophisticated approach to medical imaging visualization, combining the power of NiiVue with intelligent data management and user-friendly interfaces.*
