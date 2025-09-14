import streamlit as st
import os
from streamlit_mermaid import st_mermaid
from pathlib import Path

def render_workflow_diagram(mermaid_file_path: str = None, height: int = 600, key: str = "vista3d_workflow"):
    """
    Render the Vista3D workflow diagram using Mermaid.
    
    Args:
        mermaid_file_path: Path to the Mermaid file. If None, uses default path.
        height: Height of the diagram in pixels
        key: Unique key for the Streamlit component
    
    Returns:
        bool: True if diagram was rendered successfully, False otherwise
    """
    if mermaid_file_path is None:
        # Default to conf/vista3d_workflow.mmd relative to project root
        project_root = Path(__file__).parent.parent
        mermaid_file_path = project_root / "conf" / "vista3d_workflow.mmd"
    
    try:
        with open(mermaid_file_path, 'r') as file:
            mermaid_content = file.read()
        
        # Display the Mermaid diagram with full page width styling
        # Add comprehensive CSS to ensure maximum width and better responsiveness
        st.markdown("""
        <style>
        /* Target all possible Mermaid containers for full width */
        .mermaid {
            width: 100vw !important;
            max-width: 100vw !important;
            min-width: 100vw !important;
            margin-left: calc(-50vw + 50%) !important;
            margin-right: calc(-50vw + 50%) !important;
        }
        .stMermaid {
            width: 100vw !important;
            max-width: 100vw !important;
            margin-left: calc(-50vw + 50%) !important;
            margin-right: calc(-50vw + 50%) !important;
        }
        div[data-testid="stMermaid"] {
            width: 100vw !important;
            max-width: 100vw !important;
            margin-left: calc(-50vw + 50%) !important;
            margin-right: calc(-50vw + 50%) !important;
        }
        /* Additional selectors for better coverage */
        .stMermaid > div {
            width: 100vw !important;
            max-width: 100vw !important;
        }
        .mermaid svg {
            width: 100% !important;
            max-width: 100% !important;
        }
        /* Ensure the container itself is full width */
        .main .block-container {
            max-width: 100% !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        /* Custom full-width container styling */
        .full-width-mermaid {
            width: 100vw !important;
            max-width: 100vw !important;
            margin-left: calc(-50vw + 50%) !important;
            margin-right: calc(-50vw + 50%) !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Use full width container with no padding
        with st.container():
            # Add a custom CSS class for this specific container
            st.markdown('<div class="full-width-mermaid">', unsafe_allow_html=True)
            st_mermaid(mermaid_content, height=height, key=key)
            st.markdown('</div>', unsafe_allow_html=True)
        return True
        
    except FileNotFoundError:
        st.error(f"❌ Mermaid file not found at: {mermaid_file_path}")
        st.markdown("Please ensure the file exists in the conf folder.")
        
        # Show example Mermaid content as fallback with full width styling
        st.markdown("### Example Workflow")
        example_mermaid = """
graph TD
    A[Start] --> B[Process]
    B --> C[End]
    """
        st.code(example_mermaid, language="text")
        
        # Apply the same full-width styling to fallback
        st.markdown('<div class="full-width-mermaid">', unsafe_allow_html=True)
        st_mermaid(example_mermaid, height=300, key=f"{key}_fallback")
        st.markdown('</div>', unsafe_allow_html=True)
        return False
        
    except Exception as e:
        st.error(f"❌ Error loading Mermaid file: {str(e)}")
        return False

def render_workflow_section():
    """
    Render the complete workflow section with title and diagram.
    """
    st.header("🔄 Workflow")
    #st.markdown("The diagram below shows the complete Vista3D segmentation workflow:")
    
    # Use full width container for the workflow diagram
    with st.container():
        # Render the workflow diagram with enhanced width
        success = render_workflow_diagram(height=700)  # Increased height for better visibility
    
    if success:
        st.markdown("*Diagram showing the data flow from DICOM images through Vista3D processing to 3D visualization.*")