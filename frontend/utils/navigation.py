"""
Navigation Component for Streamlit Applications

Simple navigation system with sidebar buttons and page routing.
"""

import streamlit as st
from typing import Dict, List, Optional
import base64
import json
from pathlib import Path


class NavigationItem:
    """Represents a single navigation menu item."""
    
    def __init__(self, key: str, label: str, page_key: str, icon: str = "", is_image: bool = False):
        if not all([key, label, page_key]):
            raise ValueError("Required parameters (key, label, page_key) must be non-empty")
            
        self.key = key
        self.label = label
        self.icon = icon
        self.page_key = page_key
        self.is_image = is_image
        
    @property
    def display_text(self) -> str:
        """Get the formatted display text with icon and label."""
        if self.icon:
            return f"{self.icon} {self.label}"
        return self.label


class Navigation:
    """Main navigation component for the Streamlit application."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.items: List[NavigationItem] = []
        self.config = {}
        
        # Load navigation configuration
        self._load_config(config_path)
        
        # Initialize session state for navigation if not exists
        default_page = self.config.get('settings', {}).get('default_page', 'home')
        if 'current_page' not in st.session_state:
            st.session_state.current_page = default_page

    def _load_config(self, config_path: Optional[str] = None) -> None:
        """Load navigation configuration from JSON file."""
        try:
            if config_path is None:
                config_path = Path(__file__).parent.parent / "conf" / "navigation_config.json"
            else:
                config_path = Path(config_path)
            
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.config = data.get('navigation', {})
                    
                # Load navigation items from config
                items_config = self.config.get('items', [])
                items_config.sort(key=lambda x: x.get('order', 999))
                
                # Create NavigationItem objects for enabled items
                for item_config in items_config:
                    if item_config.get('enabled', True):
                        nav_item = NavigationItem(
                            key=item_config['key'],
                            label=item_config['label'],
                            page_key=item_config['page_key'],
                            icon=item_config.get('icon', ''),
                            is_image=item_config.get('is_image', False)
                        )
                        self.items.append(nav_item)
            else:
                self._load_default_items()
                
        except Exception as e:
            st.warning(f"Error loading navigation config: {e}. Using default navigation.")
            self._load_default_items()
    
    def _load_default_items(self) -> None:
        """Load default navigation items when config file is not available."""
        self.items = [
            NavigationItem("about", "About", "home"),
            NavigationItem("niivue", "NiiVue Viewer", "niivue"),
        ]
        self.config = {
            'settings': {
                'default_page': 'home',
                'use_container_width': True,
                'show_logo': True,
                'logo_path': 'assets/HPE-NVIDIA.png'
            }
        }

    def get_logo_base64(self) -> str:
        """Get the logo as a base64 encoded string for HTML embedding."""
        try:
            logo_filename = self.config.get('settings', {}).get('logo_path', 'assets/HPE-NVIDIA.png')
            
            if logo_filename.startswith('assets/'):
                logo_path = Path(__file__).parent.parent / logo_filename
            else:
                logo_path = Path(logo_filename)
                
            if logo_path.exists():
                with open(logo_path, "rb") as f:
                    return base64.b64encode(f.read()).decode()
            return ""
        except Exception:
            return ""
    
    def navigate_to(self, page: str) -> None:
        """Navigate to a specific page by updating session state."""
        st.session_state.current_page = page
        st.rerun()
    
    def render_sidebar(self) -> None:
        """Render navigation buttons in the Streamlit sidebar."""
        with st.sidebar:
            # Show logo if enabled in config
            show_logo = self.config.get('settings', {}).get('show_logo', True)
            if show_logo:
                logo_b64 = self.get_logo_base64()
                if logo_b64:
                    st.markdown(f"""
                        <div style="width: 100%; margin: 0; padding: 0; overflow: hidden;">
                            <img src="data:image/png;base64,{logo_b64}" style="width: 100%; height: auto; display: block;">
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    logo_path = self.config.get('settings', {}).get('logo_path', 'assets/HPE-NVIDIA.png')
                    st.image(logo_path, use_container_width=True)
                
                st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

            use_container_width = self.config.get('settings', {}).get('use_container_width', True)

            for item in self.items:
                if item.is_image and item.icon:
                    col1, col2 = st.columns([0.2, 0.8])
                    with col1:
                        st.image(item.icon, width=40)
                    with col2:
                        if st.button(item.label, key=item.key, use_container_width=use_container_width):
                            self.navigate_to(item.page_key)
                else:
                    if st.button(item.display_text, key=item.key, use_container_width=use_container_width):
                        self.navigate_to(item.page_key)
    
    def get_current_page(self) -> str:
        """Get the current active page from session state."""
        return st.session_state.current_page
    
    def is_current_page(self, page: str) -> bool:
        """Check if the given page is currently active."""
        return st.session_state.current_page == page
    
    def add_item(self, key: str, label: str, page_key: str, icon: str = "", is_image: bool = False) -> None:
        """Add a new navigation item to the navigation menu."""
        if self.get_item_by_key(key) is not None:
            raise ValueError(f"Navigation item with key '{key}' already exists")
            
        new_item = NavigationItem(key, label, page_key, icon, is_image)
        self.items.append(new_item)
    
    def get_item_by_key(self, key: str) -> Optional[NavigationItem]:
        """Get a navigation item by its unique key."""
        for item in self.items:
            if item.key == key:
                return item
        return None
    

def render_navigation(config_path: Optional[str] = None) -> Navigation:
    """Create and render navigation in sidebar."""
    nav = Navigation(config_path)
    nav.render_sidebar()
    return nav
