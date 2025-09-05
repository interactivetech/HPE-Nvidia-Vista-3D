#!/usr/bin/env python3
"""
Test script for the image cache functionality.

This script demonstrates how the caching system works and can be used
to test the cache performance and functionality.
"""

import os
import time
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent
import sys
sys.path.append(str(project_root))

from utils.image_cache import ImageCacheManager, get_cache_manager, get_cached_file, clear_cache, get_cache_stats

def test_cache_functionality():
    """Test the basic cache functionality."""
    print("🧪 Testing Image Cache Functionality")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    image_server_url = os.getenv('IMAGE_SERVER', 'https://localhost:8888')
    
    # Initialize cache manager
    cache = ImageCacheManager(
        cache_dir="./test_cache",
        max_cache_size_mb=100,  # 100MB for testing
        default_ttl_hours=1     # 1 hour TTL for testing
    )
    
    print(f"📁 Cache directory: {cache.cache_dir}")
    print(f"📊 Initial stats: {cache.get_stats()}")
    
    # Test URLs (these should be real URLs from your image server)
    test_urls = [
        f"{image_server_url}/README.md",  # Small file for testing
        f"{image_server_url}/assets/sample_brain.nii.gz",  # NIfTI file
    ]
    
    print(f"\n🔗 Testing with {len(test_urls)} URLs")
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n--- Test {i}: {url} ---")
        
        try:
            # First request (should download and cache)
            print("📥 First request (download + cache)...")
            start_time = time.time()
            cached_path = get_cached_file(url)
            first_duration = time.time() - start_time
            print(f"✅ Downloaded in {first_duration:.2f}s")
            print(f"📁 Cached at: {cached_path}")
            
            # Second request (should hit cache)
            print("📥 Second request (cache hit)...")
            start_time = time.time()
            cached_path2 = get_cached_file(url)
            second_duration = time.time() - start_time
            print(f"✅ Retrieved from cache in {second_duration:.2f}s")
            print(f"📁 Same path: {cached_path == cached_path2}")
            
            # Show speed improvement
            if first_duration > 0:
                speedup = first_duration / second_duration if second_duration > 0 else float('inf')
                print(f"🚀 Speed improvement: {speedup:.1f}x faster")
            
        except Exception as e:
            print(f"❌ Error testing {url}: {e}")
    
    # Show final statistics
    print(f"\n📊 Final cache statistics:")
    stats = cache.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Test cache cleanup
    print(f"\n🧹 Testing cache cleanup...")
    cache.cleanup()
    print(f"📊 Stats after cleanup: {cache.get_stats()}")
    
    # Test cache clearing
    print(f"\n🗑️ Testing cache clearing...")
    cache.clear_cache()
    print(f"📊 Stats after clearing: {cache.get_stats()}")
    
    print(f"\n✅ Cache testing completed!")

def test_cache_performance():
    """Test cache performance with multiple requests."""
    print("\n🏃 Testing Cache Performance")
    print("=" * 50)
    
    cache = get_cache_manager()
    image_server_url = os.getenv('IMAGE_SERVER', 'https://localhost:8888')
    test_url = f"{image_server_url}/README.md"
    
    # Test multiple requests
    num_requests = 10
    print(f"🔄 Making {num_requests} requests to {test_url}")
    
    times = []
    for i in range(num_requests):
        start_time = time.time()
        try:
            get_cached_file(test_url)
            duration = time.time() - start_time
            times.append(duration)
            print(f"  Request {i+1}: {duration:.3f}s")
        except Exception as e:
            print(f"  Request {i+1}: Error - {e}")
    
    if times:
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        print(f"\n📊 Performance Summary:")
        print(f"  Average time: {avg_time:.3f}s")
        print(f"  Min time: {min_time:.3f}s")
        print(f"  Max time: {max_time:.3f}s")
        print(f"  Total requests: {len(times)}")
    
    # Show cache stats
    stats = get_cache_stats()
    print(f"\n📊 Cache Statistics:")
    print(f"  Hit rate: {stats['hit_rate']:.1%}")
    print(f"  Cache hits: {stats['hits']}")
    print(f"  Cache misses: {stats['misses']}")

if __name__ == "__main__":
    print("🚀 Starting Image Cache Tests")
    print("=" * 60)
    
    try:
        test_cache_functionality()
        test_cache_performance()
        
        print(f"\n🎉 All tests completed successfully!")
        print(f"\n💡 To use the cache in your application:")
        print(f"   1. Import: from utils.image_cache import get_cached_file")
        print(f"   2. Use: cached_path = get_cached_file(remote_url)")
        print(f"   3. The file will be automatically cached and reused")
        
    except KeyboardInterrupt:
        print(f"\n⏹️ Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
