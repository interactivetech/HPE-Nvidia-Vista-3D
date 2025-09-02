import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="NIfTI Vessel Segmentation and Viewer",
    page_icon="🧠",
    layout="centered",
)

st.title("Welcome to the NIfTI Vessel Segmentation and Viewer!")

# Display CT image planes illustration
image_path = Path(__file__).parent / "assets" / "CT-Image-Planes-768x768.jpeg"
st.image(str(image_path), caption="CT Image Planes (Axial, Sagittal, Coronal)", use_container_width=True)

st.info("Use the sidebar to navigate to the NiiVue page to view your NIfTI files.")
