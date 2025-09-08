"""
Navigation Component for NIfTI Vessel Segmentation and Viewer Application

This module provides a reusable navigation system for Streamlit applications,
specifically designed for the medical imaging viewer application. It handles
sidebar navigation, page routing, and session state management.

Key Features:
- Centralized navigation configuration
- Reusable navigation components
- Session state management
- Dynamic navigation item management
- Type-safe navigation items

Example Usage:
    Basic usage in main application:
    ```python
    from utils.navigation import render_navigation
    
    # Render navigation and get instance
    nav = render_navigation()
    
    # Route based on current page
    current_page = nav.get_current_page()
    if current_page == 'home':
        render_home_page()
    elif current_page == 'niivue':
        render_niivue_page()
    ```
    
    Advanced usage with custom navigation:
    ```python
    from utils.navigation import Navigation
    
    # Create custom navigation
    nav = Navigation()
    nav.add_item("admin", "Admin Panel", "admin")
    nav.render_sidebar()
    ```

Author: Medical Imaging Team
Version: 1.0.0
"""

import streamlit as st
from typing import Dict, List, Optional
import base64
from pathlib import Path


class NavigationItem:
    """
    Represents a single navigation menu item.
    
    A navigation item consists of a unique key, display label, icon, and
    the target page key for routing purposes.
    
    Attributes:
        key (str): Unique identifier for the navigation item (used for Streamlit button keys)
        label (str): Human-readable label displayed in the navigation
        icon (str): Emoji, icon character, or image path displayed before the label
        page_key (str): Target page identifier used for routing
        is_image (bool): Whether the icon is an image file path
    
    Example:
        >>> item = NavigationItem("viewer", "Medical Viewer", "niivue")
        >>> print(item.display_text)
        "Medical Viewer"
        
        >>> item = NavigationItem("about", "About", "home", "assets/HPE.png", is_image=True)
    """
    
    def __init__(self, key: str, label: str, page_key: str, icon: str = "", is_image: bool = False):
        """
        Initialize a navigation item.
        
        Args:
            key: Unique identifier for the navigation item
            label: Display label for the navigation button
            page_key: Page identifier for routing (e.g., "home", "niivue")
            icon: Emoji, icon character, or image path (e.g., "🩻", "ℹ️", "assets/HPE.png") - optional
            is_image: Whether the icon is an image file path
        
        Raises:
            ValueError: If required parameters are empty or None
        """
        if not all([key, label, page_key]):
            raise ValueError("Required parameters (key, label, page_key) must be non-empty")
            
        self.key = key
        self.label = label
        self.icon = icon
        self.page_key = page_key
        self.is_image = is_image
        
    @property
    def display_text(self) -> str:
        """
        Get the formatted display text with icon and label.
        
        Returns:
            str: Formatted text with icon and label if icon exists, otherwise just the label
        
        Example:
            >>> item = NavigationItem("cache", "Cache Management", "cache", "💾")
            >>> item.display_text
            "💾 Cache Management"
            
            >>> item = NavigationItem("about", "About", "home")
            >>> item.display_text
            "About"
        """
        if self.icon:
            return f"{self.icon} {self.label}"
        return self.label
    
    def __repr__(self) -> str:
        """Return string representation of the navigation item."""
        return f"NavigationItem(key='{self.key}', label='{self.label}', icon='{self.icon}', page_key='{self.page_key}')"


class Navigation:
    """
    Main navigation component for the Streamlit application.
    
    This class manages the navigation state, renders navigation UI elements,
    and provides methods for dynamic navigation management. It automatically
    handles Streamlit session state for page routing.
    
    The navigation system uses a sidebar with buttons for each navigation item.
    When a button is clicked, the current page is updated in the session state
    and the page is rerun to reflect the change.
    
    Default Navigation Items:
        - About: Application information and welcome page
        - NiiVue Viewer: Medical image viewer interface
    
    Attributes:
        items (List[NavigationItem]): List of navigation items
    
    Example:
        >>> nav = Navigation()
        >>> nav.render_sidebar()  # Renders navigation in Streamlit sidebar
        >>> current = nav.get_current_page()  # Get current active page
        >>> nav.add_item("settings", "Settings", "settings")  # Add new item
    """
    
    def __init__(self):
        """
        Initialize the navigation component with default items.
        
        Sets up the default navigation structure and initializes the
        Streamlit session state if not already present.
        """
        self.items: List[NavigationItem] = [
            NavigationItem("about", "About", "home"),
            NavigationItem("niivue", "NiiVue Viewer", "niivue"),
        ]
        
        # Initialize session state for navigation if not exists
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 'home'

    def get_logo_base64(self) -> str:
        """
        Get the HPE-NVIDIA logo as a base64 encoded string for HTML embedding.

        Returns:
            str: Base64 encoded logo image data
        """
        try:
            logo_path = Path(__file__).parent.parent / "assets" / "HPE-NVIDIA.png"
            if logo_path.exists():
                with open(logo_path, "rb") as f:
                    return base64.b64encode(f.read()).decode()
            else:
                return ""
        except Exception:
            return ""
    
    def navigate_to(self, page: str) -> None:
        """
        Navigate to a specific page by updating session state.
        
        This method updates the current page in Streamlit's session state
        and triggers a rerun to reflect the navigation change.
        
        Args:
            page: The target page key to navigate to
            
        Example:
            >>> nav = Navigation()
            >>> nav.navigate_to('niivue')  # Navigate to NiiVue viewer
        """
        st.session_state.current_page = page
        st.rerun()
    
    def render_sidebar(self) -> None:
        """
        Render navigation buttons in the Streamlit sidebar.
        
        Creates a button for each navigation item in the sidebar. When a button
        is clicked, it automatically navigates to the corresponding page.
        All buttons use full container width for consistent appearance.
        
        Note:
            This method should be called within the Streamlit app context.
            It uses st.sidebar context manager internally.
            
        Example:
            >>> nav = Navigation()
            >>> nav.render_sidebar()  # Renders all navigation buttons
        """
        with st.sidebar:
            # Add HPE-NVIDIA logo at the top - full sidebar width
            logo_b64 = self.get_logo_base64()
            if logo_b64:
                st.markdown(f"""
                    <div style="width: 100%; margin: 0; padding: 0; overflow: hidden;">
                        <img src="data:image/png;base64,{logo_b64}" style="width: 100%; height: auto; display: block;">
                    </div>
                """, unsafe_allow_html=True)
            else:
                # Fallback to regular st.image if base64 fails
                st.image("assets/HPE-NVIDIA.png", use_container_width=True)
            # Add spacing to prevent styling conflicts with other sidebar elements
            st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

            for item in self.items:
                if item.is_image and item.icon:
                    # For image icons, create a container with image and button
                    col1, col2 = st.columns([0.2, 0.8])
                    with col1:
                        st.image(item.icon, width=40)
                    with col2:
                        if st.button(item.label, key=item.key, use_container_width=True):
                            self.navigate_to(item.page_key)
                else:
                    # For text-only buttons (no icons), use just the label
                    if st.button(item.label, key=item.key, use_container_width=True):
                        self.navigate_to(item.page_key)
    
    def get_current_page(self) -> str:
        """
        Get the current active page from session state.
        
        Returns:
            str: The page key of the currently active page
            
        Example:
            >>> nav = Navigation()
            >>> current = nav.get_current_page()
            >>> print(current)  # 'home', 'niivue', 'cache', etc.
        """
        return st.session_state.current_page
    
    def is_current_page(self, page: str) -> bool:
        """
        Check if the given page is currently active.
        
        Args:
            page: Page key to check
            
        Returns:
            bool: True if the page is currently active, False otherwise
            
        Example:
            >>> nav = Navigation()
            >>> if nav.is_current_page('niivue'):
            ...     print("Currently viewing NiiVue")
        """
        return st.session_state.current_page == page
    
    def add_item(self, key: str, label: str, page_key: str, icon: str = "", is_image: bool = False) -> None:
        """
        Add a new navigation item to the navigation menu.
        
        Args:
            key: Unique identifier for the navigation item
            label: Display label for the button
            page_key: Target page for navigation
            icon: Emoji, icon character, or image path (optional)
            is_image: Whether the icon is an image file path
            
        Raises:
            ValueError: If any parameter is empty or if key already exists
            
        Example:
            >>> nav = Navigation()
            >>> nav.add_item("settings", "Settings", "settings")
            >>> nav.add_item("help", "Help", "help", "❓")
            >>> nav.add_item("logo", "Logo", "logo", "assets/logo.png", is_image=True)
        """
        # Check if key already exists
        if self.get_item_by_key(key) is not None:
            raise ValueError(f"Navigation item with key '{key}' already exists")
            
        new_item = NavigationItem(key, label, page_key, icon, is_image)
        self.items.append(new_item)
    
    def remove_item(self, key: str) -> bool:
        """
        Remove a navigation item by its key.
        
        Args:
            key: The key of the navigation item to remove
            
        Returns:
            bool: True if item was found and removed, False if not found
            
        Example:
            >>> nav = Navigation()
            >>> success = nav.remove_item("cache")
            >>> if success:
            ...     print("Cache navigation item removed")
        """
        for i, item in enumerate(self.items):
            if item.key == key:
                self.items.pop(i)
                return True
        return False
    
    def get_item_by_key(self, key: str) -> Optional[NavigationItem]:
        """
        Get a navigation item by its unique key.
        
        Args:
            key: The key of the navigation item to find
            
        Returns:
            NavigationItem or None: The navigation item if found, None otherwise
            
        Example:
            >>> nav = Navigation()
            >>> item = nav.get_item_by_key("niivue")
            >>> if item:
            ...     print(f"Found: {item.display_text}")
        """
        for item in self.items:
            if item.key == key:
                return item
        return None
    
    def get_item_by_page(self, page_key: str) -> Optional[NavigationItem]:
        """
        Get a navigation item by its page key.
        
        Args:
            page_key: The page key of the navigation item to find
            
        Returns:
            NavigationItem or None: The navigation item if found, None otherwise
            
        Example:
            >>> nav = Navigation()
            >>> item = nav.get_item_by_page("home")
            >>> if item:
            ...     print(f"Home page item: {item.label}")
        """
        for item in self.items:
            if item.page_key == page_key:
                return item
        return None
    
    def get_all_pages(self) -> List[str]:
        """
        Get a list of all available page keys.
        
        Returns:
            List[str]: List of all page keys in the navigation
            
        Example:
            >>> nav = Navigation()
            >>> pages = nav.get_all_pages()
            >>> print(pages)  # ['home', 'niivue', 'cache']
        """
        return [item.page_key for item in self.items]
    
    def get_navigation_count(self) -> int:
        """
        Get the total number of navigation items.
        
        Returns:
            int: Number of navigation items
            
        Example:
            >>> nav = Navigation()
            >>> count = nav.get_navigation_count()
            >>> print(f"Total navigation items: {count}")
        """
        return len(self.items)
    


# Factory Functions

def create_navigation() -> Navigation:
    """
    Factory function to create a navigation instance.
    
    This is a convenience function that creates a new Navigation instance
    with default configuration. Use this when you need a navigation instance
    but want to customize it before rendering.
    
    Returns:
        Navigation: A new navigation instance with default items
        
    Example:
        >>> nav = create_navigation()
        >>> nav.add_item("admin", "Admin", "admin")
        >>> nav.render_sidebar()
    """
    return Navigation()


def render_navigation() -> Navigation:
    """
    Convenience function to create and render navigation in sidebar.
    
    This is the most common way to use the navigation component. It creates
    a navigation instance with default items and immediately renders it in
    the Streamlit sidebar.
    
    Returns:
        Navigation: The navigation instance for further manipulation
        
    Example:
        Basic usage:
        >>> nav = render_navigation()
        >>> current_page = nav.get_current_page()
        
        With additional customization:
        >>> nav = render_navigation()
        >>> nav.add_item("reports", "Reports", "📊", "reports")
        
    Note:
        This function should be called early in your Streamlit app,
        typically right after st.set_page_config().
    """
    nav = create_navigation()
    nav.render_sidebar()
    return nav


# Module Usage Summary
"""
Quick Reference:

1. Simple Usage (Most Common):
   ```python
   from utils.navigation import render_navigation
   nav = render_navigation()
   current_page = nav.get_current_page()
   ```

2. Custom Navigation:
   ```python
   from utils.navigation import Navigation
   nav = Navigation()
   nav.add_item("custom", "Custom Page", "custom")
   nav.add_item("logo", "Logo Page", "logo", "assets/logo.png", is_image=True)
   nav.render_sidebar()
   ```

3. Navigation Management:
   ```python
   # Check current page
   if nav.is_current_page('niivue'):
       # Render NiiVue content
   
   # Get all available pages
   pages = nav.get_all_pages()
   
   # Remove navigation item
   nav.remove_item("cache")
   ```

4. Error Handling:
   ```python
   try:
       nav.add_item("", "Invalid", "❌", "invalid")
   except ValueError as e:
       print(f"Navigation error: {e}")
   ```
"""
