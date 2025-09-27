# CT Visualization Enhancement Guide

This guide explains how to achieve the impressive CT rendering effects shown in the reference images, based on the NiiVue issue #83 implementation.

## Overview

The enhanced CT visualization system implements the standardized colormap format proposed in [NiiVue issue #83](https://github.com/niivue/niivue/issues/83) with proper intensity mapping, alpha blending, and volume rendering capabilities.

## Key Components

### 1. Enhanced Colormap Format

The new colormap format includes all required properties from the NiiVue specification:

```json
{
  "name": "CT Enhanced Visualization",
  "colormaps": {
    "niivue-ct_enhanced": {
      "min": -1000,           // Minimum HU value
      "max": 3000,            // Maximum HU value
      "R": [0, 0, 0, ...],    // Red channel values
      "G": [0, 50, 100, ...], // Green channel values
      "B": [0, 100, 150, ...],// Blue channel values
      "A": [0, 5, 15, ...],   // Alpha/transparency values
      "I": [-1000, -500, ...],// Intensity mapping (HU values)
      "labels": ["Air", "Lung", ...] // Tissue type labels
    }
  }
}
```

### 2. Available CT Colormaps

#### Soft Tissue Visualization
- **niivue-ct_soft**: Enhanced soft tissue colormap with warm colors and proper transparency
- **niivue-ct_translucent**: Optimized for translucent soft tissue effects with high transparency

#### Bone Visualization  
- **niivue-ct_bones**: Enhanced bone colormap with proper intensity mapping
- **niivue-ct_metallic**: Metallic bone visualization with reflective properties

#### Combined Visualization
- **niivue-ct_enhanced**: Comprehensive colormap combining soft tissue and bone visualization

### 3. CT Window Presets

Enhanced window presets for optimal tissue contrast:

- **CT Brain** (W:80, L:40): Optimized for brain tissue visualization
- **CT Chest** (W:350, L:50): Best for lung and chest imaging
- **CT Abdomen** (W:350, L:40): Ideal for abdominal organs
- **CT Spine** (W:1800, L:400): Optimized for spinal imaging
- **CT Skull** (W:4000, L:700): High contrast for skull visualization

### 4. Volume Rendering Settings

For 3D effects similar to the reference images:

```javascript
// Volume rendering configuration
const volumeSettings = {
    volume_rendering: true,
    volume_opacity: 0.8,
    volume_gamma: 1.0,
    lighting_enabled: true,
    material_shininess: 0.5
};
```

## Achieving Specific Effects

### Translucent Soft Tissue Effect (Left Image)

1. **Colormap**: Use `niivue-ct_translucent` or `niivue-ct_soft`
2. **Window**: CT Chest or CT Abdomen preset
3. **Opacity**: Set to 0.3-0.5 for transparency
4. **Volume Rendering**: Enable for 3D effects
5. **Alpha Values**: Higher alpha values (50-110) for tissue visibility

### Metallic Bone Effect (Right Image)

1. **Colormap**: Use `niivue-ct_metallic` or `niivue-ct_bones`
2. **Window**: CT Skull or CT Spine preset
3. **Opacity**: Set to 0.8-1.0 for solid appearance
4. **Volume Rendering**: Enable with lighting
5. **Material Properties**: High shininess (0.7-1.0) for metallic look

### Combined Visualization

1. **Colormap**: Use `niivue-ct_enhanced`
2. **Window**: Custom or Standard preset
3. **Opacity**: Adjust based on tissue type (0.3-0.8)
4. **Volume Rendering**: Enable with proper lighting
5. **Alpha Blending**: Use gradient alpha values for smooth transitions

## Implementation Details

### Built-in Colormap System

The system now supports built-in NiiVue colormaps as specified in issue #83:

```python
BUILTIN_NIIVUE_COLORMAPS = {
    'gray': {'__builtin__': True},
    'jet': {'__builtin__': True},
    'hot': {'__builtin__': True},
    # ... other built-in colormaps
}
```

### Alpha Blending Improvements

Enhanced alpha blending for realistic tissue visualization:
- Proper intensity-to-alpha mapping
- Smooth transitions between tissue types
- Configurable transparency levels

### Volume Rendering Enhancements

- 3D volume rendering capabilities
- Lighting and material properties
- Configurable opacity and gamma
- Support for multiple rendering modes

## Usage Examples

### Basic CT Visualization

```python
# Load enhanced CT colormap
colormap_data = load_colormap_data('niivue-ct_enhanced')

# Apply CT windowing
window_center, window_width = get_optimal_window_settings(min_val, max_val, mean_val)

# Set volume properties
volume.opacity = 0.6
volume.cal_min = window_center - window_width / 2
volume.cal_max = window_center + window_width / 2
```

### Advanced 3D Rendering

```javascript
// Enable volume rendering
nv.setSliceType(4); // 3D Render mode

// Configure lighting and materials
nv.setVolumeRenderOpacity(0.8);
nv.setVolumeRenderGamma(1.0);
nv.setLightingEnabled(true);
nv.setMaterialShininess(0.7);
```

## Performance Considerations

- Use appropriate window presets for optimal performance
- Adjust opacity levels based on hardware capabilities
- Enable volume rendering only when needed
- Use built-in colormaps when possible for better performance

## Future Enhancements

- Real-time colormap editing
- Advanced lighting models
- Multi-volume rendering
- GPU-accelerated rendering
- Custom material properties

## References

- [NiiVue Issue #83](https://github.com/niivue/niivue/issues/83): Standardized colormap format
- NiiVue Documentation: Volume rendering and colormap specifications
- Medical imaging standards: DICOM and NIfTI format specifications
