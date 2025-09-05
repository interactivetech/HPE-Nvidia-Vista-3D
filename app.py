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
    st.info("Use the sidebar to navigate to the NiiVue page to view your NIfTI files.")
    
    # Display CT image planes illustration in sidebar
    image_path = Path(__file__).parent / "assets" / "CT-Image-Planes-768x768.jpeg"
    st.image(str(image_path), caption="CT Image Planes (Axial, Sagittal, Coronal)", use_container_width=True)

