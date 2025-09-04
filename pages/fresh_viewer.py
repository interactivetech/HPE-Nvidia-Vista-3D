import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(layout="wide")
st.title("🧠 Fresh NiiVue Implementation")

st.write("Starting completely fresh with the exact NiiVue documentation pattern!")

# Ultra-minimal HTML following NiiVue docs exactly
html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>NiiVue Basic Example</title>
    <style>
        body {
            margin: 0;
            padding: 20px;
            background: #1e1e1e;
            color: white;
            font-family: Arial, sans-serif;
        }
        #gl {
            border: 2px solid #333;
            background: #000;
        }
        #status {
            margin-top: 10px;
            padding: 10px;
            background: #333;
            border-radius: 5px;
            font-family: monospace;
        }
    </style>
</head>
<body>
    <h2>NiiVue Test Viewer</h2>
    <canvas id="gl" width="800" height="600"></canvas>
    <div id="status">Loading...</div>
    
    <script src="https://unpkg.com/@niivue/niivue@0.57.0/dist/niivue.umd.js"></script>
    <script>
        console.log('🚀 Starting fresh NiiVue implementation...');
        
        function updateStatus(msg) {
            document.getElementById('status').textContent = msg;
            console.log('📊', msg);
        }
        
        updateStatus('Initializing NiiVue...');
        
        try {
            // Create volume list exactly as in docs
            const volumeList = [
                {
                    url: "assets/simple_test.nii.gz",
                    name: "simple_test.nii.gz",
                },
            ];
            
            console.log('📁 Volume list:', volumeList);
            
            // Create NiiVue instance exactly as in docs
            const nv = new niivue.Niivue();
            console.log('✅ NiiVue instance created');
            
            // Attach to canvas exactly as in docs
            nv.attachTo('gl');
            console.log('✅ Attached to canvas');
            
            updateStatus('Loading volume...');
            
            // Load volumes exactly as in docs
            nv.loadVolumes(volumeList);
            console.log('✅ loadVolumes called');
            
            updateStatus('✅ Ready! Check console for details');
            
        } catch (error) {
            console.error('❌ Error:', error);
            updateStatus('❌ Error: ' + error.message);
        }
    </script>
</body>
</html>
"""

st.subheader("🖼️ Fresh NiiVue Implementation")
st.write("Using the exact pattern from NiiVue documentation - no customizations!")

components.html(html_content, height=700, scrolling=False)

st.subheader("📖 What This Does")
st.markdown("""
This implementation:
- Uses the **exact code pattern** from NiiVue documentation
- Uses **NiiVue 0.57.0** (older, more stable version)
- **No custom volume creation** - just loads our NIfTI file
- **No 3D rendering** - uses default slice view
- **Minimal code** - follows docs exactly

**If this doesn't work, the issue is with our NIfTI file or environment, not our code!**
""")

st.subheader("🔧 Debugging Steps")
st.markdown("""
1. **Check console** for any errors
2. **Verify** the NIfTI file loads
3. **Check** if canvas shows anything
4. **Look for** any volumeObject3D errors

If this works, we know the issue was with our complex implementation!
""")
