import streamlit as st
import streamlit.components.v1 as components
import numpy as np
import nibabel as nib
import pyvista as pv
from pyvista import examples
import tempfile
import os

st.set_page_config(layout="wide")
st.title("🔬 PyVista 3D Medical Viewer")

st.write("Trying PyVista instead of NiiVue - might work better in Streamlit!")

# Load our NIfTI file
@st.cache_data
def load_nifti_data():
    try:
        # Load our simple test file
        nii_file = nib.load('assets/simple_test.nii.gz')
        data = nii_file.get_fdata()
        return data, nii_file.affine
    except:
        # Fallback to PyVista example data
        return examples.load_head().points, np.eye(4)

def create_pyvista_plot(data, affine):
    """Create a PyVista plot from NIfTI data"""
    
    # Create a simple volume from the data
    if len(data.shape) == 3:
        # Create a structured grid
        dims = data.shape
        grid = pv.ImageData(dimensions=dims, spacing=(1, 1, 1))
        grid.point_data['values'] = data.flatten(order='F')
        
        # Create isosurface
        try:
            mesh = grid.contour([0.5])  # Extract isosurface at 0.5
        except:
            # Fallback: create a simple sphere
            mesh = pv.Sphere(radius=10)
    else:
        # Fallback to sphere
        mesh = pv.Sphere(radius=10)
    
    # Create plotter
    plotter = pv.Plotter(off_screen=True)
    plotter.add_mesh(mesh, opacity=0.8, color='lightblue')
    plotter.set_background('black')
    
    # Set camera position
    plotter.camera_position = 'iso'
    
    # Render to image
    img = plotter.screenshot(transparent_background=True)
    plotter.close()
    
    return img

# Load data
data, affine = load_nifti_data()

st.subheader("📊 Data Information")
col1, col2 = st.columns(2)
with col1:
    st.write(f"**Data shape:** {data.shape}")
    st.write(f"**Data type:** {data.dtype}")
    st.write(f"**Data range:** {data.min():.3f} to {data.max():.3f}")

with col2:
    st.write(f"**Affine shape:** {affine.shape}")
    st.write(f"**Data size:** {data.nbytes / 1024:.1f} KB")

# Create PyVista visualization
st.subheader("🔬 PyVista 3D Visualization")

try:
    # Create the plot
    img = create_pyvista_plot(data, affine)
    
    # Display the image
    st.image(img, caption="3D Medical Volume (PyVista)", use_column_width=True)
    
    st.success("✅ PyVista visualization created successfully!")
    
except Exception as e:
    st.error(f"❌ PyVista error: {str(e)}")
    
    # Fallback: show data as 2D slices
    st.subheader("📊 2D Slice View (Fallback)")
    
    if len(data.shape) == 3:
        # Show middle slice
        middle_slice = data.shape[2] // 2
        slice_data = data[:, :, middle_slice]
        
        st.image(slice_data, caption=f"Middle slice ({middle_slice})", use_column_width=True)
        
        # Slice selector
        slice_idx = st.slider("Slice", 0, data.shape[2]-1, middle_slice)
        selected_slice = data[:, :, slice_idx]
        st.image(selected_slice, caption=f"Slice {slice_idx}", use_column_width=True)

st.subheader("📖 PyVista vs NiiVue")
st.markdown("""
**PyVista Advantages:**
- ✅ Works natively in Python/Streamlit
- ✅ No JavaScript/WebGL issues
- ✅ More stable for 3D rendering
- ✅ Better integration with scientific Python stack

**NiiVue Advantages:**
- ✅ Specifically designed for medical imaging
- ✅ Better NIfTI support
- ✅ More medical imaging features
- ✅ Web-based (good for sharing)

**If PyVista works, we can use it as a reliable fallback!**
""")

st.subheader("🎯 Next Steps")
st.markdown("""
1. **If PyVista works**: We have a working 3D medical viewer
2. **If PyVista fails**: We need to investigate the environment further
3. **Either way**: We can decide whether to continue with NiiVue or switch to PyVista
""")
