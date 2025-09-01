# Vista3D Services Test Suite

This directory contains comprehensive test scripts to verify that the Vista3D Docker server and external HTTPS image server are running correctly and can communicate with each other.

## Overview

The test suite verifies:
- **Docker Availability**: Docker daemon is running and accessible
- **Vista3D Container**: Vista3D Docker container is running on port 8000
- **External Image Server**: HTTPS image server is running on port 8888
- **SSL Certificates**: Self-signed certificates are valid
- **File Serving**: Image server can serve files properly
- **Communication**: Vista3D can access the external image server
- **Directory Structure**: Required output directories exist

## Files

- **`test_vista3d_services.py`** - Main Python test script with comprehensive testing
- **`test_vista3d.sh`** - Shell script wrapper for easier usage
- **`TEST_README.md`** - This documentation file

## Prerequisites

Before running the tests, ensure you have:

1. **Python 3.7+** installed
2. **Docker** installed and running
3. **Required Python packages**: `requests`, `urllib3`
4. **OpenSSL** (optional, for certificate validation)

## Quick Start

### Option 1: Using the Shell Script (Recommended)

```bash
# Run all tests
./test_vista3d.sh

# Run with verbose output
./test_vista3d.sh --verbose

# Run quick tests only
./test_vista3d.sh --quick

# Check dependencies
./test_vista3d.sh --check-deps

# Create test file and run tests
./test_vista3d.sh --create-test-file
```

### Option 2: Using Python Script Directly

```bash
# Run all tests
python3 test_vista3d_services.py

# Run with verbose output
python3 test_vista3d_services.py --verbose

# Create test file and run tests
python3 test_vista3d_services.py --create-test-file
```

## Test Details

### 1. Docker Availability Test
- Checks if Docker daemon is running
- Verifies Docker version and accessibility
- **Required for**: All other tests

### 2. Outputs Directory Structure Test
- Verifies `outputs/`, `outputs/certs/`, and `outputs/nifti/` directories exist
- **Required for**: SSL certificates and file serving tests

### 3. SSL Certificates Test
- Checks if `server.crt` and `server.key` files exist
- Validates certificate format using OpenSSL
- **Required for**: HTTPS image server functionality

### 4. Image Server Process Test
- Verifies `image_server.py` process is running
- Checks process IDs and status
- **Required for**: Image server accessibility

### 5. Image Server Endpoint Test
- Tests HTTPS connectivity to `https://localhost:8888`
- Handles self-signed certificate warnings gracefully
- **Required for**: File serving functionality

### 6. Image Server File Serving Test
- Creates a test file if needed
- Verifies files can be accessed via HTTP
- **Required for**: Vista3D to access image files

### 7. Vista3D Container Status Test
- Checks if Vista3D Docker container is running
- Verifies container name, status, and port mapping
- **Required for**: Vista3D service accessibility

### 8. Vista3D Endpoint Test
- Tests HTTP connectivity to `http://localhost:8000`
- Attempts to access health endpoint
- **Required for**: Vista3D API functionality

### 9. Communication Test
- Verifies Vista3D can communicate with external image server
- Tests both `localhost` and `host.docker.internal` access
- **Required for**: End-to-end functionality

## Output and Results

### Success Example
```
🚀 Starting Vista3D Services Test Suite...
============================================================

📋 Running: Docker Availability
🔍 Testing Docker availability...
✅ Docker is available: Docker version 20.10.21, build baeda1f

📋 Running: Outputs Directory Structure
🔍 Testing outputs directory structure...
✅ Outputs directory structure is correct

📋 Running: SSL Certificates
🔍 Testing SSL certificates...
✅ SSL certificates exist and are valid

📋 Running: Image Server Process
🔍 Testing external image server process...
✅ External image server process is running (PIDs: 12345)

📋 Running: Image Server Endpoint
🔍 Testing external image server endpoint accessibility...
✅ External image server endpoint is accessible

📋 Running: Image Server File Serving
🔍 Testing image server file serving capability...
✅ Image server can serve files properly

📋 Running: Vista3D Container Status
🔍 Testing Vista3D container status...
✅ Vista3D container is running

📋 Running: Vista3D Endpoint
🔍 Testing Vista3D endpoint accessibility...
✅ Vista3D health endpoint is accessible

📋 Running: Vista3D ↔ Image Server Communication
🔍 Testing Vista3D ↔ Image Server communication...
✅ Vista3D can communicate with external image server

============================================================
📊 TEST RESULTS SUMMARY
============================================================
✅ PASS - Docker Available
✅ PASS - Outputs Directory Structure
✅ PASS - Ssl Certificates Valid
✅ PASS - Image Server Process Running
✅ PASS - Image Server Endpoint Accessible
✅ PASS - Image Server File Serving
✅ PASS - Vista3d Container Running
✅ PASS - Vista3d Endpoint Accessible
✅ PASS - Vista3d To Image Server Communication
------------------------------------------------------------
Total Tests: 9
Passed: 9
Failed: 0
Success Rate: 100.0%

🎉 All tests passed! Vista3D services are running correctly.
============================================================
```

### Failure Example
```
📋 Running: Vista3D Container Status
🔍 Testing Vista3D container status...
⚠️  Vista3D container is not running

📋 Running: Vista3D Endpoint
🔍 Testing Vista3D endpoint accessibility...
❌ Cannot connect to Vista3D endpoint - connection refused

============================================================
📊 TEST RESULTS SUMMARY
============================================================
✅ PASS - Docker Available
✅ PASS - Outputs Directory Structure
✅ PASS - Ssl Certificates Valid
✅ PASS - Image Server Process Running
✅ PASS - Image Server Endpoint Accessible
✅ PASS - Image Server File Serving
❌ FAIL - Vista3d Container Running
❌ FAIL - Vista3d Endpoint Accessible
❌ FAIL - Vista3d To Image Server Communication
------------------------------------------------------------
Total Tests: 9
Passed: 6
Failed: 3
Success Rate: 66.7%

⚠️  3 test(s) failed. Please check the issues above.
============================================================

🔧 SUGGESTED FIXES
============================================================
• Vista3D container is not running. Start it with: python3 utils/vista3d.py
============================================================
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Docker Not Running
```bash
# Start Docker service
sudo systemctl start docker

# Check Docker status
sudo systemctl status docker

# Verify Docker is accessible
docker info
```

#### 2. Image Server Not Running
```bash
# Start image server manually
python3 utils/image_server.py

# Check if process is running
pgrep -f image_server.py

# View image server logs
tail -f /tmp/image_server.log
```

#### 3. Vista3D Container Not Running
```bash
# Start Vista3D container
python3 utils/vista3d.py

# Check container status
docker ps -a | grep vista3d

# View container logs
docker logs vista3d
```

#### 4. SSL Certificate Issues
```bash
# Remove existing certificates
rm -f outputs/certs/server.crt outputs/certs/server.key

# Restart image server to regenerate certificates
pkill -f image_server.py
python3 utils/image_server.py
```

#### 5. Port Conflicts
```bash
# Check what's using the ports
sudo netstat -tlnp | grep :8000
sudo netstat -tlnp | grep :8888

# Kill conflicting processes
sudo fuser -k 8000/tcp
sudo fuser -k 8888/tcp
```

### Dependency Installation

If you're missing required Python packages:

```bash
# Install requests and urllib3
pip3 install requests urllib3

# Or use the dependency checker
./test_vista3d.sh --check-deps
```

## Integration with CI/CD

The test script returns appropriate exit codes for CI/CD integration:

- **Exit code 0**: All tests passed
- **Exit code 1**: One or more tests failed

Example CI/CD usage:
```bash
# Run tests in CI pipeline
if ./test_vista3d.sh; then
    echo "✅ All tests passed - deploying Vista3D services"
    # Continue with deployment
else
    echo "❌ Tests failed - aborting deployment"
    exit 1
fi
```

## Monitoring and Automation

### Continuous Monitoring
```bash
# Run tests every 5 minutes
while true; do
    ./test_vista3d.sh --quick
    sleep 300
done
```

### Log Analysis
```bash
# View test results in logs
tail -f start_vista.log

# Check for specific test failures
grep "❌" start_vista.log
```

## Advanced Usage

### Custom Test Configuration
You can modify the test script to:
- Change test timeouts
- Add custom health checks
- Modify endpoint URLs
- Add new test categories

### Extending Tests
To add new tests:
1. Create a new test method in `Vista3DServicesTester` class
2. Add it to the `tests` list in `run_all_tests()`
3. Update the test results dictionary

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Run with `--verbose` flag for detailed output
3. Check the logs in `start_vista.log`
4. Verify all prerequisites are met

## License

This test suite is part of the Vista3D project. Please refer to the main project license for usage terms.
