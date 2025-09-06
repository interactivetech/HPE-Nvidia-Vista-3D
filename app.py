import streamlit as st
from pathlib import Path
import sys
import requests
import os
from urllib.parse import urlparse

# Add utils to path for imports
sys.path.append(str(Path(__file__).parent / 'utils'))
from navigation import render_navigation

def check_image_server_status():
    """Check if the image server is available."""
    # Get server URL from environment variable (matching image_server.py)
    image_server_url = os.getenv("IMAGE_SERVER", "http://localhost:8888")
    
    try:
        # Make a quick HEAD request to check if server is responding
        response = requests.head(image_server_url, timeout=3)
        return True if response.status_code == 200 else False
    except (requests.exceptions.RequestException, requests.exceptions.Timeout):
        return False

def render_server_status_sidebar():
    """Render server status message in sidebar."""
    st.sidebar.markdown("---")
    
    if check_image_server_status():
        image_server_url = os.getenv("IMAGE_SERVER", "http://localhost:8888")
        
        st.sidebar.info(f"🖥️ **Image Server**  \n🟢 Online • {image_server_url}")
    else:
        st.sidebar.error(f"🖥️ **Image Server**  \n❌ Offline  \nStart with: `python utils/image_server.py`")

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
    # Render server status in sidebar (only on home page)
    render_server_status_sidebar()
    
    # Sidebar image only on Home page
    st.sidebar.image(
        str(Path(__file__).parent / 'assets' / 'CT-Image-Planes-768x768.jpeg'),
        use_container_width=True,
    )
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

