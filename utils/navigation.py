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
import json
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
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the navigation component with items from config or defaults.
        
        Args:
            config_path: Optional path to navigation configuration JSON file.
                        If None, uses default config path: conf/navigation_config.json
        
        Sets up the navigation structure from configuration file and initializes the
        Streamlit session state if not already present.
        """
        self.items: List[NavigationItem] = []
        self.config = {}
        
        # Load navigation configuration
        self._load_config(config_path)
        
        # Initialize session state for navigation if not exists
        default_page = self.config.get('settings', {}).get('default_page', 'home')
        if 'current_page' not in st.session_state:
            st.session_state.current_page = default_page

    def _load_config(self, config_path: Optional[str] = None) -> None:
        """
        Load navigation configuration from JSON file.
        
        Args:
            config_path: Optional path to configuration file. If None, uses default path.
        """
        try:
            if config_path is None:
                # Use default config path relative to this file
                config_path = Path(__file__).parent.parent / "conf" / "navigation_config.json"
            else:
                config_path = Path(config_path)
            
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.config = data.get('navigation', {})
                    
                # Load navigation items from config
                items_config = self.config.get('items', [])
                
                # Sort items by order field
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
                # Config file doesn't exist, use defaults
                self._load_default_items()
                
        except Exception as e:
            # Error loading config, fall back to defaults
            st.warning(f"Error loading navigation config: {e}. Using default navigation.")
            self._load_default_items()
    
    def _load_default_items(self) -> None:
        """
        Load default navigation items when config file is not available.
        """
        self.items = [
            NavigationItem("about", "About", "home"),
            NavigationItem("niivue", "NiiVue Viewer", "niivue"),
            NavigationItem("ply_viewer", "Open3d Viewer", "ply_viewer", "🔺"),
            NavigationItem("dicom", "DICOM Inspector", "dicom"),
        ]
        # Set default config
        self.config = {
            'settings': {
                'default_page': 'home',
                'use_container_width': True,
                'show_logo': True,
                'logo_path': 'assets/HPE-NVIDIA.png'
            }
        }

    def get_logo_base64(self) -> str:
        """
        Get the logo as a base64 encoded string for HTML embedding.
        Uses logo path from configuration or falls back to default.

        Returns:
            str: Base64 encoded logo image data
        """
        try:
            # Get logo path from config or use default
            logo_filename = self.config.get('settings', {}).get('logo_path', 'assets/HPE-NVIDIA.png')
            
            # Handle both relative and absolute paths
            if logo_filename.startswith('assets/'):
                logo_path = Path(__file__).parent.parent / logo_filename
            else:
                logo_path = Path(logo_filename)
                
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
        Uses configuration settings for button appearance and behavior.
        
        Note:
            This method should be called within the Streamlit app context.
            It uses st.sidebar context manager internally.
            
        Example:
            >>> nav = Navigation()
            >>> nav.render_sidebar()  # Renders all navigation buttons
        """
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
                    # Fallback to regular st.image if base64 fails
                    logo_path = self.config.get('settings', {}).get('logo_path', 'assets/HPE-NVIDIA.png')
                    st.image(logo_path, use_container_width=True)
                
                # Add spacing to prevent styling conflicts with other sidebar elements
                st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

            # Get button width setting from config
            use_container_width = self.config.get('settings', {}).get('use_container_width', True)

            for item in self.items:
                if item.is_image and item.icon:
                    # For image icons, create a container with image and button
                    col1, col2 = st.columns([0.2, 0.8])
                    with col1:
                        st.image(item.icon, width=40)
                    with col2:
                        if st.button(item.label, key=item.key, use_container_width=use_container_width):
                            self.navigate_to(item.page_key)
                else:
                    # For text icons or no icons, use display_text which includes icon
                    if st.button(item.display_text, key=item.key, use_container_width=use_container_width):
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
    
    def reload_config(self, config_path: Optional[str] = None) -> None:
        """
        Reload navigation configuration from JSON file.
        
        This method allows for dynamic reloading of the navigation configuration
        without recreating the Navigation instance.
        
        Args:
            config_path: Optional path to configuration file. If None, uses default path.
            
        Example:
            >>> nav = Navigation()
            >>> nav.reload_config()  # Reload from default config
            >>> nav.reload_config("/path/to/custom_nav.json")  # Load custom config
        """
        self.items.clear()
        self.config.clear()
        self._load_config(config_path)
        
        # Update session state default page if needed
        default_page = self.config.get('settings', {}).get('default_page', 'home')
        if 'current_page' not in st.session_state:
            st.session_state.current_page = default_page
    
    def get_config(self) -> Dict:
        """
        Get the current navigation configuration.
        
        Returns:
            Dict: Current navigation configuration
            
        Example:
            >>> nav = Navigation()
            >>> config = nav.get_config()
            >>> print(config.get('settings', {}).get('default_page'))
        """
        return self.config.copy()
    


# Factory Functions

def create_navigation(config_path: Optional[str] = None) -> Navigation:
    """
    Factory function to create a navigation instance.
    
    This is a convenience function that creates a new Navigation instance
    with configuration from specified file or default. Use this when you need 
    a navigation instance but want to customize it before rendering.
    
    Args:
        config_path: Optional path to navigation configuration JSON file
    
    Returns:
        Navigation: A new navigation instance with configured items
        
    Example:
        >>> nav = create_navigation()  # Use default config
        >>> nav.add_item("admin", "Admin", "admin")
        >>> nav.render_sidebar()
        
        >>> nav = create_navigation("custom_nav.json")  # Use custom config
    """
    return Navigation(config_path)


def render_navigation(config_path: Optional[str] = None) -> Navigation:
    """
    Convenience function to create and render navigation in sidebar.
    
    This is the most common way to use the navigation component. It creates
    a navigation instance with configuration and immediately renders it in
    the Streamlit sidebar.
    
    Args:
        config_path: Optional path to navigation configuration JSON file
    
    Returns:
        Navigation: The navigation instance for further manipulation
        
    Example:
        Basic usage:
        >>> nav = render_navigation()  # Use default config
        >>> current_page = nav.get_current_page()
        
        With custom config:
        >>> nav = render_navigation("custom_nav.json")
        >>> current_page = nav.get_current_page()
        
        With additional customization:
        >>> nav = render_navigation()
        >>> nav.add_item("reports", "Reports", "📊", "reports")
        
    Note:
        This function should be called early in your Streamlit app,
        typically right after st.set_page_config().
    """
    nav = create_navigation(config_path)
    nav.render_sidebar()
    return nav


# Module Usage Summary
"""
Quick Reference:

1. Simple Usage (Most Common) - Uses JSON Config:
   ```python
   from utils.navigation import render_navigation
   nav = render_navigation()  # Loads from conf/navigation_config.json
   current_page = nav.get_current_page()
   ```

2. Custom Config File:
   ```python
   from utils.navigation import render_navigation
   nav = render_navigation("path/to/custom_nav.json")
   current_page = nav.get_current_page()
   ```

3. Programmatic Navigation (with config base):
   ```python
   from utils.navigation import Navigation
   nav = Navigation()  # Loads from JSON config first
   nav.add_item("custom", "Custom Page", "custom")  # Add additional items
   nav.render_sidebar()
   ```

4. Configuration Management:
   ```python
   # Reload configuration
   nav.reload_config()
   
   # Get current config
   config = nav.get_config()
   print(config['settings']['default_page'])
   
   # Check current page
   if nav.is_current_page('niivue'):
       # Render NiiVue content
   ```

5. JSON Configuration Structure:
   ```json
   {
     "navigation": {
       "items": [
         {
           "key": "home",
           "label": "Home",
           "page_key": "home",
           "icon": "🏠",
           "enabled": true,
           "order": 1
         }
       ],
       "settings": {
         "default_page": "home",
         "show_logo": true,
         "logo_path": "assets/HPE-NVIDIA.png"
       }
     }
   }
   ```

6. Error Handling:
   ```python
   try:
       nav.add_item("", "Invalid", "❌", "invalid")
   except ValueError as e:
       print(f"Navigation error: {e}")
   ```
"""
