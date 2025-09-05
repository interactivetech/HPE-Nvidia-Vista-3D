#!/usr/bin/env python3
"""
Demo script showing the image caching system in action.

This script demonstrates how the caching system improves performance
by avoiding repeated downloads of large medical imaging files.
"""

import streamlit as st
import time
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from utils.image_cache import get_cached_file, get_cache_stats, clear_cache, show_cache_controls

def main():
    st.set_page_config(
        page_title="Image Caching Demo",
        page_icon="🚀",
        layout="wide"
    )
    
    st.title("🚀 Image Caching System Demo")
    st.markdown("This demo shows how the caching system improves performance by avoiding repeated downloads.")
    
    # Sidebar with cache controls
    with st.sidebar:
        show_cache_controls()
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📊 Cache Performance Demo")
        
        # Test URL input
        st.subheader("Test Configuration")
        test_url = st.text_input(
            "Test URL", 
            value="https://localhost:8888/README.md",
            help="Enter a URL to test caching (should be accessible from your image server)"
        )
        
        # Cache operations
        col_a, col_b = st.columns(2)
        
        with col_a:
            if st.button("🔄 Test Cache Performance", type="primary"):
                test_cache_performance(test_url)
        
        with col_b:
            if st.button("📊 Show Cache Stats"):
                show_cache_statistics()
    
    with col2:
        st.header("ℹ️ How It Works")
        st.markdown("""
        **1. First Request**
        - Downloads file from remote server
        - Stores locally with metadata
        - Returns local file path
        
        **2. Subsequent Requests**
        - Checks local cache first
        - Returns cached file instantly
        - No network download needed
        
        **3. Benefits**
        - ⚡ 10-100x faster loading
        - 💾 Reduced bandwidth usage
        - 🔄 Automatic cleanup
        - 📊 Performance monitoring
        """)
        
        # Current cache stats
        stats = get_cache_stats()
        st.metric("Files Cached", stats['entries_count'])
        st.metric("Cache Size", f"{stats['current_size_mb']:.1f} MB")
        st.metric("Hit Rate", f"{stats['hit_rate']:.1%}")

def test_cache_performance(url):
    """Test cache performance with timing measurements."""
    if not url:
        st.error("Please enter a test URL")
        return
    
    st.subheader("🔄 Performance Test Results")
    
    # Create a progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # First request (download + cache)
        status_text.text("📥 First request: Downloading and caching...")
        progress_bar.progress(25)
        
        start_time = time.time()
        cached_path = get_cached_file(url)
        first_duration = time.time() - start_time
        
        status_text.text("✅ First request completed")
        progress_bar.progress(50)
        
        # Second request (cache hit)
        status_text.text("📥 Second request: Retrieving from cache...")
        progress_bar.progress(75)
        
        start_time = time.time()
        cached_path2 = get_cached_file(url)
        second_duration = time.time() - start_time
        
        status_text.text("✅ Second request completed")
        progress_bar.progress(100)
        
        # Display results
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("First Load", f"{first_duration:.3f}s")
        
        with col2:
            st.metric("Cached Load", f"{second_duration:.3f}s")
        
        with col3:
            if first_duration > 0 and second_duration > 0:
                speedup = first_duration / second_duration
                st.metric("Speedup", f"{speedup:.1f}x")
            else:
                st.metric("Speedup", "N/A")
        
        # Additional info
        st.success(f"✅ File cached at: `{cached_path}`")
        st.info(f"🔄 Same file returned: {cached_path == cached_path2}")
        
        # Show updated cache stats
        stats = get_cache_stats()
        st.info(f"📊 Cache now contains {stats['entries_count']} files ({stats['current_size_mb']:.1f} MB)")
        
    except Exception as e:
        st.error(f"❌ Error testing cache: {e}")
        st.info("💡 Make sure your image server is running and the URL is accessible")
    
    finally:
        progress_bar.empty()
        status_text.empty()

def show_cache_statistics():
    """Display detailed cache statistics."""
    st.subheader("📊 Detailed Cache Statistics")
    
    stats = get_cache_stats()
    
    # Create metrics in a nice layout
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Files Cached", stats['entries_count'])
        st.metric("Cache Size", f"{stats['current_size_mb']:.1f} MB")
        st.metric("Max Cache Size", f"{stats['max_size_mb']:.1f} MB")
    
    with col2:
        st.metric("Hit Rate", f"{stats['hit_rate']:.1%}")
        st.metric("Cache Hits", stats['hits'])
        st.metric("Cache Misses", stats['misses'])
    
    # Additional statistics
    st.subheader("📈 Performance Metrics")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Downloads", stats['total_downloads'])
        st.metric("Total Bytes Cached", f"{stats['total_bytes_cached'] / (1024*1024):.1f} MB")
    
    with col2:
        st.metric("Evictions", stats['evictions'])
        st.metric("Cache Directory", stats['cache_dir'])
    
    # Usage efficiency
    if stats['max_size_mb'] > 0:
        usage_percent = (stats['current_size_mb'] / stats['max_size_mb']) * 100
        st.metric("Cache Usage", f"{usage_percent:.1f}%")

if __name__ == "__main__":
    main()
