import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(layout="wide")
st.title("🔄 LoadImages NiiVue Test")

st.write("Trying the loadImages method with an older NiiVue version!")

# HTML using loadImages method and older NiiVue version
html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>NiiVue LoadImages Test</title>
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
    <h2>NiiVue LoadImages Test</h2>
    <canvas id="gl" width="800" height="600"></canvas>
    <div id="status">Loading...</div>
    
    <!-- Try older, more stable version -->
    <script src="https://unpkg.com/@niivue/niivue@0.33.0/dist/niivue.umd.js"></script>
    <script>
        console.log('🚀 Starting loadImages test...');
        
        function updateStatus(msg) {
            document.getElementById('status').textContent = msg;
            console.log('📊', msg);
        }
        
        updateStatus('Loading NiiVue...');
        
        // Wait for NiiVue to load
        function waitForNiiVue() {
            if (typeof niivue !== 'undefined') {
                console.log('✅ NiiVue loaded');
                updateStatus('NiiVue loaded, creating viewer...');
                initViewer();
            } else {
                setTimeout(waitForNiiVue, 100);
            }
        }
        
        async function initViewer() {
            try {
                updateStatus('Creating NiiVue instance...');
                
                // Create NiiVue instance
                const nv = new niivue.Niivue();
                console.log('✅ NiiVue instance created');
                
                // Attach to canvas
                nv.attachTo('gl');
                console.log('✅ Attached to canvas');
                
                updateStatus('Loading volume with loadImages...');
                
                // Use loadImages method as suggested
                const imageList = [
                    {
                        url: "https://niivue.github.io/niivue-demo-images/mni152.nii.gz",
                        name: "mni152.nii.gz"
                    }
                ];
                
                console.log('📁 Loading with loadImages...');
                await nv.loadImages(imageList);
                
                console.log('✅ Volume loaded with loadImages');
                updateStatus('✅ Volume loaded successfully!');
                
            } catch (error) {
                console.error('❌ Error:', error);
                updateStatus('❌ Error: ' + error.message);
            }
        }
        
        waitForNiiVue();
    </script>
</body>
</html>
"""

st.subheader("🔄 LoadImages Method Test")
st.write("Using the loadImages method with NiiVue 0.33.0 (older version)")

components.html(html_content, height=700, scrolling=False)

st.subheader("📖 What This Tests")
st.markdown("""
This tests:
- **loadImages method** instead of loadVolumes
- **NiiVue 0.33.0** (much older, more stable version)
- **Internet NIfTI file** (known to work)
- **Async/await pattern** as suggested in docs

**This should work if the issue was with loadVolumes or newer NiiVue versions!**
""")
