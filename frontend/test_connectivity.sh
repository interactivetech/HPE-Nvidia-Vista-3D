#!/bin/bash
# Vista3D Connectivity Test Script
# Tests all connections needed for Vista3D to work

set +e  # Don't exit on errors

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

print_header() {
    echo -e "\n${BOLD}${BLUE}======================================================================${NC}"
    echo -e "${BOLD}${BLUE}$1${NC}"
    echo -e "${BOLD}${BLUE}======================================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

PASSED=0
FAILED=0

# Load environment
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

print_info "Vista3D Connectivity Test"
print_info "Running inside container environment\n"

# Test 1: Environment Variables
print_header "Test 1: Environment Variables"
if [ -n "$VISTA3D_SERVER" ]; then
    print_success "VISTA3D_SERVER = $VISTA3D_SERVER"
    ((PASSED++))
else
    print_error "VISTA3D_SERVER not set"
    ((FAILED++))
fi

if [ -n "$VISTA3D_IMAGE_SERVER_URL" ]; then
    print_success "VISTA3D_IMAGE_SERVER_URL = $VISTA3D_IMAGE_SERVER_URL"
    ((PASSED++))
else
    print_error "VISTA3D_IMAGE_SERVER_URL not set"
    ((FAILED++))
fi

# Test 2: Frontend -> Backend
print_header "Test 2: Frontend -> Vista3D Backend"
print_info "Testing: $VISTA3D_SERVER/v1/vista3d/info"

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 "$VISTA3D_SERVER/v1/vista3d/info" 2>&1)

if [ "$HTTP_CODE" = "200" ]; then
    print_success "Backend is reachable! HTTP $HTTP_CODE"
    ((PASSED++))
else
    print_error "Backend not reachable! HTTP $HTTP_CODE"
    print_warning "Check: SSH tunnel running? Backend running on Ubuntu?"
    ((FAILED++))
fi

# Test 3: Image Server
print_header "Test 3: Local Image Server"
IMAGE_SERVER=${IMAGE_SERVER:-http://localhost:8888}
print_info "Testing: $IMAGE_SERVER/health"

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$IMAGE_SERVER/health" 2>&1)

if [ "$HTTP_CODE" = "200" ]; then
    print_success "Image server is reachable! HTTP $HTTP_CODE"
    ((PASSED++))
else
    print_error "Image server not reachable! HTTP $HTTP_CODE"
    ((FAILED++))
fi

# Test 4: Backend -> Image Server (CRITICAL TEST)
print_header "Test 4: Backend -> Image Server (CRITICAL)"
print_info "Vista3D backend will fetch images from: $VISTA3D_IMAGE_SERVER_URL"
print_info "This requires SSH reverse tunnel: -R 8888:0.0.0.0:8888"

# Find a test file
OUTPUT_FOLDER=${OUTPUT_FOLDER:-/app/output}
TEST_FILE=$(find "$OUTPUT_FOLDER" -name "*.nii.gz" -type f | head -1)

if [ -z "$TEST_FILE" ]; then
    print_warning "No test NIfTI files found in $OUTPUT_FOLDER"
else
    # Get relative path
    REL_PATH=${TEST_FILE#$OUTPUT_FOLDER/}
    TEST_URL="$VISTA3D_IMAGE_SERVER_URL/output/$REL_PATH"
    
    print_info "Test file: $(basename $TEST_FILE)"
    print_info "Image URL: $TEST_URL"
    print_info "Sending test inference request..."
    
    # Create test payload
    PAYLOAD='{"image":"'$TEST_URL'","prompts":{"labels":["liver"]}}'
    
    RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" --connect-timeout 30 \
        -X POST "$VISTA3D_SERVER/v1/vista3d/inference" \
        -H "Content-Type: application/json" \
        -d "$PAYLOAD" 2>&1)
    
    HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
    BODY=$(echo "$RESPONSE" | sed '/HTTP_CODE:/d')
    
    if [ "$HTTP_CODE" = "200" ]; then
        print_success "Backend successfully fetched the image!"
        print_success "Reverse SSH tunnel is working!"
        ((PASSED++))
    else
        print_error "Backend inference failed! HTTP $HTTP_CODE"
        if echo "$BODY" | grep -q "Failed to fetch image"; then
            print_error ""
            print_error "🚨 PROBLEM: Backend cannot fetch images from image server!"
            print_error ""
            print_warning "Possible causes:"
            print_warning "  1. SSH reverse tunnel not active: -R 8888:0.0.0.0:8888"
            print_warning "  2. Image server not accessible from Ubuntu"
            print_warning "  3. VISTA3D_IMAGE_SERVER_URL incorrect"
            
            if echo "$BODY" | grep -q "host.docker.internal"; then
                print_error "Backend is using 'host.docker.internal' - won't work on Ubuntu!"
                print_info "Fix: VISTA3D_IMAGE_SERVER_URL=http://localhost:8888"
            fi
        fi
        echo "$BODY" | head -5
        ((FAILED++))
    fi
fi

# Test 5: SSH Tunnel
print_header "Test 5: SSH Tunnel Status"
if ps aux | grep -q "[s]sh.*8000.*8888"; then
    print_success "SSH tunnel process is running"
    ps aux | grep "[s]sh.*8000.*8888"
    ((PASSED++))
else
    print_error "No SSH tunnel found!"
    print_info "Start: ssh -L 8000:localhost:8000 -R 8888:0.0.0.0:8888 user@server"
    ((FAILED++))
fi

# Summary
print_header "SUMMARY"
echo -e "\nTests: ${GREEN}$PASSED passed${NC}, ${RED}$FAILED failed${NC}\n"

if [ $FAILED -eq 0 ]; then
    print_success "ALL TESTS PASSED! Vista3D should work."
    exit 0
else
    print_error "SOME TESTS FAILED. Fix issues above."
    exit 1
fi

