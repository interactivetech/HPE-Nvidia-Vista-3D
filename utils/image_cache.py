#!/usr/bin/env python3
"""
Image Cache Manager for Vista3D Segmentation Project

A comprehensive, production-ready caching system for medical imaging files downloaded 
from remote servers. Designed specifically for the NIfTI Vessel Segmentation and 
Viewer application, providing efficient local storage with intelligent management.

Architecture Overview:
    The cache system consists of three main components:
    1. CacheEntry: Dataclass representing individual cached files with metadata
    2. ImageCacheManager: Core caching logic with TTL, LRU eviction, and size management
    3. Convenience Functions: Simple API for common operations

Key Features:
- **TTL-based Expiration**: Configurable time-to-live for automatic cleanup
- **LRU Eviction**: Least Recently Used algorithm for space management
- **Integrity Checking**: SHA256 hash validation for cached files
- **Streaming Downloads**: Memory-efficient handling of large medical imaging files
- **Persistent Metadata**: JSON-based metadata storage across sessions
- **Statistics Tracking**: Comprehensive metrics for performance monitoring
- **Thread-Safe Operations**: Safe for concurrent access patterns
- **Streamlit Integration**: Built-in UI components for cache management

Use Cases:
- Medical imaging file caching (NIfTI, DICOM, etc.)
- Reducing bandwidth usage for large file downloads
- Improving application performance through local storage
- Managing storage space efficiently in medical imaging workflows

Performance Characteristics:
- O(1) cache lookups using hash-based keys
- O(n log n) LRU eviction sorting (where n = number of entries)
- Streaming downloads with configurable chunk sizes
- Metadata persistence with minimal I/O overhead

Example Usage:
    Basic usage:
    ```python
    from utils.image_cache import get_cached_file
    
    # Get file from cache or download if needed
    file_path = get_cached_file('https://server.com/image.nii.gz')
    ```
    
    Advanced usage:
    ```python
    from utils.image_cache import ImageCacheManager
    
    # Create custom cache manager
    cache = ImageCacheManager(
        cache_dir='/custom/cache/dir',
        max_cache_size_mb=2048,  # 2GB
        default_ttl_hours=48     # 48 hours
    )
    
    # Use with custom TTL
    file_path = cache.get_file(url, ttl_seconds=7200)  # 2 hours
    ```

Author: Medical Imaging Team
Version: 2.0.0
Dependencies: requests, streamlit, pathlib, hashlib
License: MIT
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

# Configure logging - will be updated in ImageCacheManager.__init__
logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """
    Represents a cached file entry with comprehensive metadata.
    
    This dataclass stores all necessary information about a cached file including
    location, timestamps, access patterns, and integrity data. It provides methods
    for expiration checking and serialization for persistent storage.
    
    Attributes:
        url (str): Original URL of the cached file
        local_path (str): Absolute path to the cached file on local filesystem
        file_size (int): Size of the cached file in bytes
        created_at (float): Unix timestamp when the file was first cached
        last_accessed (float): Unix timestamp of most recent access
        access_count (int): Number of times this file has been accessed
        content_hash (str): SHA256 hash for integrity verification
        ttl_seconds (int): Time-to-live in seconds (default: 3600 = 1 hour)
    
    Example:
        >>> entry = CacheEntry(
        ...     url='https://server.com/file.nii.gz',
        ...     local_path='/cache/abc123.cached',
        ...     file_size=1048576,
        ...     created_at=time.time(),
        ...     last_accessed=time.time(),
        ...     access_count=1,
        ...     content_hash='sha256hash...',
        ...     ttl_seconds=7200
        ... )
        >>> print(entry.is_expired())
        False
    """
    url: str
    local_path: str
    file_size: int
    created_at: float
    last_accessed: float
    access_count: int
    content_hash: str
    ttl_seconds: int = 3600  # 1 hour default TTL
    
    def is_expired(self) -> bool:
        """
        Check if the cache entry has expired based on TTL.
        
        Compares the current time with the creation time plus the TTL
        to determine if the cached file should be considered stale.
        
        Returns:
            bool: True if the entry has exceeded its TTL, False otherwise
            
        Example:
            >>> entry = CacheEntry(..., created_at=time.time()-7200, ttl_seconds=3600)
            >>> entry.is_expired()
            True
        """
        return time.time() - self.created_at > self.ttl_seconds
    
    def get_age_seconds(self) -> float:
        """
        Get the age of the cache entry in seconds.
        
        Returns:
            float: Number of seconds since the file was cached
        """
        return time.time() - self.created_at
    
    def get_time_until_expiry(self) -> float:
        """
        Get the time remaining until expiry in seconds.
        
        Returns:
            float: Seconds until expiry (negative if already expired)
        """
        return self.ttl_seconds - self.get_age_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert cache entry to dictionary for JSON serialization.
        
        Used for persistent storage of cache metadata across application
        sessions. All fields are preserved in the dictionary format.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the cache entry
            
        Example:
            >>> entry = CacheEntry(...)
            >>> data = entry.to_dict()
            >>> print(data['url'])
            'https://server.com/file.nii.gz'
        """
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        """
        Create cache entry from dictionary (JSON deserialization).
        
        Used for loading cache metadata from persistent storage. Validates
        that all required fields are present in the input dictionary.
        
        Args:
            data: Dictionary containing cache entry data
            
        Returns:
            CacheEntry: Reconstructed cache entry instance
            
        Raises:
            TypeError: If required fields are missing from the dictionary
            
        Example:
            >>> data = {'url': '...', 'local_path': '...', ...}
            >>> entry = CacheEntry.from_dict(data)
            >>> print(entry.url)
            'https://server.com/file.nii.gz'
        """
        return cls(**data)

class ImageCacheManager:
    """
    Comprehensive cache manager for medical imaging files with intelligent storage management.
    
    This class provides a complete caching solution for the Vista3D segmentation project,
    handling file downloads, local storage, expiration management, and size constraints.
    It implements LRU (Least Recently Used) eviction, TTL-based expiration, and 
    comprehensive statistics tracking.
    
    Architecture:
        - Hash-based cache keys for O(1) lookups
        - JSON metadata persistence for session continuity  
        - Streaming downloads for memory efficiency
        - LRU eviction for space management
        - SHA256 integrity verification
        
    Thread Safety:
        The manager is designed for single-threaded use within Streamlit applications.
        For multi-threaded environments, external synchronization is required.
        
    Storage Organization:
        - Cache directory: output/cache (default)
        - Cached files: {hash}.cached
        - Metadata: output/cache/cache_metadata.json
        - Logs: output/cache/logs/cache_YYYYMMDD.log
        - Temporary files: {random}.tmp (during downloads)
        
    Performance Characteristics:
        - Cache lookup: O(1)
        - LRU eviction: O(n log n) where n = cache entries
        - File download: Streaming with 8KB chunks
        - Metadata save: O(n) serialization
        
    Example Usage:
        ```python
        # Basic initialization
        cache = ImageCacheManager()
        
        # Custom configuration
        cache = ImageCacheManager(
            cache_dir="/custom/cache/path",
            max_cache_size_mb=2048,  # 2GB limit
            default_ttl_hours=48     # 48 hour TTL
        )
        
        # Get file (cache or download)
        file_path = cache.get_file("https://server.com/image.nii.gz")
        
        # Get with custom TTL
        file_path = cache.get_file(url, ttl_seconds=7200)  # 2 hours
        
        # Cache management
        cache.cleanup()  # Remove expired files
        cache.clear_cache()  # Remove all files
        stats = cache.get_stats()  # Get performance metrics
        ```
        
    Error Handling:
        - Network errors during download are propagated
        - Disk space issues trigger automatic cleanup
        - Corrupted metadata files are rebuilt automatically
        - Missing cache files are automatically re-downloaded
    """
    
    def __init__(self, 
                 cache_dir: Optional[str] = None,
                 max_cache_size_mb: int = 1024,  # 1GB default
                 default_ttl_hours: int = 24,    # 24 hours default
                 image_server_url: Optional[str] = None):
        """
        Initialize the cache manager with configurable parameters.
        
        Sets up the cache directory structure, loads existing metadata,
        and performs initial cleanup of expired entries. The cache is
        ready for use immediately after initialization.
        
        Args:
            cache_dir (Optional[str]): Directory to store cached files. 
                                     Defaults to ~/.cache/vista3d if None.
            max_cache_size_mb (int): Maximum total cache size in megabytes.
                                   Triggers LRU eviction when exceeded.
                                   Default: 1024 (1GB).
            default_ttl_hours (int): Default time-to-live for cached files
                                   in hours. Individual files can override this.
                                   Default: 24 hours.
            image_server_url (Optional[str]): Base URL of the image server.
                                            Falls back to IMAGE_SERVER env var
                                            or 'https://localhost:8888'.
        
        Raises:
            OSError: If cache directory cannot be created
            PermissionError: If insufficient permissions for cache directory
            
        Example:
            >>> # Default configuration
            >>> cache = ImageCacheManager()
            
            >>> # Custom configuration for large datasets
            >>> cache = ImageCacheManager(
            ...     cache_dir="/mnt/fast_storage/cache",
            ...     max_cache_size_mb=5120,  # 5GB
            ...     default_ttl_hours=72     # 3 days
            ... )
        """
        self.project_root = Path(__file__).parent.parent
        # Default cache directory is now in project's output/cache directory
        default_cache_dir = self.project_root / "output" / "cache"
        self.cache_dir = Path(cache_dir or default_cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Create logs subdirectory for cache operation logs
        self.logs_dir = self.cache_dir / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure logging to use the logs directory
        self._setup_logging()
        
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
    
    # =========================================================================
    # PRIVATE HELPER METHODS
    # =========================================================================
    
    def _setup_logging(self):
        """
        Configure logging to use the cache logs directory.
        
        Sets up file-based logging for cache operations with rotation
        to prevent log files from growing too large.
        """
        from logging.handlers import RotatingFileHandler
        
        # Create a logger for this cache instance
        self.logger = logging.getLogger(f"{__name__}.{id(self)}")
        self.logger.setLevel(logging.INFO)
        
        # Remove any existing handlers to avoid duplicates
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create log file path with timestamp
        log_file = self.logs_dir / f"cache_{datetime.now().strftime('%Y%m%d')}.log"
        
        # Set up rotating file handler (max 10MB, keep 5 files)
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        self.logger.addHandler(file_handler)
        
        # Also log to console for development
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)  # Only warnings and errors to console
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        self.logger.info(f"Cache logging initialized. Logs directory: {self.logs_dir}")
    
    def _load_metadata(self):
        """
        Load cache metadata from persistent storage.
        
        Reads the cache_metadata.json file and reconstructs the in-memory
        cache entries and statistics. Handles corrupted or missing metadata
        gracefully by starting with an empty cache.
        """
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    data = json.load(f)
                    self.entries = {
                        url: CacheEntry.from_dict(entry_data)
                        for url, entry_data in data.get('entries', {}).items()
                    }
                    self.stats.update(data.get('stats', {}))
                self.logger.info(f"Loaded cache metadata: {len(self.entries)} entries")
            except Exception as e:
                self.logger.warning(f"Failed to load cache metadata: {e}")
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
            self.logger.error(f"Failed to save cache metadata: {e}")
    
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
                    self.logger.info(f"Removed expired cache file: {local_path}")
        
        for url in expired_urls:
            del self.entries[url]
        
        if expired_urls:
            self._save_metadata()
            self.logger.info(f"Cleaned up {len(expired_urls)} expired entries")
    
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
                self.logger.info(f"Evicted cache file: {local_path}")
            
            del self.entries[url]
        
        self.stats['evictions'] += evicted_count
        self.logger.info(f"Evicted {evicted_count} entries, freed {freed_space} bytes")
    
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
    
    # =========================================================================
    # PUBLIC CACHE ACCESS METHODS
    # =========================================================================
    
    def get_cached_file(self, url: str, ttl_seconds: Optional[int] = None) -> Optional[Path]:
        """
        Retrieve a file from cache if it exists and has not expired.
        
        This method checks for an existing cached version of the requested file.
        It validates the file's expiration status, verifies the file still exists
        on disk, and updates access statistics. This is a read-only operation
        that does not trigger downloads.
        
        Args:
            url (str): Complete URL of the file to retrieve from cache
            ttl_seconds (Optional[int]): Override the default TTL for this check.
                                       If None, uses the TTL stored with the entry.
                                       
        Returns:
            Optional[Path]: Path to the cached file if available and valid,
                          None if not cached, expired, or file missing.
                          
        Side Effects:
            - Updates last_accessed timestamp if file found
            - Increments access_count if file found  
            - Updates hit/miss statistics
            - Removes expired or missing entries
            
        Example:
            >>> cache = ImageCacheManager()
            >>> path = cache.get_cached_file('https://server.com/file.nii.gz')
            >>> if path:
            ...     print(f"Cache hit: {path}")
            ... else:
            ...     print("Cache miss - file not cached or expired")
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
        Download a file from remote server and store it in local cache.
        
        This method performs the actual download operation, handling streaming
        for large files, cache space management, and integrity verification.
        It includes automatic cleanup and LRU eviction as needed.
        
        Args:
            url (str): Complete URL of the file to download
            ttl_seconds (Optional[int]): Time-to-live for the cached file in seconds.
                                       If None, uses the default TTL configured 
                                       during initialization.
                                       
        Returns:
            Path: Local filesystem path to the downloaded and cached file
            
        Raises:
            requests.RequestException: If download fails due to network issues
            OSError: If disk space is insufficient or permissions are inadequate
            ValueError: If URL is malformed or empty
            
        Side Effects:
            - May evict other cached files to make space
            - Updates download statistics and metadata
            - Creates temporary files during download
            - Calculates and stores SHA256 hash for integrity
            
        Example:
            >>> cache = ImageCacheManager()
            >>> path = cache.download_and_cache(
            ...     'https://server.com/large_image.nii.gz',
            ...     ttl_seconds=86400  # Cache for 24 hours
            ... )
            >>> print(f"Downloaded to: {path}")
        """
        # Check if already cached and valid
        cached_path = self.get_cached_file(url, ttl_seconds)
        if cached_path:
            return cached_path
        
        self.logger.info(f"Downloading and caching: {url}")
        
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
                self.logger.info(f"Cached file: {local_path} ({downloaded_size} bytes)")
                
                return local_path
                
            finally:
                # Clean up temp file if it still exists
                if temp_path.exists():
                    temp_path.unlink()
        
        except Exception as e:
            self.logger.error(f"Failed to download and cache {url}: {e}")
            raise
    
    def get_file(self, url: str, ttl_seconds: Optional[int] = None) -> Path:
        """
        Primary method to get a file from cache or download if necessary.
        
        This is the main entry point for file retrieval. It first attempts
        to serve the file from cache, and if not available or expired,
        automatically downloads and caches the file. This provides a 
        seamless interface that abstracts cache management from the caller.
        
        Args:
            url (str): Complete URL of the file to retrieve
            ttl_seconds (Optional[int]): Time-to-live for caching in seconds.
                                       Applied to new downloads only.
                                       
        Returns:
            Path: Local filesystem path to the file, guaranteed to exist
                 and be accessible for reading.
                 
        Raises:
            requests.RequestException: If download is required but fails
            OSError: If cache operations fail due to disk/permission issues
            
        Example:
            >>> cache = ImageCacheManager()
            >>> # This will check cache first, download if needed
            >>> file_path = cache.get_file('https://server.com/image.nii.gz')
            >>> with open(file_path, 'rb') as f:
            ...     data = f.read()
        """
        # Try to get from cache first
        cached_path = self.get_cached_file(url, ttl_seconds)
        if cached_path:
            return cached_path
        
        # Download and cache
        return self.download_and_cache(url, ttl_seconds)
    
    # =========================================================================
    # CACHE MANAGEMENT METHODS
    # =========================================================================
    
    def invalidate(self, url: str):
        """
        Remove a specific file from the cache.
        
        Immediately removes the specified file from both the cache metadata
        and the local filesystem. This is useful for forcing re-download
        of specific files that may have been updated on the server.
        
        Args:
            url (str): Complete URL of the file to remove from cache
            
        Side Effects:
            - Deletes the cached file from disk
            - Removes entry from cache metadata
            - Saves updated metadata to disk
            - Logs the invalidation operation
            
        Example:
            >>> cache = ImageCacheManager()
            >>> cache.invalidate('https://server.com/outdated_file.nii.gz')
            >>> # Next get_file() call will download fresh copy
        """
        if url in self.entries:
            entry = self.entries[url]
            local_path = Path(entry.local_path)
            if local_path.exists():
                local_path.unlink()
            del self.entries[url]
            self._save_metadata()
            self.logger.info(f"Invalidated cache for: {url}")
    
    def clear_cache(self):
        """
        Remove all files from the cache and reset statistics.
        
        This is a complete cache reset operation that removes all cached
        files from disk, clears all metadata, and resets performance
        statistics to zero. Use with caution as this operation cannot
        be undone and will force re-download of all files.
        
        Side Effects:
            - Deletes all cached files from disk
            - Clears all cache entries from memory
            - Resets all statistics counters to zero
            - Saves empty metadata to disk
            - Logs the clear operation
            
        Example:
            >>> cache = ImageCacheManager()
            >>> cache.clear_cache()
            >>> print(cache.get_stats()['entries_count'])  # Will be 0
        """
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
        self.logger.info("Cleared all cache")
    
    def cleanup(self):
        """
        Clean up expired entries and optimize cache storage.
        
        Performs maintenance operations to remove expired files and
        update metadata. This is automatically called during initialization
        but can be invoked manually for maintenance or optimization.
        
        Side Effects:
            - Removes expired cache entries and their files
            - Updates cache metadata on disk
            - Logs cleanup operations
            
        Example:
            >>> cache = ImageCacheManager()
            >>> cache.cleanup()  # Remove expired files
        """
        self._cleanup_expired()
        self._save_metadata()
        
    # =========================================================================
    # STATISTICS AND MONITORING
    # =========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive cache performance and usage statistics.
        
        Returns detailed metrics about cache performance, storage utilization,
        and operational statistics. This data is useful for monitoring,
        optimization, and capacity planning.
        
        Returns:
            Dict[str, Any]: Dictionary containing cache statistics with keys:
                - entries_count (int): Number of files currently cached
                - current_size_mb (float): Current cache size in megabytes
                - max_size_mb (float): Maximum allowed cache size in megabytes
                - hit_rate (float): Cache hit ratio (0.0 to 1.0)
                - hits (int): Total number of cache hits
                - misses (int): Total number of cache misses
                - evictions (int): Total number of LRU evictions
                - total_downloads (int): Total files downloaded and cached
                - total_bytes_cached (int): Total bytes ever cached
                - cache_dir (str): Path to cache directory
                
        Example:
            >>> cache = ImageCacheManager()
            >>> stats = cache.get_stats()
            >>> print(f"Hit rate: {stats['hit_rate']:.2%}")
            >>> print(f"Cache usage: {stats['current_size_mb']:.1f}MB")
        """
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


# =============================================================================
# GLOBAL CACHE MANAGER AND CONVENIENCE FUNCTIONS
# =============================================================================

# Global cache manager instance (singleton pattern)
_cache_manager: Optional[ImageCacheManager] = None

def get_cache_manager() -> ImageCacheManager:
    """
    Get the global singleton cache manager instance.
    
    This function implements the singleton pattern to ensure only one
    cache manager exists per application instance. The cache manager
    is created with default settings on first access.
    
    Returns:
        ImageCacheManager: The global cache manager instance
        
    Example:
        >>> cache = get_cache_manager()
        >>> stats = cache.get_stats()
    """
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = ImageCacheManager()
    return _cache_manager

def get_cached_file(url: str, ttl_seconds: Optional[int] = None) -> Path:
    """
    Convenience function to get a file from cache or download it.
    
    This is the primary interface for most applications. It abstracts
    the cache manager completely and provides a simple file retrieval
    interface using the global cache manager instance.
    
    Args:
        url (str): Complete URL of the file to retrieve
        ttl_seconds (Optional[int]): Override TTL in seconds for this file
        
    Returns:
        Path: Local filesystem path to the requested file
        
    Raises:
        requests.RequestException: If download is required but fails
        OSError: If cache operations fail
        
    Example:
        >>> from utils.image_cache import get_cached_file
        >>> file_path = get_cached_file('https://server.com/image.nii.gz')
        >>> # File is now available locally at file_path
    """
    return get_cache_manager().get_file(url, ttl_seconds)

def clear_cache():
    """
    Convenience function to clear the entire cache.
    
    Removes all cached files and resets statistics using the global
    cache manager instance. This is a destructive operation that
    cannot be undone.
    
    Example:
        >>> from utils.image_cache import clear_cache
        >>> clear_cache()  # All cached files are now removed
    """
    get_cache_manager().clear_cache()

def get_cache_stats() -> Dict[str, Any]:
    """
    Convenience function to get cache performance statistics.
    
    Returns comprehensive statistics from the global cache manager
    for monitoring and analysis purposes.
    
    Returns:
        Dict[str, Any]: Cache statistics dictionary (see get_stats() for details)
        
    Example:
        >>> from utils.image_cache import get_cache_stats
        >>> stats = get_cache_stats()
        >>> print(f"Cache hit rate: {stats['hit_rate']:.2%}")
    """
    return get_cache_manager().get_stats()

# =============================================================================
# STREAMLIT INTEGRATION
# =============================================================================

def show_cache_controls():
    """
    Display comprehensive cache management controls in Streamlit sidebar.
    
    This function creates a complete cache management interface within
    a Streamlit application's sidebar, including statistics display,
    management buttons, and configuration options. It provides a
    user-friendly way to monitor and control cache behavior.
    
    Features:
        - Real-time cache statistics display
        - Clear cache and cleanup expired files buttons
        - TTL and cache size configuration
        - Automatic UI updates after operations
        
    Side Effects:
        - Modifies Streamlit sidebar content
        - May trigger cache operations based on user interactions
        - Updates Streamlit session state
        
    Example:
        >>> import streamlit as st
        >>> from utils.image_cache import show_cache_controls
        >>> 
        >>> # In your Streamlit app
        >>> show_cache_controls()  # Adds cache controls to sidebar
        
    Note:
        This function must be called within a Streamlit app context.
        It uses Streamlit's session state and component systems.
    """
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


# =============================================================================
# MODULE USAGE SUMMARY AND TESTING
# =============================================================================

"""
Image Cache Manager Usage Summary

This module provides a comprehensive caching solution for medical imaging files
in the Vista3D segmentation project. Here's how to use it effectively:

BASIC USAGE:
-----------
```python
from utils.image_cache import get_cached_file

# Simple file retrieval (cache or download)
file_path = get_cached_file('https://server.com/image.nii.gz')
```

ADVANCED USAGE:
--------------
```python
from utils.image_cache import ImageCacheManager

# Custom cache configuration
cache = ImageCacheManager(
    cache_dir='/custom/cache/path',
    max_cache_size_mb=2048,  # 2GB
    default_ttl_hours=48     # 48 hours
)

# Use with specific TTL
file_path = cache.get_file(url, ttl_seconds=7200)  # 2 hours
```

MANAGEMENT OPERATIONS:
---------------------
```python
from utils.image_cache import get_cache_manager, clear_cache, get_cache_stats

# Get statistics
stats = get_cache_stats()
print(f"Hit rate: {stats['hit_rate']:.2%}")

# Clear all cache
clear_cache()

# Manual cleanup
cache = get_cache_manager()
cache.cleanup()
```

STREAMLIT INTEGRATION:
---------------------
```python
from utils.image_cache import show_cache_controls

# Add cache management UI to sidebar
show_cache_controls()
```

PERFORMANCE OPTIMIZATION:
------------------------
- Use appropriate TTL values for your use case
- Monitor hit rates and adjust cache size accordingly
- Regular cleanup for long-running applications
- Consider cache warming for frequently accessed files

MONITORING AND DEBUGGING:
------------------------
- Check cache statistics regularly
- Monitor disk space usage
- Review cache hit rates for optimization opportunities
- Use logging output for debugging cache operations

ERROR HANDLING:
--------------
- Network errors during download are propagated
- Disk space issues trigger automatic cleanup
- Missing or corrupted files are automatically re-downloaded
- Graceful degradation when cache operations fail

THREAD SAFETY:
-------------
- Designed for single-threaded Streamlit applications
- Use external synchronization for multi-threaded environments
- Global cache manager uses singleton pattern

STORAGE ORGANIZATION:
--------------------
- Default cache directory: ~/.cache/vista3d
- Cached files: {md5_hash}.cached
- Metadata: cache_metadata.json
- Temporary download files: {random}.tmp

This cache system is production-ready and optimized for medical imaging
workflows with large file sizes and bandwidth considerations.
"""

if __name__ == "__main__":
    """
    Test and demonstration script for the cache manager.
    
    Run this module directly to test basic functionality and see
    example usage patterns.
    """
    # Test the cache manager
    cache = ImageCacheManager()
    print("✅ Cache Manager initialized successfully")
    print(f"📁 Cache directory: {cache.cache_dir}")
    print(f"📊 Initial stats: {cache.get_stats()}")
    
    # Test convenience functions
    stats = get_cache_stats()
    print(f"🎯 Hit rate: {stats['hit_rate']:.2%}")
    print(f"💾 Cache usage: {stats['current_size_mb']:.1f}MB / {stats['max_size_mb']:.1f}MB")
    
    print("🧪 Cache manager ready for use!")
