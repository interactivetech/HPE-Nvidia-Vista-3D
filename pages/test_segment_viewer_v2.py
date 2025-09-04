import os
import json
import requests
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# New, clean NiiVue viewer focused on correct label colormap application
# Uses a minimal JS flow aligned with NiiVue docs: https://niivue.com/docs/

st.set_page_config(layout="wide")
load_dotenv()

IMAGE_SERVER_URL = "https://localhost:8888"

# Fixed test file (int16 labels created by utils/segment.py)
TEST_REL_PATH = "output/segments/PA00000058/2.5_mm_STD_-_30%_ASIR_2.nii.gz"
# Build from the fixed HTTPS image server base
TEST_FILE_URL = f"{IMAGE_SERVER_URL}/{TEST_REL_PATH}"

st.title("NiiVue Label Viewer (v2)")

def list_server_dir(path: str):
    """Return (dirs, files) from the image server directory listing."""
    url = f"{IMAGE_SERVER_URL}/{path.strip('/')}/"
    try:
        r = requests.get(url, verify=False, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        dirs, files = [], []
        for a in soup.find_all('a'):
            href = a.get('href') or ""
            name = a.text.strip()
            if name in ("📁 ../", "../"):
                continue
            if href.endswith('/'):
                # Directory link text usually contains the folder name
                # Extract last component from href
                comp = href.strip('/').split('/')[-1]
                if comp and not comp.startswith('.'): 
                    dirs.append(comp)
            else:
                comp = href.split('/')[-1]
                if comp and (comp.endswith('.nii') or comp.endswith('.nii.gz')):
                    files.append(comp)
        return sorted(dirs), sorted(files)
    except Exception:
        return [], []

# Sidebar
with st.sidebar:
    st.header("Viewer Options")
    st.caption("Image Server: https://localhost:8888")
    # Remote browser for output/segments
    base_segments_path = "output/segments"
    patients, _ = list_server_dir(base_segments_path)
    default_patient = "PA00000058" if "PA00000058" in patients else (patients[0] if patients else "")
    selected_patient = st.selectbox("Select patient (server)", patients or [""], index=(patients.index(default_patient) if default_patient in patients else 0))
    files = []
    if selected_patient:
        files_path = f"{base_segments_path}/{selected_patient}"
        _, files = list_server_dir(files_path)
    default_file = "2.5_mm_STD_-_30%_ASIR_2.nii.gz" if "2.5_mm_STD_-_30%_ASIR_2.nii.gz" in files else (files[0] if files else "")
    selected_file = st.selectbox("Select file (server)", files or [""], index=(files.index(default_file) if default_file in files else 0))
    use_embedded_lut = st.radio(
        "Color Source",
        ["Vista3D JSON", "NIfTI embedded (if present)"],
        index=0,
    ).startswith("NIfTI")
    opacity = st.slider("Opacity", 0.0, 1.0, 1.0)
    custom_url = st.text_input("Or paste full image URL (overrides selection)", value="")

# If a valid selection was made, update the test file URL
if selected_patient and selected_file:
    TEST_REL_PATH = f"output/segments/{selected_patient}/{selected_file}"
    TEST_FILE_URL = f"{IMAGE_SERVER_URL}/{TEST_REL_PATH}"

# Allow direct URL override from the image server
if custom_url.strip().startswith("http"):
    TEST_FILE_URL = custom_url.strip()

st.write(f"Using test file: `{TEST_REL_PATH}`")
st.code(f"URL: {TEST_FILE_URL}")

# Build label colormap from conf/vista3d_label_colors.json
label_colors_path = "conf/vista3d_label_colors.json"

# Collect all label data first
label_data = []
try:
    with open(label_colors_path, "r") as f:
        data = json.load(f)
    
    # Add background (label 0)
    label_data.append({
        "id": 0,
        "name": "Background", 
        "color": [0, 0, 0],
        "alpha": 0  # Transparent background
    })
    
    # Add all Vista3D labels
    for item in data:
        label_id = int(item.get("id", 0))
        name = item.get("name", f"Label_{label_id}")
        color = item.get("color", [128, 128, 128])
        
        label_data.append({
            "id": label_id,
            "name": name,
            "color": color,
            "alpha": 255  # Opaque
        })
    
    # Sort by ID to ensure proper mapping
    label_data.sort(key=lambda x: x["id"])
    
except Exception as e:
    st.error(f"Failed to load label colors: {e}")
    label_data = [{"id": 0, "name": "Background", "color": [0, 0, 0], "alpha": 0}]

# Build NiiVue colormap arrays
r_values = []
g_values = []
b_values = []
a_values = []
i_values = []  # Actual label IDs (not sequential indices)
labels = []

for item in label_data:
    r_values.append(item["color"][0])
    g_values.append(item["color"][1]) 
    b_values.append(item["color"][2])
    a_values.append(item["alpha"])
    i_values.append(item["id"])  # Use actual label ID
    labels.append(item["name"])

# NiiVue label colormap format
colormap_label_json = json.dumps(
    {
        "R": r_values,
        "G": g_values,
        "B": b_values,
        "A": a_values,
        "I": i_values,  # Maps to actual label IDs: [0, 1, 3, 4, 5, 6, 7, ...]
        "labels": labels,
    }
)

st.write(f"Built colormap for {len(label_data)} labels (IDs: {i_values[:10]}...)")

# Debug: Show some bone entries
st.subheader("Bone Color Mapping (Debug)")
bone_examples = []
for i, item in enumerate(label_data):
    name = item["name"].lower()
    if any(keyword in name for keyword in ["vertebrae", "rib", "skull", "bone"]):
        bone_examples.append(f"ID {item['id']}: {item['name']} → RGB{tuple(item['color'])}")
        if len(bone_examples) >= 10:  # Show first 10 bone entries
            break

for example in bone_examples:
    st.write(f"- {example}")

# Simple HTML + JS using ESM build to avoid global name issues
html_template = """
<style>
  html, body { margin: 0; padding: 0; height: 100%; background: #111; }
  #wrap { position: relative; height: 800px; }
  #gl { width: 100%; height: 100%; display: block; }
  #status { position: absolute; top: 8px; left: 8px; color: #0f0; font: 12px monospace; background: rgba(0,0,0,0.6); padding: 6px; }
  .row { margin: 2px 0; }
  .ok { color: #0f0; }
  .warn { color: #ff0; }
  .err { color: #f55; }
</style>
<div id="wrap">
  <div id="status">
    <div class="row">NiiVue v2 viewer</div>
    <div class="row" id="s-niivue">NiiVue: ...</div>
    <div class="row" id="s-load">Load: ...</div>
    <div class="row" id="s-colormap">Colormap: ...</div>
  </div>
  <canvas id="gl"></canvas>
</div>

<script type="module">
  import { Niivue } from "https://unpkg.com/@niivue/niivue@0.62.1/dist/index.js";

  const s1 = document.getElementById('s-niivue');
  const s2 = document.getElementById('s-load');
  const s3 = document.getElementById('s-colormap');

  const nv = new Niivue({ 
    sliceType: 4, 
    isColorbar: true, 
    isResizeCanvas: true, 
    backColor: [0,0,0,1],
    dragMode: 1,  // Enable drag to rotate
    multiplanarPadPixels: 0,
    textHeight: 0.05
  });
  s1.textContent = 'NiiVue: initializing';
  await nv.attachTo("gl");
  s1.textContent = 'NiiVue: attached';
  
  // Ensure mouse controls are enabled
  console.log('NiiVue instance:', nv);
  console.log('Canvas element:', document.getElementById('gl'));

  const labelMap = %%LABEL_MAP%%;
  const tryEmbedded = %%TRY_EMBEDDED%%;
  
  // Validate colormap data
  console.log('Colormap validation:');
  console.log('- labelMap exists:', !!labelMap);
  console.log('- labelMap type:', typeof labelMap);
  if (labelMap) {
    console.log('- R array length:', labelMap.R ? labelMap.R.length : 'undefined');
    console.log('- G array length:', labelMap.G ? labelMap.G.length : 'undefined');
    console.log('- B array length:', labelMap.B ? labelMap.B.length : 'undefined');
    console.log('- A array length:', labelMap.A ? labelMap.A.length : 'undefined');
    console.log('- I array length:', labelMap.I ? labelMap.I.length : 'undefined');
    console.log('- labels length:', labelMap.labels ? labelMap.labels.length : 'undefined');
  }

  // Load volume first with basic settings
  const vol = {
    url: "%%URL%%",
    opacity: %%OPACITY%%
  };

  try {
    console.log('Loading volume...');
    await nv.loadVolumes([vol]);
    s2.textContent = 'Load: ok';
    
    const vol0 = nv.volumes[0];
    console.log('Volume loaded successfully');
    console.log('Volume data range:', vol0.global_min, 'to', vol0.global_max);
    
    // Apply Vista3D colormap using proper NiiVue method
    if (labelMap && labelMap.R && labelMap.R.length > 0) {
      console.log('Adding Vista3D colormap to NiiVue...');
      console.log('Colormap sample - first 10 entries:');
      for (let i = 0; i < Math.min(10, labelMap.I.length); i++) {
        console.log(`  ID ${labelMap.I[i]}: ${labelMap.labels[i]} → RGB(${labelMap.R[i]}, ${labelMap.G[i]}, ${labelMap.B[i]})`);
      }
      
      // Look for bones specifically
      console.log('Bone entries in colormap:');
      for (let i = 0; i < labelMap.labels.length; i++) {
        const name = labelMap.labels[i].toLowerCase();
        if (name.includes('vertebrae') || name.includes('rib') || name.includes('skull')) {
          console.log(`  ID ${labelMap.I[i]}: ${labelMap.labels[i]} → RGB(${labelMap.R[i]}, ${labelMap.G[i]}, ${labelMap.B[i]})`);
        }
      }
      
      // Add the colormap to NiiVue's colormap collection
      nv.addColormap('Vista3D', labelMap);
      
      // Apply the colormap to the volume
      const volumeId = vol0.id;
      console.log('Setting colormap Vista3D for volume ID:', volumeId);
      nv.setColormap(volumeId, 'Vista3D');
      
      s3.textContent = `Colormap: Vista3D applied (${labelMap.R.length} colors)`;
      console.log('Vista3D colormap successfully applied');
    } else {
      s3.textContent = 'Colormap: no valid colormap data';
    }
  } catch (e) {
    console.error('Load error details:', e);
    s2.textContent = 'Load: error - ' + e.message;
    s3.textContent = 'Colormap: load failed';
  }
</script>
"""

html = (
    html_template
    .replace("%%LABEL_MAP%%", colormap_label_json)
    .replace("%%TRY_EMBEDDED%%", str(use_embedded_lut).lower())
    .replace("%%URL%%", TEST_FILE_URL)
    .replace("%%OPACITY%%", str(opacity))
)

components.html(html, height=820, scrolling=False)

# Basic file sanity + label summary
st.subheader("Segmentation Summary (v2)")
try:
    import io
    import gzip
    import numpy as np
    import nibabel as nib
    resp = requests.get(TEST_FILE_URL, timeout=30, verify=False)
    resp.raise_for_status()
    bio = io.BytesIO(resp.content)
    if TEST_FILE_URL.endswith('.nii.gz'):
        with gzip.GzipFile(fileobj=bio) as gz:
            nii = nib.Nifti1Image.from_bytes(gz.read())
    else:
        nii = nib.Nifti1Image.from_bytes(bio.read())
    arr = np.asarray(nii.dataobj).astype('int64')
    ids, counts = np.unique(arr, return_counts=True)
    # Map to names/colors
    with open(label_colors_path, 'r') as f:
        color_list = json.load(f)
    id2entry = {int(it['id']): it for it in color_list}
    rows = []
    for uid, c in zip(ids.tolist(), counts.tolist()):
        entry = id2entry.get(int(uid))
        name = entry['name'] if entry else '(unknown)'
        color = entry['color'] if entry else [128,128,128]
        rows.append((uid, c, name, color))
    rows.sort(key=lambda r: r[1], reverse=True)
    st.write(f"Unique labels: {len(rows)}")
    for uid, c, name, color in rows[:25]:
        st.write(f"- ID {uid}: {name} — voxels: {c:,} — RGB{tuple(color)}")
except Exception as e:
    st.warning(f"Summary unavailable: {e}")


