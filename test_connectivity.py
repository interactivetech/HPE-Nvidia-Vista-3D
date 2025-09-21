#!/usr/bin/env python3
"""
Test script to check connectivity from within Docker container
"""
import requests
import os

def test_connectivity():
    """Test connectivity to image server and Vista3D server"""
    print("🔍 Testing connectivity from within container...")
    print(f"DOCKER_CONTAINER env var: {os.getenv('DOCKER_CONTAINER', 'Not set')}")
    print()
    
    # Test Image Server
    print("📡 Testing Image Server connectivity...")
    image_urls = [
        "http://host.docker.internal:8888",
        "http://localhost:8888",
        "http://127.0.0.1:8888",
        "http://image-server:8888",
    ]
    
    for url in image_urls:
        try:
            response = requests.head(url, timeout=3)
            status = "✅ SUCCESS" if response.status_code == 200 else f"❌ FAILED ({response.status_code})"
            print(f"  {url}: {status}")
        except Exception as e:
            print(f"  {url}: ❌ FAILED ({type(e).__name__}: {e})")
    
    print()
    
    # Test Vista3D Server
    print("🧠 Testing Vista3D Server connectivity...")
    vista3d_urls = [
        "http://host.docker.internal:8000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    
    for url in vista3d_urls:
        try:
            response = requests.get(f"{url}/v1/vista3d/info", timeout=3)
            status = "✅ SUCCESS" if response.status_code == 200 else f"❌ FAILED ({response.status_code})"
            print(f"  {url}/v1/vista3d/info: {status}")
        except Exception as e:
            print(f"  {url}/v1/vista3d/info: ❌ FAILED ({type(e).__name__}: {e})")
    
    print()
    print("🌐 Network Configuration:")
    try:
        import socket
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"  Container hostname: {hostname}")
        print(f"  Container IP: {local_ip}")
    except Exception as e:
        print(f"  Could not get network info: {e}")

if __name__ == "__main__":
    test_connectivity()
