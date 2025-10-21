# Release Notes - Vista3D Helm Chart v1.2.0

**Release Date**: October 10, 2025  
**Chart Version**: 1.2.0  
**App Version**: 1.2.0

## 🎉 Overview

This release introduces enhanced colormap support for medical imaging visualization, providing better tools for CT and MRI analysis with 23+ built-in colormaps.

## ✨ New Features

### Enhanced Colormap Support

The frontend now includes native support for 23 built-in NiiVue colormaps:

#### Scientific Colormaps
- **Standard**: gray, jet, hot, cool, warm
- **Perceptually Uniform**: viridis, plasma, magma, inferno
- **Specialized**: parula, turbo, hsv, bone, copper, cubehelix, cividis

#### Seasonal Colormaps
- spring, summer, autumn, winter

#### Scientific Visualization
- rainbow, linspecer, batlow, blues

### Technical Improvements

1. **Intelligent Colormap Loading**
   - Built-in colormaps are now handled natively by NiiVue
   - No need to load JSON data for standard colormaps
   - Reduced memory footprint and faster loading times

2. **Performance Optimization**
   - Colormap detection happens at load time
   - Built-in colormaps skip unnecessary data transfer
   - Improved caching mechanism

3. **Code Quality**
   - Fixed typo in Chart.yaml (Healthcare maintainer name)
   - Better separation of built-in vs. custom colormaps
   - Cleaner code organization in constants.py

## 📋 What's Changed

### Frontend Changes

**File**: `frontend/utils/constants.py`
- Added `BUILTIN_NIIVUE_COLORMAPS` dictionary with 23 colormap definitions
- Modified `load_colormap_data()` to check for built-ins first
- Improved `load_colormaps()` to include built-in options
- Better error handling and fallback logic

**File**: `frontend/assets/niivue_viewer.html`
- Updated to skip `addColormap` call for built-in colormaps
- Improved colormap initialization logic

### Helm Chart Changes

**Updated Files**:
- `Chart.yaml` - Version bump to 1.2.0, fixed maintainer typo
- `README.md` - Updated version numbers and added "What's New" section
- `NOTES.txt` - Added release highlights
- `CHANGELOG.md` - New file documenting all changes

**New Files**:
- `helm/UPGRADE_GUIDE.md` - Comprehensive upgrade instructions
- `helm/RELEASE_NOTES_v1.2.0.md` - This file

**Enhanced Documentation**:
- `helm/README.md` - Updated architecture section with colormap features

## 🔄 Upgrade Instructions

### Quick Upgrade

```bash
# Pull latest changes
git pull origin main

# Upgrade the Helm release
cd helm/vista3d
helm upgrade vista3d . --namespace vista3d
```

### Detailed Instructions

See [UPGRADE_GUIDE.md](UPGRADE_GUIDE.md) for comprehensive upgrade instructions.

## ✅ Compatibility

- **Kubernetes**: 1.19+
- **Helm**: 3.0+
- **NVIDIA GPU**: Required for backend
- **Backward Compatibility**: ✅ Fully compatible with v1.1.0

## 📦 Container Images

- **Frontend**: `dwtwp/vista3d-frontend:latest` (updated)
- **Backend**: `nvcr.io/nim/nvidia/vista3d:1.0.0` (no changes)
- **Image Server**: `dwtwp/vista3d-image-server:latest` (no changes)

**Note**: Rebuild the frontend image after pulling the latest code to get the colormap improvements.

## 🚀 Getting Started

### New Installation

```bash
# Clone the repository
git clone https://github.com/dw-flyingw/HPE-Nvidia-Vista-3D.git
cd HPE-Nvidia-Vista-3D/helm/vista3d

# Install the chart
helm install vista3d . \
  --namespace vista3d \
  --create-namespace \
  --set secrets.ngcApiKey="your-ngc-api-key"
```

### Using the New Colormaps

1. Access the Vista3D web interface
2. Navigate to the NiiVue Viewer
3. Select a patient and NIfTI file
4. Use the colormap dropdown to choose from:
   - Medical CT colormaps (niivue-ct_*)
   - Scientific colormaps (viridis, plasma, magma)
   - Standard colormaps (gray, jet, hot, cool)
   - Anatomical colormaps (custom medical imaging)
5. Observe the improved visualization options

## 📊 Benefits

### For Radiologists
- Better tissue contrast with specialized CT colormaps
- More intuitive color schemes for different anatomical structures
- Faster colormap switching without loading delays

### For Researchers
- Access to scientifically validated colormaps (viridis, plasma)
- Perceptually uniform color scales for accurate data representation
- Consistent colormap behavior across sessions

### For Developers
- Cleaner code with better separation of concerns
- Easier to add new built-in colormaps in the future
- Improved maintainability of colormap logic

## 🔧 Technical Details

### Architecture Changes

```
Frontend Container:
├── assets/
│   ├── colormaps/          # Custom medical colormaps (JSON)
│   └── niivue_viewer.html  # Updated viewer with built-in support
└── utils/
    └── constants.py        # Added BUILTIN_NIIVUE_COLORMAPS
```

### Colormap Loading Logic

```python
# Old behavior: Always loaded from JSON
colormap_data = load_json(colormap_name)

# New behavior: Check for built-ins first
if colormap_name in BUILTIN_NIIVUE_COLORMAPS:
    return {'__builtin__': True}  # Signal to use native NiiVue colormap
else:
    return load_json(colormap_name)  # Load custom colormap
```

### Viewer HTML Changes

```javascript
// Old: Always called addColormap
nv.addColormap(name, colormap_data)

// New: Skip for built-ins
if (!colormap_data['__builtin__']) {
    nv.addColormap(name, colormap_data)
}
```

## 🐛 Bug Fixes

- Fixed typo in Chart.yaml maintainer field (Helathcare → Healthcare)
- Improved error handling in colormap loading functions
- Better fallback behavior when colormaps are not found

## 📚 Documentation Updates

- Updated Helm chart README with new features
- Added comprehensive CHANGELOG.md
- Created detailed UPGRADE_GUIDE.md
- Enhanced architecture documentation in helm/README.md
- Updated NOTES.txt with release highlights

## 🔍 Testing

All changes have been tested with:
- ✅ Helm lint validation passed
- ✅ Chart structure verified
- ✅ Template rendering validated
- ✅ Backward compatibility confirmed
- ✅ Frontend colormap functionality tested

## 🤝 Contributing

We welcome contributions! If you'd like to add more colormaps or improve the visualization:

1. Fork the repository
2. Create a feature branch
3. Add your colormaps to `frontend/assets/colormaps/`
4. Update the documentation
5. Submit a pull request

## 📞 Support

- **Documentation**: [Main README](../../README.md)
- **Issues**: [GitHub Issues](https://github.com/dw-flyingw/HPE-Nvidia-Vista-3D/issues)
- **Email**: dave.wright@hpe.com

## 🙏 Acknowledgments

- **NiiVue Team**: For the excellent medical imaging viewer
- **HPE Healthcare AI Team**: For platform development
- **NVIDIA**: For Vista3D AI model and NIM platform

## 📄 License

Apache 2.0 License

---

**Previous Version**: [v1.1.0](https://github.com/dw-flyingw/HPE-Nvidia-Vista-3D/releases/tag/v1.1.0)  
**Full Changelog**: See [CHANGELOG.md](vista3d/CHANGELOG.md)

