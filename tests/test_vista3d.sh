#!/bin/bash

# Vista3D Services Test Script Wrapper
# This script provides an easy way to test Vista3D Docker server and external image server

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    cat << EOF
Vista3D Services Test Script

Usage: $0 [OPTIONS]

OPTIONS:
    -h, --help              Show this help message
    -v, --verbose           Run tests with verbose output
    -c, --create-test-file  Create test file before running tests
    -q, --quick             Run only essential tests (faster)
    --check-deps            Check if required dependencies are installed

EXAMPLES:
    $0                      # Run all tests
    $0 --verbose            # Run with verbose output
    $0 --create-test-file  # Create test file and run tests
    $0 --quick             # Run quick test suite
    $0 --check-deps        # Check dependencies only

DESCRIPTION:
    This script tests that:
    • Vista3D Docker server is running and accessible
    • External HTTPS image server is running and accessible
    • Both services can communicate with each other
    • The image server can serve files properly

    The script will provide detailed feedback and suggestions for any issues found.
EOF
}

# Function to check dependencies
check_dependencies() {
    print_status "Checking required dependencies..."
    
    # Check Python
    if command -v python3 &> /dev/null; then
        python_version=$(python3 --version 2>&1)
        print_success "Python3 found: $python_version"
    else
        print_error "Python3 is not installed"
        return 1
    fi
    
    # Check required Python packages
    print_status "Checking Python packages..."
    
    # Check requests
    if python3 -c "import requests" 2>/dev/null; then
        print_success "requests package is available"
    else
        print_warning "requests package not found. Installing..."
        pip3 install requests urllib3
    fi
    
    # Check Docker
    if command -v docker &> /dev/null; then
        docker_version=$(docker --version 2>&1)
        print_success "Docker found: $docker_version"
        
        # Check if Docker daemon is running
        if docker info &> /dev/null; then
            print_success "Docker daemon is running"
        else
            print_error "Docker daemon is not running"
            print_status "Start Docker with: sudo systemctl start docker"
            return 1
        fi
    else
        print_error "Docker is not installed"
        return 1
    fi
    
    # Check openssl
    if command -v openssl &> /dev/null; then
        print_success "OpenSSL found"
    else
        print_warning "OpenSSL not found (needed for SSL certificate validation)"
    fi
    
    print_success "All dependencies checked successfully!"
    return 0
}

# Function to run quick tests
run_quick_tests() {
    print_status "Running quick test suite..."
    
    # Check Docker availability
    if ! docker info &> /dev/null; then
        print_error "Docker is not available"
        return 1
    fi
    
    # Check Vista3D container
    if docker ps --filter name=vista3d --format "{{.Names}}" | grep -q vista3d; then
        print_success "Vista3D container is running"
    else
        print_warning "Vista3D container is not running"
    fi
    
    # Check image server process
    if pgrep -f "image_server.py" &> /dev/null; then
        print_success "Image server process is running"
    else
        print_warning "Image server process is not running"
    fi
    
    # Quick connectivity test
    if curl -s -k https://localhost:8888/ &> /dev/null; then
        print_success "Image server is accessible"
    else
        print_warning "Image server is not accessible"
    fi
    
    if curl -s http://localhost:8000/ &> /dev/null; then
        print_success "Vista3D server is accessible"
    else
        print_warning "Vista3D server is not accessible"
    fi
    
    print_success "Quick tests completed!"
}

# Main script logic
main() {
    local verbose=false
    local create_test_file=false
    local quick_mode=false
    local check_deps=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -v|--verbose)
                verbose=true
                shift
                ;;
            -c|--create-test-file)
                create_test_file=true
                shift
                ;;
            -q|--quick)
                quick_mode=true
                shift
                ;;
            --check-deps)
                check_deps=true
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Check dependencies if requested
    if [[ "$check_deps" == true ]]; then
        check_dependencies
        exit $?
    fi
    
    # Check if test script exists
    if [[ ! -f "test_vista3d_services.py" ]]; then
        print_error "Test script 'test_vista3d_services.py' not found in current directory"
        exit 1
    fi
    
    # Run quick tests if requested
    if [[ "$quick_mode" == true ]]; then
        run_quick_tests
        exit $?
    fi
    
    # Build command for Python script
    local cmd="python3 test_vista3d_services.py"
    
    if [[ "$verbose" == true ]]; then
        cmd="$cmd --verbose"
    fi
    
    if [[ "$create_test_file" == true ]]; then
        cmd="$cmd --create-test-file"
    fi
    
    # Run the test script
    print_status "Starting Vista3D services test suite..."
    print_status "Command: $cmd"
    echo
    
    # Execute the command
    if eval "$cmd"; then
        print_success "Test suite completed successfully!"
        exit 0
    else
        print_error "Test suite failed!"
        exit 1
    fi
}

# Run main function with all arguments
main "$@"
