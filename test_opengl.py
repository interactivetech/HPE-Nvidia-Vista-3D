#!/usr/bin/env python3
"""
Test script to verify OpenGL and Open3D functionality in Docker container.
This script can be run to test if the OpenGL setup is working correctly.
"""

import os
import sys

def test_opengl_environment():
    """Test OpenGL environment variables and libraries."""
    print("Testing OpenGL Environment...")
    print(f"DISPLAY: {os.environ.get('DISPLAY', 'Not set')}")
    print(f"LIBGL_ALWAYS_SOFTWARE: {os.environ.get('LIBGL_ALWAYS_SOFTWARE', 'Not set')}")
    print(f"MESA_GL_VERSION_OVERRIDE: {os.environ.get('MESA_GL_VERSION_OVERRIDE', 'Not set')}")
    print(f"MESA_GLSL_VERSION_OVERRIDE: {os.environ.get('MESA_GLSL_VERSION_OVERRIDE', 'Not set')}")
    print()

def test_opengl_libraries():
    """Test if OpenGL libraries are available."""
    print("Testing OpenGL Libraries...")
    try:
        import ctypes
        from ctypes import CDLL
        
        # Try to load libGL
        try:
            libgl = CDLL("libGL.so.1")
            print("✅ libGL.so.1 loaded successfully")
        except OSError as e:
            print(f"❌ libGL.so.1 failed to load: {e}")
            return False
        
        # Try to load libGLU
        try:
            libglu = CDLL("libGLU.so.1")
            print("✅ libGLU.so.1 loaded successfully")
        except OSError as e:
            print(f"⚠️  libGLU.so.1 failed to load: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing OpenGL libraries: {e}")
        return False

def test_open3d_import():
    """Test Open3D import."""
    print("Testing Open3D Import...")
    try:
        import open3d as o3d
        print("✅ Open3D imported successfully")
        print(f"Open3D version: {o3d.__version__}")
        
        # Try to create a simple geometry
        try:
            mesh = o3d.geometry.TriangleMesh.create_sphere()
            print("✅ Open3D geometry creation successful")
            return True
        except Exception as e:
            print(f"❌ Open3D geometry creation failed: {e}")
            return False
            
    except ImportError as e:
        print(f"❌ Open3D import failed: {e}")
        return False
    except OSError as e:
        if "libGL.so.1" in str(e):
            print(f"❌ Open3D failed due to missing OpenGL: {e}")
        else:
            print(f"❌ Open3D failed with OSError: {e}")
        return False
    except Exception as e:
        print(f"❌ Open3D failed with unexpected error: {e}")
        return False

def test_mesa_utils():
    """Test Mesa utilities."""
    print("Testing Mesa Utilities...")
    try:
        import subprocess
        result = subprocess.run(['glxinfo'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ glxinfo executed successfully")
            # Look for OpenGL version
            for line in result.stdout.split('\n'):
                if 'OpenGL version' in line:
                    print(f"   {line.strip()}")
                    break
            return True
        else:
            print(f"❌ glxinfo failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ glxinfo timed out")
        return False
    except FileNotFoundError:
        print("❌ glxinfo not found (mesa-utils not installed?)")
        return False
    except Exception as e:
        print(f"❌ Mesa utils test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("OpenGL and Open3D Test Suite")
    print("=" * 60)
    print()
    
    # Test environment
    test_opengl_environment()
    
    # Test libraries
    opengl_ok = test_opengl_libraries()
    print()
    
    # Test Mesa utils
    mesa_ok = test_mesa_utils()
    print()
    
    # Test Open3D
    open3d_ok = test_open3d_import()
    print()
    
    # Summary
    print("=" * 60)
    print("Test Summary:")
    print(f"OpenGL Libraries: {'✅ PASS' if opengl_ok else '❌ FAIL'}")
    print(f"Mesa Utils: {'✅ PASS' if mesa_ok else '❌ FAIL'}")
    print(f"Open3D Import: {'✅ PASS' if open3d_ok else '❌ FAIL'}")
    
    if opengl_ok and open3d_ok:
        print("\n🎉 All tests passed! Open3D should work correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Open3D may not work correctly.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
