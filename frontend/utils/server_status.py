
import streamlit as st
import os
import requests

def check_image_server_status():
    """Check if the image server is available."""
    # Get server URL from environment variable (matching image_server.py)
    image_server_url = os.getenv("IMAGE_SERVER", "http://localhost:8888")
    
    # If running in Docker container, try multiple approaches
    if os.getenv("DOCKER_CONTAINER") == "true":
        # List of URLs to try in order of preference for health checks
        urls_to_try = [
            "http://image-server:8888",  # Container name (primary for Docker Compose)
            image_server_url,  # Configured URL
            "http://localhost:8888",  # localhost fallback
            "http://127.0.0.1:8888",  # IP fallback
        ]
        
        for url in urls_to_try:
            try:
                response = requests.head(url, timeout=2)
                if response.status_code == 200:
                    # Keep the external URL for browser access, don't change IMAGE_SERVER
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
        # List of URLs to try in order of preference
        urls_to_try = [
            vista3d_server_url,  # Configured URL (likely host.docker.internal:8000)
            "http://vista3d-server:8000",  # Container name (if Vista3D is in same compose)
            "http://localhost:8000",  # localhost fallback
            "http://127.0.0.1:8000",  # IP fallback
        ]
        
        for base_url in urls_to_try:
            try:
                response = requests.get(f"{base_url}/v1/vista3d/info", timeout=3)
                if response.status_code == 200:
                    # Keep the configured URL for browser access, don't change VISTA3D_SERVER
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
        # Prioritize EXTERNAL_IMAGE_SERVER for display if available, otherwise use IMAGE_SERVER
        display_image_server_url = os.getenv("EXTERNAL_IMAGE_SERVER", os.getenv("IMAGE_SERVER", "http://localhost:8888"))

        st.sidebar.info(f"""🖥️ **Image Server**  
✅ Online • {display_image_server_url}""")
    else:
        st.sidebar.error(f"""🖥️ **Image Server**  
❌ Offline  
Start with: `python utils/image_server.py`""")

    # Vista3D Server Status
    vista3d_server_url = os.getenv("VISTA3D_SERVER", "http://localhost:8000")
    if check_vista3d_server_status():
        st.sidebar.info(f"""🫁 **Vista3D Server**  
✅ Online • {vista3d_server_url}""")
    else:
        st.sidebar.error(f"""🫁 **Vista3D Server**  
❌ Offline • {vista3d_server_url}""")
