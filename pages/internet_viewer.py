import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(layout="wide")
st.title("🌐 Internet NIfTI Viewer")

st.write("Using a known working NIfTI file from the internet!")

# Ultra-minimal HTML using internet NIfTI file
html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>NiiVue Internet Example</title>
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
    <h2>NiiVue Internet Test</h2>
    <canvas id="gl" width="800" height="600"></canvas>
    <div id="status">Loading...</div>
    
    <script src="https://unpkg.com/@niivue/niivue@0.57.0/dist/niivue.umd.js"></script>
    <script>
        console.log('🚀 Starting internet NIfTI test...');
        
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
        
        function initViewer() {
            try {
                // Use the exact example from NiiVue docs
                const volumeList = [
                    {
                        url: "https://niivue.github.io/niivue-demo-images/mni152.nii.gz",
                        name: "mni152.nii.gz",
                    },
                ];
                
                console.log('📁 Loading internet NIfTI file...');
                updateStatus('Loading internet NIfTI file...');
                
                const nv = new niivue.Niivue();
                nv.attachTo('gl');
                nv.loadVolumes(volumeList);
                
                console.log('✅ Internet NIfTI loaded');
                updateStatus('✅ Internet NIfTI loaded successfully!');
                
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

st.subheader("🌐 Internet NIfTI Test")
st.write("Using the exact NIfTI file from NiiVue documentation examples!")

components.html(html_content, height=700, scrolling=False)

st.subheader("📖 What This Tests")
st.markdown("""
This tests:
- **Internet NIfTI file** from NiiVue docs (known to work)
- **Exact code pattern** from documentation
- **NiiVue 0.57.0** (stable version)
- **No local files** - eliminates file path issues

**If this works, NiiVue is fine and the issue is with our local files!**
**If this fails, there's a fundamental issue with NiiVue in this environment!**
""")

st.subheader("🎯 Next Steps")
st.markdown("""
1. **Test this first** - if it works, NiiVue is fine
2. **If it works**, the issue is with our local NIfTI file
3. **If it fails**, we need to investigate the environment
4. **Either way**, we'll have a clear path forward
""")
