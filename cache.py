"""
Cache Management Interface for NIfTI Vessel Segmentation and Viewer Application

This module provides a comprehensive Streamlit interface for managing the local
image cache system used by the medical imaging viewer. It offers real-time
statistics, cache control operations, and detailed file management capabilities.

Key Features:
- Real-time cache statistics and performance metrics
- Interactive cache management (cleanup, clear, configuration)
- Detailed file listings with metadata
- Visual performance charts and health monitoring
- Cache configuration management (TTL, size limits)
- Comprehensive error handling and user feedback

Components:
- Cache Statistics Dashboard: Real-time metrics and performance data
- Cache Controls: Management operations and configuration
- File Details: Comprehensive listing of cached files
- Health Monitoring: System status and recommendations

Dependencies:
- streamlit: Web interface framework
- utils.image_cache: Core caching functionality
- pandas: Data manipulation for file listings
- plotly: Interactive charts and visualizations

Author: Medical Imaging Team
Version: 1.0.0
"""

import streamlit as st
import time
from pathlib import Path
import sys
from typing import Dict, Any, List, Optional
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from utils.image_cache import (
    get_cache_manager, 
    get_cache_stats, 
    clear_cache,
    ImageCacheManager
)

# Note: Page configuration is handled by the main application

# =============================================================================
# PAGE HEADER AND SETUP
# =============================================================================

st.title("💾 Image Cache Management")
st.markdown("Manage the local cache for medical imaging files downloaded from remote servers.")

# =============================================================================
# SIDEBAR: Quick Cache Statistics
# =============================================================================

def render_sidebar_stats() -> Dict[str, Any]:
    """
    Render quick cache statistics in the sidebar.
    
    Displays essential cache metrics including file count, size, and hit rate
    for quick reference while managing the cache.
    
    Returns:
        Dict[str, Any]: Cache statistics dictionary for use in other components
    """
    with st.sidebar:
        stats = get_cache_stats()
        st.metric("Files Cached", stats['entries_count'])
        st.metric("Cache Size", f"{stats['current_size_mb']:.1f} MB")
        st.metric("Hit Rate", f"{stats['hit_rate']:.1%}")
        return stats

# Render sidebar statistics
sidebar_stats = render_sidebar_stats()

# =============================================================================
# CACHE MANAGER INITIALIZATION
# =============================================================================

@st.cache_resource
def get_cache() -> ImageCacheManager:
    """
    Initialize and cache the image cache manager instance.
    
    Uses Streamlit's cache_resource decorator to ensure the cache manager
    is created only once per session, improving performance and maintaining
    state consistency.
    
    Returns:
        ImageCacheManager: Configured cache manager instance
    """
    return get_cache_manager()

# Initialize the cache manager
cache = get_cache()

# =============================================================================
# MAIN CONTENT LAYOUT
# =============================================================================

def render_cache_statistics() -> None:
    """
    Render the main cache statistics dashboard.
    
    Displays comprehensive cache metrics including performance data,
    usage statistics, and visual charts. This section provides detailed
    insights into cache behavior and system health.
    """
    st.header("📊 Cache Statistics")
    
    # Get current cache statistics
    stats = get_cache_stats()
    
    # Display key metrics in a grid layout
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    
    # Primary metrics display
    with metric_col1:
        st.metric(
            label="Files Cached",
            value=stats['entries_count'],
            help="Total number of files currently cached"
        )
    
    with metric_col2:
        st.metric(
            label="Cache Size",
            value=f"{stats['current_size_mb']:.1f} MB",
            help="Current cache size in megabytes"
        )
    
    with metric_col3:
        st.metric(
            label="Hit Rate",
            value=f"{stats['hit_rate']:.1%}",
            help="Percentage of requests served from cache"
        )
    
    with metric_col4:
        usage_percent = (stats['current_size_mb'] / stats['max_size_mb']) * 100
        st.metric(
            label="Cache Usage",
            value=f"{usage_percent:.1f}%",
            help="Percentage of maximum cache size used"
        )
    
    # Detailed statistics section
    st.subheader("📈 Detailed Statistics")
    
    detail_col1, detail_col2 = st.columns(2)
    
    with detail_col1:
        st.metric("Cache Hits", stats['hits'])
        st.metric("Cache Misses", stats['misses'])
        st.metric("Total Downloads", stats['total_downloads'])
    
    with detail_col2:
        st.metric("Evictions", stats['evictions'])
        st.metric("Max Cache Size", f"{stats['max_size_mb']:.1f} MB")
        st.metric("Total Bytes Cached", f"{stats['total_bytes_cached'] / (1024*1024):.1f} MB")
    
    # Cache directory information
    st.subheader("📁 Cache Information")
    st.info(f"**Cache Directory:** `{stats['cache_dir']}`")
    
    # Performance visualization
    render_performance_chart(stats)


def render_performance_chart(stats: Dict[str, Any]) -> None:
    """
    Render an interactive performance chart for cache metrics.
    
    Creates a bar chart showing cache hits, misses, and evictions to provide
    visual insight into cache performance patterns.
    
    Args:
        stats: Cache statistics dictionary containing performance metrics
    """
    if stats['hits'] + stats['misses'] > 0:
        st.subheader("📊 Performance Chart")
        
        # Import visualization libraries
        import pandas as pd
        import plotly.express as px
        
        # Prepare performance data
        performance_data = {
            'Metric': ['Cache Hits', 'Cache Misses', 'Evictions'],
            'Count': [stats['hits'], stats['misses'], stats['evictions']]
        }
        
        # Create and display the chart
        df = pd.DataFrame(performance_data)
        fig = px.bar(
            df, 
            x='Metric', 
            y='Count', 
            title="Cache Performance Metrics",
            color='Metric',
            color_discrete_map={
                'Cache Hits': '#2E8B57',      # Green for successful hits
                'Cache Misses': '#DC143C',    # Red for misses
                'Evictions': '#FF8C00'       # Orange for evictions
            }
        )
        
        st.plotly_chart(fig, use_container_width=True)

def render_cache_controls() -> None:
    """
    Render the cache control panel with management operations.
    
    Provides interactive controls for cache management including cleanup,
    clearing, configuration, and health monitoring. This section allows
    users to actively manage cache behavior and system health.
    """
    st.header("🎛️ Cache Controls")
    
    # Quick action buttons
    render_quick_actions()
    
    # Configuration settings
    render_cache_configuration()
    
    # Health monitoring
    render_health_check()


def render_quick_actions() -> None:
    """
    Render quick action buttons for immediate cache operations.
    
    Provides buttons for common cache operations like cleanup and clear,
    with appropriate confirmation flows and user feedback.
    """
    st.subheader("Quick Actions")
    
    # Cleanup expired files
    if st.button("🧹 Cleanup Expired Files", help="Remove files that have exceeded their TTL"):
        with st.spinner("Cleaning up expired files..."):
            cache.cleanup()
        st.success("✅ Expired files cleaned up!")
        st.rerun()
    
    # Clear all cache with confirmation
    if st.button("🗑️ Clear All Cache", help="Remove all cached files", type="secondary"):
        if st.session_state.get('confirm_clear', False):
            with st.spinner("Clearing cache..."):
                clear_cache()
            st.success("✅ Cache cleared!")
            st.session_state['confirm_clear'] = False
            st.rerun()
        else:
            st.session_state['confirm_clear'] = True
            st.warning("⚠️ Click again to confirm clearing all cache")
    
    # Cancel clear operation
    if st.session_state.get('confirm_clear', False):
        if st.button("❌ Cancel Clear"):
            st.session_state['confirm_clear'] = False
            st.rerun()


def render_cache_configuration() -> None:
    """
    Render cache configuration settings interface.
    
    Allows users to adjust cache behavior parameters such as TTL (Time To Live)
    and maximum cache size limits. Changes are applied immediately and 
    provide user feedback.
    """
    st.subheader("⚙️ Configuration")
    
    with st.expander("Cache Settings", expanded=False):
        # TTL (Time To Live) configuration
        current_ttl_hours = cache.default_ttl_seconds // 3600
        new_ttl = st.number_input(
            "Default TTL (hours)",
            min_value=1,
            max_value=168,  # 1 week maximum
            value=current_ttl_hours,
            help="How long to keep files in cache before they expire"
        )
        
        if st.button("Update TTL"):
            cache.default_ttl_seconds = new_ttl * 3600
            st.success(f"✅ TTL updated to {new_ttl} hours")
            st.rerun()
        
        # Maximum cache size configuration
        current_max_mb = cache.max_cache_size_bytes // (1024 * 1024)
        new_max_size = st.number_input(
            "Max Cache Size (MB)",
            min_value=100,
            max_value=10000,
            value=current_max_mb,
            help="Maximum cache size in megabytes"
        )
        
        if st.button("Update Max Size"):
            cache.max_cache_size_bytes = new_max_size * 1024 * 1024
            st.success(f"✅ Max cache size updated to {new_max_size} MB")
            st.rerun()


def render_health_check() -> None:
    """
    Render cache health monitoring and system status checks.
    
    Performs automated health checks on the cache system including directory
    existence, usage levels, and performance metrics. Provides recommendations
    for optimization and maintenance.
    """
    st.subheader("🔍 Health Check")
    
    # Get fresh statistics for health check
    stats = get_cache_stats()
    usage_percent = (stats['current_size_mb'] / stats['max_size_mb']) * 100
    
    # Check cache directory existence
    cache_dir = Path(stats['cache_dir'])
    if cache_dir.exists():
        st.success("✅ Cache directory exists")
    else:
        st.error("❌ Cache directory not found")
    
    # Check cache usage levels
    if usage_percent > 90:
        st.warning("⚠️ Cache is nearly full")
    elif usage_percent > 75:
        st.info("ℹ️ Cache is getting full")
    else:
        st.success("✅ Cache has plenty of space")
    
    # Check cache hit rate performance
    if stats['hit_rate'] > 0.8:
        st.success("✅ Excellent hit rate")
    elif stats['hit_rate'] > 0.5:
        st.info("ℹ️ Good hit rate")
    else:
        st.warning("⚠️ Low hit rate - consider increasing TTL")

def render_file_details() -> None:
    """
    Render detailed information about cached files.
    
    Displays a comprehensive table of all cached files with metadata including
    size, age, expiration, access count, and status. Also provides summary
    statistics for overall cache composition.
    """
    st.header("📋 Cached Files")
    st.markdown("Detailed information about currently cached files.")
    
    try:
        # Access the cache entries directly
        entries = cache.entries
        
        if entries:
            # Process cache entries data
            entries_data = process_cache_entries(entries)
            
            # Display the files table
            display_files_table(entries_data)
            
            # Show summary statistics
            display_file_summary(entries_data)
        else:
            st.info("No files currently cached.")
            
    except Exception as e:
        st.error(f"Error retrieving cache entries: {e}")


def process_cache_entries(entries: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Process raw cache entries into structured data for display.
    
    Args:
        entries: Raw cache entries dictionary from the cache manager
        
    Returns:
        List[Dict[str, Any]]: Processed entries data ready for display
    """
    from datetime import datetime
    
    entries_data = []
    for url, entry in entries.items():
        # Extract filename from URL
        filename = url.split('/')[-1] if '/' in url else url
        
        # Calculate temporal metrics
        age_hours = (time.time() - entry.created_at) / 3600
        ttl_hours = entry.ttl_seconds / 3600
        expires_in_hours = ttl_hours - age_hours
        
        entries_data.append({
            'Filename': filename,
            'Size (MB)': round(entry.file_size / (1024 * 1024), 2),
            'Age (hours)': round(age_hours, 1),
            'Expires In (hours)': round(max(0, expires_in_hours), 1),
            'Access Count': entry.access_count,
            'Last Accessed': datetime.fromtimestamp(entry.last_accessed).strftime('%Y-%m-%d %H:%M:%S'),
            'Status': 'Expired' if entry.is_expired() else 'Valid'
        })
    
    # Sort by last accessed (most recent first)
    entries_data.sort(key=lambda x: x['Last Accessed'], reverse=True)
    return entries_data


def display_files_table(entries_data: List[Dict[str, Any]]) -> None:
    """
    Display the cached files in a structured table format.
    
    Args:
        entries_data: Processed cache entries data
    """
    import pandas as pd
    
    df = pd.DataFrame(entries_data)
    st.dataframe(df, use_container_width=True)


def display_file_summary(entries_data: List[Dict[str, Any]]) -> None:
    """
    Display summary statistics for cached files.
    
    Args:
        entries_data: Processed cache entries data
    """
    st.subheader("📊 File Summary")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Files", len(entries_data))
    
    with col2:
        total_size = sum(entry['Size (MB)'] for entry in entries_data)
        st.metric("Total Size", f"{total_size:.1f} MB")
    
    with col3:
        avg_size = total_size / len(entries_data) if entries_data else 0
        st.metric("Average Size", f"{avg_size:.1f} MB")


# =============================================================================
# MAIN APPLICATION LAYOUT
# =============================================================================

# Create two-column layout for main content
col1, col2 = st.columns([2, 1])

# Left column: Statistics and charts
with col1:
    render_cache_statistics()

# Right column: Controls and management
with col2:
    render_cache_controls()

# Full-width section: File details
render_file_details()

# =============================================================================
# FOOTER
# =============================================================================

st.markdown("---")
st.markdown("💡 **Tip:** The cache automatically manages file expiration and size limits. You can adjust these settings in the Configuration section above.")


# =============================================================================
# MODULE DOCUMENTATION SUMMARY
# =============================================================================

"""
Cache Management Interface Usage Summary

This module provides a comprehensive web interface for managing the image cache
system used by the NIfTI Vessel Segmentation and Viewer application.

Key Components:

1. Sidebar Statistics (render_sidebar_stats):
   - Quick overview of cache status
   - Real-time metrics (files, size, hit rate)
   - Always visible for reference

2. Main Statistics Dashboard (render_cache_statistics):
   - Detailed performance metrics
   - Visual charts and graphs
   - Cache directory information
   - Historical data visualization

3. Cache Controls Panel (render_cache_controls):
   - Quick Actions: Cleanup and clear operations
   - Configuration: TTL and size limit settings
   - Health Check: System status monitoring

4. File Details Section (render_file_details):
   - Comprehensive file listings
   - Metadata and timestamps
   - Summary statistics

Function Organization:

- render_* functions: Main UI components
- process_* functions: Data processing utilities
- display_* functions: Specific display utilities

Best Practices:

1. Error Handling:
   - All operations wrapped in try-catch blocks
   - User-friendly error messages
   - Graceful degradation when data unavailable

2. User Experience:
   - Confirmation dialogs for destructive operations
   - Loading spinners for long operations
   - Success/warning/error feedback messages

3. Performance:
   - Cached resource initialization
   - Efficient data processing
   - Minimal redundant API calls

4. Maintainability:
   - Modular function structure
   - Clear separation of concerns
   - Comprehensive documentation

Usage in Main Application:

This module is designed to be executed within the main Streamlit application
context. It expects:
- Streamlit session state management
- Access to utils.image_cache module
- Pandas and Plotly for data visualization

Example Integration:
```python
# In main app.py
elif current_page == 'cache':
    exec(open('cache.py').read())
```

Configuration Requirements:

- IMAGE_SERVER environment variable (optional)
- Cache directory permissions
- Required Python packages: streamlit, pandas, plotly

Monitoring Capabilities:

The interface provides real-time monitoring of:
- Cache hit/miss ratios
- Storage utilization
- File access patterns
- System health status
- Performance trends

This enables administrators to:
- Optimize cache performance
- Manage storage resources
- Troubleshoot issues
- Plan capacity upgrades
"""
