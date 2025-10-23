#!/bin/bash

# Script to deploy the frontend and image-server to MicroK8s

set -e # Exit on error

echo "=== Building and pushing Docker images ==="
VERSION=$(kube/build_and_push_docker.sh)
echo "Captured VERSION: ${VERSION}"

if helm status vista3d &> /dev/null; then
    echo "=== Upgrading Helm release ==="
    helm upgrade vista3d ./helm/vista3d \
        --set frontend.image.tag="${VERSION}" \
        --set imageServer.image.tag="${VERSION}"
else
    echo "=== Installing Helm release ==="
    helm install vista3d ./helm/vista3d \
        --set frontend.image.tag="${VERSION}" \
        --set imageServer.image.tag="${VERSION}"
fi

echo "=== Deleting frontend pod to force image re-pull ==="
# This ensures the new image is pulled even if the tag is 'latest' and pullPolicy is IfNotPresent
microk8s kubectl delete pod -l app.kubernetes.io/component=frontend

echo "=== Deployment process complete ==="
echo "Please monitor the pod status manually by running: microk8s kubectl get pods -l app.kubernetes.io/component=frontend --watch"

echo "Once the pod is running, you can port-forward to access the web interface:"
echo "microk8s kubectl port-forward service/vista3d-frontend 8501:8501"