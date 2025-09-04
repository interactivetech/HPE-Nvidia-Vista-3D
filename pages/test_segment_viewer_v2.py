import os
import json
import requests
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

# New, clean NiiVue viewer focused on correct label colormap application
# Uses a minimal JS flow aligned with NiiVue docs: https://niivue.com/docs/

st.set_page_config(layout="wide")
load_dotenv()

IMAGE_SERVER_URL = os.getenv("IMAGE_SERVER", "https://localhost:8888")

# Fixed test file (int16 labels created by utils/segment.py)
TEST_REL_PATH = "outputs/segments/PA00000002/01_2.5MM_ARTERIAL_seg_int16.nii.gz"
TEST_FILE_URL = f"{IMAGE_SERVER_URL}/{TEST_REL_PATH}"

st.title("NiiVue Label Viewer (v2)")
st.write(f"Using test file: `{TEST_REL_PATH}`")

# Sidebar
with st.sidebar:
    st.header("Viewer Options")
    use_embedded_lut = st.radio(
        "Color Source",
        ["Vista3D JSON", "NIfTI embedded (if present)"],
        index=0,
    ).startswith("NIfTI")
    opacity = st.slider("Opacity", 0.0, 1.0, 1.0)

# Build label colormap from conf/vista3d_label_colors.json
label_colors_path = "conf/vista3d_label_colors.json"
r_values = [0] * 256
g_values = [0] * 256
b_values = [0] * 256
a_values = [0] * 256
labels = [""] * 256

# background transparent
r_values[0] = 0
g_values[0] = 0
b_values[0] = 0
a_values[0] = 0
labels[0] = "Background"

max_id = 0
try:
    with open(label_colors_path, "r") as f:
        data = json.load(f)
    for item in data:
        idx = int(item["id"]) if "id" in item else 0
        name = item.get("name", "")
        color = item.get("color", [0, 0, 0])
        if 0 <= idx < 256:
            r_values[idx] = int(color[0])
            g_values[idx] = int(color[1])
            b_values[idx] = int(color[2])
            a_values[idx] = 255
            labels[idx] = name
            if idx > max_id:
                max_id = idx
except Exception as e:
    st.error(f"Failed to load label colors: {e}")

# trim
r_values = r_values[: max_id + 1]
g_values = g_values[: max_id + 1]
b_values = b_values[: max_id + 1]
a_values = a_values[: max_id + 1]
labels = labels[: max_id + 1]

# JSON for safe JS injection (no f-string eval inside)
colormap_label_json = json.dumps(
    {
        "R": r_values,
        "G": g_values,
        "B": b_values,
        "A": a_values,
        "labels": labels,
    }
)
# Intensity style map (for nv.addColormap / nv.setColormap)
i_values = list(range(len(r_values)))
colormap_intensity_json = json.dumps(
    {
        "R": r_values,
        "G": g_values,
        "B": b_values,
        "A": a_values,
        "I": i_values,
    }
)

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

  const nv = new Niivue({ sliceType: 4, isColorbar: true, isResizeCanvas: true, backColor: [0,0,0,1] });
  s1.textContent = 'NiiVue: initializing';
  await nv.attachTo("gl");
  s1.textContent = 'NiiVue: attached';

  const labelMap = %%LABEL_MAP%%;
  const cmapIntensity = %%CMAP_INTENSITY%%;
  const tryEmbedded = %%TRY_EMBEDDED%%;

  const vol = {
    url: "%%URL%%",
    opacity: %%OPACITY%%
  };

  try {
    await nv.loadVolumes([vol]);
    s2.textContent = 'Load: ok';
  } catch (e) {
    s2.textContent = 'Load: error';
    console.error(e);
  }

  try {
    const vol0 = (nv.volumes && nv.volumes.length) ? nv.volumes[0] : null;
    if (tryEmbedded && vol0 && vol0.colormapLabel) {
      // Some NIfTI may expose embedded label LUT via colormapLabel, not always present
      // If present, we could add it as a custom map, but most builds use intensity maps.
      // Fallback to intensity approach if not available.
      s3.textContent = 'Colormap: embedded LUT detected but unsupported in this build; using JSON';
    }
    // Use intensity-style custom colormap
    nv.addColormap('Vista3D', cmapIntensity);
    if (nv.volumes && nv.volumes.length) {
      const firstId = nv.volumes[0].id;
      nv.setColormap(firstId, 'Vista3D');
    }
    s3.textContent = 'Colormap: JSON applied';
    nv.drawScene();
  } catch (e) {
    s3.textContent = 'Colormap: error';
    console.error(e);
  }
</script>
"""

html = (
    html_template
    .replace("%%LABEL_MAP%%", colormap_label_json)
    .replace("%%CMAP_INTENSITY%%", colormap_intensity_json)
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


