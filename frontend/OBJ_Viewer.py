import streamlit as st
import streamlit.components.v1 as components
import os
import json
from typing import Optional, List
from dotenv import load_dotenv

# Import utility modules
from utils.config_manager import ConfigManager
from utils.data_manager import DataManager
from utils.template_renderer import TemplateRenderer

# Import badge components
from assets.vista3d_badge import render_nvidia_vista_card
from assets.hpe_badge import render_hpe_badge

# --- Initial Setup ---
load_dotenv()
initial_image_server_url = os.getenv('IMAGE_SERVER', 'http://localhost:8888')
initial_external_image_server_url = os.getenv('EXTERNAL_IMAGE_SERVER', 'http://localhost:8888')

# Initialize URLs for container-to-container communication
if os.getenv("DOCKER_CONTAINER") == "true":
    IMAGE_SERVER_URL = "http://image-server:8888"
else:
    temp_data_manager = DataManager(initial_image_server_url)
    IMAGE_SERVER_URL = temp_data_manager.image_server_url

# For external URL, use the environment variable directly
EXTERNAL_IMAGE_SERVER_URL = initial_external_image_server_url

# Get output folder from environment - must be absolute path
OUTPUT_FOLDER = os.getenv('OUTPUT_FOLDER')
if not OUTPUT_FOLDER:
    raise ValueError("OUTPUT_FOLDER must be set in .env file with absolute path")
if not os.path.isabs(OUTPUT_FOLDER):
    raise ValueError("OUTPUT_FOLDER must be set in .env file with absolute path")

# Initialize managers
config_manager = ConfigManager()
data_manager = DataManager(IMAGE_SERVER_URL)
external_data_manager = DataManager(EXTERNAL_IMAGE_SERVER_URL, force_external_url=True)
template_renderer = TemplateRenderer()

# Viewer settings
VIEWER_HEIGHT = 1000
OBJ_EXTENSIONS = ('.obj',)

print(f"DEBUG (OBJ_Viewer): Final IMAGE_SERVER_URL: {IMAGE_SERVER_URL}")
print(f"DEBUG (OBJ_Viewer): Final EXTERNAL_IMAGE_SERVER_URL: {EXTERNAL_IMAGE_SERVER_URL}")


# --- Helper Functions ---
def get_obj_file_color(filename: str) -> tuple:
    """Get color for an OBJ file based on label colors from config."""
    # Remove .obj extension and convert underscores to spaces
    label_name = filename.replace('.obj', '').replace('_', ' ')
    
    # Try to find matching color in label colors
    for label in config_manager.label_colors:
        if label['name'].lower() == label_name.lower():
            color = label['color']
            # Convert RGB [0-255] to RGB [0-1] for Three.js
            return (color[0] / 255.0, color[1] / 255.0, color[2] / 255.0)
    
    # Default color if not found (gray)
    return (0.7, 0.7, 0.7)


# --- Sidebar UI ---
def render_sidebar():
    """Render the sidebar with patient/scan/file selection."""
    with st.sidebar:
        st.header("🫁 OBJ Viewer Navigation")
        
        # Get patient folders
        patient_folders = data_manager.get_server_data('', 'folders', ('',))
        
        # Debug information - only show if no patient folders found
        if not patient_folders:
            st.warning("No patient folders found. Check if:")
            st.write("1. Image server is running")
            st.write("2. OUTPUT_FOLDER contains patient directories")
            st.write("3. Patient directories contain obj/ folders")
            
            with st.expander("Debug Info", expanded=False):
                st.write(f"**Image Server URL:** {IMAGE_SERVER_URL}")
                st.write(f"**External Image Server URL:** {EXTERNAL_IMAGE_SERVER_URL}")
                st.write(f"**Output Folder:** {OUTPUT_FOLDER}")
        
        # Patient selection
        patient_options = [None] + patient_folders
        selected_patient = st.selectbox("Select Patient", patient_options, index=0)

        selected_scan = None
        selected_files = []
        
        if selected_patient:
            # Get scan folders
            scan_folders = data_manager.get_obj_scans(selected_patient)
            
            if scan_folders:
                scan_options = [None] + scan_folders
                selected_scan = st.selectbox("Select Scan", scan_options, index=0)
                
                if selected_scan:
                    # Get OBJ files for this scan
                    obj_files = data_manager.get_obj_files(selected_patient, selected_scan)
                    
                    if obj_files:
                        # Display scan info
                        st.info(f"📊 {len(obj_files)} OBJ files available")
                        
                        # File selection with multiselect
                        st.markdown("### Select Objects to Display")
                        
                        # Initialize session state for multiselect
                        if 'obj_multiselect_default' not in st.session_state:
                            st.session_state.obj_multiselect_default = []
                        
                        # Select All / Clear All buttons
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Select All", use_container_width=True):
                                st.session_state.obj_multiselect_default = obj_files.copy()
                                st.rerun()
                        with col2:
                            if st.button("Clear All", use_container_width=True):
                                st.session_state.obj_multiselect_default = []
                                st.rerun()
                        
                        # Multiselect for file selection
                        # Create display names without .obj extension
                        display_names = [f.replace('.obj', '').replace('_', ' ') for f in obj_files]
                        
                        # Filter session state defaults to only include files that exist in current obj_files
                        valid_defaults = [f for f in st.session_state.obj_multiselect_default if f in obj_files]
                        default_display_names = [f.replace('.obj', '').replace('_', ' ') for f in valid_defaults]
                        
                        selected_display_names = st.multiselect(
                            "Choose objects:",
                            display_names,
                            default=default_display_names,
                            label_visibility="collapsed"
                        )
                        
                        # Map back to filenames
                        selected_files = [
                            obj_files[display_names.index(name)]
                            for name in selected_display_names
                        ]
                        
                        # Update session state
                        st.session_state.obj_multiselect_default = selected_files.copy()
                        
                        # Show selection count
                        if selected_files:
                            st.caption(f"✓ {len(selected_files)} object(s) selected")
                        else:
                            st.caption("No objects selected")
                    else:
                        st.warning("No OBJ files found in this scan.")
            else:
                st.warning("No OBJ scan folders found for this patient.")
        
        # Viewer Settings
        st.markdown("---")
        st.markdown("### ⚙️ Viewer Settings")
        
        # Fixed black background
        background_color = "#000000"
        
        # Wireframe toggle
        show_wireframe = st.checkbox(
            "Show Wireframe",
            value=False,
            help="Display wireframe overlay on objects"
        )
        
        # Opacity slider
        object_opacity = st.slider(
            "Object Opacity",
            min_value=0.0,
            max_value=1.0,
            value=1.0,
            step=0.05,
            help="Adjust transparency of objects"
        )
        
        # Auto-rotate
        auto_rotate = st.checkbox(
            "Auto Rotate",
            value=False,
            help="Automatically rotate the view"
        )
        
        # Lighting settings
        with st.expander("💡 Lighting Settings", expanded=False):
            ambient_intensity = st.slider(
                "Ambient Light",
                min_value=0.0,
                max_value=2.0,
                value=0.6,
                step=0.1
            )
            
            directional_intensity = st.slider(
                "Directional Light",
                min_value=0.0,
                max_value=2.0,
                value=0.8,
                step=0.1
            )
        
        # Add spacing before badges
        st.sidebar.markdown("---")
        
        # Render badges
        render_nvidia_vista_card()
        render_hpe_badge()

    return (selected_patient, selected_scan, selected_files, 
            show_wireframe, object_opacity, auto_rotate,
            ambient_intensity, directional_intensity)


# --- Main Viewer ---
def render_viewer(selected_patient: str, selected_scan: str, selected_files: List[str],
                  show_wireframe: bool, object_opacity: float,
                  auto_rotate: bool, ambient_intensity: float, directional_intensity: float):
    """Render the main OBJ viewer."""
    if not selected_patient or not selected_scan:
        st.info("📦 Select a patient and scan to view 3D objects.")
        return
    
    if not selected_files:
        st.info("📦 Select one or more objects to display.")
        return
    
    # Build list of OBJ file URLs with colors
    obj_data = []
    for filename in selected_files:
        file_url = f"{EXTERNAL_IMAGE_SERVER_URL}/output/{selected_patient}/obj/{selected_scan}/{filename}"
        color = get_obj_file_color(filename)
        obj_data.append({
            'url': file_url,
            'name': filename.replace('.obj', '').replace('_', ' '),
            'color': color
        })
    
    # Prepare JavaScript data
    obj_data_js = json.dumps(obj_data)
    
    # Fixed black background
    bg_r = 0.0
    bg_g = 0.0
    bg_b = 0.0
    
    # Load Three.js from CDN and create viewer
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>OBJ Viewer</title>
    <style>
        body {{
            margin: 0;
            overflow: hidden;
            font-family: Arial, sans-serif;
        }}
        #viewer-container {{
            width: 100vw;
            height: {VIEWER_HEIGHT}px;
            position: relative;
        }}
        #loading {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: white;
            font-size: 18px;
            z-index: 10;
        }}
        #controls-hint {{
            position: absolute;
            bottom: 10px;
            left: 10px;
            color: white;
            background: rgba(0, 0, 0, 0.7);
            padding: 8px 12px;
            border-radius: 5px;
            font-size: 11px;
            z-index: 5;
        }}
    </style>
</head>
<body>
    <div id="viewer-container">
        <div id="loading">Loading 3D objects...</div>
        <div id="controls-hint">
            🖱️ Left-click: Rotate | Right-click: Pan | Scroll: Zoom
        </div>
    </div>

    <script type="importmap">
    {{
        "imports": {{
            "three": "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js",
            "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"
        }}
    }}
    </script>

    <script type="module">
        import * as THREE from 'three';
        import {{ OrbitControls }} from 'three/addons/controls/OrbitControls.js';
        import {{ OBJLoader }} from 'three/addons/loaders/OBJLoader.js';

        // Initialize scene, camera, renderer
        const container = document.getElementById('viewer-container');
        const loading = document.getElementById('loading');
        
        const scene = new THREE.Scene();
        scene.background = new THREE.Color({bg_r}, {bg_g}, {bg_b});
        
        const camera = new THREE.PerspectiveCamera(
            45,
            container.clientWidth / container.clientHeight,
            0.1,
            10000
        );
        camera.position.set(0, 0, 500);
        
        const renderer = new THREE.WebGLRenderer({{ antialias: true }});
        renderer.setSize(container.clientWidth, container.clientHeight);
        container.appendChild(renderer.domElement);
        
        // Lighting
        const ambientLight = new THREE.AmbientLight(0xffffff, {ambient_intensity});
        scene.add(ambientLight);
        
        const directionalLight = new THREE.DirectionalLight(0xffffff, {directional_intensity});
        directionalLight.position.set(1, 1, 1);
        scene.add(directionalLight);
        
        const directionalLight2 = new THREE.DirectionalLight(0xffffff, {directional_intensity * 0.5});
        directionalLight2.position.set(-1, -1, -1);
        scene.add(directionalLight2);
        
        // Controls
        const controls = new OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
        controls.autoRotate = {str(auto_rotate).lower()};
        controls.autoRotateSpeed = 1.0;
        
        // Load OBJ files
        const objData = {obj_data_js};
        const loader = new OBJLoader();
        let loadedCount = 0;
        const totalObjects = objData.length;
        
        // Group to hold all objects
        const objectGroup = new THREE.Group();
        scene.add(objectGroup);
        
        // Load each OBJ file
        objData.forEach((objInfo, index) => {{
            loader.load(
                objInfo.url,
                function(object) {{
                    // Set material with color
                    const material = new THREE.MeshPhongMaterial({{
                        color: new THREE.Color(objInfo.color[0], objInfo.color[1], objInfo.color[2]),
                        opacity: {object_opacity},
                        transparent: {str(object_opacity < 1.0).lower()},
                        side: THREE.DoubleSide
                    }});
                    
                    object.traverse(function(child) {{
                        if (child instanceof THREE.Mesh) {{
                            child.material = material;
                        }}
                    }});
                    
                    // Add wireframe if enabled
                    if ({str(show_wireframe).lower()}) {{
                        object.traverse(function(child) {{
                            if (child instanceof THREE.Mesh) {{
                                const wireframe = new THREE.WireframeGeometry(child.geometry);
                                const lineMaterial = new THREE.LineBasicMaterial({{ 
                                    color: 0x000000,
                                    linewidth: 1,
                                    opacity: 0.3,
                                    transparent: true
                                }});
                                const line = new THREE.LineSegments(wireframe, lineMaterial);
                                child.add(line);
                            }}
                        }});
                    }}
                    
                    objectGroup.add(object);
                    loadedCount++;
                    
                    if (loadedCount === totalObjects) {{
                        loading.style.display = 'none';
                        
                        // Center and scale the scene
                        const box = new THREE.Box3().setFromObject(objectGroup);
                        const center = box.getCenter(new THREE.Vector3());
                        const size = box.getSize(new THREE.Vector3());
                        
                        // Center the group
                        objectGroup.position.sub(center);
                        
                        // Calculate camera distance
                        const maxDim = Math.max(size.x, size.y, size.z);
                        const fov = camera.fov * (Math.PI / 180);
                        let cameraZ = Math.abs(maxDim / 2 / Math.tan(fov / 2));
                        cameraZ *= 1.5; // Zoom out a bit
                        
                        camera.position.set(cameraZ, cameraZ * 0.5, cameraZ);
                        camera.lookAt(0, 0, 0);
                        controls.target.set(0, 0, 0);
                        controls.update();
                    }}
                }},
                function(xhr) {{
                    // Progress callback
                    if (xhr.lengthComputable) {{
                        const percentComplete = xhr.loaded / xhr.total * 100;
                        console.log(`Loading ${{objInfo.name}}: ${{percentComplete.toFixed(2)}}%`);
                    }}
                }},
                function(error) {{
                    console.error(`Error loading ${{objInfo.url}}:`, error);
                    loadedCount++;
                    
                    if (loadedCount === totalObjects) {{
                        loading.style.display = 'none';
                    }}
                }}
            );
        }});
        
        // Animation loop
        function animate() {{
            requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        }}
        animate();
        
        // Handle window resize
        window.addEventListener('resize', function() {{
            camera.aspect = container.clientWidth / container.clientHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(container.clientWidth, container.clientHeight);
        }});
    </script>
</body>
</html>
    """
    
    # Display the viewer
    components.html(html_content, height=VIEWER_HEIGHT, scrolling=False)


# --- Main Application Flow ---
def main():
    """Main application entry point."""
    # Set page title
    st.header("🫁 OBJ 3D Viewer")
    
    # Render sidebar and get selections
    (selected_patient, selected_scan, selected_files,
     show_wireframe, object_opacity, auto_rotate,
     ambient_intensity, directional_intensity) = render_sidebar()

    # Render main viewer
    render_viewer(
        selected_patient, selected_scan, selected_files,
        show_wireframe, object_opacity, auto_rotate,
        ambient_intensity, directional_intensity
    )


if __name__ == "__main__":
    main()

