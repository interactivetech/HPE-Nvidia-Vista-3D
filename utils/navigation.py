"""
Navigation component for the NIfTI Vessel Segmentation and Viewer application.

This module provides reusable navigation functionality that can be used
across different pages of the application.
"""

import streamlit as st
from typing import Dict, List, Optional


class NavigationItem:
    """Represents a single navigation item."""
    
    def __init__(self, key: str, label: str, icon: str, page_key: str):
        self.key = key
        self.label = label
        self.icon = icon
        self.page_key = page_key
        
    @property
    def display_text(self) -> str:
        """Get the display text with icon and label."""
        return f"{self.icon} {self.label}"


class Navigation:
    """Navigation component for the application."""
    
    def __init__(self):
        self.items: List[NavigationItem] = [
            NavigationItem("about", "About", "ℹ️", "home"),
            NavigationItem("niivue", "NiiVue Viewer", "🩻", "niivue"),
            NavigationItem("cache", "Cache Management", "💾", "cache"),
        ]
        
        # Initialize session state for navigation if not exists
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 'home'
    
    def navigate_to(self, page: str) -> None:
        """Navigate to a specific page."""
        st.session_state.current_page = page
        st.rerun()
    
    def render_sidebar(self) -> None:
        """Render the navigation buttons in the sidebar."""
        with st.sidebar:
            for item in self.items:
                if st.button(item.display_text, key=item.key, use_container_width=True):
                    self.navigate_to(item.page_key)
    
    def get_current_page(self) -> str:
        """Get the current active page."""
        return st.session_state.current_page
    
    def is_current_page(self, page: str) -> bool:
        """Check if the given page is the current active page."""
        return st.session_state.current_page == page
    
    def add_item(self, key: str, label: str, icon: str, page_key: str) -> None:
        """Add a new navigation item."""
        new_item = NavigationItem(key, label, icon, page_key)
        self.items.append(new_item)
    
    def remove_item(self, key: str) -> bool:
        """Remove a navigation item by key. Returns True if item was found and removed."""
        for i, item in enumerate(self.items):
            if item.key == key:
                self.items.pop(i)
                return True
        return False
    
    def get_item_by_key(self, key: str) -> Optional[NavigationItem]:
        """Get a navigation item by its key."""
        for item in self.items:
            if item.key == key:
                return item
        return None
    
    def get_item_by_page(self, page_key: str) -> Optional[NavigationItem]:
        """Get a navigation item by its page key."""
        for item in self.items:
            if item.page_key == page_key:
                return item
        return None


def create_navigation() -> Navigation:
    """Factory function to create a navigation instance."""
    return Navigation()


def render_navigation() -> Navigation:
    """
    Convenience function to create and render navigation in sidebar.
    Returns the navigation instance for further use.
    """
    nav = create_navigation()
    nav.render_sidebar()
    return nav
