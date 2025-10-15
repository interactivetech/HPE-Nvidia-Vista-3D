# OBJ Analyzer Utility

A comprehensive utility for analyzing `.obj` 3D mesh files, providing detailed statistics, quality metrics, and structural information.

## Features

The OBJ Analyzer provides a complete analysis of 3D mesh files, including:

### File Information
- File size and path
- Last modification date

### Geometry Analysis
- Vertex, face, and edge counts
- Presence of normals, colors, and UV coordinates

### Bounding Box Information
- Dimensions (X, Y, Z)
- Center point
- Min/max coordinates
- Bounding box volume

### Quality Metrics
- **Watertight check** - determines if mesh has holes
- **Winding consistency** - checks if face normals are consistent
- **Surface area** calculation
- **Volume** calculation (for watertight meshes)
- **Euler number** - topological property
- **Scale** - characteristic dimension

### Edge Statistics
- Edge count
- Min/max/mean/median edge lengths
- Standard deviation of edge lengths

### Face Statistics
- Triangle count
- Degenerate face detection
- Face angle distribution (min/max/mean)
- Face area statistics

### Connectivity Analysis
- Number of connected components
- Per-component statistics (vertices, faces, watertight status)
- Single body detection

### Vertex Statistics
- Min/max/mean coordinates
- Standard deviation of coordinates

### Visual Properties
- Vertex color information
- UV coordinate detection
- Material detection
- Color palette extraction

### Mesh Issues Detection
- Identifies common mesh problems:
  - Non-watertight meshes
  - Inconsistent winding
  - Degenerate faces
  - Duplicate vertices
  - Duplicate faces
  - Unreferenced vertices

## Installation

Required dependencies:
```bash
pip install trimesh numpy
```

Optional for advanced clustering:
```bash
pip install scikit-learn
```

## Usage

### Command Line

#### Basic analysis
```bash
python obj_analyzer.py model.obj
```

#### Verbose output with progress messages
```bash
python obj_analyzer.py model.obj --verbose
```

#### Detailed output with component information
```bash
python obj_analyzer.py model.obj --detailed
```

#### Export analysis to JSON
```bash
python obj_analyzer.py model.obj --json analysis.json
```

#### JSON export only (no console output)
```bash
python obj_analyzer.py model.obj --json analysis.json --json-only
```

### Python Code

#### Basic usage
```python
from utils.obj_analyzer import analyze_obj_file, print_analysis

# Analyze a file
analysis = analyze_obj_file("model.obj")

# Print formatted report
print_analysis(analysis)
```

#### Programmatic access
```python
from utils.obj_analyzer import analyze_obj_file

analysis = analyze_obj_file("model.obj")

if analysis['success']:
    # Access specific data
    vertex_count = analysis['geometry']['vertex_count']
    face_count = analysis['geometry']['face_count']
    is_watertight = analysis['quality_metrics']['is_watertight']
    surface_area = analysis['quality_metrics']['surface_area']
    
    print(f"Vertices: {vertex_count:,}")
    print(f"Faces: {face_count:,}")
    print(f"Watertight: {is_watertight}")
    print(f"Surface Area: {surface_area:.2f}")
    
    # Check for issues
    if analysis['mesh_issues']['has_issues']:
        for issue in analysis['mesh_issues']['issues']:
            print(f"Issue: {issue}")
```

#### Batch analysis
```python
from pathlib import Path
from utils.obj_analyzer import analyze_obj_file

# Get all OBJ files in a directory
obj_files = Path("obj_directory").glob("*.obj")

results = []
for obj_file in obj_files:
    analysis = analyze_obj_file(str(obj_file))
    
    if analysis['success']:
        results.append({
            'name': obj_file.name,
            'vertices': analysis['geometry']['vertex_count'],
            'faces': analysis['geometry']['face_count'],
            'watertight': analysis['quality_metrics']['is_watertight'],
        })

# Process results...
```

#### Export to JSON
```python
from utils.obj_analyzer import analyze_obj_file, export_analysis_json

analysis = analyze_obj_file("model.obj")
export_analysis_json(analysis, "analysis.json")
```

## Output Format

### Console Output

The console output is formatted into sections:

```
======================================================================
OBJ FILE ANALYSIS REPORT
======================================================================

📄 FILE INFORMATION
----------------------------------------------------------------------
  File Name:        model.obj
  File Size:        5.2 MB
  ...

📐 GEOMETRY
----------------------------------------------------------------------
  Vertices:         10,000
  Faces:            20,000
  ...

✨ QUALITY METRICS
----------------------------------------------------------------------
  Watertight:       ✓ Yes
  Surface Area:     1234.56
  ...

⚠️  MESH ISSUES
----------------------------------------------------------------------
  ✓ No critical issues found
```

### JSON Output

The JSON output contains a complete structured representation of all analysis data:

```json
{
  "success": true,
  "timestamp": "2025-10-12T09:00:00",
  "file_info": {
    "file_path": "/path/to/model.obj",
    "file_name": "model.obj",
    "file_size_bytes": 5242880,
    "file_size_mb": 5.0
  },
  "geometry": {
    "vertex_count": 10000,
    "face_count": 20000,
    "edge_count": 30000
  },
  "quality_metrics": {
    "is_watertight": true,
    "surface_area": 1234.56,
    "volume": 5678.90
  },
  ...
}
```

## Analysis Dictionary Structure

When using programmatically, the analysis dictionary contains:

- `success` (bool) - Whether analysis succeeded
- `timestamp` (str) - ISO format timestamp
- `file_info` (dict) - File metadata
- `raw_obj_data` (dict) - Raw OBJ file element counts
- `geometry` (dict) - Basic geometry information
- `bounding_box` (dict) - Bounding box data
- `quality_metrics` (dict) - Mesh quality assessments
- `edge_statistics` (dict) - Edge analysis
- `face_statistics` (dict) - Face analysis
- `vertex_statistics` (dict) - Vertex analysis
- `connectivity` (dict) - Connected component analysis
- `visual_properties` (dict) - Color and material info
- `mesh_issues` (dict) - Detected problems and warnings

## Examples

See `obj_analyzer_example.py` for complete working examples:

1. Basic analysis
2. Programmatic access
3. Batch analysis
4. JSON export

Run examples:
```bash
python obj_analyzer_example.py
```

## Use Cases

### Quality Assurance
Check mesh quality before using in production:
```bash
python obj_analyzer.py mesh.obj --detailed
```

### Batch Processing
Analyze all meshes in a directory:
```python
from pathlib import Path
from utils.obj_analyzer import analyze_obj_file

for obj_file in Path("meshes").glob("*.obj"):
    analysis = analyze_obj_file(str(obj_file))
    if not analysis['quality_metrics']['is_watertight']:
        print(f"Warning: {obj_file.name} is not watertight")
```

### Data Collection
Export analysis data for statistical analysis:
```bash
for f in *.obj; do
    python obj_analyzer.py "$f" --json "${f%.obj}.json"
done
```

### Pipeline Integration
Integrate into processing pipelines:
```python
from utils.obj_analyzer import analyze_obj_file

def process_mesh(obj_path):
    analysis = analyze_obj_file(obj_path)
    
    if not analysis['success']:
        raise ValueError(f"Failed to analyze {obj_path}")
    
    # Check quality requirements
    if not analysis['quality_metrics']['is_watertight']:
        print(f"Warning: Mesh is not watertight")
    
    if analysis['mesh_issues']['has_issues']:
        print(f"Issues detected: {analysis['mesh_issues']['issues']}")
    
    # Use analysis data for further processing...
    return analysis
```

## Notes

- The analyzer uses `trimesh` for mesh processing
- Large meshes may take time to analyze
- Non-watertight meshes cannot have volume calculated
- Edge statistics use Euclidean distance
- Color analysis includes vertex colors only (not texture maps)

## Related Files

- `obj_analyzer.py` - Main analyzer script
- `obj_analyzer_example.py` - Usage examples
- `OBJ_Viewer.py` - 3D viewer for OBJ files

