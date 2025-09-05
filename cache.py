import streamlit as st
import time
from pathlib import Path
import sys
from typing import Dict, Any
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

# Note: page config is handled by the main app

st.title("💾 Image Cache Management")
st.markdown("Manage the local cache for medical imaging files downloaded from remote servers.")

# Quick cache stats in sidebar
with st.sidebar:
    stats = get_cache_stats()
    st.metric("Files Cached", stats['entries_count'])
    st.metric("Cache Size", f"{stats['current_size_mb']:.1f} MB")
    st.metric("Hit Rate", f"{stats['hit_rate']:.1%}")

# Initialize cache manager
@st.cache_resource
def get_cache():
    return get_cache_manager()

cache = get_cache()

# Main content layout
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📊 Cache Statistics")
    
    # Get current cache statistics
    stats = get_cache_stats()
    
    # Display key metrics
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    
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
    
    # Detailed statistics
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
    
    # Cache directory info
    st.subheader("📁 Cache Information")
    st.info(f"**Cache Directory:** `{stats['cache_dir']}`")
    
    # Performance chart (if we have enough data)
    if stats['hits'] + stats['misses'] > 0:
        st.subheader("📊 Performance Chart")
        
        # Create a simple performance chart
        import pandas as pd
        import plotly.express as px
        
        performance_data = {
            'Metric': ['Cache Hits', 'Cache Misses', 'Evictions'],
            'Count': [stats['hits'], stats['misses'], stats['evictions']]
        }
        
        df = pd.DataFrame(performance_data)
        fig = px.bar(df, x='Metric', y='Count', 
                    title="Cache Performance Metrics",
                    color='Metric',
                    color_discrete_map={
                        'Cache Hits': '#2E8B57',
                        'Cache Misses': '#DC143C', 
                        'Evictions': '#FF8C00'
                    })
        
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.header("🎛️ Cache Controls")
    
    # Cache management buttons
    st.subheader("Quick Actions")
    
    if st.button("🧹 Cleanup Expired Files", help="Remove files that have exceeded their TTL"):
        with st.spinner("Cleaning up expired files..."):
            cache.cleanup()
        st.success("✅ Expired files cleaned up!")
        st.rerun()
    
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
    
    if st.session_state.get('confirm_clear', False):
        if st.button("❌ Cancel Clear"):
            st.session_state['confirm_clear'] = False
            st.rerun()
    
    # Cache configuration
    st.subheader("⚙️ Configuration")
    
    with st.expander("Cache Settings", expanded=False):
        # TTL configuration
        current_ttl_hours = cache.default_ttl_seconds // 3600
        new_ttl = st.number_input(
            "Default TTL (hours)",
            min_value=1,
            max_value=168,  # 1 week max
            value=current_ttl_hours,
            help="How long to keep files in cache before they expire"
        )
        
        if st.button("Update TTL"):
            cache.default_ttl_seconds = new_ttl * 3600
            st.success(f"✅ TTL updated to {new_ttl} hours")
            st.rerun()
        
        # Max cache size configuration
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
    
    # Cache health check
    st.subheader("🔍 Health Check")
    
    # Check cache directory
    cache_dir = Path(stats['cache_dir'])
    if cache_dir.exists():
        st.success("✅ Cache directory exists")
    else:
        st.error("❌ Cache directory not found")
    
    # Check if cache is full
    if usage_percent > 90:
        st.warning("⚠️ Cache is nearly full")
    elif usage_percent > 75:
        st.info("ℹ️ Cache is getting full")
    else:
        st.success("✅ Cache has plenty of space")
    
    # Check hit rate
    if stats['hit_rate'] > 0.8:
        st.success("✅ Excellent hit rate")
    elif stats['hit_rate'] > 0.5:
        st.info("ℹ️ Good hit rate")
    else:
        st.warning("⚠️ Low hit rate - consider increasing TTL")

# Cache entries details
st.header("📋 Cached Files")
st.markdown("Detailed information about currently cached files.")

# Get detailed cache entries
try:
    # Access the cache entries directly
    entries = cache.entries
    
    if entries:
        # Create a DataFrame for better display
        import pandas as pd
        from datetime import datetime
        
        entries_data = []
        for url, entry in entries.items():
            # Extract filename from URL
            filename = url.split('/')[-1] if '/' in url else url
            
            # Calculate age
            age_hours = (time.time() - entry.created_at) / 3600
            
            # Calculate time until expiration
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
        
        # Display as table
        df = pd.DataFrame(entries_data)
        st.dataframe(df, use_container_width=True)
        
        # Summary statistics
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
        
    else:
        st.info("No files currently cached.")
        
except Exception as e:
    st.error(f"Error retrieving cache entries: {e}")

# Footer
st.markdown("---")
st.markdown("💡 **Tip:** The cache automatically manages file expiration and size limits. You can adjust these settings in the Configuration section above.")
