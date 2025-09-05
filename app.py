import streamlit as st
from pathlib import Path

# Initialize session state for navigation
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'home'

st.set_page_config(
    page_title="NIfTI Vessel Segmentation and Viewer",
    page_icon="🩻",
    layout="wide",
)

# Navigation function
def navigate_to(page):
    st.session_state.current_page = page
    st.rerun()

# Sidebar for controls
with st.sidebar:
    # Navigation
    if st.button("ℹ️ About", use_container_width=True):
        navigate_to('home')
    
    if st.button("🩻 NiiVue Viewer", use_container_width=True):
        navigate_to('niivue')
    
    if st.button("💾 Cache Management", use_container_width=True):
        navigate_to('cache')
    
    if st.button("🧪 PyVista Test", use_container_width=True):
        navigate_to('pyvista')

# Main content based on current page
if st.session_state.current_page == 'home':
    st.title("Vessel Segmentation Viewer")
    st.markdown("Welcome to the NIfTI Vessel Segmentation and Viewer application.")
    st.markdown("Use the sidebar to navigate to different tools and features.")
elif st.session_state.current_page == 'niivue':
    # Import and run NiiVue content
    import sys
    sys.path.append(str(Path(__file__).parent))
    exec(open('NiiVue.py').read())
elif st.session_state.current_page == 'cache':
    # Import and run cache content
    import sys
    sys.path.append(str(Path(__file__).parent))
    exec(open('cache.py').read())
elif st.session_state.current_page == 'pyvista':
    # Import and run PyVista content
    import sys
    sys.path.append(str(Path(__file__).parent))
    exec(open('minimal_pyvista_test.py').read())

