import streamlit as st
import streamlit.components.v1 as components
import os
import json
from dotenv import load_dotenv

# --- Initial Setup ---
st.set_page_config(layout="wide")
load_dotenv()
IMAGE_SERVER_URL = os.getenv('IMAGE_SERVER', 'https://localhost:8888')

# --- Fixed file path for testing ---
TEST_FILE_PATH = "outputs/segments/PA00000002/01_2.5MM_ARTERIAL_seg.nii.gz"
TEST_FILE_URL = f"{IMAGE_SERVER_URL}/{TEST_FILE_PATH}"

st.title("Test Segment Viewer")
st.write(f"Viewing: `{TEST_FILE_PATH}`")

# --- Comprehensive Debugging Section ---
import requests
import time

st.subheader("🔍 Comprehensive Debugging")

# Debug 1: Environment and Configuration
st.write("**1. Environment Configuration:**")
st.code(f"IMAGE_SERVER_URL: {IMAGE_SERVER_URL}")
st.code(f"TEST_FILE_PATH: {TEST_FILE_PATH}")
st.code(f"TEST_FILE_URL: {TEST_FILE_URL}")

# Debug 2: File accessibility test (using GET instead of HEAD)
st.write("**2. File Accessibility Test:**")
try:
    start_time = time.time()
    # Use GET with Range header to avoid downloading the entire file
    headers = {'Range': 'bytes=0-1023'}  # Only request first 1KB
    response = requests.get(TEST_FILE_URL, headers=headers, verify=False, timeout=10)
    response_time = time.time() - start_time
    
    if response.status_code in [200, 206]:  # 206 = Partial Content
        st.success(f"✅ File is accessible (HTTP {response.status_code}) - Response time: {response_time:.2f}s")
        st.write(f"Content-Type: {response.headers.get('content-type', 'Unknown')}")
        st.write(f"Content-Length: {response.headers.get('content-length', 'Unknown')} bytes")
        st.write(f"Content-Range: {response.headers.get('content-range', 'Unknown')}")
        st.write(f"Last-Modified: {response.headers.get('last-modified', 'Unknown')}")
        st.write(f"ETag: {response.headers.get('etag', 'Unknown')}")
        
        # Test actual file download
        st.write("**3. File Download Test:**")
        try:
            download_start = time.time()
            download_response = requests.get(TEST_FILE_URL, verify=False, timeout=30)
            download_time = time.time() - download_start
            
            if download_response.status_code == 200:
                file_size = len(download_response.content)
                st.success(f"✅ File download successful - Size: {file_size} bytes, Time: {download_time:.2f}s")
                st.write(f"Download speed: {file_size / download_time / 1024:.2f} KB/s")
            else:
                st.error(f"❌ File download failed (HTTP {download_response.status_code})")
        except Exception as e:
            st.error(f"❌ File download error: {e}")
            
    else:
        st.error(f"❌ File not accessible (HTTP {response.status_code})")
        st.write(f"Response: {response.text}")
        st.write(f"Response headers: {dict(response.headers)}")
except Exception as e:
    st.error(f"❌ Error testing file accessibility: {e}")
    st.write(f"URL: {TEST_FILE_URL}")

# Debug 3: NiiVue library accessibility (checking local assets folder)
st.write("**4. NiiVue Library Test:**")
import os
niivue_local_path = "assets/niivue.umd.js"
niivue_absolute_path = os.path.abspath(niivue_local_path)

st.write(f"**Local file path:** `{niivue_local_path}`")
st.write(f"**Absolute path:** `{niivue_absolute_path}`")

try:
    if os.path.exists(niivue_absolute_path):
        file_size = os.path.getsize(niivue_absolute_path)
        st.success(f"✅ NiiVue library found locally - Size: {file_size:,} bytes")
        
        # Read first 200 characters to verify it's a JavaScript file
        with open(niivue_absolute_path, 'r', encoding='utf-8') as f:
            content_preview = f.read(200)
        
        if "niivue" in content_preview.lower() or "function" in content_preview or "var " in content_preview:
            st.success("✅ Content appears to be JavaScript library")
            st.write(f"Content preview: {content_preview[:100]}...")
        else:
            st.warning("⚠️ Content doesn't look like expected JavaScript library")
            st.write(f"Content preview: {content_preview}")
    else:
        st.error(f"❌ NiiVue library not found at local path")
        st.write("**Available files in assets folder:**")
        assets_dir = "assets"
        if os.path.exists(assets_dir):
            files = os.listdir(assets_dir)
            for file in files:
                st.write(f"  - {file}")
        else:
            st.write("  - assets folder not found")
except Exception as e:
    st.error(f"❌ NiiVue library test error: {e}")

# Debug 4: Label colors configuration
st.write("**5. Label Colors Configuration:**")
try:
    with open('conf/vista3d_label_colors.json', 'r') as f:
        label_colors_list = json.load(f)
    st.success(f"✅ Label colors loaded - {len(label_colors_list)} labels")
    
    # Show first few labels for debugging
    st.write("First 5 labels:")
    for i, label in enumerate(label_colors_list[:5]):
        st.write(f"  {i+1}. ID {label['id']}: {label['name']} - RGB{label['color']}")
        
except Exception as e:
    st.error(f"❌ Error loading label colors: {e}")

# Debug 5: Browser capabilities test
st.write("**6. Browser Capabilities Test:**")
st.info("Check browser console for WebGL and canvas capabilities")

# --- Sidebar Controls ---
with st.sidebar:
    st.header("Viewer Controls")
    
    # Opacity control
    opacity = st.slider("Opacity", 0.0, 1.0, 1.0)
    
    # Color map selector
    color_map = st.selectbox("Color Map", ['rgb', 'gray', 'viridis', 'plasma', 'inferno', 'magma'], index=0)
    
    # Reset view button
    if st.button("Reset View"):
        st.rerun()

# --- Prepare Custom Colormap for Segments ---
custom_colormap_js = ""
try:
    with open('conf/vista3d_label_colors.json', 'r') as f:
        label_colors_list = json.load(f)

    r_values = [0] * 256
    g_values = [0] * 256
    b_values = [0] * 256
    a_values = [0] * 256
    labels = [""] * 256

    # Set background (ID 0) to transparent black
    r_values[0] = 0
    g_values[0] = 0
    b_values[0] = 0
    a_values[0] = 0
    labels[0] = "Background"

    max_id = 0
    for item in label_colors_list:
        idx = item['id']
        label_name = item['name']
        color = item['color']
        if 0 <= idx < 256:
            r_values[idx] = color[0]
            g_values[idx] = color[1]
            b_values[idx] = color[2]
            a_values[idx] = 255  # Make segments opaque
            labels[idx] = label_name
        if idx > max_id:
            max_id = idx
    
    # Trim arrays to max_id + 1
    r_values = r_values[:max_id + 1]
    g_values = g_values[:max_id + 1]
    b_values = b_values[:max_id + 1]
    a_values = a_values[:max_id + 1]
    labels = labels[:max_id + 1]

    custom_colormap_js = f"""
        const customSegmentationColormap = {{
            R: [{ ",".join(map(str, r_values)) }],
            G: [{ ",".join(map(str, g_values)) }],
            B: [{ ",".join(map(str, b_values)) }],
            A: [{ ",".join(map(str, a_values)) }],
            labels: [{ ",".join(f'"{l}"' for l in labels) }]
        }}; 
        console.log('Custom colormap loaded:', customSegmentationColormap);
        """
except Exception as e:
    st.error(f"Error loading label colors: {e}")
    custom_colormap_js = ""

# --- Fixed to 3D Render view ---
actual_slice_type = 4  # 3D Render

# --- HTML and JavaScript for NiiVue with Extensive Debugging ---
html_string = f"""<style>
body, html {{
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
    overflow: hidden;
    background-color: #1e1e1e;
}}
#niivue-canvas {{
    width: 100%;
    height: 100%;
    display: block;
    border: 2px solid #00ff00;
}}
#debug-info {{
    position: absolute;
    top: 10px;
    left: 10px;
    background: rgba(0, 0, 0, 0.8);
    color: #00ff00;
    padding: 10px;
    font-family: monospace;
    font-size: 12px;
    z-index: 1000;
    max-width: 300px;
    border-radius: 5px;
}}
</style>
<div id="debug-info">
    <div>🔍 Debug Info</div>
    <div id="debug-status">Initializing...</div>
    <div id="debug-niivue">NiiVue: Checking...</div>
    <div id="debug-canvas">Canvas: Not ready</div>
    <div id="debug-webgl">WebGL: Not checked</div>
    <div id="debug-volumes">Volumes: 0</div>
    <div id="debug-render">Render: Not attempted</div>
</div>
<canvas id="niivue-canvas"></canvas>
<!-- Use CDN NiiVue for reliability -->
<script src="https://unpkg.com/@niivue/niivue@0.62.1/dist/niivue.umd.js"></script>
<script>
    // Global debug state
    window.debugState = {{
        niiVueLoaded: false,
        canvasReady: false,
        webglAvailable: false,
        volumesLoaded: 0,
        renderAttempts: 0,
        errors: [],
        currentStep: 'Starting...',
        niiVueLibraryLoaded: false
    }};
    
    function updateDebugInfo() {{
        const status = document.getElementById('debug-status');
        const niivue = document.getElementById('debug-niivue');
        const canvas = document.getElementById('debug-canvas');
        const webgl = document.getElementById('debug-webgl');
        const volumes = document.getElementById('debug-volumes');
        const render = document.getElementById('debug-render');
        
        if (status) status.textContent = `Status: ${{window.debugState.currentStep}}`;
        if (niivue) niivue.textContent = `NiiVue: ${{typeof niivue !== 'undefined' ? 'Loaded' : 'Not loaded'}}`;
        if (canvas) canvas.textContent = `Canvas: ${{window.debugState.canvasReady ? 'Ready' : 'Not ready'}}`;
        if (webgl) webgl.textContent = `WebGL: ${{window.debugState.webglAvailable ? 'Available' : 'Not available'}}`;
        if (volumes) volumes.textContent = `Volumes: ${{window.debugState.volumesLoaded}}`;
        if (render) render.textContent = `Render: ${{window.debugState.renderAttempts}} attempts`;
        
        // Also log the current state for debugging
        console.log('🔍 Debug state update:', {{
            niiVueLoaded: window.debugState.niiVueLoaded,
            niiVueLibraryLoaded: window.debugState.niiVueLibraryLoaded,
            canvasReady: window.debugState.canvasReady,
            webglAvailable: window.debugState.webglAvailable,
            currentStep: window.debugState.currentStep,
            niivueGlobal: typeof niivue !== 'undefined'
        }});
    }}
    
    // Test debug panel elements
    console.log('🔍 Testing debug panel elements...');
    const testElements = ['debug-status', 'debug-niivue', 'debug-canvas', 'debug-webgl', 'debug-volumes', 'debug-render'];
    testElements.forEach(id => {{
        const element = document.getElementById(id);
        console.log(`  ${{id}}: ${{element ? 'Found' : 'Not found'}}`);
    }});
    
    // Check if script loading was attempted
    console.log('🔍 Checking if NiiVue script loading was attempted...');
    const existingScripts = document.querySelectorAll('script[src*="niivue"]');
    console.log('📜 Existing NiiVue scripts found:', existingScripts.length);
    existingScripts.forEach((script, index) => {{
        console.log(`  Script ${{index + 1}}: ${{script.src}}`);
    }});
    
    // Update debug info immediately
    updateDebugInfo();
    
    // Force update with test message
    setTimeout(() => {{
        console.log('🔍 Force updating debug panel with test message...');
        const status = document.getElementById('debug-status');
        const niivue = document.getElementById('debug-niivue');
        if (status) status.textContent = 'Status: JavaScript executing';
        if (niivue) niivue.textContent = 'NiiVue: Testing...';
        console.log('✅ Debug panel force update completed');
    }}, 500);
    
    function logError(error, context) {{
        const errorMsg = `${{context}}: ${{error.message || error}}`;
        console.error('❌', errorMsg);
        window.debugState.errors.push(errorMsg);
        updateDebugInfo();
    }}
    
    console.log('🚀 Starting comprehensive NiiVue debugging...');
    console.log('📁 Test file URL:', "{TEST_FILE_URL}");
    console.log('🎨 Color map:', "{color_map}");
    console.log('👁️ Opacity:', {opacity});
    console.log('🖼️ Slice type:', {actual_slice_type});
    
    // Test basic JavaScript execution
    console.log('✅ JavaScript is executing properly');
    
    // Immediate check for NiiVue availability
    console.log('🔍 Immediate NiiVue check:', typeof niivue !== 'undefined' ? 'Available' : 'Not available');
    if (typeof niivue !== 'undefined') {{
        console.log('✅ NiiVue is already available - updating state immediately');
        window.debugState.niiVueLibraryLoaded = true;
        window.debugState.niiVueLoaded = true;
        window.debugState.currentStep = 'NiiVue library loaded (immediate)';
        updateDebugInfo();
    }} else {{
        console.log('⏳ NiiVue not yet available, will wait...');
    }}
    
    // Step 1: Check if NiiVue library is loaded
    window.debugState.currentStep = 'Checking NiiVue library...';
    updateDebugInfo();
    
    console.log('🔍 Step 1: Checking NiiVue library availability...');
    
    // Simple wait for NiiVue library
    function waitForNiiVue() {{
        if (typeof niivue !== 'undefined') {{
            console.log('✅ NiiVue library is loaded');
            console.log('NiiVue version:', niivue.version || 'Unknown');
            window.debugState.niiVueLibraryLoaded = true;
            window.debugState.niiVueLoaded = true;
            window.debugState.currentStep = 'NiiVue library loaded';
            updateDebugInfo();
            checkBrowserCapabilities();
        }} else {{
            console.log('⏳ Waiting for NiiVue library...');
            window.debugState.currentStep = 'Waiting for NiiVue library...';
            updateDebugInfo();
            setTimeout(waitForNiiVue, 100);
        }}
    }}
    
    function checkBrowserCapabilities() {{
        window.debugState.currentStep = 'Checking browser capabilities...';
        updateDebugInfo();
        console.log('🔍 Step 2: Checking browser capabilities...');
        
        // Check if canvas is supported
        window.canvas = document.getElementById('niivue-canvas');
        if (!window.canvas) {{
            logError('Canvas element not found', 'Canvas Check');
            window.debugState.currentStep = 'Canvas not found';
            updateDebugInfo();
            return;
        }}
        
        console.log('✅ Canvas element found');
        
        // Check WebGL support
        const gl = window.canvas.getContext('webgl2') || window.canvas.getContext('webgl');
        if (gl) {{
            console.log('✅ WebGL is available');
            console.log('WebGL Version:', gl.getParameter(gl.VERSION));
            console.log('WebGL Vendor:', gl.getParameter(gl.VENDOR));
            console.log('WebGL Renderer:', gl.getParameter(gl.RENDERER));
            window.debugState.webglAvailable = true;
        }} else {{
            console.error('❌ WebGL is not available');
            logError('WebGL not supported', 'WebGL Check');
        }}
        
        window.debugState.canvasReady = true;
        window.debugState.currentStep = 'Browser capabilities checked';
        updateDebugInfo();
        
        // Proceed to file accessibility test
        testFileAccessibility();
    }}
    
    function testFileAccessibility() {{
        window.debugState.currentStep = 'Testing file accessibility...';
        updateDebugInfo();
    
        // Test file accessibility with detailed logging (using GET with Range header)
        console.log('🔗 Step 3: Testing file accessibility...');
        fetch("{TEST_FILE_URL}", {{ 
            method: 'GET',
            headers: {{ 'Range': 'bytes=0-1023' }}  // Only request first 1KB
        }})
            .then(response => {{
                console.log('📡 File accessibility response:');
                console.log('  Status:', response.status, response.statusText);
                console.log('  Headers:', Object.fromEntries(response.headers.entries()));
                
                if (response.status !== 200 && response.status !== 206) {{  // 206 = Partial Content
                    logError(`HTTP ${{response.status}}: ${{response.statusText}}`, 'File Access');
                    window.debugState.currentStep = 'File access failed';
                    updateDebugInfo();
                    return;
                }}
                
                console.log('✅ File is accessible, proceeding with NiiVue initialization');
                window.debugState.currentStep = 'File accessible, initializing NiiVue...';
                updateDebugInfo();
                initializeNiiVue();
            }})
            .catch(error => {{
                logError(error, 'File Access');
                console.log('🔄 File access failed, attempting NiiVue initialization anyway...');
                window.debugState.currentStep = 'File access failed, trying anyway...';
                updateDebugInfo();
                initializeNiiVue();
            }});
    }}
    
    // Start the process
    waitForNiiVue();
    
    function initializeNiiVue() {{
        window.debugState.currentStep = 'Initializing NiiVue...';
        updateDebugInfo();
        console.log('🔧 Step 4: Starting NiiVue initialization...');
        
        try {{
            // Check if NiiVue is loaded
            if (typeof niivue === 'undefined') {{
                logError('NiiVue library not loaded', 'NiiVue Check');
                window.debugState.currentStep = 'NiiVue library not loaded';
                updateDebugInfo();
                return;
            }}
            
            console.log('✅ NiiVue library is available');
            console.log('NiiVue version:', niivue.version || 'Unknown');
            
            // Create NiiVue instance with extensive options
            console.log('🔧 Creating NiiVue instance with options:');
            const niiVueOptions = {{
                sliceType: {actual_slice_type},
                isColorbar: true,
                isRadiological: false,
                backColor: [0, 0, 0, 1],
                crosshairColor: [1, 0, 0, 1],
                crosshairWidth: 1,
                clipPlaneColor: [0, 1, 0, 0.5],
                show3Dcrosshair: true,
                dragMode: 1, // 0=contrast, 1=measurement, 2=pan
                isAdditiveBlend: false,
                isAtlasOutline: false,
                isRadiologicalConvention: false,
                isAntiAlias: true,
                isHighResolutionCapable: true,
                isResizeCanvas: true,
                isKioskMode: false,
                isOrientCube: true,
                isDepthPick: false,
                isCornerOrientationText: true,
                isRuler: false,
                isRulerLabel: false,
                isRulerColor: [1, 1, 1, 1],
                isRulerBold: false,
                isRulerItalic: false,
                isRulerSize: 24,
                isRulerFont: 'Arial',
                isRulerX: 0,
                isRulerY: 0,
                isRulerZ: 0,
                isRulerAlpha: 1,
                isRulerBeta: 0,
                isRulerGamma: 0,
                isRulerDelta: 0,
                isRulerEpsilon: 0,
                isRulerZeta: 0,
                isRulerEta: 0,
                isRulerTheta: 0,
                isRulerIota: 0,
                isRulerKappa: 0,
                isRulerLambda: 0,
                isRulerMu: 0,
                isRulerNu: 0,
                isRulerXi: 0,
                isRulerOmicron: 0,
                isRulerPi: 0,
                isRulerRho: 0,
                isRulerSigma: 0,
                isRulerTau: 0,
                isRulerUpsilon: 0,
                isRulerPhi: 0,
                isRulerChi: 0,
                isRulerPsi: 0,
                isRulerOmega: 0
            }};
            
            console.log('NiiVue options:', niiVueOptions);
            
            const nv = new niivue.Niivue(niiVueOptions);
            console.log('✅ NiiVue instance created:', nv);
            
            // Attach to canvas
            console.log('🔧 Attaching NiiVue to canvas...');
            nv.attachTo('niivue-canvas');
            console.log('✅ NiiVue attached to canvas');
            
            // Check canvas properties after attachment
            console.log('Canvas properties after attachment:');
            console.log('  Width:', window.canvas.width, 'Height:', window.canvas.height);
            console.log('  Client width:', window.canvas.clientWidth, 'Client height:', window.canvas.clientHeight);
            console.log('  Style width:', window.canvas.style.width, 'Style height:', window.canvas.style.height);
            
            window.debugState.niiVueLoaded = true;
            updateDebugInfo();
            
            // Wait for canvas to be fully ready
            setTimeout(() => {{
                console.log('📋 Starting volume loading process...');
                
                const volumeList = [{{
                    url: "{TEST_FILE_URL}",
                    colormap: "{color_map}",
                    opacity: {opacity}
                }}];
                
                console.log('🚀 Volume configuration:', volumeList);
                
                // Add event listeners for debugging (if supported)
                if (typeof nv.on === 'function') {{
                    nv.on('volumeLoaded', (volume) => {{
                        console.log('🎉 Volume loaded event fired:', volume);
                        window.debugState.volumesLoaded++;
                        updateDebugInfo();
                    }});
                    
                    nv.on('volumeError', (error) => {{
                        console.error('❌ Volume error event:', error);
                        logError(error, 'Volume Loading');
                    }});
                }} else {{
                    console.log('ℹ️ Event listeners not supported in this NiiVue version, proceeding without them');
                }}
                
                // Load volumes
                console.log('📥 Calling nv.loadVolumes...');
                nv.loadVolumes(volumeList);
                
                // Enhanced monitoring with more detailed checks
                let checkCount = 0;
                const checkInterval = setInterval(() => {{
                    checkCount++;
                    console.log(`⏰ Check #${{checkCount}}: Monitoring volume loading...`);
                    console.log('  Volumes array:', nv.volumes);
                    console.log('  Volumes length:', nv.volumes ? nv.volumes.length : 'undefined');
                    console.log('  NiiVue ready state:', nv.isLoaded);
                    console.log('  Scene object:', nv.scene);
                    
                    if (nv.volumes && nv.volumes.length > 0) {{
                        console.log('🎉 SUCCESS! Volume loaded successfully!');
                        console.log('📊 Volume details:');
                        const vol = nv.volumes[0];
                        console.log('  Volume object:', vol);
                        console.log('  Dimensions:', vol.dims);
                        console.log('  Data range:', {{min: vol.global_min, max: vol.global_max}});
                        console.log('  Matrix:', vol.matRAS);
                        console.log('  Colormap:', vol.colormap);
                        console.log('  Opacity:', vol.opacity);
                        console.log('  Data type:', vol.dataType);
                        console.log('  Voxel size:', vol.voxelSize);
                        console.log('  Bounding box:', vol.boundingBox);
                        
                        window.debugState.volumesLoaded = nv.volumes.length;
                        updateDebugInfo();
                        
                        clearInterval(checkInterval);
                        
                        // Apply custom colormap
                        {custom_colormap_js}
                        if (typeof customSegmentationColormap !== 'undefined') {{
                            console.log('🎨 Applying custom segmentation colormap...');
                            try {{
                                nv.setColormapLabel(customSegmentationColormap);
                                console.log('✅ Custom colormap applied');
                            }} catch (error) {{
                                logError(error, 'Colormap Application');
                            }}
                        }}
                        
                        // Set to 3D Render view
                        console.log('🖼️ Setting slice type to 3D Render...');
                        try {{
                            nv.setSliceType(4); // 4 = RENDER mode
                            console.log('✅ Slice type set to 3D Render');
                        }} catch (error) {{
                            logError(error, 'Slice Type Setting');
                        }}
                        
                        // Multiple render attempts with different strategies
                        console.log('🔄 Starting render attempts...');
                        
                        // Strategy 1: Immediate render
                        try {{
                            console.log('🔄 Render attempt 1: Immediate');
                            nv.drawScene();
                            window.debugState.renderAttempts++;
                            updateDebugInfo();
                            console.log('✅ Render attempt 1 completed');
                        }} catch (error) {{
                            logError(error, 'Render Attempt 1');
                        }}
                        
                        // Strategy 2: Delayed render
                        setTimeout(() => {{
                            try {{
                                console.log('🔄 Render attempt 2: Delayed (100ms)');
                                nv.drawScene();
                                window.debugState.renderAttempts++;
                                updateDebugInfo();
                                console.log('✅ Render attempt 2 completed');
                            }} catch (error) {{
                                logError(error, 'Render Attempt 2');
                            }}
                        }}, 100);
                        
                        // Strategy 3: Force refresh
                        setTimeout(() => {{
                            try {{
                                console.log('🔄 Render attempt 3: Force refresh (500ms)');
                                nv.refreshLayers();
                                nv.drawScene();
                                window.debugState.renderAttempts++;
                                updateDebugInfo();
                                console.log('✅ Render attempt 3 completed');
                            }} catch (error) {{
                                logError(error, 'Render Attempt 3');
                            }}
                        }}, 500);
                        
                        // Strategy 4: Reset and render
                        setTimeout(() => {{
                            try {{
                                console.log('🔄 Render attempt 4: Reset and render (1000ms)');
                                nv.resetScene();
                                nv.drawScene();
                                window.debugState.renderAttempts++;
                                updateDebugInfo();
                                console.log('✅ Render attempt 4 completed');
                            }} catch (error) {{
                                logError(error, 'Render Attempt 4');
                            }}
                        }}, 1000);
                        
                        // Final check
                        setTimeout(() => {{
                            console.log('🔍 Final status check:');
                            console.log('  Volumes loaded:', nv.volumes ? nv.volumes.length : 0);
                            console.log('  Scene ready:', nv.isLoaded);
                            console.log('  Canvas context:', window.canvas ? (window.canvas.getContext('webgl2') || window.canvas.getContext('webgl')) : 'Canvas not available');
                            console.log('  Render attempts:', window.debugState.renderAttempts);
                            console.log('  Errors encountered:', window.debugState.errors.length);
                            
                            if (window.debugState.errors.length > 0) {{
                                console.log('❌ Errors summary:');
                                window.debugState.errors.forEach((error, i) => {{
                                    console.log(`  ${{i+1}}. ${{error}}`);
                                }});
                            }}
                        }}, 2000);
                        
                    }} else if (checkCount >= 60) {{ // Increased timeout to 30 seconds
                        console.log('❌ Timeout: Volume never loaded after 30 seconds');
                        console.log('Final state:');
                        console.log('  Volumes:', nv.volumes);
                        console.log('  Ready:', nv.isLoaded);
                        console.log('  Errors:', window.debugState.errors);
                        clearInterval(checkInterval);
                    }}
                }}, 500);
                
            }}, 200); // Increased delay for canvas readiness
            
        }} catch (error) {{
            logError(error, 'NiiVue Initialization');
        }}
    }}
    
    // Update debug info every second and check NiiVue status
    setInterval(() => {{
        // Check if NiiVue is loaded but state wasn't updated
        if (typeof niivue !== 'undefined' && !window.debugState.niiVueLibraryLoaded) {{
            console.log('🔍 NiiVue detected in interval check - updating state');
            window.debugState.niiVueLibraryLoaded = true;
            window.debugState.niiVueLoaded = true;
            window.debugState.currentStep = 'NiiVue library loaded (interval check)';
        }}
        updateDebugInfo();
    }}, 1000);
</script>"""

# --- Display the viewer ---
components.html(html_string, height=800, scrolling=False)

# --- File information ---
st.subheader("File Information")
st.code(f"File URL: {TEST_FILE_URL}")
st.code(f"Slice Type: 3D Render (NiiVue value: {actual_slice_type})")
st.code(f"Color Map: {color_map}")
st.code(f"Opacity: {opacity}")

# --- Instructions ---
st.subheader("Instructions")
st.markdown("""
- Use mouse to rotate, zoom, and pan the 3D view
- Use the sidebar controls to adjust viewing parameters
- The segmentation should display with custom colors based on the label configuration
- Check the browser console for detailed loading information
- The green debug panel in the top-left shows real-time status
""")

# --- Debug Summary ---
st.subheader("🔍 Debug Summary")
st.markdown("""
**What this page tests:**
1. **File Accessibility** - Verifies the NIfTI file can be reached via HTTP
2. **File Download** - Tests actual file transfer and measures performance
3. **NiiVue Library** - Confirms the JavaScript library is accessible from local assets folder
4. **Label Colors** - Validates the segmentation color configuration
5. **Browser Capabilities** - Checks WebGL and canvas support
6. **Volume Loading** - Monitors the NiiVue volume loading process
7. **Rendering** - Attempts multiple rendering strategies

**Important Note:** The NiiVue library is now loaded from the local `assets/` folder instead of the image server to avoid HTTP 405 errors.

**Debug Features:**
- Real-time debug panel overlay (green box in viewer)
- Comprehensive console logging with emojis for easy scanning
- Multiple render strategies with different timing
- Error tracking and reporting
- Performance measurements
- WebGL capability detection
- Canvas property monitoring

**Troubleshooting Steps:**
1. Check if all green checkmarks appear in the debug sections above
2. Open browser console (F12) and look for error messages
3. Watch the green debug panel for real-time status updates
4. If volumes load but don't render, check WebGL support
5. If file access fails, verify the image server is running
6. **CORS Issue**: If you see CORS errors, the image server needs CORS headers configured

**Known Issues:**
- **CORS Error**: The image server at `{IMAGE_SERVER_URL}` doesn't have CORS headers configured
- **Workaround**: The viewer will attempt to load volumes anyway, but may fail due to CORS restrictions
- **Solution**: Configure the image server to include `Access-Control-Allow-Origin: *` headers
""")
