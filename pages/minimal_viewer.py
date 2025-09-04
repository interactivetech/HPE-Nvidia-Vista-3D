import streamlit as st
import streamlit.components.v1 as components
import numpy as np
import base64
import io

st.set_page_config(layout="wide")
st.title("🧠 Minimal 3D NIfTI Viewer")

# Create a simple 3D volume in memory
@st.cache_data
def create_test_volume():
    """Create a simple test volume"""
    # Create a 32x32x32 volume with a sphere
    size = 32
    data = np.zeros((size, size, size), dtype=np.float32)
    
    center = size // 2
    radius = 12
    
    for x in range(size):
        for y in range(size):
            for z in range(size):
                dist = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
                if dist <= radius:
                    intensity = 1.0 - (dist / radius) * 0.3
                    data[x, y, z] = intensity
    
    return data

# Generate test data
test_data = create_test_volume()

# Convert to base64 data URL
def array_to_data_url(data):
    """Convert numpy array to base64 data URL"""
    # Normalize to 0-255
    normalized = ((data - data.min()) / (data.max() - data.min()) * 255).astype(np.uint8)
    
    # Create a simple binary format (just the raw data)
    binary_data = normalized.tobytes()
    b64_data = base64.b64encode(binary_data).decode('utf-8')
    
    return f"data:application/octet-stream;base64,{b64_data}"

data_url = array_to_data_url(test_data)

# Simple HTML viewer
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
        #info {{
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(0, 0, 0, 0.8);
            color: #ffffff;
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
        <div id="status">Loading NiiVue...</div>
        <div id="info">Generated Test Volume<br>32×32×32 voxels</div>
        <canvas id="niivue-canvas"></canvas>
    </div>
    
    <!-- Load NiiVue from CDN -->
    <script src="https://unpkg.com/@niivue/niivue@0.62.1/dist/niivue.umd.js"></script>
    
    <script>
        console.log('🚀 Starting minimal NiiVue viewer...');
        
        function updateStatus(message) {{
            const status = document.getElementById('status');
            if (status) status.textContent = message;
            console.log('📊', message);
        }}
        
        function waitForNiiVue() {{
            if (typeof niivue !== 'undefined') {{
                console.log('✅ NiiVue loaded');
                updateStatus('NiiVue loaded, creating viewer...');
                initializeViewer();
            }} else {{
                setTimeout(waitForNiiVue, 100);
            }}
        }}
        
        function initializeViewer() {{
            try {{
                updateStatus('Creating NiiVue instance...');
                
                const nv = new niivue.Niivue({{
                    sliceType: 4, // 3D Render
                    isColorbar: true,
                    backColor: [0, 0, 0, 1]
                }});
                
                nv.attachTo('niivue-canvas');
                console.log('✅ Attached to canvas');
                
                updateStatus('Creating test volume...');
                
                // Create a simple test volume directly in JavaScript
                const size = 32;
                const data = new Float32Array(size * size * size);
                
                // Create a sphere
                for (let x = 0; x < size; x++) {{
                    for (let y = 0; y < size; y++) {{
                        for (let z = 0; z < size; z++) {{
                            const dx = x - size/2;
                            const dy = y - size/2;
                            const dz = z - size/2;
                            const dist = Math.sqrt(dx*dx + dy*dy + dz*dz);
                            
                            if (dist <= 12) {{
                                const intensity = 1.0 - (dist / 12) * 0.3;
                                data[x + y*size + z*size*size] = intensity;
                            }}
                        }}
                    }}
                }}
                
                // Create volume object
                const volume = {{
                    img: data,
                    dims: [size, size, size],
                    pixDims: [1, 1, 1],
                    cal_min: 0,
                    cal_max: 1,
                    colormap: "gray"
                }};
                
                console.log('✅ Test volume created');
                updateStatus('Loading volume...');
                
                // Load the volume
                nv.loadVolumes([volume]);
                
                // Set to 3D render (use numeric value)
                nv.setSliceType(4); // 4 = RENDER mode
                
                // Render
                nv.drawScene();
                
                updateStatus('✅ Ready! Mouse: rotate/zoom');
                console.log('🎉 Viewer ready!');
                
            }} catch (error) {{
                console.error('❌ Error:', error);
                updateStatus('❌ Error: ' + error.message);
            }}
        }}
        
        updateStatus('Loading NiiVue...');
        waitForNiiVue();
    </script>
</body>
</html>
"""

st.subheader("🖼️ 3D Test Volume Viewer")
st.write("This viewer creates a test volume directly in JavaScript - no file loading required!")

components.html(html_content, height=650, scrolling=False)

st.subheader("📖 Controls")
st.markdown("""
- **Left click + drag**: Rotate the 3D volume
- **Right click + drag**: Pan the view
- **Scroll wheel**: Zoom in/out
- **Status**: Check the green status box for loading progress
""")

st.subheader("ℹ️ About This Viewer")
st.markdown("""
This is a minimal, self-contained 3D viewer that:
- ✅ Loads NiiVue from CDN (no local file issues)
- ✅ Creates test data in JavaScript (no file loading)
- ✅ Uses 3D rendering mode
- ✅ Has proper error handling
- ✅ Shows loading status

**If this works**, then the issue with the other viewer is file loading/CORS related.
**If this doesn't work**, then there's a deeper issue with NiiVue or WebGL.
""")
