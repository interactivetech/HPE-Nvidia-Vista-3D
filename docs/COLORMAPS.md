# Colormaps in Vista3D

This document describes how colormaps work in the Vista3D medical imaging visualization project, including their structure, usage, and management.

## Overview

Vista3D uses colormaps to provide meaningful color representations for medical imaging data. The system supports multiple colormap sets optimized for different medical imaging modalities and scientific visualization needs.

## Colormap Architecture

### File Structure

```
assets/colormaps/
├── basic_medical.json     # Essential medical imaging colormaps
├── medical_specific.json  # Specialized medical modality colormaps
└── scientific.json        # Scientific visualization colormaps
```

### Colormap Format

Each colormap JSON file follows this structure:

```json
{
  "name": "Colormap Set Name",
  "description": "Description of the colormap set",
  "version": "1.0",
  "default": "default_colormap_name",
  "colormaps": {
    "colormap_name": {
      "R": [r1, r2, r3, ...],
      "G": [g1, g2, g3, ...],
      "B": [b1, b2, b3, ...],
      "A": [a1, a2, a3, ...],
      "labels": ["Label1", "Label2", "Label3", ...]
    }
  }
}
```

#### Field Descriptions

- **R, G, B, A**: Arrays of color channel values (0-255) defining the colormap
- **labels**: Descriptive labels for each color point in the map
- **default**: The default colormap to use from this set

## Available Colormap Sets

### 1. Basic Medical (`basic_medical.json`)

Essential colormaps for general medical imaging:

- **gray**: Standard grayscale for CT and MRI data
- **viridis**: Perceptually uniform colormap for continuous data
- **plasma**: High-contrast colormap for highlighting features
- **inferno**: Dark-to-bright colormap for intensity visualization
- **magma**: Purple-to-yellow colormap for thermal-like visualization

### 2. Medical Specific (`medical_specific.json`)

Specialized colormaps for different medical imaging modalities:

- **bone**: Optimized for bone visualization in CT scans
- **cool**: Cool color palette (cyan to magenta)
- **hot**: Hot color palette (black to red to yellow to white)
- **warm**: Warm color palette (magenta to yellow)
- **ct_skull**: Specialized for skull CT visualization
- **ct_bone**: Optimized for bone structures in CT
- **ct_soft**: For soft tissue visualization in CT
- **ct_lung**: Specialized for lung tissue visualization

### 3. Scientific (`scientific.json`)

Perceptually uniform colormaps for scientific data:

- **turbo**: Google's improved replacement for jet colormap
- **jet**: Traditional rainbow colormap (use with caution)
- **hsv**: Hue-saturation-value based colormap
- **parula**: MATLAB's default colormap
- **rainbow**: Traditional rainbow colors
- **spectral**: Spectral color progression

## Usage in the Application

### 1. Python Backend (`utils/constants.py`)

The backend loads all available colormaps dynamically:

```python
def load_colormaps():
    """Load colormap names from all JSON files, with fallback to basic set."""
    # Scans assets/colormaps/ for JSON files
    # Extracts colormap names from each file
    # Returns list of all available colormap names
```

### 2. JavaScript Frontend (`utils/colormap_manager.js`)

The ColormapManager class handles colormap loading and management:

```javascript
class ColormapManager {
    constructor() {
        this.colormapSets = {};
        this.defaultSet = 'basic_medical';
        this.loadColormapSets();
    }

    async loadColormapSets() {
        // Loads colormap JSON files asynchronously
    }

    getColormaps(setName = null) {
        // Returns colormaps from specified set
    }

    getAllColormaps() {
        // Returns all colormaps from all sets
    }
}
```

### 3. NiiVue Integration

Colormaps are applied to medical imaging data through the NiiVue viewer:

1. **Main Volume Colormaps**: Applied to primary medical images (CT, MRI)
2. **Overlay Colormaps**: Used for segmentation and annotation overlays
3. **Custom Colormaps**: Dynamically created for specific visualization needs

## Colormap Selection Guidelines

### For Medical Imaging

1. **CT Scans**:
   - Use `gray` for general viewing
   - Use `ct_bone` for bone structures
   - Use `ct_soft` for soft tissues
   - Use `ct_lung` for lung imaging

2. **MRI**:
   - Use `gray` for T1/T2 weighted images
   - Use `bone` for structural imaging

3. **Segmentation Overlays**:
   - Custom colormaps with specific colors for each segment
   - High opacity for clear visualization
   - Distinct colors to avoid confusion

### For Scientific Data

1. **Continuous Data**: Use `viridis`, `plasma`, or `turbo`
2. **Categorical Data**: Use `hsv` or custom discrete colormaps
3. **Avoid**: `jet` and `rainbow` for quantitative data (perceptually non-uniform)

## Implementation Details

### Dynamic Colormap Loading

The application loads colormaps in two stages:

1. **Backend Loading**: Python scans colormap files and makes names available
2. **Frontend Loading**: JavaScript loads colormap data for NiiVue integration

### Custom Colormap Creation

For segmentation overlays, the application creates custom colormaps:

```javascript
// Example: Create custom colormap for specific overlay
const customColormap = {
    R: [0, color[0]],
    G: [0, color[1]], 
    B: [0, color[2]],
    A: [0, 255],
    labels: ['Background', labelName]
};
```

### Colormap Application

1. **NiiVue Registration**: `nv.addColormap(name, colormap)`
2. **Volume Assignment**: `nv.setColormap(volumeId, colormapName)`
3. **Dynamic Updates**: Colormaps can be changed at runtime

## Configuration

### Viewer Settings

Colormaps are configured through the viewer settings:

- **Color Map Selection**: Available in the NIfTI Image Settings
- **Opacity Control**: Adjustable opacity for overlays
- **Gamma Correction**: Fine-tuning of colormap appearance

### Default Settings

- Default colormap set: `basic_medical`
- Default colormap: `gray`
- Fallback colormaps: `['gray', 'viridis', 'plasma', 'inferno', 'magma']`

## Best Practices

### Colormap Design

1. **Perceptual Uniformity**: Use colormaps with uniform perceptual changes
2. **Accessibility**: Consider colorblind-friendly options
3. **Medical Standards**: Follow established medical imaging conventions
4. **Context Appropriate**: Match colormap to data type and purpose

### Performance Considerations

1. **Lazy Loading**: Colormaps are loaded only when needed
2. **Caching**: Loaded colormaps are cached for reuse
3. **Fallback Handling**: Graceful degradation when colormaps fail to load

### File Organization

1. **Logical Grouping**: Separate colormaps by use case (medical, scientific)
2. **Descriptive Names**: Use clear, descriptive colormap names
3. **Version Control**: Include version information in colormap files
4. **Documentation**: Include labels and descriptions for each colormap

## Troubleshooting

### Common Issues

1. **Colormap Not Loading**: Check file path and JSON syntax
2. **Colors Not Displaying**: Verify colormap registration with NiiVue
3. **Performance Issues**: Reduce number of color points in large colormaps

### Debug Information

The application logs colormap loading status to the browser console:
- `Loaded colormap set: {setName}`
- `Custom segmentation colormap added`
- Warnings for failed loads

## Adding New Colormaps

### Steps to Add a New Colormap

1. **Create JSON Structure**: Follow the established format
2. **Add to Appropriate File**: Choose the right colormap set file
3. **Test Loading**: Verify the colormap loads correctly
4. **Update Documentation**: Document the new colormap's purpose

### Example Addition

```json
{
  "new_colormap": {
    "R": [0, 64, 128, 192, 255],
    "G": [0, 32, 64, 96, 128],
    "B": [0, 16, 32, 48, 64],
    "A": [255, 255, 255, 255, 255],
    "labels": ["Min", "Low", "Mid", "High", "Max"]
  }
}
```

## Related Components

- **NiiVue Viewer**: Primary visualization component
- **Template Renderer**: Handles HTML template generation
- **Viewer Configuration**: Manages UI settings and controls
- **Constants**: Defines available colormap lists
- **Config Manager**: Handles application configuration

This colormap system provides flexible, extensible color visualization for medical imaging data while maintaining performance and usability standards.
