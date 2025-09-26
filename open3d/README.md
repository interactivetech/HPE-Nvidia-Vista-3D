# Vista3D Open3D Service

Advanced 3D visualization and processing service for Vista3D using Open3D.

## Features

- **3D Mesh Visualization**: Advanced PLY file viewing with Open3D
- **Point Cloud Processing**: Interactive point cloud analysis and filtering
- **3D Printing Preparation**: Mesh repair, scaling, and optimization for 3D printing
- **Multiple Format Support**: Import/export PLY, STL, OBJ, OFF, XYZ formats
- **Mesh Analysis**: Quality analysis, statistics, and repair tools
- **Color Support**: Vertex color visualization and analysis

## Quick Start

### Using Docker Compose (Recommended)

```bash
cd open3d
docker-compose up
```

The service will be available at `http://localhost:8502`

### Using Docker directly

```bash
cd open3d
docker build -t vista3d-open3d .
docker run -p 8502:8502 vista3d-open3d
```

### Local Development

```bash
cd open3d
uv sync
uv run streamlit run Open3d_Viewer.py --server.port=8502
```

## Dependencies

- **Open3D**: Advanced 3D processing and visualization
- **Streamlit**: Web interface
- **Plotly**: Interactive 3D plotting
- **Trimesh**: Mesh processing and format conversion
- **NumPy/SciPy**: Numerical computing
- **Pandas**: Data analysis and display

## Architecture

This service is designed to run independently from the main Vista3D frontend, providing:

- **Isolation**: Open3D dependencies don't affect the main frontend
- **Performance**: Dedicated resources for 3D processing
- **Scalability**: Can be scaled independently
- **Maintenance**: Easier to update Open3D-specific features

## Integration

The service integrates with the main Vista3D system through:

- **Image Server**: Accesses PLY files from the shared output directory
- **Data Manager**: Uses the same data management utilities
- **Environment Variables**: Configured through Docker environment

## Environment Variables

- `IMAGE_SERVER`: URL of the Vista3D image server (default: http://image-server:8888)
- `EXTERNAL_IMAGE_SERVER`: External URL for image server (default: http://localhost:8888)
- `OUTPUT_FOLDER`: Path to the shared output directory
- `STREAMLIT_SERVER_PORT`: Port for the Streamlit server (default: 8502)

## API

The service provides a Streamlit web interface with the following main features:

1. **Patient/CT Scan Selection**: Browse available medical imaging data
2. **PLY File Selection**: Choose single or multiple PLY files for visualization
3. **3D Visualization**: Interactive 3D rendering with multiple view modes
4. **Mesh Analysis**: Detailed mesh statistics and quality analysis
5. **3D Printing Tools**: Prepare meshes for 3D printing
6. **Export Options**: Download processed meshes in various formats

## Troubleshooting

### OpenGL Issues

If you encounter OpenGL-related errors in Docker:

1. Ensure the container has access to OpenGL libraries
2. Use the provided Dockerfile which includes necessary OpenGL dependencies
3. For headless environments, the service will gracefully fall back to alternative visualization methods

### Performance Issues

For large meshes:

1. Use the point cloud view mode for better performance
2. Adjust the point sample ratio to reduce the number of displayed points
3. Enable mesh optimization for complex geometries

## Development

To contribute to this service:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with `uv run streamlit run Open3d_Viewer.py`
5. Submit a pull request

## License

This project is part of the Vista3D system and follows the same licensing terms.
