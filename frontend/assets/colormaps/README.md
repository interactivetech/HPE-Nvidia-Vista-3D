# Medical Imaging Colormaps

This directory contains specialized colormaps optimized for different anatomical structures in medical imaging (CT and MRI scans).

## Vessel Visualization

### `vessels.json`
- **Purpose**: Basic red-based colormap for vessel visualization
- **Use Cases**: General blood vessel highlighting in CT and MRI
- **Color Scheme**: Black to bright red

### `vessels_enhanced.json`
- **Purpose**: Enhanced red-to-yellow colormap for detailed vessel visualization
- **Use Cases**: High-contrast vessel analysis, detailed vascular studies
- **Color Scheme**: Black to red to yellow

### `arteries.json`
- **Purpose**: Bright red colormap specifically for arterial structures
- **Use Cases**: CT angiography, arterial analysis
- **Color Scheme**: Black to bright red

### `veins.json`
- **Purpose**: Blue-to-purple colormap for venous structures
- **Use Cases**: Venous analysis, contrast-enhanced studies
- **Color Scheme**: Black to blue to purple

## Bone and Skeletal Visualization

### `bones.json`
- **Purpose**: White-to-yellow colormap for bone structures
- **Use Cases**: CT bone analysis, skeletal studies
- **Color Scheme**: Black to white to yellow

### `skeleton.json`
- **Purpose**: High contrast white colormap for skeletal system
- **Use Cases**: Detailed bone analysis, orthopedic studies
- **Color Scheme**: Black to bright white

## Soft Tissue and Muscle Visualization

### `soft_tissue.json`
- **Purpose**: Blue-to-cyan colormap for soft tissues
- **Use Cases**: General soft tissue analysis in CT and MRI
- **Color Scheme**: Black to blue to cyan

### `muscles.json`
- **Purpose**: Pink-to-red colormap for muscle tissue
- **Use Cases**: Muscle analysis, musculoskeletal studies
- **Color Scheme**: Black to pink to red

### `cardiac_tissue.json`
- **Purpose**: Red-to-pink colormap for cardiac muscle
- **Use Cases**: Heart imaging, cardiac analysis
- **Color Scheme**: Black to red to pink

## Organ-Specific Colormaps

### `organs.json`
- **Purpose**: Green-to-yellow colormap for organ visualization
- **Use Cases**: General organ analysis in CT and MRI
- **Color Scheme**: Black to green to yellow

### `brain_tissue.json`
- **Purpose**: Purple-to-pink colormap for brain tissue
- **Use Cases**: Brain MRI analysis, neurological studies
- **Color Scheme**: Black to purple to pink

### `lung_tissue.json`
- **Purpose**: Cyan-to-white colormap for lung tissue
- **Use Cases**: Chest CT analysis, pulmonary studies
- **Color Scheme**: Black to cyan to white

### `liver_tissue.json`
- **Purpose**: Brown-to-yellow colormap for liver tissue
- **Use Cases**: Abdominal CT/MRI, hepatic analysis
- **Color Scheme**: Black to brown to yellow

### `kidney_tissue.json`
- **Purpose**: Green-to-cyan colormap for kidney tissue
- **Use Cases**: Renal analysis, abdominal imaging
- **Color Scheme**: Black to green to cyan

## Specialized Imaging

### `contrast_enhanced.json`
- **Purpose**: Multi-color colormap for contrast-enhanced studies
- **Use Cases**: Contrast-enhanced CT and MRI
- **Color Scheme**: Black to blue to cyan to white

### `ct_angiography.json`
- **Purpose**: High contrast red-to-white for CT angiography
- **Use Cases**: CT angiography studies, vascular imaging
- **Color Scheme**: Black to red to white

## Usage Notes

- All colormaps are designed to work with both CT and MRI scans
- Colormaps use automatic intensity mapping (min: 0, max: 0)
- Alpha values are optimized for medical imaging visualization
- Each colormap has 16 color stops for smooth gradients
- Colormaps are automatically loaded by the Vista3D system

## Integration

These colormaps are automatically integrated into the Vista3D viewer and can be selected from the colormap dropdown in the interface. The system will automatically detect and load these colormaps when the application starts.
