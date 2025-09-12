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
        
        # Display the Mermaid diagram with enhanced width styling
        # Add CSS to ensure maximum width and better responsiveness
        st.markdown("""
        <style>
        .mermaid {
            width: 100% !important;
            max-width: none !important;
            min-width: 100% !important;
        }
        .stMermaid {
            width: 100% !important;
            max-width: none !important;
        }
        div[data-testid="stMermaid"] {
            width: 100% !important;
            max-width: none !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Use container to ensure full width
        with st.container():
            st_mermaid(mermaid_content, height=height, key=key)
        return True
        
    except FileNotFoundError:
        st.error(f"❌ Mermaid file not found at: {mermaid_file_path}")
        st.markdown("Please ensure the file exists in the conf folder.")
        
        # Show example Mermaid content as fallback
        st.markdown("### Example Workflow")
        example_mermaid = """
graph TD
    A[Start] --> B[Process]
    B --> C[End]
    """
        st.code(example_mermaid, language="text")
        st_mermaid(example_mermaid, height=300, key=f"{key}_fallback")
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