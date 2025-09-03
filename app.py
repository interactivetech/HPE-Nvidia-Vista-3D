import streamlit as st
from pathlib import Path
import json

# Load label dictionaries
PROJECT_ROOT = Path(__file__).parent
LABEL_DICT_PATH = PROJECT_ROOT / "conf" / "label_dict.json"
LABEL_COLORS_PATH = PROJECT_ROOT / "conf" / "label_colors.json"

with open(LABEL_DICT_PATH, 'r') as f:
    LABEL_DICT = json.load(f)

with open(LABEL_COLORS_PATH, 'r') as f:
    LABEL_COLORS = json.load(f)

st.set_page_config(
    page_title="NIfTI Vessel Segmentation and Viewer",
    page_icon="🧠",
    layout="wide",
)

st.title("NIfTI Vessel Segmentation and Viewer!")

# Sidebar for controls
with st.sidebar:
    st.info("Use the sidebar to navigate to the NiiVue page to view your NIfTI files.")
    
    # Display CT image planes illustration in sidebar
    image_path = Path(__file__).parent / "assets" / "CT-Image-Planes-768x768.jpeg"
    st.image(str(image_path), caption="CT Image Planes (Axial, Sagittal, Coronal)", use_container_width=True)

    # Pop down for segment colors
    with st.expander("Segment Colors"):
        st.write("Colors used for segmentation visualization:")
        for label_name, label_id in LABEL_DICT.items():
            color_rgb = LABEL_COLORS.get(str(label_id), [0, 0, 0]) # Default to black if not found
            color_hex = f"#{color_rgb[0]:02x}{color_rgb[1]:02x}{color_rgb[2]:02x}"
            st.markdown(f"<div style=\"display: flex; align-items: center; margin-bottom: 5px;\">" 
                        f"<div style=\"width: 20px; height: 20px; background-color: {color_hex}; border: 1px solid #ccc; margin-right: 10px;\"></div>" 
                        f"<span>{label_name} (ID: {label_id})</span>" 
                        f"</div>", unsafe_allow_html=True)