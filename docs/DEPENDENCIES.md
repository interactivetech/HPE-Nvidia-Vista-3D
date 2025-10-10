# Vista3D Dependency Structure

This project uses a unified dependency configuration for simplified management and development.

## Dependency File

### `pyproject.toml`
**Used by**: All containers and development environment
**Purpose**: Complete platform dependencies for both frontend and backend
**Key dependencies**:
- `streamlit`, `fastapi`, `uvicorn` - Web framework
- `nibabel`, `dcm2niix` - Medical imaging
- `torch` - AI/ML framework (includes Triton)
- `vtk`, `trimesh` - 3D visualization
- `pandas`, `plotly` - Data handling and visualization

**Includes**: All dependencies for complete Vista3D platform functionality

## Docker Configuration

### Unified Container (`Dockerfile`)
- Uses `pyproject.toml` (unified configuration)
- Includes all dependencies for complete platform
- Suitable for both frontend and backend functionality

### Backend Container (`Dockerfile.backend`)
- Uses `pyproject.toml` (unified configuration)
- Includes full AI/ML stack
- Optimized for Vista3D server processing

## Benefits

1. **Simplified management**: Single dependency file
2. **Consistent environment**: Same dependencies everywhere
3. **Easier development**: One environment to manage
4. **Complete functionality**: All features available in all containers

## Usage

### Development Environment
```bash
# Activate unified environment
source .venv/bin/activate

# Install all dependencies
uv sync

# Start frontend & image server
cd frontend
docker compose up -d

# Start backend
cd backend
docker compose up -d
```

### Docker Builds
```bash
# Main container (frontend + image server)
docker build -f Dockerfile -t vista3d-app .

# Backend container  
docker build -f Dockerfile.backend -t vista3d-backend .
```

## Migration Notes

- Consolidated from separate frontend/backend dependency files
- All existing scripts continue to work unchanged
- Docker Compose automatically uses the correct Dockerfile
- No changes needed to application code
