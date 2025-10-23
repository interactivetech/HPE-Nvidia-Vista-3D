# Kubernetes Deployment

This folder contains scripts and configurations related to deploying the HPE-Nvidia-Vista-3D application to Kubernetes, specifically MicroK8s.

## Scripts

- `build_and_push_docker.sh`: Builds and pushes the Docker images for the `frontend` and `image-server` to Docker Hub.
- `deploy_frontend.sh`: Automates the deployment process for the `frontend` and `image-server` to a Kubernetes cluster. This script:
    1. Builds and pushes the Docker images using `build_and_push_docker.sh`.
    2. Upgrades the Helm release for `vista3d`.
    3. Deletes the existing `frontend` pod to force Kubernetes to pull the new image.
    4. Watches for the new `frontend` pod to become ready.

## Usage

To deploy the `frontend` and `image-server` with the latest changes, run the `deploy_frontend.sh` script:

```bash
./kube/deploy_frontend.sh
```

## MicroK8s Configuration

If you are using MicroK8s, ensure your `kubectl` is configured correctly. You can export the MicroK8s configuration and set the `KUBECONFIG` environment variable:

```bash
microk8s config > ~/.kube/config
export KUBECONFIG=~/.kube/config
```

To make the `KUBECONFIG` environment variable persistent, add the `export` command to your shell's configuration file (e.g., `~/.bashrc` or `~/.zshrc`).

## Accessing the Frontend

Once the `frontend` pod is running, you can access the web interface by port-forwarding:

```bash
microk8s kubectl port-forward service/vista3d-frontend 8501:8501
```

Then, open your browser to `http://localhost:8501`.