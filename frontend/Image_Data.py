#!/usr/bin/env python3
"""
Image Data Page - Embeds the image server interface in an iframe.
"""

import streamlit as st
import streamlit.components.v1 as components
import requests
import os

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Fallback if python-dotenv is not available
    pass

from assets.vista3d_badge import render_nvidia_vista_card as _render_nvidia_vista_card
from assets.hpe_badge import render_hpe_badge as _render_hpe_badge

from utils.server_status import check_image_server_status, render_server_status_sidebar

def render_nvidia_vista_card():
    """Delegate rendering to assets.vista3d_badge module."""
    _render_nvidia_vista_card()


def main():
    """Main function for the Image Data page."""
    # Note: This function is called from app.py, so navigation is already rendered
    # We don't need to call render_navigation() or set_page_config() here
    
    # Render Nvidia Vista 3D card in sidebar
    render_nvidia_vista_card()
    # Render HPE AI badge in sidebar
    _render_hpe_badge()
    
    # Render server status widgets in sidebar
    render_server_status_sidebar()
    
    # Get image server URLs
    # For browser access (iframe), we need the external URL that the browser can reach
    # For server-side checks, we use the internal URL (works within Docker network)
    external_image_server_url = os.getenv("EXTERNAL_IMAGE_SERVER", "http://localhost:8888")
    
    # Check if image server is running
    if check_image_server_status():
        # Embed the image server in an iframe using the external URL (accessible from browser)
        components.iframe(external_image_server_url, height=800, scrolling=True)
    else:
        st.error(f"❌ **Image Server is Offline**")
        st.write(f"The image server at `{external_image_server_url}` is not responding.")
        st.write("Please start the image server using:")
        st.code("python image_server/server.py", language="bash")
        st.write("Or check your `.env` file to ensure `IMAGE_SERVER` is set correctly.")

if __name__ == "__main__":
    main()
