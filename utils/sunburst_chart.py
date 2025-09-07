#!/usr/bin/env python3
"""
Script to generate D3.js Sunburst chart data from image server analysis.
Creates a beautiful hierarchical visualization showing the relationship between patients, CT scans, and voxel data.

Usage:
    python utils/sunburst_chart.py
    python utils/sunburst_chart.py --url https://localhost:8888
    python utils/sunburst_chart.py --output sunburst_data.json
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import argparse
from collections import defaultdict

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

def run_server_analysis() -> Tuple[Optional[Dict], Optional[str]]:
    """Run the server analysis script and return parsed data."""
    try:
        # Run the analysis script
        result = subprocess.run([
            'python3', 'utils/analyze_server_data.py', '--quiet'
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        
        if result.returncode != 0:
            return None, f"Error running analysis: {result.stderr}"
        
        # Parse the output to extract key statistics
        output_lines = result.stdout.split('\n')
        
        # Extract summary statistics
        stats = {}
        for line in output_lines:
            if "Total Patients Found:" in line:
                stats['total_patients'] = int(line.split(":")[1].strip())
            elif "Total CT Scans:" in line:
                stats['total_ct_scans'] = int(line.split(":")[1].strip())
            elif "Patients with CT Scans:" in line:
                stats['patients_with_ct'] = int(line.split(":")[1].strip())
            elif "Patients with Voxel Data:" in line:
                stats['patients_with_voxels'] = int(line.split(":")[1].strip())
        
        # Extract patient details
        patients = []
        current_patient = None
        
        for line in output_lines:
            if "Patient ID:" in line:
                if current_patient:
                    patients.append(current_patient)
                current_patient = {
                    'id': line.split(":")[1].strip(),
                    'ct_scans': 0,
                    'voxel_files': 0,
                    'scans': []
                }
            elif "CT Scans:" in line and current_patient:
                current_patient['ct_scans'] = int(line.split(":")[1].strip())
            elif "Voxel Files:" in line and current_patient:
                current_patient['voxel_files'] = int(line.split(":")[1].strip())
            elif "✅" in line and current_patient and "(" in line:
                # Parse scan details like "✅ 2.5_mm_STD_-_30%_ASIR_2 (segmentation file, 84 voxels)"
                scan_line = line.strip()
                if "✅" in scan_line:
                    # Extract scan name and voxel count
                    parts = scan_line.split("(")
                    if len(parts) >= 2:
                        scan_name = parts[0].replace("✅", "").strip()
                        voxel_info = parts[1].replace(")", "").strip()
                        voxel_count = 0
                        if "voxels" in voxel_info:
                            try:
                                voxel_count = int(voxel_info.split("voxels")[0].split()[-1])
                            except:
                                pass
                        current_patient['scans'].append({
                            'name': scan_name,
                            'voxel_count': voxel_count
                        })
        
        if current_patient:
            patients.append(current_patient)
        
        return {'stats': stats, 'patients': patients}, None
        
    except Exception as e:
        return None, f"Error: {str(e)}"

def categorize_scan_type(scan_name: str) -> str:
    """Categorize scan based on filename patterns."""
    scan_lower = scan_name.lower()
    
    if 'arterial' in scan_lower:
        return 'Arterial Scans'
    elif 'venous' in scan_lower:
        return 'Venous Scans'
    elif 'std' in scan_lower:
        return 'Standard Scans'
    elif '1.25' in scan_name or '1_25' in scan_name:
        return 'High Resolution (1.25mm)'
    elif '2.5' in scan_name or '2_5' in scan_name:
        return 'Standard Resolution (2.5mm)'
    elif 'asir' in scan_lower:
        return 'ASIR Enhanced'
    else:
        return 'Other Scans'

def categorize_voxel_data(voxel_count: int) -> str:
    """Categorize voxel data based on count."""
    if voxel_count == 0:
        return 'No Voxel Data'
    elif voxel_count < 10:
        return 'Low Voxel Count'
    elif voxel_count < 50:
        return 'Medium Voxel Count'
    else:
        return 'High Voxel Count'

def generate_sunburst_data(analysis_data: Dict) -> Dict[str, Any]:
    """Generate Sunburst chart data from analysis results."""
    stats = analysis_data['stats']
    patients = analysis_data['patients']
    
    # Create hierarchical data structure for sunburst
    root = {
        "name": "Medical Imaging Data",
        "children": [],
        "value": 0,
        "color": "#1f77b4"
    }
    
    # Group patients by scan types
    scan_type_groups = defaultdict(list)
    for patient in patients:
        for scan in patient['scans']:
            scan_type = categorize_scan_type(scan['name'])
            scan_type_groups[scan_type].append({
                'patient_id': patient['id'],
                'scan_name': scan['name'],
                'voxel_count': scan['voxel_count']
            })
    
    # Create scan type nodes
    for scan_type, scans in scan_type_groups.items():
        scan_type_node = {
            "name": scan_type,
            "children": [],
            "value": len(scans),
            "color": "#ff7f0e"
        }
        
        # Group scans by voxel data categories
        voxel_groups = defaultdict(list)
        for scan in scans:
            voxel_cat = categorize_voxel_data(scan['voxel_count'])
            voxel_groups[voxel_cat].append(scan)
        
        # Create voxel data nodes
        for voxel_cat, voxel_scans in voxel_groups.items():
            voxel_node = {
                "name": voxel_cat,
                "children": [],
                "value": len(voxel_scans),
                "color": "#2ca02c"
            }
            
            # Add individual scans as leaf nodes
            for scan in voxel_scans:
                scan_node = {
                    "name": f"{scan['patient_id']}: {scan['scan_name'][:30]}{'...' if len(scan['scan_name']) > 30 else ''}",
                    "value": 1,
                    "color": "#d62728",
                    "patient_id": scan['patient_id'],
                    "scan_name": scan['scan_name'],
                    "voxel_count": scan['voxel_count']
                }
                voxel_node["children"].append(scan_node)
            
            scan_type_node["children"].append(voxel_node)
        
        root["children"].append(scan_type_node)
    
    # Calculate total value
    def calculate_total_value(node):
        if "children" in node:
            node["value"] = sum(calculate_total_value(child) for child in node["children"])
        return node["value"]
    
    root["value"] = calculate_total_value(root)
    
    return {
        "data": root,
        "metadata": {
            "total_patients": stats.get('total_patients', 0),
            "total_ct_scans": stats.get('total_ct_scans', 0),
            "patients_with_voxels": stats.get('patients_with_voxels', 0),
            "total_scans": root["value"],
            "generated_at": str(Path(__file__).stat().st_mtime)
        }
    }

def create_html_template(sunburst_data: Dict[str, Any]) -> str:
    """Create HTML template with D3.js Sunburst chart."""
    
    # Convert data to JSON for JavaScript
    data_json = json.dumps(sunburst_data['data'])
    metadata_json = json.dumps(sunburst_data['metadata'])
    
    html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Medical Imaging Data - Sunburst Chart</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-size: 1.1em;
        }}
        
        .stats {{
            display: flex;
            justify-content: space-around;
            padding: 20px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
        }}
        
        .stat-item {{
            text-align: center;
        }}
        
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #2c3e50;
        }}
        
        .stat-label {{
            color: #6c757d;
            font-size: 0.9em;
            margin-top: 5px;
        }}
        
        .chart-container {{
            padding: 30px;
            position: relative;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        
        .sunburst-chart {{
            width: 600px;
            height: 600px;
        }}
        
        .path {{
            stroke: #fff;
            stroke-width: 2px;
            cursor: pointer;
            transition: opacity 0.3s;
        }}
        
        .path:hover {{
            opacity: 0.8;
        }}
        
        .tooltip {{
            position: absolute;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 10px;
            border-radius: 5px;
            font-size: 12px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.3s;
            max-width: 300px;
            z-index: 1000;
        }}
        
        .legend {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 20px;
            flex-wrap: wrap;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 3px;
        }}
        
        .loading {{
            text-align: center;
            padding: 50px;
            color: #6c757d;
        }}
        
        .breadcrumb {{
            margin-bottom: 20px;
            font-size: 14px;
            color: #666;
        }}
        
        .breadcrumb span {{
            cursor: pointer;
            color: #1e3c72;
            text-decoration: underline;
        }}
        
        .breadcrumb span:hover {{
            color: #2a5298;
        }}
        
        .breadcrumb span:not(:last-child)::after {{
            content: " > ";
            color: #999;
            text-decoration: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🩻 Medical Imaging Data Hierarchy</h1>
            <p>Interactive Sunburst diagram showing the hierarchical structure of patients, CT scans, and voxel data</p>
        </div>
        
        <div class="stats">
            <div class="stat-item">
                <div class="stat-value" id="total-patients">-</div>
                <div class="stat-label">Total Patients</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" id="total-scans">-</div>
                <div class="stat-label">CT Scans</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" id="patients-with-voxels">-</div>
                <div class="stat-label">Patients with Voxel Data</div>
            </div>
        </div>
        
        <div class="chart-container">
            <div class="loading" id="loading">Loading visualization...</div>
            <div class="breadcrumb" id="breadcrumb"></div>
            <svg class="sunburst-chart" id="sunburst-chart"></svg>
            <div class="tooltip" id="tooltip"></div>
        </div>
        
        <div class="legend">
            <div class="legend-item">
                <div class="legend-color" style="background: #1f77b4;"></div>
                <span>Root Level</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #ff7f0e;"></div>
                <span>Scan Types</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #2ca02c;"></div>
                <span>Voxel Data</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #d62728;"></div>
                <span>Individual Scans</span>
            </div>
        </div>
    </div>

    <script>
        // Data from Python
        const data = {data_json};
        const metadata = {metadata_json};
        
        // Update stats
        document.getElementById('total-patients').textContent = metadata.total_patients;
        document.getElementById('total-scans').textContent = metadata.total_ct_scans;
        document.getElementById('patients-with-voxels').textContent = metadata.patients_with_voxels;
        
        // Hide loading
        document.getElementById('loading').style.display = 'none';
        
        // Set up dimensions
        const width = 600;
        const height = 600;
        const radius = Math.min(width, height) / 2 - 10;
        
        // Create SVG
        const svg = d3.select("#sunburst-chart")
            .attr("width", width)
            .attr("height", height);
        
        const g = svg.append("g")
            .attr("transform", `translate(${{width/2}}, ${{height/2}})`);
        
        // Create tooltip
        const tooltip = d3.select("#tooltip");
        const breadcrumb = d3.select("#breadcrumb");
        
        // Create breadcrumb trail
        function updateBreadcrumb(nodeArray) {{
            const trail = nodeArray.map(d => d.data.name).join(" > ");
            breadcrumb.html(`<span>Click to navigate: ${{trail}}</span>`);
        }}
        
        // Create color scale
        const color = d3.scaleOrdinal(d3.schemeCategory10);
        
        // Create partition layout
        const partition = d3.partition()
            .size([2 * Math.PI, radius]);
        
        // Process data
        const root = d3.hierarchy(data)
            .sum(d => d.value)
            .sort((a, b) => b.value - a.value);
        
        partition(root);
        
        // Create arcs
        const arc = d3.arc()
            .startAngle(d => d.x0)
            .endAngle(d => d.x1)
            .innerRadius(d => d.y0)
            .outerRadius(d => d.y1);
        
        // Add arcs to chart
        const arcs = g.selectAll("path")
            .data(root.descendants())
            .join("path")
            .attr("d", arc)
            .attr("fill", d => d.data.color || color(d.depth))
            .attr("opacity", 0.8)
            .on("mouseover", function(event, d) {{
                const percentage = ((d.value / root.value) * 100).toFixed(1);
                let tooltipText = `<strong>${{d.data.name}}</strong><br/>Value: ${{d.value}}<br/>Percentage: ${{percentage}}%`;
                
                if (d.data.patient_id) {{
                    tooltipText += `<br/>Patient: ${{d.data.patient_id}}<br/>Voxels: ${{d.data.voxel_count}}`;
                }}
                
                tooltip
                    .style("opacity", 1)
                    .html(tooltipText)
                    .style("left", (event.pageX + 10) + "px")
                    .style("top", (event.pageY - 10) + "px");
            }})
            .on("mouseout", function() {{
                tooltip.style("opacity", 0);
            }})
            .on("click", function(event, d) {{
                // Zoom into clicked segment
                if (d.children) {{
                    const newRoot = d;
                    const newData = d3.hierarchy(newRoot)
                        .sum(d => d.value)
                        .sort((a, b) => b.value - a.value);
                    
                    partition(newData);
                    
                    // Update arcs
                    arcs.data(newData.descendants())
                        .transition()
                        .duration(750)
                        .attrTween("d", function(d) {{
                            const interpolate = d3.interpolate(this._current, d);
                            this._current = interpolate(0);
                            return function(t) {{
                                return arc(interpolate(t));
                            }};
                        }});
                    
                    // Update breadcrumb
                    updateBreadcrumb([newRoot]);
                }}
            }});
        
        // Add labels
        const labels = g.selectAll("text")
            .data(root.descendants().filter(d => d.y0 > 20 && (d.y1 - d.y0) > 10))
            .join("text")
            .attr("transform", d => {{
                const x = (d.x0 + d.x1) / 2 * 180 / Math.PI;
                const y = (d.y0 + d.y1) / 2;
                return `rotate(${{x - 90}}) translate(${{y}},0) rotate(${{x < 180 ? 0 : 180}})`;
            }})
            .attr("text-anchor", "middle")
            .attr("font-size", "12px")
            .attr("fill", "white")
            .text(d => d.data.name.length > 15 ? d.data.name.substring(0, 15) + "..." : d.data.name);
        
        // Add animation
        arcs
            .style("opacity", 0)
            .transition()
            .duration(1000)
            .style("opacity", 0.8);
        
        // Initialize breadcrumb
        updateBreadcrumb([root]);
        
        // Add reset button
        const resetButton = d3.select(".chart-container")
            .append("button")
            .text("Reset View")
            .style("margin-top", "10px")
            .style("padding", "8px 16px")
            .style("background", "#1e3c72")
            .style("color", "white")
            .style("border", "none")
            .style("border-radius", "4px")
            .style("cursor", "pointer")
            .on("click", function() {{
                // Reset to original view
                const newData = d3.hierarchy(data)
                    .sum(d => d.value)
                    .sort((a, b) => b.value - a.value);
                
                partition(newData);
                
                arcs.data(newData.descendants())
                    .transition()
                    .duration(750)
                    .attrTween("d", function(d) {{
                        const interpolate = d3.interpolate(this._current, d);
                        this._current = interpolate(0);
                        return function(t) {{
                            return arc(interpolate(t));
                        }};
                    }});
                
                updateBreadcrumb([newData]);
            }});
    </script>
</body>
</html>
"""
    return html_template

def main():
    """Main function to generate Sunburst chart data and HTML."""
    parser = argparse.ArgumentParser(description="Generate D3.js Sunburst chart for medical imaging data")
    parser.add_argument("--url", help="Override IMAGE_SERVER URL from environment")
    parser.add_argument("--output", "-o", help="Save Sunburst data to JSON file")
    parser.add_argument("--html", help="Save HTML visualization to file")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress progress output")
    
    args = parser.parse_args()
    
    if not args.quiet:
        print("🩻 Medical Imaging Data Hierarchy - Sunburst Chart Generator")
        print("=" * 70)
    
    # Run server analysis
    if not args.quiet:
        print("📊 Analyzing image server data...")
    
    analysis_data, error = run_server_analysis()
    
    if error:
        print(f"❌ Error: {error}")
        sys.exit(1)
    
    if not analysis_data:
        print("❌ No analysis data available")
        sys.exit(1)
    
    # Generate Sunburst data
    if not args.quiet:
        print("🎨 Generating Sunburst chart data...")
    
    sunburst_data = generate_sunburst_data(analysis_data)
    
    # Save JSON data if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(sunburst_data, f, indent=2)
        if not args.quiet:
            print(f"💾 Sunburst data saved to: {args.output}")
    
    # Generate and save HTML if requested
    if args.html:
        html_content = create_html_template(sunburst_data)
        with open(args.html, 'w') as f:
            f.write(html_content)
        if not args.quiet:
            print(f"🌐 HTML visualization saved to: {args.html}")
    
    # Print summary
    if not args.quiet:
        print(f"\n📈 Sunburst Chart Summary:")
        print(f"   • Total Scans: {sunburst_data['metadata']['total_scans']}")
        print(f"   • Patients: {sunburst_data['metadata']['total_patients']}")
        print(f"   • CT Scans: {sunburst_data['metadata']['total_ct_scans']}")
        print(f"   • Patients with Voxel Data: {sunburst_data['metadata']['patients_with_voxels']}")
        print("\n✅ Sunburst chart data generated successfully!")

if __name__ == "__main__":
    main()
