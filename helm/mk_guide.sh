#!/bin/bash

# Guide for starting/stopping the vista3d frontend

set -e

# --- Functions ---

start() {
    echo "Checking minikube status..."
    if minikube status --format='{{.Host}}' 2>/dev/null | grep -q "Running"; then
        echo "Minikube is already running ✓"
    else
        echo "Starting minikube..."
        # Clean up any corrupted minikube state first
        echo "Cleaning up any corrupted minikube state..."
        minikube delete 2>/dev/null || true
        # Clean up problematic temp files
        sudo rm -rf /var/folders/zz/zyxvpxvq6csfxvn_n0000000000000/T/juju-* 2>/dev/null || true
        sudo rm -rf /var/folders/zz/zyxvpxvq6csfxvn_n0000000000000/T/minikube* 2>/dev/null || true
        
        echo "Starting fresh minikube instance..."
        minikube start
    fi
    
    # Check if the helm release already exists
    if helm list -q | grep -q "^vista3d-frontend$"; then
        echo "
vista3d-frontend release already exists. Upgrading..."
        helm upgrade vista3d-frontend ./vista3d -f vista3d/values-frontend-imageserver.yaml
    else
        echo "
Installing frontend and image server release (vista3d-frontend)..."
        helm install vista3d-frontend ./vista3d -f vista3d/values-frontend-imageserver.yaml
    fi
    
    echo "
Waiting for frontend deployment to be ready..."
    echo "(Note: First-time startup may take 1-2 minutes for storage provisioning and image pulls)"
    kubectl wait --for=condition=available deployment/vista3d-frontend-frontend --timeout=300s
    echo "
Waiting for image server deployment to be ready..."
    kubectl wait --for=condition=available deployment/vista3d-frontend-image-server --timeout=300s

    echo "
Pods for vista3d-frontend release:"
    kubectl get pods -l app.kubernetes.io/instance=vista3d-frontend
    echo "
Services for vista3d-frontend release:"
    kubectl get services -l app.kubernetes.io/instance=vista3d-frontend
    
    echo "
Setting up port forwarding..."
    echo "  - Frontend GUI: http://localhost:8501"
    echo "  - Image Server: http://localhost:8888"
    
    # Kill any existing port-forward processes on these ports
    pkill -f "port-forward.*vista3d-frontend-frontend" 2>/dev/null || true
    pkill -f "port-forward.*vista3d-frontend-image-server" 2>/dev/null || true
    
    # Start port forwarding in the background
    kubectl port-forward service/vista3d-frontend-frontend 8501:8501 > /dev/null 2>&1 &
    kubectl port-forward service/vista3d-frontend-image-server 8888:8888 > /dev/null 2>&1 &
    
    # Give port-forward a moment to start
    sleep 2
    
    echo "
✅ Vista3D is ready!"
    echo "   Frontend: http://localhost:8501"
    echo "   Image Server: http://localhost:8888"
    echo "
To stop port forwarding, run: pkill -f 'port-forward.*vista3d-frontend'"
}

stop() {
    echo "Stopping port forwarding..."
    pkill -f "port-forward.*vista3d-frontend" 2>/dev/null || true
    
    echo "Uninstalling helm release..."
    helm uninstall vista3d-frontend || true
    
    echo "
Stopping minikube..."
    minikube stop 2>/dev/null || true
    
    echo "
✅ Vista3D stopped successfully"
}

status() {
    echo "=== Minikube Status ==="
    minikube status || echo "Minikube is not running"
    
    echo "
=== Helm Releases ==="
    helm list | grep vista3d || echo "No vista3d releases found"
    
    echo "
=== Pods ==="
    kubectl get pods -l app.kubernetes.io/instance=vista3d-frontend 2>/dev/null || echo "No pods found"
    
    echo "
=== Services ==="
    kubectl get services -l app.kubernetes.io/instance=vista3d-frontend 2>/dev/null || echo "No services found"
    
    echo "
=== Port Forwarding ==="
    pgrep -fl "port-forward.*vista3d-frontend" || echo "No port forwarding active"
    
    echo "
=== Access URLs ==="
    if pgrep -f "port-forward.*vista3d-frontend-frontend" > /dev/null; then
        echo "✅ Frontend: http://localhost:8501"
    else
        echo "❌ Frontend: Not accessible (no port forwarding)"
    fi
    
    if pgrep -f "port-forward.*vista3d-frontend-image-server" > /dev/null; then
        echo "✅ Image Server: http://localhost:8888"
    else
        echo "❌ Image Server: Not accessible (no port forwarding)"
    fi
}

usage() {
    echo "Usage: $0 {start|stop|status}"
    echo "  start:  Starts minikube and deploys the frontend and image server release."
    echo "  stop:   Uninstalls the frontend and image server release and stops minikube."
    echo "  status: Shows the current status of all Vista3D components."
}

# --- Main Logic ---

if [ -z "$1" ]; then
    usage
    exit 1
fi

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    status)
        status
        ;;
    *)
        usage
        exit 1
        ;;
esac