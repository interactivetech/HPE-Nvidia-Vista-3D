#!/usr/bin/env python3
"""
Image Cache Manager for Vista3D Segmentation Project

A modular, efficient caching system for medical imaging files downloaded from remote servers.
Provides TTL-based expiration, size management, and seamless integration with existing GUI components.

Features:
- Local file caching with configurable TTL
- Size-based cache management (LRU eviction)
- Cache validation and integrity checking
- Streaming support for large files
- Statistics and monitoring
- Easy integration with existing codebase
"""

import os
import hashlib
import time
import json
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import requests
import streamlit as st
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Represents a cached file entry with metadata."""
    url: str
    local_path: str
    file_size: int
    created_at: float
    last_accessed: float
    access_count: int
    content_hash: str
    ttl_seconds: int = 3600  # 1 hour default TTL
    
    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        return time.time() - self.created_at > self.ttl_seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        """Create from dictionary (JSON deserialization)."""
        return cls(**data)

class ImageCacheManager:
    """
    Manages local caching of images downloaded from remote servers.
    
    Provides efficient caching with TTL, size management, and seamless integration
    with the existing Vista3D segmentation project.
    """
    
    def __init__(self, 
                 cache_dir: Optional[str] = None,
                 max_cache_size_mb: int = 1024,  # 1GB default
                 default_ttl_hours: int = 24,    # 24 hours default
                 image_server_url: Optional[str] = None):
        """
        Initialize the cache manager.
        
        Args:
            cache_dir: Directory to store cached files (default: ~/.cache/vista3d)
            max_cache_size_mb: Maximum cache size in MB
            default_ttl_hours: Default TTL for cached files in hours
            image_server_url: Base URL of the image server
        """
        self.project_root = Path(__file__).parent.parent
        self.cache_dir = Path(cache_dir or os.path.expanduser("~/.cache/vista3d"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_cache_size_bytes = max_cache_size_mb * 1024 * 1024
        self.default_ttl_seconds = default_ttl_hours * 3600
        self.image_server_url = image_server_url or os.getenv('IMAGE_SERVER', 'https://localhost:8888')
        
        # Cache metadata file
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self.entries: Dict[str, CacheEntry] = {}
        
        # Statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'total_downloads': 0,
            'total_bytes_cached': 0,
            'last_cleanup': time.time()
        }
        
        # Load existing cache metadata
        self._load_metadata()
        
        # Clean up expired entries on startup
        self._cleanup_expired()
    
    def _load_metadata(self):
        """Load cache metadata from disk."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    data = json.load(f)
                    self.entries = {
                        url: CacheEntry.from_dict(entry_data)
                        for url, entry_data in data.get('entries', {}).items()
                    }
                    self.stats.update(data.get('stats', {}))
                logger.info(f"Loaded cache metadata: {len(self.entries)} entries")
            except Exception as e:
                logger.warning(f"Failed to load cache metadata: {e}")
                self.entries = {}
    
    def _save_metadata(self):
        """Save cache metadata to disk."""
        try:
            data = {
                'entries': {url: entry.to_dict() for url, entry in self.entries.items()},
                'stats': self.stats
            }
            with open(self.metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache metadata: {e}")
    
    def _get_cache_key(self, url: str) -> str:
        """Generate a cache key for the URL."""
        return hashlib.md5(url.encode()).hexdigest()
    
    def _get_local_path(self, url: str) -> Path:
        """Get the local path for a cached URL."""
        cache_key = self._get_cache_key(url)
        return self.cache_dir / f"{cache_key}.cached"
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _cleanup_expired(self):
        """Remove expired cache entries and their files."""
        expired_urls = []
        for url, entry in self.entries.items():
            if entry.is_expired():
                expired_urls.append(url)
                # Remove the file
                local_path = Path(entry.local_path)
                if local_path.exists():
                    local_path.unlink()
                    logger.info(f"Removed expired cache file: {local_path}")
        
        for url in expired_urls:
            del self.entries[url]
        
        if expired_urls:
            self._save_metadata()
            logger.info(f"Cleaned up {len(expired_urls)} expired entries")
    
    def _evict_lru(self, required_space: int):
        """Evict least recently used entries to make space."""
        if not self.entries:
            return
        
        # Sort by last_accessed time (oldest first)
        sorted_entries = sorted(
            self.entries.items(),
            key=lambda x: x[1].last_accessed
        )
        
        freed_space = 0
        evicted_count = 0
        
        for url, entry in sorted_entries:
            if freed_space >= required_space:
                break
            
            local_path = Path(entry.local_path)
            if local_path.exists():
                local_path.unlink()
                freed_space += entry.file_size
                evicted_count += 1
                logger.info(f"Evicted cache file: {local_path}")
            
            del self.entries[url]
        
        self.stats['evictions'] += evicted_count
        logger.info(f"Evicted {evicted_count} entries, freed {freed_space} bytes")
    
    def _get_current_cache_size(self) -> int:
        """Calculate current cache size in bytes."""
        return sum(entry.file_size for entry in self.entries.values())
    
    def _make_space(self, required_bytes: int):
        """Ensure there's enough space in the cache."""
        current_size = self._get_current_cache_size()
        if current_size + required_bytes <= self.max_cache_size_bytes:
            return
        
        # Calculate how much space we need to free
        space_to_free = (current_size + required_bytes) - self.max_cache_size_bytes
        self._evict_lru(space_to_free)
    
    def get_cached_file(self, url: str, ttl_seconds: Optional[int] = None) -> Optional[Path]:
        """
        Get a cached file if it exists and is not expired.
        
        Args:
            url: URL of the file to retrieve
            ttl_seconds: Override default TTL for this request
            
        Returns:
            Path to cached file if available, None otherwise
        """
        if url not in self.entries:
            self.stats['misses'] += 1
            return None
        
        entry = self.entries[url]
        
        # Check if expired
        ttl = ttl_seconds or entry.ttl_seconds
        if time.time() - entry.created_at > ttl:
            # Remove expired entry
            local_path = Path(entry.local_path)
            if local_path.exists():
                local_path.unlink()
            del self.entries[url]
            self.stats['misses'] += 1
            return None
        
        # Check if file still exists
        local_path = Path(entry.local_path)
        if not local_path.exists():
            del self.entries[url]
            self.stats['misses'] += 1
            return None
        
        # Update access statistics
        entry.last_accessed = time.time()
        entry.access_count += 1
        self.stats['hits'] += 1
        
        self._save_metadata()
        return local_path
    
    def download_and_cache(self, url: str, ttl_seconds: Optional[int] = None) -> Path:
        """
        Download a file and cache it locally.
        
        Args:
            url: URL of the file to download
            ttl_seconds: TTL for the cached file (uses default if None)
            
        Returns:
            Path to the cached file
        """
        # Check if already cached and valid
        cached_path = self.get_cached_file(url, ttl_seconds)
        if cached_path:
            return cached_path
        
        logger.info(f"Downloading and caching: {url}")
        
        # Make space for new file
        self._make_space(1024 * 1024)  # Reserve 1MB initially
        
        # Download file
        try:
            response = requests.get(url, verify=False, timeout=30, stream=True)
            response.raise_for_status()
            
            # Get file size from Content-Length header
            file_size = int(response.headers.get('Content-Length', 0))
            if file_size > 0:
                self._make_space(file_size)
            
            # Download to temporary file first
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.tmp')
            temp_path = Path(temp_file.name)
            
            try:
                downloaded_size = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        temp_file.write(chunk)
                        downloaded_size += len(chunk)
                
                temp_file.close()
                
                # Move to final location
                local_path = self._get_local_path(url)
                shutil.move(str(temp_path), str(local_path))
                
                # Calculate file hash
                content_hash = self._calculate_file_hash(local_path)
                
                # Create cache entry
                entry = CacheEntry(
                    url=url,
                    local_path=str(local_path),
                    file_size=downloaded_size,
                    created_at=time.time(),
                    last_accessed=time.time(),
                    access_count=1,
                    content_hash=content_hash,
                    ttl_seconds=ttl_seconds or self.default_ttl_seconds
                )
                
                self.entries[url] = entry
                self.stats['total_downloads'] += 1
                self.stats['total_bytes_cached'] += downloaded_size
                
                self._save_metadata()
                logger.info(f"Cached file: {local_path} ({downloaded_size} bytes)")
                
                return local_path
                
            finally:
                # Clean up temp file if it still exists
                if temp_path.exists():
                    temp_path.unlink()
        
        except Exception as e:
            logger.error(f"Failed to download and cache {url}: {e}")
            raise
    
    def get_file(self, url: str, ttl_seconds: Optional[int] = None) -> Path:
        """
        Get a file from cache or download and cache it.
        
        Args:
            url: URL of the file to retrieve
            ttl_seconds: TTL for the cached file (uses default if None)
            
        Returns:
            Path to the file (cached or newly downloaded)
        """
        # Try to get from cache first
        cached_path = self.get_cached_file(url, ttl_seconds)
        if cached_path:
            return cached_path
        
        # Download and cache
        return self.download_and_cache(url, ttl_seconds)
    
    def invalidate(self, url: str):
        """Remove a specific file from cache."""
        if url in self.entries:
            entry = self.entries[url]
            local_path = Path(entry.local_path)
            if local_path.exists():
                local_path.unlink()
            del self.entries[url]
            self._save_metadata()
            logger.info(f"Invalidated cache for: {url}")
    
    def clear_cache(self):
        """Clear all cached files."""
        for entry in self.entries.values():
            local_path = Path(entry.local_path)
            if local_path.exists():
                local_path.unlink()
        
        self.entries.clear()
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'total_downloads': 0,
            'total_bytes_cached': 0,
            'last_cleanup': time.time()
        }
        self._save_metadata()
        logger.info("Cleared all cache")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        current_size = self._get_current_cache_size()
        hit_rate = 0
        if self.stats['hits'] + self.stats['misses'] > 0:
            hit_rate = self.stats['hits'] / (self.stats['hits'] + self.stats['misses'])
        
        return {
            'entries_count': len(self.entries),
            'current_size_mb': current_size / (1024 * 1024),
            'max_size_mb': self.max_cache_size_bytes / (1024 * 1024),
            'hit_rate': hit_rate,
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'evictions': self.stats['evictions'],
            'total_downloads': self.stats['total_downloads'],
            'total_bytes_cached': self.stats['total_bytes_cached'],
            'cache_dir': str(self.cache_dir)
        }
    
    def cleanup(self):
        """Clean up expired entries and save metadata."""
        self._cleanup_expired()
        self._save_metadata()

# Global cache manager instance
_cache_manager: Optional[ImageCacheManager] = None

def get_cache_manager() -> ImageCacheManager:
    """Get the global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = ImageCacheManager()
    return _cache_manager

def get_cached_file(url: str, ttl_seconds: Optional[int] = None) -> Path:
    """
    Convenience function to get a cached file.
    
    Args:
        url: URL of the file to retrieve
        ttl_seconds: TTL for the cached file (uses default if None)
        
    Returns:
        Path to the file (cached or newly downloaded)
    """
    return get_cache_manager().get_file(url, ttl_seconds)

def clear_cache():
    """Convenience function to clear the cache."""
    get_cache_manager().clear_cache()

def get_cache_stats() -> Dict[str, Any]:
    """Convenience function to get cache statistics."""
    return get_cache_manager().get_stats()

# Streamlit integration functions
def show_cache_controls():
    """Display cache management controls in Streamlit sidebar."""
    with st.sidebar:
        st.header("Cache Management")
        
        cache_manager = get_cache_manager()
        stats = cache_manager.get_stats()
        
        # Display cache statistics
        st.subheader("Cache Statistics")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Files Cached", stats['entries_count'])
            st.metric("Hit Rate", f"{stats['hit_rate']:.1%}")
        with col2:
            st.metric("Cache Size", f"{stats['current_size_mb']:.1f} MB")
            st.metric("Max Size", f"{stats['max_size_mb']:.1f} MB")
        
        # Cache management buttons
        st.subheader("Cache Actions")
        if st.button("Clear Cache", help="Remove all cached files"):
            cache_manager.clear_cache()
            st.success("Cache cleared!")
            st.rerun()
        
        if st.button("Cleanup Expired", help="Remove expired files"):
            cache_manager.cleanup()
            st.success("Expired files removed!")
            st.rerun()
        
        # Cache configuration
        with st.expander("Cache Settings", expanded=False):
            new_ttl = st.number_input(
                "Default TTL (hours)", 
                min_value=1, 
                max_value=168, 
                value=cache_manager.default_ttl_seconds // 3600,
                help="How long to keep files in cache"
            )
            if st.button("Update TTL"):
                cache_manager.default_ttl_seconds = new_ttl * 3600
                st.success(f"TTL updated to {new_ttl} hours")
            
            new_max_size = st.number_input(
                "Max Cache Size (MB)", 
                min_value=100, 
                max_value=10000, 
                value=cache_manager.max_cache_size_bytes // (1024 * 1024),
                help="Maximum cache size in megabytes"
            )
            if st.button("Update Max Size"):
                cache_manager.max_cache_size_bytes = new_max_size * 1024 * 1024
                st.success(f"Max cache size updated to {new_max_size} MB")

if __name__ == "__main__":
    # Test the cache manager
    cache = ImageCacheManager()
    print("Cache Manager initialized")
    print(f"Cache directory: {cache.cache_dir}")
    print(f"Stats: {cache.get_stats()}")
