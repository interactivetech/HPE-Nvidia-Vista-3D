#!/bin/bash

# Guide for starting/stopping the vista3d frontend

set -e

# --- Functions ---

start() {
    echo "Starting minikube..."
    minikube start
    
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
To access the frontend service, run this command in a separate terminal:"
    echo "minikube service --url vista3d-frontend-frontend"
    echo "
To access the image server service, run this command in a separate terminal:"
    echo "minikube service --url vista3d-frontend-image-server"
}

stop() {
    echo "Uninstalling helm release..."
    helm uninstall vista3d-frontend
    echo "
Stopping minikube..."
    minikube stop
}

usage() {
    echo "Usage: $0 {start|stop}"
    echo "  start: Starts minikube and deploys the frontend and image server release."
    echo "  stop:  Uninstalls the frontend and image server release and stops minikube."
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
    *)
        usage
        exit 1
        ;;
esac