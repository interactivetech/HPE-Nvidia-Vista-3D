# OBJ Analyzer - Quick Start Guide

## 1-Minute Quick Start

### Analyze a single file
```bash
python utils/obj_analyzer.py path/to/model.obj
```

### Get detailed output
```bash
python utils/obj_analyzer.py path/to/model.obj --detailed
```

### Export to JSON
```bash
python utils/obj_analyzer.py path/to/model.obj --json output.json
```

## From Python

### Simple usage
```python
from utils.obj_analyzer import analyze_obj_file, print_analysis

analysis = analyze_obj_file("model.obj")
print_analysis(analysis)
```

### Get specific info
```python
from utils.obj_analyzer import analyze_obj_file

analysis = analyze_obj_file("model.obj")

print(f"Vertices: {analysis['geometry']['vertex_count']}")
print(f"Faces: {analysis['geometry']['face_count']}")
print(f"Watertight: {analysis['quality_metrics']['is_watertight']}")
print(f"Surface Area: {analysis['quality_metrics']['surface_area']:.2f}")
```

## Common Use Cases

### Check if mesh is watertight
```bash
python utils/obj_analyzer.py model.obj | grep "Watertight"
```

### Check for mesh issues
```bash
python utils/obj_analyzer.py model.obj | grep -A 10 "MESH ISSUES"
```

### Analyze all files in output directory
```bash
for file in /path/to/output/*/obj/*/*.obj; do
    echo "Analyzing: $file"
    python utils/obj_analyzer.py "$file" --json "${file%.obj}_analysis.json"
done
```

### Compare multiple meshes
```python
from pathlib import Path
from utils.obj_analyzer import analyze_obj_file

obj_files = ["heart.obj", "liver.obj", "spleen.obj"]

print(f"{'File':<20} {'Vertices':>12} {'Faces':>12} {'Area':>12}")
print("-" * 60)

for obj_file in obj_files:
    analysis = analyze_obj_file(obj_file)
    if analysis['success']:
        name = analysis['file_info']['file_name']
        verts = analysis['geometry']['vertex_count']
        faces = analysis['geometry']['face_count']
        area = analysis['quality_metrics']['surface_area']
        print(f"{name:<20} {verts:>12,} {faces:>12,} {area:>12.2f}")
```

## Key Analysis Data

The analysis dictionary contains these main sections:

| Section | Description |
|---------|-------------|
| `file_info` | File size, path, modified date |
| `geometry` | Vertex, face, edge counts |
| `bounding_box` | Dimensions, center, min/max |
| `quality_metrics` | Watertight, surface area, volume |
| `edge_statistics` | Edge lengths (min/max/mean) |
| `face_statistics` | Face angles and areas |
| `connectivity` | Connected components |
| `mesh_issues` | Problems and warnings |
| `visual_properties` | Colors, materials, UVs |

## What to Look For

### Good mesh indicators ✓
- `is_watertight`: True
- `is_winding_consistent`: True
- `connected_component_count`: 1
- No degenerate faces
- Reasonable face angle distribution

### Potential issues ⚠️
- `is_watertight`: False (mesh has holes)
- `is_winding_consistent`: False (normals may be flipped)
- `connected_component_count` > 1 (disconnected parts)
- Degenerate faces > 0
- Extreme edge lengths (very small or very large)

## Examples

Run the examples file to see full demonstrations:
```bash
python utils/obj_analyzer_example.py
```

## Help

Full help and options:
```bash
python utils/obj_analyzer.py --help
```

Complete documentation: See `OBJ_ANALYZER_README.md`

