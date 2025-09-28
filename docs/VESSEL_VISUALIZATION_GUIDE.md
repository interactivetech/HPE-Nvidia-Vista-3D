# Vessel Visualization Guide for Vista3D

This guide explains how to create realistic vessel visualizations similar to professional medical imaging software using the Vista3D system.

## Overview

The Vista3D system now includes specialized vessel enhancement capabilities that can transform basic vessel voxels into realistic, high-quality vascular visualizations with:

- **Thick, prominent vessel walls** with realistic thickness
- **Enhanced contrast and visibility** for better vessel definition
- **Realistic texture and surface details** with granular appearance
- **Proper red/blue color coding** for arteries and veins
- **Optimized rendering settings** for medical visualization

## Quick Start

### 1. Apply Vessel Enhancement Effects

Use the specialized vessel enhancement script to process your vessel voxels:

```bash
# Basic vessel enhancement
python frontend/utils/vessel_enhancement.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3

# Enhanced vessel visualization with custom parameters
python frontend/utils/vessel_enhancement.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 \
    --thickness 2.5 --wall-enhancement 2.0 --texture 1.2 --contrast 1.8
```

### 2. Use Realistic Vessel Colormaps

After processing, use the new realistic vessel colormaps in the viewer:

- **`realistic_arteries`** - Red gradient optimized for arterial vessels
- **`realistic_veins`** - Blue gradient optimized for venous vessels  
- **`realistic_vessels_unified`** - Combined red/blue gradient for mixed vessel types

### 3. Apply Vessel-Optimized Rendering

Use the specialized vessel rendering configuration for best results:

```json
{
  "render_quality": "3d_render_vessels"
}
```

## Vessel Enhancement Parameters

### Vessel Thickness (`--thickness`)
- **Range**: 1.0 - 4.0
- **Default**: 2.0
- **Description**: Multiplies vessel wall thickness for more prominent appearance
- **Recommended**: 2.0-3.0 for realistic medical visualization

### Wall Enhancement (`--wall-enhancement`)
- **Range**: 1.0 - 3.0
- **Default**: 1.5
- **Description**: Enhances vessel wall definition and contrast
- **Recommended**: 1.5-2.0 for clear vessel boundaries

### Texture Granularity (`--texture`)
- **Range**: 0.0 - 2.0
- **Default**: 0.8
- **Description**: Adds realistic surface texture and granular details
- **Recommended**: 0.8-1.2 for medical-grade appearance

### Contrast Boost (`--contrast`)
- **Range**: 1.0 - 2.0
- **Default**: 1.3
- **Description**: Enhances vessel contrast against background
- **Recommended**: 1.3-1.8 for optimal visibility

## Advanced Usage

### Using the Voxel Effects Processor Directly

For more control, use the main voxel effects processor:

```bash
python frontend/utils/voxel_effects.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 \
    --effect vessel_enhancement \
    --vessel-thickness 2.5 \
    --wall-enhancement 2.0 \
    --texture-granularity 1.2 \
    --contrast-boost 1.8
```

### Combining with Other Effects

You can combine vessel enhancement with other effects for specialized results:

```bash
# First apply vessel enhancement
python frontend/utils/voxel_effects.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 \
    --effect vessel_enhancement

# Then apply anatomical enhancement for better structure definition
python frontend/utils/voxel_effects.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 \
    --effect anatomical_enhancement
```

## Colormap Selection Guide

### For Arterial Vessels
- **Primary**: `realistic_arteries` - Red gradient with proper transparency
- **Alternative**: `niivue-ct_artery` - Standard arterial colormap

### For Venous Vessels
- **Primary**: `realistic_veins` - Blue gradient with proper transparency
- **Alternative**: `niivue-ct_vessels` - Standard vessel colormap

### For Mixed Vessel Types
- **Primary**: `realistic_vessels_unified` - Combined red/blue gradient
- **Alternative**: `niivue-ct_vessels` - Standard vessel colormap

## Rendering Quality Settings

### Vessel-Optimized Rendering (`3d_render_vessels`)
- **Anti-aliasing**: 12 samples for smooth edges
- **Volume rendering**: 768 steps for high detail
- **Lighting**: Enhanced directional lighting (1.0 intensity)
- **Contrast**: 1.3x boost for better vessel visibility
- **Ambient occlusion**: 0.9 intensity for realistic depth
- **Bloom**: 0.7 intensity for vessel glow effect

### Performance Considerations
- **High-end hardware**: Use `3d_render_vessels` for maximum quality
- **Mid-range hardware**: Use `3d_render_quality` with vessel enhancement
- **Lower-end hardware**: Use `3d_render_balanced` with reduced parameters

## Troubleshooting

### Vessels Appear Too Thin
- Increase `--thickness` parameter (try 2.5-3.0)
- Use `realistic_arteries` or `realistic_veins` colormaps
- Enable vessel-specific rendering settings

### Vessels Lack Detail
- Increase `--texture` parameter (try 1.0-1.5)
- Increase `--wall-enhancement` parameter (try 2.0-2.5)
- Use ultra-quality rendering settings

### Poor Contrast
- Increase `--contrast` parameter (try 1.5-2.0)
- Use vessel-optimized rendering configuration
- Adjust lighting settings in the viewer

### Performance Issues
- Reduce `--thickness` parameter (try 1.5-2.0)
- Use balanced rendering quality settings
- Reduce texture granularity (try 0.5-0.8)

## Best Practices

1. **Start with default parameters** and adjust based on your specific data
2. **Use appropriate colormaps** for vessel type (arteries vs veins)
3. **Enable vessel-optimized rendering** for best visual results
4. **Test different parameter combinations** to find optimal settings
5. **Consider your hardware capabilities** when choosing rendering quality

## Example Workflows

### Medical Education Visualization
```bash
# High-quality vessel enhancement for educational content
python frontend/utils/vessel_enhancement.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 \
    --thickness 2.5 --wall-enhancement 2.0 --texture 1.0 --contrast 1.5
```

### Clinical Analysis
```bash
# Balanced enhancement for clinical analysis
python frontend/utils/vessel_enhancement.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 \
    --thickness 2.0 --wall-enhancement 1.5 --texture 0.8 --contrast 1.3
```

### Real-time Visualization
```bash
# Performance-optimized for real-time viewing
python frontend/utils/vessel_enhancement.py --patient PA00000002 --scan 2.5MM_ARTERIAL_3 \
    --thickness 1.8 --wall-enhancement 1.3 --texture 0.6 --contrast 1.2
```

## Technical Details

The vessel enhancement system uses:

- **Histogram equalization** for improved contrast
- **Morphological dilation** for vessel wall thickness
- **Distance transforms** for realistic wall gradients
- **Edge enhancement** for vessel boundary definition
- **Bilateral filtering** for texture preservation
- **Adaptive smoothing** for surface refinement

This creates vessel visualizations that closely match the quality and appearance of professional medical imaging software.
