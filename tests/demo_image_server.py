#!/usr/bin/env python3
"""
Demonstration script for the NIFTI Image HTTPS Server

This script shows different ways to use the image server.
"""

import os
import subprocess
import time
import webbrowser
from pathlib import Path

def main():
    print("🚀 NIFTI Image HTTPS Server Demo")
    print("=" * 50)
    
    # Check if utils directory exists
    utils_dir = Path("utils")
    if not utils_dir.exists():
        print("❌ Error: utils directory not found")
        return
    
    # Check if image_server.py exists
    server_script = utils_dir / "image_server.py"
    if not server_script.exists():
        print("❌ Error: image_server.py not found in utils directory")
        return
    
    # Check if images directory exists
    images_dir = Path("output/nifti")
    if not images_dir.exists():
        print("❌ Error: NIFTI images directory not found at output/nifti")
        print("   Please ensure the directory exists and contains NIFTI files")
        return
    
    print(f"✅ Found images directory: {images_dir}")
    print(f"✅ Found server script: {server_script}")
    
    # Show available NIFTI files
    nifti_files = list(images_dir.glob("**/*.nii*")) + list(images_dir.glob("**/*.hdr"))
    if nifti_files:
        print(f"\n📁 Found {len(nifti_files)} NIFTI files:")
        for file in nifti_files[:5]:  # Show first 5
            print(f"   - {file.name}")
        if len(nifti_files) > 5:
            print(f"   ... and {len(nifti_files) - 5} more")
    else:
        print("\n⚠️  No NIFTI files found in the images directory")
        print("   The server will still start but won't have files to serve")
    
    print("\n🔧 Starting NIFTI Image HTTPS Server...")
    print("   This will:")
    print("   1. Generate self-signed SSL certificates")
    print("   2. Start HTTPS server on port 8888")
    print("   3. Serve NIFTI images from output/nifti")
    print("   4. Open web browser to the server")
    
    # Ask user if they want to proceed
    response = input("\n🤔 Do you want to start the server? (y/n): ").lower().strip()
    if response not in ['y', 'yes']:
        print("👋 Demo cancelled")
        return
    
    print("\n🚀 Starting server...")
    
    try:
        # Start the server in background
        cmd = [
            "python", str(server_script),
            "--generate-certs",
            "--port", "8888",
            "--host", "localhost"
        ]
        
        print(f"   Command: {' '.join(cmd)}")
        
        # Start server process
        process = subprocess.Popen(
            cmd,
            cwd=utils_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a bit for server to start
        print("   Waiting for server to start...")
        time.sleep(3)
        
        # Check if process is still running
        if process.poll() is None:
            print("✅ Server started successfully!")
            print(f"   🌐 Access: https://localhost:8888")
            print(f"   📁 Images: {images_dir.absolute()}")
            print(f"   🔒 SSL: Self-signed certificate")
            
            # Try to open browser
            try:
                print("\n🌐 Opening web browser...")
                webbrowser.open("https://localhost:8888")
                print("✅ Browser opened successfully")
            except Exception as e:
                print(f"⚠️  Could not open browser automatically: {e}")
                print("   Please manually navigate to: https://localhost:8888")
            
            print("\n📋 Server Information:")
            print("   - URL: https://localhost:8888")
            print("   - Port: 8888")
            print("   - Images: output/nifti")
            print("   - SSL: Self-signed (accept security warning in browser)")
            
            print("\n⏹️  To stop the server:")
            print("   1. Press Ctrl+C in the terminal where server is running")
            print("   2. Or kill the process: pkill -f image_server.py")
            
            # Keep the script running
            try:
                input("\n🔄 Press Enter to stop the server and exit...")
            except KeyboardInterrupt:
                pass
            
            # Stop the server
            print("\n🛑 Stopping server...")
            process.terminate()
            process.wait(timeout=5)
            print("✅ Server stopped")
            
        else:
            # Server failed to start
            stdout, stderr = process.communicate()
            print("❌ Server failed to start")
            if stdout:
                print(f"   stdout: {stdout}")
            if stderr:
                print(f"   stderr: {stderr}")
            
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Check if port 8888 is available")
        print("   2. Ensure OpenSSL is installed")
        print("   3. Check Python dependencies")
        print("   4. Verify .env file configuration")

if __name__ == "__main__":
    main()
