import streamlit as st
from pathlib import Path


st.set_page_config(
    page_title="NIfTI Vessel Segmentation and Viewer",
    page_icon="🧠",
    layout="wide",
)

st.title("Vessel Segmentation Viewer")

# Sidebar for controls
with st.sidebar:
    st.info("Use the sidebar to navigate to different pages.")
    
    # Navigation
    st.header("Navigation")
    if st.button("🏠 Home", use_container_width=True):
        st.rerun()
    
    if st.button("🧠 NiiVue Viewer", use_container_width=True):
        st.switch_page("pages/NiiVue.py")
    
    if st.button("💾 Cache Management", use_container_width=True):
        st.switch_page("pages/cache.py")
    
    st.markdown("---")
    
    # Display CT image planes illustration in sidebar
    image_path = Path(__file__).parent / "assets" / "CT-Image-Planes-768x768.jpeg"
    st.image(str(image_path), caption="CT Image Planes (Axial, Sagittal, Coronal)", use_container_width=True)

