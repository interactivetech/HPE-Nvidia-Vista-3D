import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(layout="wide")
st.title("🧠 Stable NIfTI Viewer (Slice View)")

st.write("This viewer uses slice view instead of 3D render - should work reliably!")

# Ultra-simple HTML that loads a NIfTI file in slice view
html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {
            margin: 0;
            padding: 0;
            background: #1e1e1e;
        }
        #container {
            width: 100%;
            height: 600px;
            position: relative;
        }
        #niivue-canvas {
            width: 100%;
            height: 100%;
            display: block;
        }
        #status {
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
        }
        #controls {
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(0, 0, 0, 0.8);
            color: #ffffff;
            padding: 10px;
            border-radius: 5px;
            font-family: monospace;
            font-size: 11px;
            z-index: 1000;
        }
    </style>
</head>
<body>
    <div id="container">
        <div id="status">Loading...</div>
        <div id="controls">
            <div>Mouse: Pan/Zoom</div>
            <div>Scroll: Change slice</div>
        </div>
        <canvas id="niivue-canvas"></canvas>
    </div>
    
    <script src="https://unpkg.com/@niivue/niivue@0.62.1/dist/niivue.umd.js"></script>
    
    <script>
        console.log('🚀 Starting stable NIfTI viewer...');
        
        function updateStatus(msg) {
            document.getElementById('status').textContent = msg;
            console.log('📊', msg);
        }
        
        function waitForNiiVue() {
            if (typeof niivue !== 'undefined') {
                console.log('✅ NiiVue loaded');
                updateStatus('NiiVue loaded, initializing...');
                initViewer();
            } else {
                setTimeout(waitForNiiVue, 100);
            }
        }
        
        function initViewer() {
            try {
                updateStatus('Creating NiiVue instance...');
                
                // Create NiiVue instance with slice view
                const nv = new niivue.Niivue({
                    isColorbar: true,
                    backColor: [0, 0, 0, 1],
                    sliceType: 0, // Start with axial slice view
                    crosshairColor: [1, 1, 0, 1] // Yellow crosshair
                });
                
                // Attach to canvas
                nv.attachTo('niivue-canvas');
                console.log('✅ Attached to canvas');
                
                updateStatus('Loading NIfTI file...');
                
                // Load the NIfTI file
                const niftiUrl = 'assets/simple_test.nii.gz';
                console.log('📁 Loading file:', niftiUrl);
                
                nv.loadVolumesFromUrl(niftiUrl).then(() => {
                    console.log('🎉 NIfTI file loaded successfully!');
                    updateStatus('File loaded, ready!');
                    
                    // Draw the scene
                    nv.drawScene();
                    
                    updateStatus('✅ Ready! Mouse: pan/zoom, scroll: slice');
                    console.log('🎉 Slice viewer ready!');
                    
                    // Log volume info
                    if (nv.volumes && nv.volumes.length > 0) {
                        const vol = nv.volumes[0];
                        console.log('📊 Volume info:', {
                            dims: vol.dims,
                            name: vol.name,
                            cal_min: vol.cal_min,
                            cal_max: vol.cal_max
                        });
                    }
                    
                }).catch((error) => {
                    console.error('❌ Error loading NIfTI file:', error);
                    updateStatus('❌ Failed to load file: ' + error.message);
                });
                
            } catch (error) {
                console.error('❌ Error:', error);
                updateStatus('❌ Error: ' + error.message);
            }
        }
        
        updateStatus('Loading NiiVue...');
        waitForNiiVue();
    </script>
</body>
</html>
"""

st.subheader("🖼️ Slice View NIfTI Viewer")
st.write("This uses slice view instead of 3D render - much more stable!")

components.html(html_content, height=650, scrolling=False)

st.subheader("📖 Controls")
st.markdown("""
- **Mouse drag**: Pan the view
- **Scroll wheel**: Change slice (up/down through the volume)
- **Status**: Check the green status box for progress
- **Crosshair**: Yellow crosshair shows current position
""")

st.subheader("✅ What This Proves")
st.markdown("""
If this viewer works, it proves:
- ✅ NiiVue library loads correctly
- ✅ NIfTI file loading works
- ✅ Slice rendering works (more stable than 3D)
- ✅ Mouse controls work
- ✅ The issue was with 3D rendering, not NiiVue itself

**This should show slice views of the 3D volume that you can scroll through!**
""")

st.subheader("🔧 Technical Details")
st.markdown("""
- **View Mode**: Slice view (sliceType: 0) - more stable than 3D render
- **File**: `assets/simple_test.nii.gz` (5.4KB)
- **Dimensions**: 32×32×32 voxels
- **Method**: `nv.loadVolumesFromUrl()` - proper NIfTI loading
- **Rendering**: `nv.drawScene()` - standard slice rendering
""")

st.subheader("🎯 Next Steps")
st.markdown("""
Once this slice viewer works:
1. We know NiiVue is working perfectly
2. We can fix the original test viewer to use slice view
3. We can investigate 3D rendering issues separately
4. The main goal (viewing NIfTI files) is achieved
""")
