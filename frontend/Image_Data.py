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

def check_image_server_status():
    """Check if the image server is available."""
    # Get server URL from environment variable (matching image_server.py)
    image_server_url = os.getenv("IMAGE_SERVER", "http://localhost:8888")
    
    # If running in Docker container, try multiple approaches
    if os.getenv("DOCKER_CONTAINER") == "true":
        # List of URLs to try in order
        urls_to_try = [
            image_server_url,  # Configured URL (likely host.docker.internal:8888)
            "http://localhost:8888",  # localhost fallback
            "http://127.0.0.1:8888",  # IP fallback
            "http://image-server:8888",  # Container name (if image server is in same compose)
        ]
        
        for url in urls_to_try:
            try:
                response = requests.head(url, timeout=2)
                if response.status_code == 200:
                    return True
            except (requests.exceptions.RequestException, requests.exceptions.Timeout):
                continue
        return False
    else:
        # Running outside Docker, use the configured URL
        try:
            response = requests.head(image_server_url, timeout=3)
            return True if response.status_code == 200 else False
        except (requests.exceptions.RequestException, requests.exceptions.Timeout):
            return False

def check_vista3d_server_status():
    """Check if the Vista3D server is available."""
    # Get server URL from environment variable
    vista3d_server_url = os.getenv("VISTA3D_SERVER", "http://localhost:8000")
    
    # If running in Docker container, try multiple approaches
    if os.getenv("DOCKER_CONTAINER") == "true":
        # List of URLs to try in order
        urls_to_try = [
            vista3d_server_url,  # Configured URL (likely host.docker.internal:8000)
            "http://localhost:8000",  # localhost fallback
            "http://127.0.0.1:8000",  # IP fallback
        ]
        
        for base_url in urls_to_try:
            try:
                response = requests.get(f"{base_url}/v1/vista3d/info", timeout=3)
                if response.status_code == 200:
                    return True
                # Log the specific error for debugging
                print(f"Vista3D status check - {base_url}: HTTP {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"Vista3D status check - {base_url}: {type(e).__name__}: {e}")
                continue
        return False
    else:
        # Running outside Docker, use the configured URL
        try:
            response = requests.get(f"{vista3d_server_url}/v1/vista3d/info", timeout=5)
            return True if response.status_code == 200 else False
        except (requests.exceptions.RequestException, requests.exceptions.Timeout):
            return False



def render_server_status_sidebar():
    """Render server status message in sidebar."""
    
    if check_image_server_status():
        image_server_url = os.getenv("IMAGE_SERVER", "http://localhost:8888")
        
        st.sidebar.info(f"🖥️ **Image Server**  \n🟢 Online • {image_server_url}")
    else:
        st.sidebar.error(f"🖥️ **Image Server**  \n❌ Offline  \nStart with: `python utils/image_server.py`")
    
    # Vista3D Server Status
    vista3d_server_url = os.getenv("VISTA3D_SERVER", "http://localhost:8000")
    if check_vista3d_server_status():
        st.sidebar.info(f"🧠 **Vista3D Server**  \n🟢 Online • {vista3d_server_url}")
    else:
        st.sidebar.error(f"🧠 **Vista3D Server**  \n❌ Offline • {vista3d_server_url}")

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
    external_image_server_url = os.getenv("EXTERNAL_IMAGE_SERVER", os.getenv("IMAGE_SERVER", "http://localhost:8888"))
    
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
