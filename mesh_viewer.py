import streamlit as st
import streamlit.components.v1 as components
import os
import json
from typing import List, Dict, Optional
from dotenv import load_dotenv
from pathlib import Path
import sys

# Add utils to path for imports
sys.path.append(str(Path(__file__).parent / 'utils'))

# Import our modules
from utils.config_manager import ConfigManager
from utils.data_manager import DataManager
from utils.constants import IMAGE_EXTENSIONS, SERVER_TIMEOUT

# --- Initial Setup ---
load_dotenv()
IMAGE_SERVER_URL = os.getenv('IMAGE_SERVER', 'http://localhost:8888')

# Initialize our managers
config_manager = ConfigManager()
data_manager = DataManager(IMAGE_SERVER_URL)

# --- Helper Functions ---
def check_image_server_status():
    """Check if the image server is available."""
    try:
        import requests
        response = requests.head(IMAGE_SERVER_URL, timeout=3)
        return True if response.status_code == 200 else False
    except (ImportError, Exception):
        return False

def get_mesh_files_for_patient(patient_id: str) -> List[Dict[str, str]]:
    """Get all mesh files for a specific patient from the image server."""
    mesh_files = []
    
    # Check for mesh files in the current structure: output/{patient_id}/mesh/
    mesh_folder_path = f"{patient_id}/mesh"
    mesh_contents = data_manager.get_folder_contents(mesh_folder_path)
    
    if mesh_contents:
        # Look for subdirectories (CT scan folders) and their STL files
        for item in mesh_contents:
            if item['is_directory']:
                # This is a CT scan subfolder, get its contents
                ct_scan_name = item['name']
                ct_scan_mesh_path = f"{mesh_folder_path}/{ct_scan_name}"
                ct_scan_mesh_contents = data_manager.get_folder_contents(ct_scan_mesh_path)
                
                if ct_scan_mesh_contents:
                    for mesh_item in ct_scan_mesh_contents:
                        if not mesh_item['is_directory'] and mesh_item['name'].endswith('.stl'):
                            mesh_files.append({
                                'name': mesh_item['name'],
                                'ct_scan': ct_scan_name,
                                'path': f"{ct_scan_mesh_path}/{mesh_item['name']}",
                                'url': f"{IMAGE_SERVER_URL}/output/{ct_scan_mesh_path}/{mesh_item['name']}",
                                'size': mesh_item.get('size', 'Unknown'),
                                'size_bytes': mesh_item.get('size_bytes', 0)
                            })
    
    return mesh_files

def get_mesh_files_for_scan(patient_id: str, ct_scan_name: str) -> List[Dict[str, str]]:
    """Get mesh files for a specific CT scan."""
    mesh_files = []
    mesh_folder_path = f"{patient_id}/mesh/{ct_scan_name}"
    mesh_contents = data_manager.get_folder_contents(mesh_folder_path)
    
    if mesh_contents:
        for item in mesh_contents:
            if not item['is_directory'] and item['name'].endswith('.stl'):
                mesh_files.append({
                    'name': item['name'],
                    'ct_scan': ct_scan_name,
                    'path': f"{mesh_folder_path}/{item['name']}",
                    'url': f"{IMAGE_SERVER_URL}/output/{mesh_folder_path}/{item['name']}",
                    'size': item.get('size', 'Unknown'),
                    'size_bytes': item.get('size_bytes', 0)
                })
    
    return mesh_files

def format_file_size(size_bytes: int) -> str:
    """Format file size in bytes to human readable format."""
    if size_bytes == 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    size = float(size_bytes)
    unit_index = 0
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.1f} {units[unit_index]}"

def render_mesh_viewer(mesh_files: List[Dict[str, str]]):
    """Render a 3D mesh viewer for the selected STL files."""
    # Render the 3D viewer with default settings
    render_threejs_viewer(mesh_files, show_wireframe=False, show_axes=True, auto_rotate=False)

def render_threejs_viewer(mesh_files: List[Dict[str, str]], show_wireframe: bool, show_axes: bool, auto_rotate: bool):
    """Render a Three.js-based 3D mesh viewer for multiple STL files."""
    
    # Set background to black
    bg_color = "#000000"
    
    # Create the Three.js viewer HTML
    viewer_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>3D Mesh Viewer</title>
        <style>
            body {{ margin: 0; padding: 0; overflow: hidden; }}
            #container {{ width: 100%; height: 600px; }}
        </style>
    </head>
    <body>
        <div id="container"></div>
        
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/STLLoader.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
        
        <script>
            let scene, camera, renderer, mesh, controls;
            let wireframe, axes;
            
            function init() {{
                // Scene setup
                scene = new THREE.Scene();
                scene.background = new THREE.Color('{bg_color}');
                
                // Camera setup
                camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
                camera.position.set(50, 50, 50);
                
                // Renderer setup
                renderer = new THREE.WebGLRenderer({{ antialias: true }});
                renderer.setSize(window.innerWidth, window.innerHeight);
                renderer.shadowMap.enabled = true;
                renderer.shadowMap.type = THREE.PCFSoftShadowMap;
                
                document.getElementById('container').appendChild(renderer.domElement);
                
                // Controls
                controls = new THREE.OrbitControls(camera, renderer.domElement);
                controls.enableDamping = true;
                controls.dampingFactor = 0.05;
                controls.autoRotate = {str(auto_rotate).lower()};
                controls.autoRotateSpeed = 2.0;
                
                // Lighting
                const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
                scene.add(ambientLight);
                
                const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
                directionalLight.position.set(50, 50, 50);
                directionalLight.castShadow = true;
                scene.add(directionalLight);
                
                // Load STL file
                loadSTL();
                
                // Add axes if requested
                if ({str(show_axes).lower()}) {{
                    axes = new THREE.AxesHelper(20);
                    scene.add(axes);
                }}
                
                // Event listeners
                window.addEventListener('resize', onWindowResize);
                document.addEventListener('keydown', onKeyDown);
                
                // Start render loop
                animate();
            }}
            
            function loadSTL() {{
                const loader = new THREE.STLLoader();
                const meshFiles = {json.dumps([{'url': mf['url'], 'name': mf['name']} for mf in mesh_files])};
                const colors = [0x00ff00, 0xff0000, 0x0000ff, 0xffff00, 0xff00ff, 0x00ffff, 0xffa500, 0x800080];
                let loadedCount = 0;
                const totalFiles = meshFiles.length;
                
                meshFiles.forEach((meshFile, index) => {{
                    loader.load(
                        meshFile.url,
                        function (geometry) {{
                            // Create material with different colors for each mesh
                            const material = new THREE.MeshPhongMaterial({{
                                color: colors[index % colors.length],
                                shininess: 100,
                                side: THREE.DoubleSide
                            }});
                            
                            // Create mesh
                            const currentMesh = new THREE.Mesh(geometry, material);
                            currentMesh.castShadow = true;
                            currentMesh.receiveShadow = true;
                            currentMesh.userData = {{ name: meshFile.name }};
                            
                            // Center the mesh
                            geometry.computeBoundingBox();
                            const center = geometry.boundingBox.getCenter(new THREE.Vector3());
                            currentMesh.position.sub(center);
                            
                            // Scale to reasonable size
                            const size = geometry.boundingBox.getSize(new THREE.Vector3());
                            const maxDim = Math.max(size.x, size.y, size.z);
                            const scale = 20 / maxDim;
                            currentMesh.scale.setScalar(scale);
                            
                            scene.add(currentMesh);
                            
                            // Add wireframe if requested
                            if ({str(show_wireframe).lower()}) {{
                                const wireframeGeometry = geometry.clone();
                                const wireframeMaterial = new THREE.MeshBasicMaterial({{
                                    color: 0x000000,
                                    wireframe: true
                                }});
                                const wireframe = new THREE.Mesh(wireframeGeometry, wireframeMaterial);
                                wireframe.position.copy(currentMesh.position);
                                wireframe.scale.copy(currentMesh.scale);
                                scene.add(wireframe);
                            }}
                            
                            loadedCount++;
                            
                            // When all meshes are loaded, update camera position
                            if (loadedCount === totalFiles) {{
                                // Update camera position to fit all meshes
                                const box = new THREE.Box3();
                                scene.children.forEach(child => {{
                                    if (child.isMesh && child.userData.name) {{
                                        box.expandByObject(child);
                                    }}
                                }});
                                
                                const center2 = box.getCenter(new THREE.Vector3());
                                const size2 = box.getSize(new THREE.Vector3());
                                const maxDim2 = Math.max(size2.x, size2.y, size2.z);
                                
                                camera.position.set(
                                    center2.x + maxDim2,
                                    center2.y + maxDim2,
                                    center2.z + maxDim2
                                );
                                controls.target.copy(center2);
                                controls.update();
                                
                                console.log(`All ${{totalFiles}} STL files loaded successfully`);
                            }}
                        }},
                        function (progress) {{
                            console.log(`Loading ${{meshFile.name}}:`, (progress.loaded / progress.total * 100) + '%');
                        }},
                        function (error) {{
                            console.error(`Error loading STL file ${{meshFile.name}}:`, error);
                        }}
                    );
                }});
            }}
            
            function animate() {{
                requestAnimationFrame(animate);
                controls.update();
                renderer.render(scene, camera);
            }}
            
            function onWindowResize() {{
                camera.aspect = window.innerWidth / window.innerHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(window.innerWidth, window.innerHeight);
            }}
            
            function onKeyDown(event) {{
                if (event.key === 'r' || event.key === 'R') {{
                    // Reset view
                    camera.position.set(50, 50, 50);
                    controls.target.set(0, 0, 0);
                    controls.update();
                }}
            }}
            
            // Initialize when page loads
            window.addEventListener('load', init);
        </script>
    </body>
    </html>
    """
    
    # Display the 3D viewer
    components.html(viewer_html, height=650, scrolling=False)

def render_sidebar():
    """Render the sidebar with patient and mesh selection."""
    with st.sidebar:
        st.header("🔺 Mesh Viewer")
        
        # Check server status
        if not check_image_server_status():
            st.error("❌ Image Server Offline")
            st.info("Start the server with: `python utils/image_server.py`")
            return None, None, None
        
        st.success("✅ Image Server Online")
        
        # Patient selection
        patient_folders = data_manager.get_server_data('', 'folders', ('',))
        if not patient_folders:
            st.warning("No patients found")
            return None, None, None
        
        selected_patient = st.selectbox("Select Patient", patient_folders)
        
        if not selected_patient:
            return None, None, None
        
        # Get mesh files for this patient
        mesh_files = get_mesh_files_for_patient(selected_patient)
        
        if not mesh_files:
            st.warning(f"No mesh files found for patient {selected_patient}")
            return selected_patient, None, None
        
        # Group mesh files by CT scan
        ct_scans = {}
        for mesh_file in mesh_files:
            ct_scan = mesh_file['ct_scan']
            if ct_scan not in ct_scans:
                ct_scans[ct_scan] = []
            ct_scans[ct_scan].append(mesh_file)
        
        # CT Scan selection
        selected_ct_scan = st.selectbox("Select CT Scan", list(ct_scans.keys()))
        
        if not selected_ct_scan:
            return selected_patient, None, None
        
        # Mesh file selection
        scan_mesh_files = ct_scans[selected_ct_scan]
        
        if not scan_mesh_files:
            st.warning("No mesh files available for this CT scan.")
            selected_meshes = []
        else:
            # Create display names for multiselect
            mesh_display_names = [
                f"{mf['name']} ({format_file_size(mf['size_bytes'])})" 
                for mf in scan_mesh_files
            ]
            
            # Show mesh selection interface
            selected_display_names = st.multiselect(
                "Choose meshes to view:",
                mesh_display_names,
                default=[],
                help="Select specific mesh files to display"
            )
            
            # Map back to actual mesh files
            selected_meshes = []
            for display_name in selected_display_names:
                index = mesh_display_names.index(display_name)
                selected_meshes.append(scan_mesh_files[index])
            
            # Display selection status
            if selected_meshes:
                st.info(f"Will display {len(selected_meshes)} mesh files.")
            else:
                st.info("No meshes selected. Select specific files to display.")
        
        
        return selected_patient, selected_ct_scan, selected_meshes


def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="Mesh Viewer - Vista3D",
        page_icon="🔺",
        layout="wide",
    )
    
    st.title("🔺 3D Mesh Viewer")
    st.markdown("Navigate and view STL mesh files from the image server")
    
    # Render sidebar and get selections
    selected_patient, selected_ct_scan, selected_meshes = render_sidebar()
    
    if not selected_patient:
        st.info("Please select a patient to view mesh files")
        return
    
    if not selected_ct_scan:
        st.info("Please select a CT scan to view mesh files")
        return
    
    # Get all mesh files for the selected CT scan
    mesh_files = get_mesh_files_for_scan(selected_patient, selected_ct_scan)
    
    if not mesh_files:
        st.warning(f"No mesh files found for CT scan: {selected_ct_scan}")
        st.info("""
        **Possible reasons:**
        - The CT scan may not have been processed for mesh generation yet
        - Mesh files might be in a different location
        - The image server might not be serving the files correctly
        
        **To check:**
        1. Verify the image server is running
        2. Check if mesh files exist in the expected directory structure
        3. Look for STL files in `output/{patient_id}/mesh/{ct_scan_name}/`
        """)
        return
    
    # Main content area - show selected meshes in single viewer
    if selected_meshes:
        render_mesh_viewer(selected_meshes)
    else:
        st.info("Select one or more mesh files from the sidebar to view them")
    

if __name__ == "__main__":
    main()
