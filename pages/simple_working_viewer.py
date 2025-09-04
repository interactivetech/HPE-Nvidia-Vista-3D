import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(layout="wide")
st.title("🧠 Simple Working NIfTI Viewer")

st.write("This viewer loads a proper NIfTI file - should work reliably!")

# Ultra-simple HTML that loads a NIfTI file
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
    </style>
</head>
<body>
    <div id="container">
        <div id="status">Loading...</div>
        <canvas id="niivue-canvas"></canvas>
    </div>
    
    <script src="https://unpkg.com/@niivue/niivue@0.62.1/dist/niivue.umd.js"></script>
    
    <script>
        console.log('🚀 Starting simple NIfTI viewer...');
        
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
                
                // Create NiiVue instance
                const nv = new niivue.Niivue({
                    isColorbar: true,
                    backColor: [0, 0, 0, 1]
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
                    updateStatus('File loaded, setting 3D mode...');
                    
                    // Set to 3D render mode
                    nv.setSliceType(4); // 4 = 3D render
                    nv.drawScene();
                    
                    updateStatus('✅ Ready! Mouse: rotate/zoom');
                    console.log('🎉 3D Viewer ready!');
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

st.subheader("🖼️ 3D NIfTI File Viewer")
st.write("This loads a proper NIfTI file that should work with NiiVue!")

components.html(html_content, height=650, scrolling=False)

st.subheader("📖 Controls")
st.markdown("""
- **Left click + drag**: Rotate the 3D volume
- **Right click + drag**: Pan the view  
- **Scroll wheel**: Zoom in/out
- **Status**: Check the green status box for progress
""")

st.subheader("✅ What This Proves")
st.markdown("""
If this viewer works, it proves:
- ✅ NiiVue library loads correctly
- ✅ NIfTI file loading works
- ✅ 3D rendering works
- ✅ Mouse controls work
- ✅ The issue was with JavaScript volume creation, not NiiVue itself

**This should show a 3D sphere that you can interact with!**
""")

st.subheader("🔧 Technical Details")
st.markdown("""
- **File**: `assets/simple_test.nii.gz` (5.4KB)
- **Dimensions**: 32×32×32 voxels
- **Data Type**: Float32
- **Content**: 3D sphere with gradient
- **Method**: `nv.loadVolumesFromUrl()` - proper NIfTI loading
""")
