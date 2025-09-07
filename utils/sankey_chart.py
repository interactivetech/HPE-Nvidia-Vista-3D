#!/usr/bin/env python3
"""
Script to generate D3.js Sankey chart data from image server analysis.
Creates a beautiful flow diagram showing the relationship between patients, CT scans, and voxel data.

Usage:
    python utils/sankey_chart.py
    python utils/sankey_chart.py --url https://localhost:8888
    python utils/sankey_chart.py --output sankey_data.json
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
        return 'Arterial'
    elif 'venous' in scan_lower:
        return 'Venous'
    elif 'std' in scan_lower:
        return 'Standard'
    elif '1.25' in scan_name or '1_25' in scan_name:
        return 'High Resolution (1.25mm)'
    elif '2.5' in scan_name or '2_5' in scan_name:
        return 'Standard Resolution (2.5mm)'
    elif 'asir' in scan_lower:
        return 'ASIR Enhanced'
    else:
        return 'Other'

def categorize_voxel_type(scan_name: str, voxel_count: int) -> str:
    """Categorize voxel data based on scan and count."""
    if voxel_count == 0:
        return 'No Voxel Data'
    elif voxel_count < 10:
        return 'Low Voxel Count'
    elif voxel_count < 50:
        return 'Medium Voxel Count'
    else:
        return 'High Voxel Count'

def generate_sankey_data(analysis_data: Dict) -> Dict[str, Any]:
    """Generate Sankey chart data from analysis results."""
    stats = analysis_data['stats']
    patients = analysis_data['patients']
    
    # Create nodes for the Sankey diagram
    nodes = []
    node_id_map = {}
    node_counter = 0
    
    # Add patient nodes
    for patient in patients:
        node_id = f"patient_{patient['id']}"
        nodes.append({
            "id": node_id,
            "name": f"Patient {patient['id']}",
            "category": "Patient",
            "value": patient['ct_scans'],
            "color": "#1f77b4"
        })
        node_id_map[node_id] = node_counter
        node_counter += 1
    
    # Add scan type nodes
    scan_types = set()
    for patient in patients:
        for scan in patient['scans']:
            scan_type = categorize_scan_type(scan['name'])
            scan_types.add(scan_type)
    
    for scan_type in scan_types:
        node_id = f"scan_{scan_type.replace(' ', '_').replace('(', '').replace(')', '')}"
        nodes.append({
            "id": node_id,
            "name": scan_type,
            "category": "Scan Type",
            "value": 0,  # Will be calculated from links
            "color": "#ff7f0e"
        })
        node_id_map[node_id] = node_counter
        node_counter += 1
    
    # Add voxel category nodes
    voxel_categories = set()
    for patient in patients:
        for scan in patient['scans']:
            voxel_cat = categorize_voxel_type(scan['name'], scan['voxel_count'])
            voxel_categories.add(voxel_cat)
    
    for voxel_cat in voxel_categories:
        node_id = f"voxel_{voxel_cat.replace(' ', '_').replace('(', '').replace(')', '')}"
        nodes.append({
            "id": node_id,
            "name": voxel_cat,
            "category": "Voxel Data",
            "value": 0,  # Will be calculated from links
            "color": "#2ca02c"
        })
        node_id_map[node_id] = node_counter
        node_counter += 1
    
    # Create links between nodes
    links = []
    
    # Patient to Scan Type links
    patient_scan_counts = defaultdict(int)
    for patient in patients:
        for scan in patient['scans']:
            scan_type = categorize_scan_type(scan['name'])
            patient_scan_counts[(patient['id'], scan_type)] += 1
    
    for (patient_id, scan_type), count in patient_scan_counts.items():
        patient_node_id = f"patient_{patient_id}"
        scan_node_id = f"scan_{scan_type.replace(' ', '_').replace('(', '').replace(')', '')}"
        
        if patient_node_id in node_id_map and scan_node_id in node_id_map:
            links.append({
                "source": node_id_map[patient_node_id],
                "target": node_id_map[scan_node_id],
                "value": count,
                "color": "#888888"
            })
    
    # Scan Type to Voxel Category links
    scan_voxel_counts = defaultdict(int)
    for patient in patients:
        for scan in patient['scans']:
            scan_type = categorize_scan_type(scan['name'])
            voxel_cat = categorize_voxel_type(scan['name'], scan['voxel_count'])
            scan_voxel_counts[(scan_type, voxel_cat)] += 1
    
    for (scan_type, voxel_cat), count in scan_voxel_counts.items():
        scan_node_id = f"scan_{scan_type.replace(' ', '_').replace('(', '').replace(')', '')}"
        voxel_node_id = f"voxel_{voxel_cat.replace(' ', '_').replace('(', '').replace(')', '')}"
        
        if scan_node_id in node_id_map and voxel_node_id in node_id_map:
            links.append({
                "source": node_id_map[scan_node_id],
                "target": node_id_map[voxel_node_id],
                "value": count,
                "color": "#888888"
            })
    
    # Update node values based on incoming/outgoing links
    for link in links:
        source_idx = link['source']
        target_idx = link['target']
        value = link['value']
        
        # Add to target node value
        if target_idx < len(nodes):
            nodes[target_idx]['value'] += value
    
    return {
        "nodes": nodes,
        "links": links,
        "metadata": {
            "total_patients": stats.get('total_patients', 0),
            "total_ct_scans": stats.get('total_ct_scans', 0),
            "patients_with_voxels": stats.get('patients_with_voxels', 0),
            "generated_at": str(Path(__file__).stat().st_mtime)
        }
    }

def create_html_template(sankey_data: Dict[str, Any]) -> str:
    """Create HTML template with D3.js Sankey chart."""
    
    # Convert data to JSON for JavaScript
    nodes_json = json.dumps(sankey_data['nodes'])
    links_json = json.dumps(sankey_data['links'])
    metadata_json = json.dumps(sankey_data['metadata'])
    
    html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Medical Imaging Data Flow - Sankey Diagram</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script src="https://unpkg.com/d3-sankey@0.12.3/dist/d3-sankey.min.js"></script>
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
        }}
        
        .sankey-chart {{
            width: 100%;
            height: 600px;
        }}
        
        .node rect {{
            fill-opacity: 0.9;
            shape-rendering: crispEdges;
            stroke: #fff;
            stroke-width: 2px;
        }}
        
        .node text {{
            font-family: 'Segoe UI', sans-serif;
            font-size: 12px;
            fill: #333;
            text-anchor: middle;
            dominant-baseline: middle;
        }}
        
        .link {{
            fill: none;
            stroke-opacity: 0.6;
            stroke-width: 2px;
        }}
        
        .link:hover {{
            stroke-opacity: 0.8;
            stroke-width: 3px;
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
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🩻 Medical Imaging Data Flow</h1>
            <p>Visualizing the relationship between patients, CT scans, and voxel segmentation data</p>
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
            <svg class="sankey-chart" id="sankey-chart"></svg>
            <div class="tooltip" id="tooltip"></div>
        </div>
        
        <div class="legend">
            <div class="legend-item">
                <div class="legend-color" style="background: #1f77b4;"></div>
                <span>Patients</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #ff7f0e;"></div>
                <span>Scan Types</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #2ca02c;"></div>
                <span>Voxel Data</span>
            </div>
        </div>
    </div>

    <script>
        // Data from Python
        const nodes = {nodes_json};
        const links = {links_json};
        const metadata = {metadata_json};
        
        // Update stats
        document.getElementById('total-patients').textContent = metadata.total_patients;
        document.getElementById('total-scans').textContent = metadata.total_ct_scans;
        document.getElementById('patients-with-voxels').textContent = metadata.patients_with_voxels;
        
        // Hide loading
        document.getElementById('loading').style.display = 'none';
        
        // Create Sankey diagram
        const width = document.getElementById('sankey-chart').clientWidth;
        const height = 600;
        
        const svg = d3.select("#sankey-chart")
            .attr("width", width)
            .attr("height", height);
        
        const sankey = d3.sankey()
            .nodeId(d => d.id)
            .nodeWidth(15)
            .nodePadding(10)
            .extent([[1, 1], [width - 1, height - 1]]);
        
        const result = sankey({{
            nodes: nodes.map(d => ({{...d}})),
            links: links.map(d => ({{...d}}))
        }});
        
        const sankeyNodes = result.nodes;
        const sankeyLinks = result.links;
        
        // Create tooltip
        const tooltip = d3.select("#tooltip");
        
        // Add links
        const link = svg.append("g")
            .selectAll("path")
            .data(sankeyLinks)
            .join("path")
            .attr("class", "link")
            .attr("d", d3.sankeyLinkHorizontal())
            .attr("stroke", d => d.color || "#888888")
            .on("mouseover", function(event, d) {{
                tooltip
                    .style("opacity", 1)
                    .html(`<strong>${{d.source.name}}</strong> → <strong>${{d.target.name}}</strong><br/>Value: ${{d.value}}`)
                    .style("left", (event.pageX + 10) + "px")
                    .style("top", (event.pageY - 10) + "px");
            }})
            .on("mouseout", function() {{
                tooltip.style("opacity", 0);
            }});
        
        // Add nodes
        const node = svg.append("g")
            .selectAll("g")
            .data(sankeyNodes)
            .join("g");
        
        node.append("rect")
            .attr("x", d => d.x0)
            .attr("y", d => d.y0)
            .attr("height", d => d.y1 - d.y0)
            .attr("width", d => d.x1 - d.x0)
            .attr("fill", d => d.color)
            .on("mouseover", function(event, d) {{
                tooltip
                    .style("opacity", 1)
                    .html(`<strong>${{d.name}}</strong><br/>Category: ${{d.category}}<br/>Value: ${{d.value}}`)
                    .style("left", (event.pageX + 10) + "px")
                    .style("top", (event.pageY - 10) + "px");
            }})
            .on("mouseout", function() {{
                tooltip.style("opacity", 0);
            }});
        
        // Add labels
        node.append("text")
            .attr("x", d => d.x0 < width / 2 ? d.x1 + 6 : d.x0 - 6)
            .attr("y", d => (d.y1 + d.y0) / 2)
            .attr("dy", "0.35em")
            .attr("text-anchor", d => d.x0 < width / 2 ? "start" : "end")
            .text(d => d.name)
            .style("font-size", "12px")
            .style("fill", "#333");
        
        // Add animation
        link
            .style("stroke-dasharray", function(d) {{
                const length = this.getTotalLength();
                return length + " " + length;
            }})
            .style("stroke-dashoffset", function(d) {{
                return this.getTotalLength();
            }})
            .transition()
            .duration(2000)
            .ease(d3.easeLinear)
            .style("stroke-dashoffset", 0);
        
        // Responsive behavior
        window.addEventListener('resize', function() {{
            const newWidth = document.getElementById('sankey-chart').clientWidth;
            svg.attr("width", newWidth);
            sankey.extent([[1, 1], [newWidth - 1, height - 1]]);
            // Re-render would go here in a full implementation
        }});
    </script>
</body>
</html>
"""
    return html_template

def main():
    """Main function to generate Sankey chart data and HTML."""
    parser = argparse.ArgumentParser(description="Generate D3.js Sankey chart for medical imaging data")
    parser.add_argument("--url", help="Override IMAGE_SERVER URL from environment")
    parser.add_argument("--output", "-o", help="Save Sankey data to JSON file")
    parser.add_argument("--html", help="Save HTML visualization to file")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress progress output")
    
    args = parser.parse_args()
    
    if not args.quiet:
        print("🩻 Medical Imaging Data Flow - Sankey Chart Generator")
        print("=" * 60)
    
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
    
    # Generate Sankey data
    if not args.quiet:
        print("🎨 Generating Sankey chart data...")
    
    sankey_data = generate_sankey_data(analysis_data)
    
    # Save JSON data if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(sankey_data, f, indent=2)
        if not args.quiet:
            print(f"💾 Sankey data saved to: {args.output}")
    
    # Generate and save HTML if requested
    if args.html:
        html_content = create_html_template(sankey_data)
        with open(args.html, 'w') as f:
            f.write(html_content)
        if not args.quiet:
            print(f"🌐 HTML visualization saved to: {args.html}")
    
    # Print summary
    if not args.quiet:
        print(f"\n📈 Sankey Chart Summary:")
        print(f"   • Nodes: {len(sankey_data['nodes'])}")
        print(f"   • Links: {len(sankey_data['links'])}")
        print(f"   • Patients: {sankey_data['metadata']['total_patients']}")
        print(f"   • CT Scans: {sankey_data['metadata']['total_ct_scans']}")
        print(f"   • Patients with Voxel Data: {sankey_data['metadata']['patients_with_voxels']}")
        print("\n✅ Sankey chart data generated successfully!")

if __name__ == "__main__":
    main()
