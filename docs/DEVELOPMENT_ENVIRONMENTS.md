# Development Environment with UV

Simple guide for using a unified virtual environment for the complete Vista3D platform.

## Unified Environment

- **Single Environment**: All dependencies (frontend and backend) in one virtual environment
- **Complete Platform**: Includes both Streamlit frontend and PyTorch backend capabilities
- **Simplified Management**: One environment to manage all development needs

## Quick Setup

### 1. Create Unified Environment
```bash
# Create and activate unified environment
uv venv .venv
source .venv/bin/activate

# Install all dependencies (frontend + backend)
uv sync

# Deactivate when done
deactivate
```

## Daily Development

### Frontend Development (Streamlit + Image Server)
```bash
# Activate unified environment
source .venv/bin/activate

# Run Streamlit app
streamlit run app.py

# Run image server (in another terminal)
source .venv/bin/activate
python utils/image_server.py

# Deactivate when done
deactivate
```

### Backend Development (Vista3D + AI Processing)
```bash
# Activate unified environment
source .venv/bin/activate

# Run Vista3D server
python start_backend.py

# Run segmentation processing
python utils/segment.py

# Deactivate when done
deactivate
```

### Full Stack Development
```bash
# Terminal 1: Backend
source .venv/bin/activate
python start_backend.py

# Terminal 2: Frontend
source .venv/bin/activate
streamlit run app.py
```

## Environment Management

### Check Current Environment
```bash
# See which environment is active
echo $VIRTUAL_ENV

# List installed packages
uv pip list
```

### Update Dependencies
```bash
# Update all dependencies
source .venv/bin/activate
uv sync

# Update specific packages
uv pip install --upgrade streamlit fastapi pandas plotly torch
```

## What's in the Unified Environment

### Complete Platform (.venv)
- ✅ Streamlit, FastAPI, Uvicorn
- ✅ Medical imaging: nibabel, dcm2niix
- ✅ 3D visualization: vtk, trimesh, open3d
- ✅ Medical imaging libraries
- ✅ PyTorch (deep learning)
- ✅ Triton (GPU kernels, Linux only)

## Benefits

1. **Simplified Management**: Single environment to maintain
2. **Complete Functionality**: All features available everywhere
3. **Consistent Development**: Same dependencies across all components
4. **Easier Onboarding**: One setup process for new developers
5. **Unified Testing**: Test everything in the same environment

## Troubleshooting

### Environment Not Found
```bash
# Recreate environment
rm -rf .venv
uv venv .venv
source .venv/bin/activate
uv sync
```

### Wrong Dependencies
```bash
# Check what's installed
uv pip list | grep -E "(torch|triton)"

# Should show: torch, (triton on Linux only)
```

### Memory Issues
```bash
# Environment is large (~2GB+) due to ML dependencies
# Consider using Docker for production deployments
# Development environment includes everything for convenience
```

## File Structure

```
HPE-Nvidia-Vista-3D/
├── .venv/                   # Unified virtual environment
├── pyproject.toml           # Unified dependencies
└── ...
```

## Summary

- **Development**: `source .venv/bin/activate` → `streamlit run app.py` or `python start_backend.py`
- **Deactivate**: `deactivate`

That's it! Simple, clean, and effective.