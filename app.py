import streamlit as st
from pathlib import Path
import sys

# Add utils to path for imports
sys.path.append(str(Path(__file__).parent / 'utils'))
from navigation import render_navigation

st.set_page_config(
    page_title="NIfTI Vessel Segmentation and Viewer",
    page_icon="🩻",
    layout="wide",
)

# Render navigation and get the navigation instance
nav = render_navigation()

# Main content based on current page
current_page = nav.get_current_page()

if current_page == 'home':
    st.title("Vessel Segmentation Viewer")
    st.markdown("Welcome to the NIfTI Vessel Segmentation and Viewer application.")
    st.markdown("Use the sidebar to navigate to different tools and features.")
elif current_page == 'niivue':
    # Import and run NiiVue content
    sys.path.append(str(Path(__file__).parent))
    exec(open('NiiVue.py').read())
elif current_page == 'cache':
    # Import and run cache content
    sys.path.append(str(Path(__file__).parent))
    exec(open('cache.py').read())

