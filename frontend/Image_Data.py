#!/usr/bin/env python3
"""
Image Data Page - Opens the image server URL directly.
"""

import streamlit as st
import streamlit.components.v1 as components
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
    
    # Get image server URL from environment variable
    image_server_url = os.getenv("IMAGE_SERVER", "http://localhost:8888")
    
    # Open the URL in a new tab using components.html (more reliable than st.markdown)
    components.html(f"""
    <script>
        window.open('{image_server_url}', '_blank');
    </script>
    """, height=0)

if __name__ == "__main__":
    main()
