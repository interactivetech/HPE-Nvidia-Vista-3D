import streamlit as st
import streamlit.components.v1 as components
import os
import json
from dotenv import load_dotenv

# --- Initial Setup ---
st.set_page_config(layout="wide")
load_dotenv()
IMAGE_SERVER_URL = os.getenv('IMAGE_SERVER', 'https://localhost:8888')

st.title("🧠 Simple 3D NIfTI Viewer")
st.write("A minimal, working 3D viewer for NIfTI files")

# --- File Selection ---
st.subheader("📁 File Selection")

# Check if sample file exists, if not create it
sample_file = "assets/sample_brain.nii.gz"
if not os.path.exists(sample_file):
    st.info("Creating sample NIfTI file...")
    import subprocess
    try:
        subprocess.run(["python", "create_sample_nifti.py"], check=True)
        st.success("✅ Sample file created!")
    except:
        st.error("❌ Could not create sample file")

# File options
file_options = {
    "Sample Brain": "assets/sample_brain.nii.gz",
    "Test Segmentation": f"{IMAGE_SERVER_URL}/outputs/segments/PA00000002/01_2.5MM_ARTERIAL_seg.nii.gz"
}

selected_file_name = st.selectbox("Choose file to view:", list(file_options.keys()))
selected_file_path = file_options[selected_file_name]

st.write(f"**Selected file:** `{selected_file_path}`")

# --- Simple HTML Viewer ---
st.subheader("🖼️ 3D Viewer")

# Simple HTML with embedded NiiVue
html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            margin: 0;
            padding: 0;
            background: #1e1e1e;
            font-family: Arial, sans-serif;
        }}
        #container {{
            width: 100%;
            height: 600px;
            position: relative;
        }}
        #niivue-canvas {{
            width: 100%;
            height: 100%;
            display: block;
        }}
        #status {{
            position: absolute;
            top: 10px;
            left: 10px;
            background: rgba(0, 0, 0, 0.8);
            color: #00ff00;
            padding: 10px;
            border-radius: 5px;
            font-family: monospace;
            font-size: 12px;
            z-index: 1000;
        }}
    </style>
</head>
<body>
    <div id="container">
        <div id="status">Loading...</div>
        <canvas id="niivue-canvas"></canvas>
    </div>
    
    <!-- Load NiiVue from CDN for reliability -->
    <script src="https://unpkg.com/@niivue/niivue@0.62.1/dist/niivue.umd.js"></script>
    
    <script>
        console.log('🚀 Starting simple NiiVue viewer...');
        
        // Update status
        function updateStatus(message) {{
            const status = document.getElementById('status');
            if (status) {{
                status.textContent = message;
            }}
            console.log('📊 Status:', message);
        }}
        
        // Wait for NiiVue to load
        function waitForNiiVue() {{
            if (typeof niivue !== 'undefined') {{
                console.log('✅ NiiVue loaded successfully');
                updateStatus('NiiVue loaded, initializing...');
                initializeViewer();
            }} else {{
                console.log('⏳ Waiting for NiiVue...');
                setTimeout(waitForNiiVue, 100);
            }}
        }}
        
        function initializeViewer() {{
            try {{
                updateStatus('Creating NiiVue instance...');
                
                // Create NiiVue instance
                const nv = new niivue.Niivue({{
                    sliceType: 4, // 3D Render
                    isColorbar: true,
                    backColor: [0, 0, 0, 1]
                }});
                
                console.log('✅ NiiVue instance created');
                
                // Attach to canvas
                nv.attachTo('niivue-canvas');
                console.log('✅ Attached to canvas');
                
                updateStatus('Loading volume...');
                
                // Load the volume
                const volumeList = [{{
                    url: "{selected_file_path}",
                    colormap: "gray"
                }}];
                
                console.log('📁 Loading file:', "{selected_file_path}");
                nv.loadVolumes(volumeList);
                
                // Monitor loading
                let checkCount = 0;
                const checkInterval = setInterval(() => {{
                    checkCount++;
                    
                    if (nv.volumes && nv.volumes.length > 0) {{
                        console.log('🎉 Volume loaded successfully!');
                        updateStatus('Volume loaded, rendering...');
                        
                        // Set to 3D render mode (use numeric value)
                        nv.setSliceType(4); // 4 = RENDER mode
                        
                        // Render
                        nv.drawScene();
                        
                        updateStatus('✅ Ready! Use mouse to rotate/zoom');
                        clearInterval(checkInterval);
                        
                    }} else if (checkCount >= 20) {{
                        console.log('❌ Timeout loading volume');
                        updateStatus('❌ Failed to load volume');
                        clearInterval(checkInterval);
                    }} else {{
                        updateStatus(`Loading... (${{checkCount}}/20)`);
                    }}
                }}, 500);
                
            }} catch (error) {{
                console.error('❌ Error initializing viewer:', error);
                updateStatus('❌ Error: ' + error.message);
            }}
        }}
        
        // Start the process
        updateStatus('Loading NiiVue...');
        waitForNiiVue();
    </script>
</body>
</html>
"""

# Display the viewer
components.html(html_content, height=650, scrolling=False)

# --- Instructions ---
st.subheader("📖 Instructions")
st.markdown("""
- **Mouse Controls**: 
  - Left click + drag: Rotate
  - Right click + drag: Pan
  - Scroll wheel: Zoom
- **Status**: Check the green status box in the top-left corner
- **Console**: Open browser console (F12) for detailed logs
""")

# --- File Information ---
st.subheader("ℹ️ File Information")
st.code(f"File: {selected_file_path}")
st.code("Viewer: NiiVue 0.62.1 (CDN)")
st.code("Mode: 3D Render")

# --- Troubleshooting ---
with st.expander("🔧 Troubleshooting"):
    st.markdown("""
    **If the viewer doesn't work:**
    1. Check browser console (F12) for errors
    2. Try refreshing the page
    3. Check if the file URL is accessible
    4. Ensure WebGL is supported in your browser
    
    **Common issues:**
    - CORS errors: File server needs CORS headers
    - WebGL not supported: Try a different browser
    - File not found: Check the file path
    """)
