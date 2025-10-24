# Corrected contents for frontend/utils/server_status.py

import streamlit as st
import os
import requests

def check_image_server_status():
    """Check if the image server is available using only the configured URL."""
    # ONLY use the URL provided by the environment.
    image_server_url = os.getenv("IMAGE_SERVER")

    if not image_server_url:
        return False

    try:
        # Use the URL for the health check
        response = requests.head(f"{image_server_url.rstrip('/')}/health", timeout=2)
        return response.status_code == 200
    except (requests.exceptions.RequestException, requests.exceptions.Timeout):
        return False

def check_vista3d_server_status():
    """Check if the Vista3D server is available using only the configured URL."""
    # ONLY use the URL provided by the environment.
    vista3d_server_url = os.getenv("VISTA3D_SERVER")

    # If the variable is not set or is empty, the service is correctly considered offline.
    if not vista3d_server_url:
        return False

    try:
        # Use the full URL for the check
        response = requests.get(f"{vista3d_server_url.rstrip('/')}/v1/vista3d/info", timeout=3)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def render_server_status_sidebar():
    """Render server status message in sidebar."""
    image_server_url = os.getenv("IMAGE_SERVER", "Not Configured")
    if check_image_server_status():
        st.sidebar.info(f"""📥 **Image Server**  
✅ Online • {image_server_url}""")
    else:
        st.sidebar.error(f"""📥 **Image Server**  
❌ Offline • {image_server_url}""")

    vista3d_server_url = os.getenv("VISTA3D_SERVER", "Not Configured")
    if check_vista3d_server_status():
        st.sidebar.info(f"""🫁 **Vista3D Server**  
✅ Online • {vista3d_server_url}""")
    else:
        st.sidebar.error(f"""🫁 **Vista3D Server**  
❌ Offline • {vista3d_server_url}""")